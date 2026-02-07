#!/bin/bash
# Quick Start Script for YouTube Notes Extractor (Linux/macOS)
# This script sets up and runs the backend server

echo "========================================"
echo "YouTube Notes Extractor - Quick Start"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

echo "[1/5] Checking Python installation..."
python3 --version
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[2/5] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
else
    echo "[2/5] Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "[3/5] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi
echo ""

# Install dependencies
echo "[4/5] Installing dependencies..."
echo "This may take a few minutes..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo ""

# Create necessary directories
mkdir -p temp
mkdir -p output

# Check for Tesseract
echo "[5/5] Checking Tesseract installation..."
if ! command -v tesseract &> /dev/null; then
    echo "WARNING: Tesseract OCR not found"
    echo "Please install Tesseract:"
    echo "  macOS: brew install tesseract"
    echo "  Linux: sudo apt-get install tesseract-ocr"
    echo ""
else
    echo "Tesseract found!"
    tesseract --version
    echo ""
fi

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Starting FastAPI server..."
echo "API will be available at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Start the server
python main.py
