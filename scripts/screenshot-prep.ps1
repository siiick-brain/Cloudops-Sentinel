$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$previousMode = [Environment]::GetEnvironmentVariable("INTEGRATION_MODE", "Process")
$env:INTEGRATION_MODE = "mock"
$loadgen = $null

try {
    Write-Output "Checking Docker storage configuration"
    & "$PSScriptRoot\check-docker-storage.ps1"

    docker compose up -d --build
    if ($LASTEXITCODE -ne 0) { throw "Compose start failed" }
    Write-Output "Waiting for API readiness"
    python scripts/wait_for_stack.py
    if ($LASTEXITCODE -ne 0) { throw "Stack did not become healthy" }
    Write-Output "Sending steady traffic"
    $loadgen = Start-Process -FilePath python -ArgumentList "scripts/loadgen.py" -WorkingDirectory $root -PassThru
    Write-Output "Triggering a latency scenario"
    python chaos/run.py latency
    if ($LASTEXITCODE -ne 0) { throw "Chaos scenario failed" }
    Stop-Process -Id $loadgen.Id -ErrorAction SilentlyContinue
    $loadgen = $null
    foreach ($cue in @(
        "P2-01", "P2-02", "P2-03", "P2-04", "P2-05", "P2-06", "P2-07",
        "P2-08", "P2-09", "P2-10", "P2-11", "P2-12", "P2-13", "P2-14", "P2-15"
    )) {
        Write-Output "Now capture $cue using docs/screenshots.md."
    }

    docker compose down
    if ($LASTEXITCODE -ne 0) { throw "Local demo stack stop failed" }
    Write-Output "Starting the local production-style deployment for P2-16 and P2-17"
    docker compose -p cloudops-sentinel-prod -f compose.prod.yml up -d --build
    if ($LASTEXITCODE -ne 0) { throw "Production-style Compose start failed" }
    & "$PSScriptRoot\verify-deployment.ps1"
    Write-Output "Now capture P2-16 from docs/deployment-verification.md."
    Write-Output "Now capture P2-17 at https://localhost. Keep localhost visible."
}
finally {
    if ($null -ne $loadgen -and -not $loadgen.HasExited) {
        Stop-Process -Id $loadgen.Id -ErrorAction SilentlyContinue
    }
    if ($null -eq $previousMode) {
        Remove-Item Env:INTEGRATION_MODE -ErrorAction SilentlyContinue
    } else {
        $env:INTEGRATION_MODE = $previousMode
    }
}
