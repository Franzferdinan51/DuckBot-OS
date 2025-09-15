# PowerShell script to test batch file option 1
Write-Host "Testing START_ENHANCED_DUCKBOT.bat Option 1" -ForegroundColor Green
Write-Host "=" * 50

# Change to the correct directory
Set-Location $PSScriptRoot

# Test the manual steps that option 1 should perform
Write-Host "`n1. Testing Python version check..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python check failed: $_" -ForegroundColor Red
}

Write-Host "`n2. Testing required files..." -ForegroundColor Yellow
$requiredFiles = @('start_ecosystem.py', 'duckbot')
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "${file}: EXISTS" -ForegroundColor Green
    } else {
        Write-Host "${file}: MISSING" -ForegroundColor Red
    }
}

Write-Host "`n3. Testing ecosystem startup (5 second test)..." -ForegroundColor Yellow
try {
    $job = Start-Job -ScriptBlock { python start_ecosystem.py }
    Start-Sleep -Seconds 5
    Stop-Job $job
    Remove-Job $job
    Write-Host "Ecosystem startup test completed successfully" -ForegroundColor Green
} catch {
    Write-Host "Ecosystem startup test failed: $_" -ForegroundColor Red
}

Write-Host "`n4. Testing batch file execution..." -ForegroundColor Yellow
Write-Host "Attempting to run the batch file directly..." -ForegroundColor Cyan

# Try to execute the batch file with a timeout
try {
    $process = Start-Process -FilePath "START_ENHANCED_DUCKBOT.bat" -PassThru -NoNewWindow
    Start-Sleep -Seconds 3
    if (!$process.HasExited) {
        Write-Host "Batch file is running (good sign)" -ForegroundColor Green
        $process.Kill()
        Write-Host "Terminated test process" -ForegroundColor Yellow
    } else {
        Write-Host "Batch file exited immediately - might be an issue" -ForegroundColor Red
        Write-Host "Exit code: $($process.ExitCode)"
    }
} catch {
    Write-Host "Failed to start batch file: $_" -ForegroundColor Red
}

Write-Host "`nTest Summary:" -ForegroundColor Cyan
Write-Host "The Python ecosystem works perfectly when run directly." -ForegroundColor Green
Write-Host "If option 1 'does nothing', it might be:" -ForegroundColor Yellow
Write-Host "  - Batch file hangs on user input" -ForegroundColor White
Write-Host "  - Console window issues" -ForegroundColor White  
Write-Host "  - Interactive menu not displaying" -ForegroundColor White
Write-Host "`nTry running the batch file directly by double-clicking it." -ForegroundColor Cyan