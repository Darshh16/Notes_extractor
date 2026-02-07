@echo off
REM Quick Start Script for YouTube Notes Extractor
REM This script sets up and runs the backend server

echo ========================================
echo YouTube Notes Extractor - Quick Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Checking Python installation...
python --version
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [2/5] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo [2/5] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Install dependencies
echo [4/5] Installing dependencies...
echo This may take a few minutes...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

REM Create necessary directories
if not exist "temp\" mkdir temp
if not exist "output\" mkdir output

REM Check for Tesseract
echo [5/5] Checking Tesseract installation...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Tesseract OCR not found in PATH
    echo Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
    echo Or update the .env file with the correct path
    echo.
) else (
    echo Tesseract found!
    tesseract --version
    echo.
)

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Starting FastAPI server...
echo API will be available at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the server
python main.py

pause
