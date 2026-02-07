# YouTube Notes Extractor

Extract slides from YouTube videos as high-quality images in a ZIP file.

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements_minimal.txt
```

### 2. Start Server
```bash
python server_zip.py
```

### 3. Load Extension
1. Open Chrome: `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension` folder

### 4. Extract Slides
1. Click extension icon
2. Enter YouTube URL
3. Click "Start Extraction"
4. Wait 2-5 minutes
5. Download ZIP file with all slides

## Output

- **Format**: ZIP file
- **Contents**: High-quality JPEG images (95% quality)
- **Naming**: slide_001.jpg, slide_002.jpg, etc.
- **Size**: ~500KB - 5MB depending on video length

## Features

✅ Downloads YouTube videos  
✅ Extracts unique slides  
✅ Returns ZIP with images  
✅ Background processing  
✅ Manual URL input  
✅ **No PDF corruption issues!**

## Requirements

- Python 3.8+
- Chrome browser
- Internet connection

## Server

- **Port**: 8000
- **Endpoint**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
