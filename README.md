# YouTube Notes Extractor

Extract slides from YouTube videos as a searchable PDF.

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements_minimal.txt
```

### 2. Start Server
```bash
python server_no_ocr.py
```

### 3. Load Extension
1. Open Chrome: `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension` folder

### 4. Extract Notes
1. Click extension icon
2. Enter YouTube URL
3. Click "Start Extraction"
4. Wait 2-5 minutes
5. Download PDF

## Features

✅ Downloads YouTube videos  
✅ Extracts unique slides  
✅ Generates PDF with images  
✅ Background processing  
✅ Manual URL input  

## Requirements

- Python 3.8+
- Chrome browser
- Internet connection

## Server

- **Port**: 8000
- **Endpoint**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
