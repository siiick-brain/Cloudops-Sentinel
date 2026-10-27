$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$failed = $false
$warned = $false
$paths = Get-ChildItem -Path $root -Recurse -File -Filter *.md |
    Where-Object { $_.FullName -notmatch '[\\/](private|\.git|\.venv)[\\/]' }
$emDash = [char]0x2014
$enDash = [char]0x2013

foreach ($file in $paths) {
    $insideFence = $false
    $lineNumber = 0
    foreach ($line in Get-Content -LiteralPath $file.FullName) {
        $lineNumber++
        if ($line -match '^\s*```') {
            $insideFence = -not $insideFence
            continue
        }
        if ($insideFence) {
            continue
        }
        if ($line.Contains($emDash) -or $line.Contains($enDash) -or $line -match 'and,') {
            Write-Error "$($file.FullName):$lineNumber contains a prohibited dash or 'and,'."
            $failed = $true
        }
        if ($line -match ',\s+and\b') {
            Write-Warning "$($file.FullName):$lineNumber has a comma before 'and'."
            $warned = $true
        }
    }
}

if ($failed) {
    exit 1
}
if ($warned) {
    Write-Output "Style check passed with warnings."
} else {
    Write-Output "Style check passed."
}
