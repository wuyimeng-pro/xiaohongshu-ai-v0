@echo off
setlocal
cd /d "%~dp0"

echo [1/4] Checking MySQL80 service...
sc query MySQL80 >nul 2>nul
if errorlevel 1 (
    echo MySQL80 service not found. Please start MySQL manually, then run this script again.
    pause
    exit /b 1
)
sc query MySQL80 | findstr /i "RUNNING" >nul
if errorlevel 1 (
    echo Starting MySQL80 service...
    net start MySQL80
)

echo [2/4] Starting backend on http://127.0.0.1:8000 ...
start "xiaohongshu-backend" /D "%~dp0backend" "%~dp0venv\Scripts\python.exe" main.py

echo [3/4] Starting frontend on http://localhost:5173 ...
start "xiaohongshu-frontend" /D "%~dp0frontend" cmd /c "npm.cmd run dev"

echo [4/4] Opening browser...
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo.
echo Done! Backend: http://127.0.0.1:8000  Frontend: http://localhost:5173
echo Close the two new windows to stop the services.
endlocal
