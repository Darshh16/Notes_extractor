@echo off
echo ============================================================
echo   YouTube Notes Extractor - Production Server
echo ============================================================
echo.
echo Killing any existing Python processes...
taskkill /F /IM python.exe 2>nul

echo Waiting for ports to release...
timeout /t 3 /nobreak >nul

echo.
echo Starting PRODUCTION server...
echo This version includes REAL video processing!
echo.
python production_server.py

pause
