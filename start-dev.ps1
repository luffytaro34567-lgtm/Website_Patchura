# =============================================================
# PATCHORA — PowerShell Localhost Startup Script
# =============================================================

Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host "  PATCHORA — Localhost Development Environment Launcher" -ForegroundColor Cyan
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot

# Check for Docker option
if ($args -contains "--docker") {
    Write-Host "[PATCHORA] Launching via Docker Compose..." -ForegroundColor Green
    docker-compose up --build
    exit 0
}

Write-Host "Launching Backend on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/c `"$root\run-backend.bat`""

Start-Sleep -Seconds 2

Write-Host "Launching Frontend on http://localhost:5173 ..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/c `"$root\run-frontend.bat`""

Write-Host ""
Write-Host "=============================================================" -ForegroundColor Green
Write-Host "  PATCHORA Servers Launched!" -ForegroundColor Green
Write-Host "  - Frontend:     http://localhost:5173" -ForegroundColor Cyan
Write-Host "  - Backend API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  - API Swagger:  http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host "  - Health Check: http://localhost:8000/api/health" -ForegroundColor Cyan
Write-Host "=============================================================" -ForegroundColor Green
Write-Host ""
