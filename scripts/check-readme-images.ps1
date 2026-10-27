$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$imageExtensions = @(".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
$linkPatterns = @(
    '\[[^\]]*\]\(\s*<?([^)\s>]+)>?'
    '<img\b[^>]*\bsrc\s*=\s*["'']([^"'']+)["'']'
)
$missing = [System.Collections.Generic.List[string]]::new()
$documents = Get-ChildItem -Path $root -Recurse -File -Filter *.md |
    Where-Object { $_.FullName -notmatch '[\\/](\.git|\.venv|private)[\\/]' }

foreach ($document in $documents) {
    $insideFence = $false
    foreach ($line in Get-Content -LiteralPath $document.FullName) {
        if ($line -match '^\s*```') {
            $insideFence = -not $insideFence
            continue
        }
        if ($insideFence) {
            continue
        }

        foreach ($pattern in $linkPatterns) {
            foreach ($match in [regex]::Matches($line, $pattern)) {
                $target = [System.Uri]::UnescapeDataString($match.Groups[1].Value)
                if ($target -match '^[a-zA-Z][a-zA-Z0-9+.-]*:' -or $target.StartsWith("//")) {
                    continue
                }

                $target = ($target -split '[?#]', 2)[0]
                if ([string]::IsNullOrWhiteSpace($target)) {
                    continue
                }

                $extension = [System.IO.Path]::GetExtension($target)
                if ($imageExtensions -notcontains $extension.ToLowerInvariant()) {
                    continue
                }

                $relativePath = $target.Replace("/", [System.IO.Path]::DirectorySeparatorChar)
                $imagePath = Join-Path (Split-Path -Parent $document.FullName) $relativePath
                if (-not (Test-Path -LiteralPath $imagePath -PathType Leaf)) {
                    $missing.Add("$($document.FullName): $target")
                }
            }
        }
    }
}

if ($missing.Count -gt 0) {
    $missing | ForEach-Object { Write-Error "Missing linked image: $_" }
    exit 1
}

Write-Output "README and docs contain no links to missing images."
