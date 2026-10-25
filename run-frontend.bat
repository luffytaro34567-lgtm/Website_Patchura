@echo off
set "PATH=C:\Program Files\nodejs;%PATH%"
cd /d "%~dp0frontend"
echo ===================================================
echo   PATCHORA — Starting Frontend (Vite + React)
echo ===================================================
echo Local Web Address: http://localhost:5173
echo Proxies /api to:   http://localhost:8000
echo.

if not exist "node_modules" (
    echo [PATCHORA] Installing frontend dependencies ...
    call npm install
)

echo [PATCHORA] Launching Vite dev server on http://localhost:5173 ...
call npm run dev
pause
