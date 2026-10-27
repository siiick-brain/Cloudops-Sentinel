$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (-not (Test-Path .env)) {
    Write-Output "Not verified: create .env with Jira Cloud and Slack credentials, set INTEGRATION_MODE=real, then rerun."
    exit 2
}
$config = (Get-Content .env) -join "`n"
if ($config -notmatch "(?m)^INTEGRATION_MODE=real$") {
    Write-Output "Not verified: set INTEGRATION_MODE=real in .env before a live run."
    exit 2
}
foreach ($key in @("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY", "SLACK_WEBHOOK_URL")) {
    if ($config -notmatch "(?m)^$key=.+$") {
        Write-Output "Not verified: .env must define $key before a live run."
        exit 2
    }
}
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw "Compose start failed" }
python chaos/run.py latency
if ($LASTEXITCODE -ne 0) { throw "Live chaos scenario failed" }
python scripts/live_result.py
if ($LASTEXITCODE -ne 0) { throw "Live verification is incomplete" }
