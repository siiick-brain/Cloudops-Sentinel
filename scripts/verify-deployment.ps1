$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$checks = [System.Collections.Generic.List[object]]::new()
$failed = $false
$curl = (Get-Command curl.exe -ErrorAction Stop).Source

function Add-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail
    )
    $script:checks.Add([pscustomobject]@{
        Name = $Name
        Status = if ($Passed) { "Passed" } else { "Failed" }
        Detail = $Detail
    })
    if (-not $Passed) {
        $script:failed = $true
    }
}

$https = & $curl --silent --show-error --insecure --tlsv1.3 --tls-max 1.3 --max-time 10 --output NUL --write-out "%{http_code}" https://localhost/
$httpsExit = $LASTEXITCODE
$httpsCode = [string]$https
Add-Check "HTTPS response" ($httpsExit -eq 0 -and $httpsCode -match '^[23]\d\d$') "HTTP $httpsCode"
Add-Check "TLS version" ($httpsExit -eq 0) "TLS 1.3 only handshake succeeded"

$http = & $curl --silent --show-error --max-time 10 --output NUL --write-out "%{http_code}|%{redirect_url}" http://localhost/
$httpExit = $LASTEXITCODE
$httpParts = $http -split '\|', 2
$httpCode = if ($httpParts.Count -gt 0) { $httpParts[0] } else { "" }
$redirectUrl = if ($httpParts.Count -gt 1) { $httpParts[1] } else { "" }
Add-Check "HTTP redirect" ($httpExit -eq 0 -and $httpCode -in @("301", "308") -and $redirectUrl.StartsWith("https://localhost/")) "$httpCode to $redirectUrl"

$headers = & $curl --silent --show-error --insecure --max-time 10 --dump-header - --output NUL https://localhost/
$headerChecks = @(
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy"
)
foreach ($header in $headerChecks) {
    $present = $headers | Where-Object { $_ -match ("(?i)^" + [regex]::Escape($header) + ":") }
    Add-Check "Header $header" ($null -ne $present) $(if ($present) { "Present" } else { "Missing" })
}

$ports = @(9090, 9093, 3200, 8000, 8001, 8090, 8091, 8092, 9100, 8085, 8474, 4317, 4318, 3000)
foreach ($port in $ports) {
    $open = Test-NetConnection -ComputerName 127.0.0.1 -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet -ErrorAction SilentlyContinue
    Add-Check "Port $port closed" (-not $open) $(if ($open) { "Open" } else { "Closed" })
}

$chaosCode = & $curl --silent --show-error --insecure --max-time 10 --output NUL --write-out "%{http_code}" https://localhost/chaos
$chaosExit = $LASTEXITCODE
Add-Check "Chaos path blocked" ($chaosExit -eq 0 -and $chaosCode -eq "404") "HTTP $chaosCode"
$adminCode = & $curl --silent --show-error --insecure --max-time 10 --output NUL --write-out "%{http_code}" https://localhost/admin
$adminExit = $LASTEXITCODE
Add-Check "Admin path blocked" ($adminExit -eq 0 -and $adminCode -eq "404") "HTTP $adminCode"
$grafanaCode = & $curl --silent --show-error --insecure --max-time 10 --output NUL --write-out "%{http_code}" https://localhost/api/user
$grafanaExit = $LASTEXITCODE
Add-Check "Grafana authentication required" ($grafanaExit -eq 0 -and $grafanaCode -eq "401") "HTTP $grafanaCode"

$date = [DateTime]::UtcNow.ToString("yyyy-MM-dd")
$lines = @(
    "# Deployment verification",
    "",
    "Date (UTC): $date",
    "",
    "| Check | Status | Result |",
    "|---|---|---|"
)
foreach ($check in $checks) {
    $lines += "| $($check.Name) | $($check.Status) | $($check.Detail) |"
}
Set-Content -LiteralPath (Join-Path $root "docs\deployment-verification.md") -Value $lines -Encoding utf8

foreach ($check in $checks) {
    Write-Output ("{0}: {1} ({2})" -f $check.Name, $check.Status, $check.Detail)
}

if ($failed) {
    throw "Deployment verification failed. See docs/deployment-verification.md."
}
