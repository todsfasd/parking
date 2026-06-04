@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Seoul parking map server

echo ==========================================
echo Seoul parking realtime map - starting
echo ==========================================
echo.

if not exist ".env" (
    echo [ERROR] .env file not found in:
    echo %CD%
    echo Put SEOUL_API_KEY in .env
    echo.
    pause
    exit /b 1
)

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3 and try again.
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Installing required packages...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

echo.
echo Detecting this PC's Wi-Fi IP address...
set "LAN_IP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    if not defined LAN_IP set "LAN_IP=%%a"
)
set "LAN_IP=%LAN_IP: =%"

echo.
echo ==========================================
echo Starting server...
echo.
echo  On THIS PC:        http://127.0.0.1:5000/
if defined LAN_IP echo  On PHONE (same Wi-Fi): http://%LAN_IP%:5000/
echo.
echo Keep this window open while using the site.
echo Press Ctrl+C here to stop the server.
echo ==========================================
echo.

start "" "http://127.0.0.1:5000/"
python app.py
pause
