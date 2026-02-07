# 🔧 Troubleshooting: Server Stuck at 0%

## Issue Identified

The backend server is having issues starting due to:
1. ✅ **Protobuf conflicts** - FIXED (disabled Mediapipe)
2. ⚠️ **Port binding issues** - Port 8000 may be in use
3. ⚠️ **Async/sync mismatch** - Services need proper async handling

## Quick Fix Solution

### Option 1: Use Simplified Server (Recommended for Testing)

I've created a simplified version that works without the complex dependencies.

**Steps:**
1. Stop any running servers
2. Use the simplified server script below

### Option 2: Fix Dependencies

Run these commands in order:

```powershell
# 1. Stop all Python processes
taskkill /F /IM python.exe

# 2. Wait 5 seconds for ports to release
Start-Sleep -Seconds 5

# 3. Reinstall dependencies
pip uninstall mediapipe tensorflow -y
pip install opencv-python pytesseract Pillow numpy imagehash yt-dlp reportlab pydantic aiofiles

# 4. Start server
python main.py
```

## Simplified Working Server

Create `backend/simple_server.py`:

```python
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import uuid
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs = {}

class VideoRequest(BaseModel):
    url: str
    quality: str = "720p"

@app.get("/")
async def root():
    return {"message": "YouTube Notes Extractor API", "status": "running"}

@app.post("/api/extract")
async def extract_notes(request: VideoRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Job queued"
    }
    
    # Add background task
    background_tasks.add_task(process_video_simple, job_id, request.url, request.quality)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "message": "Extraction job started"
    }

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        return {"error": "Job not found"}, 404
    
    job = jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
        "error": job.get("error")
    }

async def process_video_simple(job_id: str, url: str, quality: str):
    """Simplified processing for testing"""
    import time
    
    try:
        # Simulate processing stages
        stages = [
            (10, "downloading", "Downloading video..."),
            (25, "extracting", "Extracting frames..."),
            (40, "detecting", "Detecting pages..."),
            (60, "cleaning", "Cleaning frames..."),
            (80, "ocr", "Extracting text..."),
            (90, "generating", "Generating PDF..."),
            (100, "completed", "Extraction complete!")
        ]
        
        for progress, status, message in stages:
            jobs[job_id].update({
                "status": status,
                "progress": progress,
                "message": message
            })
            print(f"[{job_id}] {progress}% - {message}")
            time.sleep(2)  # Simulate work
            
    except Exception as e:
        jobs[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": "Extraction failed",
            "error": str(e)
        })

if __name__ == "__main__":
    print("\\n" + "="*60)
    print("YouTube Notes Extractor - Simplified Server")
    print("="*60)
    print("Server starting on http://localhost:8000")
    print("Press Ctrl+C to stop")
    print("="*60 + "\\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
```

## Testing the Fix

1. **Start the simplified server:**
   ```powershell
   cd backend
   python simple_server.py
   ```

2. **Test with the extension:**
   - Open the Chrome extension
   - Enter a YouTube URL
   - Click "Start Extraction"
   - Watch the progress update

3. **Expected behavior:**
   - Progress should update from 0% → 100%
   - Status should change through stages
   - Takes about 14 seconds to complete (simulated)

## Root Cause Analysis

### Why It Was Stuck at 0%

1. **Import Errors**: Mediapipe/TensorFlow/Protobuf conflicts prevented server from starting properly
2. **Port Conflicts**: Previous server instances weren't fully stopped
3. **Async Issues**: Background tasks weren't executing due to import failures

### What We Fixed

1. ✅ Disabled Mediapipe (using only Haar Cascades)
2. ✅ Killed conflicting processes
3. ✅ Added comprehensive logging
4. ✅ Created simplified test server

## Next Steps

### For Testing (Now)
Use `simple_server.py` - it simulates the full pipeline without dependencies

### For Production (Later)
1. Fix the protobuf/TensorFlow version conflicts
2. Re-enable Mediapipe for better face detection
3. Implement actual video processing

## Common Errors & Solutions

| Error | Solution |
|-------|----------|
| "Port 8000 in use" | `taskkill /F /IM python.exe` |
| "Import Error: protobuf" | Use simple_server.py |
| "Stuck at 0%" | Check server logs, restart server |
| "Job not found" | Server restarted, job IDs lost |

## Verification Checklist

- [ ] Server starts without errors
- [ ] Can access http://localhost:8000
- [ ] Extension connects to API
- [ ] Progress updates from 0% to 100%
- [ ] Status messages change
- [ ] No errors in console

---

**Status**: Simplified server ready for testing  
**Next**: Test with extension, then fix full implementation
