$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Create the project virtual environment and install requirements-dev.txt before capturing."
}

$script:reported = @{}
$script:failed = $false
$previousMode = [Environment]::GetEnvironmentVariable("INTEGRATION_MODE", "Process")
$stdoutFile = [System.IO.Path]::GetTempFileName()
$stderrFile = [System.IO.Path]::GetTempFileName()
$chaosProcess = $null
$script:chaosStarted = $false

function Write-CaptureResult {
    param(
        [string]$Image,
        [string]$Status,
        [string]$Reason
    )
    $script:reported[$Image] = $true
    if ($Status -eq "Failed") {
        $script:failed = $true
    }
    Write-Output ("{0}: {1} ({2})" -f $Status, $Image, $Reason)
}

function Invoke-CaptureModule {
    param(
        [string]$ScriptName,
        [string[]]$ExpectedImages,
        [string[]]$Arguments = @()
    )
    $parsed = @{}
    $lines = & $python "scripts\$ScriptName" @Arguments 2>$null
    $exitCode = $LASTEXITCODE
    foreach ($line in $lines) {
        try {
            $item = $line | ConvertFrom-Json -ErrorAction Stop
            $parsed[$item.image] = $true
            Write-CaptureResult $item.image $item.status $item.reason
        } catch {
            continue
        }
    }
    foreach ($image in $ExpectedImages) {
        if (-not $parsed.ContainsKey($image)) {
            $reason = if ($exitCode -eq 0) { "Capture script returned no result" } else { "Capture script failed" }
            Write-CaptureResult $image "Failed" $reason
        }
    }
}

function Invoke-TerminalCapture {
    param(
        [string]$Image,
        [string]$Command,
        [int]$Timeout = 300
    )
    $output = Join-Path "docs\images" $Image
    $renderOutput = & $python "scripts\terminal_shot.py" --output $output --command $Command --timeout $Timeout 2>&1
    $exitCode = $LASTEXITCODE
    $skipLine = $renderOutput | Where-Object { [string]$_ -like "Skipped:*" } | Select-Object -First 1
    if ($exitCode -eq 0 -and $null -ne $skipLine) {
        Write-CaptureResult $Image "Skipped" ([string]$skipLine -replace '^Skipped:\s*', '')
        return
    }
    if ($exitCode -eq 0 -and (Test-Path -LiteralPath (Join-Path $root $output))) {
        $commandExitCode = $null
        foreach ($line in $renderOutput) {
            if ([string]$line -match "with command exit code (-?\d+)\.") {
                $commandExitCode = [int]$matches[1]
                break
            }
        }
        if ($null -eq $commandExitCode) {
            Write-CaptureResult $Image "Captured" "Rendered from captured command output; exit status is shown in the image"
        } elseif ($commandExitCode -eq 0) {
            Write-CaptureResult $Image "Captured" "Rendered from captured command output; command exited with code 0"
        } else {
            Write-CaptureResult $Image "Captured" "Rendered failed command output with exit code $commandExitCode"
        }
    } else {
        Write-CaptureResult $Image "Failed" "Terminal output could not be rendered within the image size limit"
    }
}

try {
    $env:INTEGRATION_MODE = "mock"
    try {
        Invoke-WebRequest -Uri "http://localhost:8000/readyz" -TimeoutSec 3 -UseBasicParsing | Out-Null
        Start-Process -FilePath $python `
            -ArgumentList @("chaos/run.py", "latency", "--duration-seconds", "90") `
            -WorkingDirectory $root `
            -WindowStyle Hidden `
            -RedirectStandardOutput $stdoutFile `
            -RedirectStandardError $stderrFile `
            -PassThru | ForEach-Object { $script:chaosProcess = $_ }
        Start-Sleep -Seconds 3
        if ($null -ne $script:chaosProcess -and -not $script:chaosProcess.HasExited) {
            $script:chaosStarted = $true
        }
    } catch {
        $script:chaosStarted = $false
    }

    Invoke-CaptureModule "capture_pages.py" @(
        "grafana-golden-signals.png",
        "grafana-slo-error-budget.png",
        "grafana-node-container-health.png",
        "grafana-distributed-traces.png",
        "P2-17-grafana-login.png",
        "grafana-exemplar.png",
        "prometheus-alert-rules.png",
        "prometheus-cpu-alert-firing.png",
        "prometheus-targets-up.png",
        "prometheus-container-cpu-metrics.png",
        "alertmanager-group.png",
        "tempo-trace.png"
    )
    Invoke-CaptureModule "capture_integrations.py" @(
        "slack-alert.png",
        "slack-resolved.png",
        "jira-ticket.png",
        "jira-resolved.png"
    )
    Invoke-CaptureModule "capture_github.py" @(
        "github-repo.png",
        "github-actions.png",
        "github-runbook.png",
        "github-contributors.png"
    )
    Invoke-CaptureModule "record_demo.py" @("demo.gif") @("--scenario-running")

    if ($script:chaosProcess) {
        try {
            Wait-Process -Id $script:chaosProcess.Id -Timeout 360 -ErrorAction Stop
        } catch {
            Write-Warning "The screenshot latency scenario has not completed. It was not stopped."
        }
    }

    Invoke-TerminalCapture "compose-services.png" "docker compose -p cloudops-sentinel-prod -f compose.prod.yml ps"
    Invoke-TerminalCapture "chaos-run.png" ".\.venv\Scripts\python.exe chaos/run.py latency --duration-seconds 90" 180
    Invoke-TerminalCapture "pytest-results.png" ".\.venv\Scripts\python.exe -m pytest" 300
    Invoke-TerminalCapture "demo-run.png" "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo.ps1" 300
    Invoke-TerminalCapture "gitleaks-history.png" 'gitleaks git --log-opts="--all" --redact --no-banner .'
    Invoke-TerminalCapture "P2-16-deployment-verification.png" "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-deployment.ps1 -OutputPath .\private\capture-deployment-verification.md" 120

    & $python "scripts\update_image_status.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not update docs/images/README.md."
    }
} finally {
    if ($null -ne $script:chaosProcess -and $script:chaosStarted) {
        if ($script:chaosProcess.HasExited) {
            Remove-Item -LiteralPath $stdoutFile, $stderrFile -Force -ErrorAction SilentlyContinue
        }
    } else {
        Remove-Item -LiteralPath $stdoutFile, $stderrFile -Force -ErrorAction SilentlyContinue
    }
    if ($null -eq $previousMode) {
        Remove-Item Env:INTEGRATION_MODE -ErrorAction SilentlyContinue
    } else {
        $env:INTEGRATION_MODE = $previousMode
    }
}

foreach ($image in @(
    "compose-services.png",
    "chaos-run.png",
    "pytest-results.png",
    "demo-run.png",
    "gitleaks-history.png",
    "P2-16-deployment-verification.png"
)) {
    if (-not $script:reported.ContainsKey($image)) {
        Write-CaptureResult $image "Failed" "Capture step did not run"
    }
}

if ($script:failed) {
    exit 1
}
