@echo off
cd /d "%~dp0backend"
echo ===================================================
echo   PATCHORA — Starting Backend (FastAPI + Uvicorn)
echo ===================================================
echo Local API Address: http://localhost:8000
echo API Docs:          http://localhost:8000/api/docs
echo Health Endpoint:   http://localhost:8000/api/health
echo.

if exist ".venv\Scripts\uvicorn.exe" (
    echo [PATCHORA] Virtual environment ready.
    ".venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo [PATCHORA] Setting up virtual environment ...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
)
pause
