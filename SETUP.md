# YouTube Notes Extractor - Setup Guide

## Prerequisites

### 1. Python 3.8+
Download from [python.org](https://www.python.org/downloads/)

### 2. Tesseract OCR
**Windows:**
- Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- Install to default location: `C:\Program Files\Tesseract-OCR`
- Add to PATH or update `.env` file

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### 3. FFmpeg (for yt-dlp)
**Windows:**
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Add to PATH

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

## Backend Setup

### 1. Navigate to backend directory
```bash
cd backend
```

### 2. Create virtual environment
```bash
python -m venv venv
```

### 3. Activate virtual environment
**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure environment (optional)
```bash
copy .env.example .env
# Edit .env file with your settings
```

### 6. Run the server
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### 7. Test the API
Open browser and navigate to `http://localhost:8000` - you should see:
```json
{
  "message": "YouTube Notes Extractor API",
  "version": "1.0.0",
  "status": "running"
}
```

## Chrome Extension Setup

### 1. Open Chrome Extensions
Navigate to `chrome://extensions/`

### 2. Enable Developer Mode
Toggle the "Developer mode" switch in the top right

### 3. Load Extension
1. Click "Load unpacked"
2. Navigate to the `extension` folder
3. Click "Select Folder"

### 4. Verify Installation
- You should see the extension icon in your toolbar
- Click it to open the popup

## Usage

### 1. Navigate to YouTube
Open any YouTube video with slides/presentations

### 2. Open Extension
Click the extension icon in your toolbar

### 3. Configure Settings
- Select video quality (480p, 720p, or 1080p)
- Higher quality = better OCR but slower processing

### 4. Start Extraction
Click "Start Extraction" button

### 5. Monitor Progress
The extension will show real-time progress:
- Downloading video
- Extracting frames
- Detecting unique pages
- Cleaning frames (removing facecams/overlays)
- Extracting text (OCR)
- Generating PDF

### 6. Download PDF
Once complete, click "Download PDF" to get your notes

## Troubleshooting

### Backend Issues

**Error: "Could not find Tesseract"**
- Ensure Tesseract is installed
- On Windows, update `.env` with correct path:
  ```
  TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
  ```
- Or add to PATH

**Error: "yt-dlp download failed"**
- Ensure FFmpeg is installed and in PATH
- Check internet connection
- Verify YouTube URL is valid

**Error: "Mediapipe initialization failed"**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Try reinstalling mediapipe: `pip install --upgrade mediapipe`

### Extension Issues

**Error: "Failed to start extraction"**
- Ensure backend server is running (`python main.py`)
- Check that API is accessible at `http://localhost:8000`
- Check browser console for CORS errors

**Extension not appearing**
- Verify extension is loaded in `chrome://extensions/`
- Check for errors in extension details
- Try reloading the extension

**No video detected**
- Ensure you're on a YouTube watch page (URL contains `/watch?v=`)
- Refresh the page and try again

## Advanced Configuration

### Custom API URL
If running backend on different host/port, update `extension/popup.js`:
```javascript
const API_BASE_URL = 'http://your-host:your-port';
```

### Adjust Detection Sensitivity
Edit `backend/services/page_detector.py`:
```python
PageDetector(
    hash_threshold=10,      # Lower = more strict (fewer duplicates)
    diff_threshold=0.15,    # Higher = more different required
    min_page_duration=2.0   # Minimum seconds per page
)
```

### Improve OCR Accuracy
Edit `backend/services/ocr_engine.py`:
```python
# Add more languages
OCREngine(lang='eng+fra+deu')  # English + French + German

# Adjust preprocessing
# Modify _preprocess_for_ocr() method
```

### Customize PDF Output
Edit `backend/services/pdf_generator.py`:
```python
# Change page size
PDFGenerator(page_size=letter)  # or A4, legal, etc.

# Customize styling
# Modify _create_title_page() method
```

## Performance Tips

1. **Use appropriate quality**: 720p is recommended for most cases
2. **Longer videos**: May take several minutes to process
3. **RAM usage**: Processing uses ~2-4GB RAM for typical videos
4. **Disk space**: Temporary files can be large, ensure adequate space

## API Endpoints

### POST /api/extract
Start extraction job
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "quality": "720p"
}
```

### GET /api/status/{job_id}
Check job status
```json
{
  "job_id": "uuid",
  "status": "processing",
  "progress": 50,
  "message": "Cleaning frames..."
}
```

### GET /api/download/{job_id}
Download generated PDF

## Development

### Running Tests
```bash
cd backend
pytest
```

### Code Structure
```
backend/
├── main.py                 # FastAPI application
├── services/
│   ├── video_processor.py  # Video download & frame extraction
│   ├── page_detector.py    # Unique page detection
│   ├── frame_cleaner.py    # Obstruction removal (AGENTIC)
│   ├── ocr_engine.py       # Text extraction
│   └── pdf_generator.py    # PDF creation
├── temp/                   # Temporary files
└── output/                 # Generated PDFs

extension/
├── manifest.json           # Extension configuration
├── popup.html             # UI
├── popup.js               # UI logic
├── background.js          # Service worker
└── content.js             # YouTube page integration
```

## Contributing

Contributions welcome! Areas for improvement:
- Support for more video platforms
- Better obstruction detection
- Multi-language OCR
- Cloud deployment
- Batch processing

## License

MIT License - See LICENSE file for details
