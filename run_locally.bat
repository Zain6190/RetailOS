@echo off
echo ===================================================
echo             SmartStore AI (RetailOS) Launcher
echo ===================================================
echo.
echo This script will start both the Frontend and Backend locally.
echo.
echo 1. Launching Backend Server on http://127.0.0.1:8000
echo 2. Launching Frontend Server on http://localhost:1688
echo.
echo Press any key to start...
pause > nul

echo.
echo Starting Backend...
start "SmartStore AI Backend" cmd /k "echo Starting Backend... && .\backend\venv\Scripts\python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"

echo Starting Frontend...
start "SmartStore AI Frontend" cmd /k "echo Starting Frontend... && cd frontend && npm run start -- --port 1688"

echo.
echo Both servers have been launched in separate command windows.
echo - Backend API Docs: http://localhost:8000/docs
echo - Frontend App:     http://localhost:1688
echo.
echo You can close this launcher window now.
pause
