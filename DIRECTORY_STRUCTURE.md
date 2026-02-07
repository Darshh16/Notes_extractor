# Project Directory Structure

```
Notes_extractor/
│
├── 📄 README.md                    # Project overview and quick start
├── 📄 SETUP.md                     # Detailed installation guide
├── 📄 ARCHITECTURE.md              # System architecture and design
├── 📄 PROJECT_SUMMARY.md           # Comprehensive project summary
│
├── 📁 backend/                     # Python FastAPI Backend
│   ├── 📄 main.py                  # FastAPI application entry point
│   ├── 📄 requirements.txt         # Python dependencies
│   ├── 📄 .env.example             # Environment configuration template
│   ├── 📄 .gitignore               # Git ignore rules
│   ├── 📄 start.bat                # Windows quick start script
│   ├── 📄 start.sh                 # Linux/macOS quick start script
│   ├── 📄 test_agentic.py          # Comprehensive test suite
│   │
│   ├── 📁 services/                # Core processing services
│   │   ├── 📄 __init__.py          # Package initialization
│   │   ├── 📄 video_processor.py   # Video download & frame extraction
│   │   ├── 📄 page_detector.py     # Unique page detection (pHash)
│   │   ├── 📄 frame_cleaner.py     # ⭐ AGENTIC obstruction removal
│   │   ├── 📄 ocr_engine.py        # Text extraction (Tesseract)
│   │   └── 📄 pdf_generator.py     # PDF creation (ReportLab)
│   │
│   ├── 📁 temp/                    # Temporary files (auto-created)
│   │   └── [job_id]/               # Per-job temporary storage
│   │       └── video.mp4           # Downloaded video
│   │
│   └── 📁 output/                  # Generated PDFs (auto-created)
│       └── [job_id].pdf            # Final searchable PDF
│
└── 📁 extension/                   # Chrome Extension (Manifest V3)
    ├── 📄 manifest.json            # Extension configuration
    ├── 📄 popup.html               # User interface
    ├── 📄 popup.js                 # UI logic & API communication
    ├── 📄 background.js            # Service worker
    ├── 📄 content.js               # YouTube page integration
    ├── 📄 styles.css               # Premium styling
    │
    └── 📁 icons/                   # Extension icons
        ├── 📄 README.md            # Icon creation guide
        ├── 🖼️ icon16.png           # 16x16 toolbar icon (create this)
        ├── 🖼️ icon48.png           # 48x48 management icon (create this)
        └── 🖼️ icon128.png          # 128x128 store icon (create this)
```

## 📂 File Descriptions

### Root Level
- **README.md**: Quick overview, features, and basic usage
- **SETUP.md**: Step-by-step installation and troubleshooting
- **ARCHITECTURE.md**: Detailed system design with Mermaid diagrams
- **PROJECT_SUMMARY.md**: Complete project documentation

### Backend (`backend/`)

#### Main Files
- **main.py**: FastAPI application with REST endpoints
  - `POST /api/extract` - Start extraction
  - `GET /api/status/{job_id}` - Check progress
  - `GET /api/download/{job_id}` - Download PDF

- **requirements.txt**: All Python dependencies
  - FastAPI, OpenCV, Mediapipe, Tesseract, etc.

- **test_agentic.py**: Comprehensive test suite
  - Quality detection tests
  - Self-correction validation
  - Integration tests

#### Services (`backend/services/`)
- **video_processor.py**: Downloads YouTube videos and extracts frames
  - Uses yt-dlp for downloading
  - OpenCV for frame extraction
  - Configurable FPS (default: 1 fps)

- **page_detector.py**: Detects unique slides/pages
  - Perceptual hashing (pHash)
  - Hamming distance comparison
  - Minimum duration filtering

- **frame_cleaner.py**: ⭐ **AGENTIC CORE**
  - Multi-method face detection
  - Intelligent inpainting
  - Self-correction with validation
  - Fallback strategies

- **ocr_engine.py**: Extracts text from frames
  - Tesseract OCR
  - Image preprocessing
  - Text cleanup

- **pdf_generator.py**: Creates searchable PDFs
  - ReportLab for generation
  - Invisible text layer
  - Professional formatting

### Extension (`extension/`)

#### Core Files
- **manifest.json**: Chrome extension configuration
  - Manifest V3 format
  - Permissions and host access
  - Icon references

- **popup.html**: User interface
  - Video info display
  - Progress tracking
  - Quality selection
  - Action buttons

- **popup.js**: UI logic
  - API communication
  - Status polling (every 2 seconds)
  - Download handling
  - Error management

- **background.js**: Service worker
  - Message passing
  - Notifications
  - Settings storage

- **content.js**: YouTube page integration
  - Video metadata extraction
  - Optional visual indicators

- **styles.css**: Premium styling
  - Gradient backgrounds
  - Smooth animations
  - Responsive design

## 🎯 Key Files to Understand

### For Backend Development
1. **main.py** - API endpoints and job management
2. **services/frame_cleaner.py** - Agentic self-correction logic
3. **services/page_detector.py** - Slide detection algorithm

### For Frontend Development
1. **popup.js** - UI logic and API integration
2. **styles.css** - Design and animations
3. **manifest.json** - Extension configuration

### For Testing
1. **test_agentic.py** - Comprehensive test suite
2. **start.bat** / **start.sh** - Quick start scripts

## 🔄 Data Flow Through Files

```
User clicks extension button
    ↓
popup.html (UI)
    ↓
popup.js (sends request)
    ↓
main.py (creates job)
    ↓
video_processor.py (downloads video)
    ↓
page_detector.py (finds unique slides)
    ↓
frame_cleaner.py (removes obstructions) ⭐
    ↓
ocr_engine.py (extracts text)
    ↓
pdf_generator.py (creates PDF)
    ↓
main.py (serves download)
    ↓
popup.js (downloads PDF)
```

## 📝 Configuration Files

- **backend/.env.example**: Environment variables template
- **backend/requirements.txt**: Python dependencies
- **extension/manifest.json**: Extension settings

## 🗂️ Auto-Generated Directories

These are created automatically when the backend runs:
- **backend/temp/**: Temporary video and frame storage
- **backend/output/**: Generated PDF files

## 🎨 Assets Needed

You need to create these icon files (see `extension/icons/README.md`):
- icon16.png (16x16 pixels)
- icon48.png (48x48 pixels)
- icon128.png (128x128 pixels)

## 🚀 Getting Started

1. **Read**: README.md for overview
2. **Setup**: Follow SETUP.md for installation
3. **Run**: Use start.bat (Windows) or start.sh (Linux/macOS)
4. **Load**: Extension in Chrome
5. **Test**: On a YouTube video with slides

## 📚 Further Reading

- **ARCHITECTURE.md**: Deep dive into system design
- **PROJECT_SUMMARY.md**: Complete feature list
- **test_agentic.py**: Examples of agentic behavior
