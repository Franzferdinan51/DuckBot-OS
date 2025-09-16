param(
  [string]$Name
)

$ErrorActionPreference = 'Stop'

Push-Location $PSScriptRoot
try {
    # Move to repo root (parent of scripts)
    $repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
    Set-Location $repoRoot

    $timestamp = Get-Date -Format 'yyyyMMdd-HHmm'
    $zipName = if ($Name) { $Name } else { "DuckBotComplete-$timestamp.zip" }
    $zipPath = Join-Path (Get-Location) $zipName

    # Decide if we should use git archive
    $gitAvailable = $false
    try { git --version 1>$null 2>$null; $gitAvailable = $true } catch {}
    $isGitRepo = Test-Path (Join-Path $repoRoot '.git')

    if ($gitAvailable -and $isGitRepo) {
        try {
            git -C $repoRoot rev-parse --is-inside-work-tree 1>$null 2>$null
            git -C $repoRoot archive --format=zip --output "$zipPath" HEAD 1>$null 2>$null
            Write-Host "Created $zipPath (git tracked files)." -ForegroundColor Green
            exit 0
        } catch {
            Write-Host "git detected but archive failed; using Compress-Archive instead." -ForegroundColor Yellow
        }
    }

    # Fallback: Compress-Archive while excluding common noise
    $pattern = '\\(\.git|\.venv|env|logs|__pycache__|\.pytest_cache|\.mypy_cache|node_modules)(\\|$)'
    $items = Get-ChildItem -Force -Recurse -File |
        Where-Object { $_.FullName -notmatch $pattern } |
        Where-Object { $_.Name -notmatch '\\.(pyc|pyo|log)$' -and $_.Name -ne '.DS_Store' }

    if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
    if (-not $items -or $items.Count -eq 0) { throw "No files to archive." }
    $items | Compress-Archive -DestinationPath $zipPath -Force
    Write-Host "Created $zipPath (Compress-Archive, excludes common noise)." -ForegroundColor Green
} finally {
    Pop-Location
}
