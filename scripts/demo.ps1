$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Create the project virtual environment before running the demo."
}

Write-Output "Checking Docker storage configuration"
& "$PSScriptRoot\check-docker-storage.ps1"

Write-Output "1/6 Starting services"
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw "Compose start failed" }

Write-Output "2/6 Waiting for API readiness"
& $python scripts/wait_for_stack.py
if ($LASTEXITCODE -ne 0) { throw "Stack did not become healthy" }

Write-Output "3/6 Sending service traffic"
Invoke-RestMethod http://localhost:8000/orders/demo-sku -TimeoutSec 10 | Out-Null

Write-Output "4/6 Checking the cross-service trace"
& $python scripts/check_trace.py
if ($LASTEXITCODE -ne 0) { throw "Trace verification failed" }

Write-Output "5/6 Triggering a latency chaos scenario"
& $python chaos/run.py latency
if ($LASTEXITCODE -ne 0) { throw "Chaos scenario failed" }

Write-Output "6/6 Checking stack health"
docker compose ps
if ($LASTEXITCODE -ne 0) { throw "Compose status check failed" }
