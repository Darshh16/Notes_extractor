# YouTube Notes Extractor

An intelligent system that extracts clean, high-quality study notes from YouTube videos and compiles them into searchable PDFs.

## Features

- **Smart Page Detection**: Uses perceptual hashing and frame differencing to detect slide changes
- **Intelligent Obstruction Removal**: Automatically removes facecams and overlays using AI
- **OCR & Text Extraction**: Makes PDFs searchable using Tesseract OCR
- **Self-Correcting Algorithm**: Detects and handles low-quality frames automatically
- **Chrome Extension**: Easy-to-use interface for capturing YouTube videos

## Architecture

- **Frontend**: Chrome Extension (Manifest V3)
- **Backend**: Python FastAPI with OpenCV, Mediapipe, and Tesseract
- **Processing Pipeline**: Frame extraction → Page detection → Cleaning → OCR → PDF generation

## Installation

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Chrome Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension` directory

## Usage

1. Navigate to a YouTube video with slides/presentations
2. Click the extension icon
3. Click "Start Extraction"
4. Wait for processing to complete
5. Download the generated PDF

## Tech Stack

- **Backend**: FastAPI, OpenCV, Mediapipe, Tesseract, yt-dlp, imagehash
- **Frontend**: JavaScript (Manifest V3)
- **Image Processing**: NumPy, Pillow
- **PDF Generation**: ReportLab

## License

MIT
