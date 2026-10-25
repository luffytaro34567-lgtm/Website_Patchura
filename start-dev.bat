@echo off
echo =============================================================
echo   PATCHORA — 1-Click Localhost Development Environment
echo =============================================================
echo.
echo Launching Backend server in dedicated terminal...
start "PATCHORA Backend (FastAPI)" "%~dp0run-backend.bat"

echo Launching Frontend server in dedicated terminal...
start "PATCHORA Frontend (Vite)" "%~dp0run-frontend.bat"

echo.
echo =============================================================
echo   PATCHORA local servers launched!
echo =============================================================
echo - Frontend URL:     http://localhost:5173
echo - Backend API URL:  http://localhost:8000
echo - Swagger API Docs: http://localhost:8000/api/docs
echo - System Health:    http://localhost:8000/api/health
echo =============================================================
echo.
timeout /t 5
