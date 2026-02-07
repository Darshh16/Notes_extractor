@echo off
echo Killing any existing Python processes...
taskkill /F /IM python.exe 2>nul

echo Waiting for ports to release...
timeout /t 3 /nobreak >nul

echo Starting simplified server...
python simple_server.py

pause
