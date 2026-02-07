"""
Simple Working Server - Returns ZIP of slide images
No PDF generation - just clean slide images in a ZIP file
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from pathlib import Path
from typing import Optional
import uuid
from datetime import datetime
import traceback
import cv2
import zipfile

app = FastAPI(title="YouTube Notes Extractor", version="2.0.0-zip")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

jobs = {}

class VideoRequest(BaseModel):
    url: str
    quality: Optional[str] = "720p"

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    pdf_url: Optional[str] = None
    error: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "YouTube Notes Extractor", "status": "running", "format": "ZIP"}

@app.post("/api/extract", response_model=JobStatus)
async def extract_notes(request: VideoRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Job queued",
        "created_at": datetime.now(),
        "url": str(request.url)
    }
    
    print(f"\n{'='*60}")
    print(f"Job: {job_id}")
    print(f"URL: {request.url}")
    print(f"{'='*60}\n")
    
    background_tasks.add_task(process_video, job_id=job_id, url=str(request.url))
    
    return JobStatus(job_id=job_id, status="queued", progress=0, message="Started")

@app.get("/api/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        pdf_url=job.get("pdf_url"),
        error=job.get("error")
    )

@app.get("/api/download/{job_id}")
async def download_pdf(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Not completed")
    
    zip_path = job.get("pdf_path")  # Using pdf_path for compatibility
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        zip_path,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=slides_{job_id}.zip"}
    )

def process_video(job_id: str, url: str):
    print(f"[{job_id}] START")
    
    try:
        # Download
        jobs[job_id].update({"status": "downloading", "progress": 10, "message": "Downloading..."})
        print(f"[{job_id}] Downloading...")
        
        job_dir = TEMP_DIR / job_id
        job_dir.mkdir(exist_ok=True)
        
        import yt_dlp
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': str(job_dir / 'video.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = Path(ydl.prepare_filename(info))
        
        print(f"[{job_id}] ✓ Downloaded")
        
        # Extract frames
        jobs[job_id].update({"status": "extracting", "progress": 30, "message": "Extracting frames..."})
        print(f"[{job_id}] Extracting frames...")
        
        frames = []
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        interval = int(fps)
        
        count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if count % interval == 0:
                frames.append(frame)
            count += 1
        
        cap.release()
        print(f"[{job_id}] ✓ {len(frames)} frames")
        
        # Detect unique
        jobs[job_id].update({"status": "detecting", "progress": 50, "message": "Finding unique slides..."})
        print(f"[{job_id}] Detecting unique...")
        
        import imagehash
        from PIL import Image
        
        unique = []
        last_hash = None
        
        for frame in frames:
            pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            h = imagehash.phash(pil, hash_size=8)
            
            if last_hash is None or (h - last_hash) > 10:
                unique.append(frame)
                last_hash = h
        
        print(f"[{job_id}] ✓ {len(unique)} unique slides")
        
        # Create ZIP
        jobs[job_id].update({"status": "generating", "progress": 80, "message": "Creating ZIP..."})
        print(f"[{job_id}] Creating ZIP...")
        
        zip_path = OUTPUT_DIR / f"{job_id}.zip"
        
        # Save all images FIRST
        image_paths = []
        for i, frame in enumerate(unique):
            img_path = job_dir / f"slide_{i+1:03d}.jpg"
            cv2.imwrite(str(img_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            image_paths.append(img_path)
            print(f"[{job_id}]   Saved slide_{i+1:03d}.jpg")
        
        print(f"[{job_id}] ✓ Saved {len(image_paths)} images")
        
        # Now create ZIP with all saved images
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for img_path in image_paths:
                if img_path.exists():
                    zf.write(img_path, img_path.name)
                else:
                    print(f"[{job_id}] ⚠ Missing: {img_path.name}")
        
        # Verify ZIP was created and has content
        if not zip_path.exists():
            raise Exception("ZIP file was not created")
        
        zip_size = zip_path.stat().st_size
        if zip_size < 1000:
            raise Exception(f"ZIP file too small: {zip_size} bytes")
        
        print(f"[{job_id}] ✓ ZIP created: {zip_size} bytes")
        
        # Complete
        jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"{len(unique)} slides ready",
            "pdf_path": str(zip_path),
            "pdf_url": f"/api/download/{job_id}"
        })
        
        print(f"[{job_id}] ✅ DONE")
        
        # Cleanup temp files AFTER everything is complete
        import shutil
        import time
        time.sleep(1)  # Wait to ensure ZIP is fully written
        
        try:
            if job_dir.exists():
                shutil.rmtree(job_dir)
                print(f"[{job_id}] ✓ Cleaned up")
        except Exception as e:
            print(f"[{job_id}] ⚠ Cleanup: {e}")
        
    except Exception as e:
        print(f"[{job_id}] ❌ {e}")
        traceback.print_exc()
        jobs[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": "Failed",
            "error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  YouTube Slides Extractor - ZIP VERSION")
    print("="*60)
    print("  Server: http://localhost:8000")
    print("  Output: ZIP file with slide images")
    print("  Simple, reliable, no PDF issues!")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
