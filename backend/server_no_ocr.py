"""
Production Server - NO OCR VERSION
Works without Tesseract - just extracts slides as images
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
import numpy as np

app = FastAPI(
    title="YouTube Notes Extractor API",
    description="Extract slides from YouTube videos (No OCR)",
    version="1.0.0-no-ocr"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage paths
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
    return {
        "message": "YouTube Notes Extractor API (No OCR)",
        "version": "1.0.0-no-ocr",
        "status": "running"
    }

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
    print(f"New extraction job: {job_id}")
    print(f"URL: {request.url}")
    print(f"{'='*60}\n")
    
    background_tasks.add_task(process_video, job_id=job_id, url=str(request.url), quality=request.quality)
    
    return JobStatus(
        job_id=job_id,
        status="queued",
        progress=0,
        message="Extraction job started"
    )

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
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    pdf_path = job.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"notes_{job_id}.pdf"
    )

def process_video(job_id: str, url: str, quality: str):
    print(f"[{job_id}] Starting extraction...")
    
    try:
        # Download video
        jobs[job_id].update({"status": "downloading", "progress": 10, "message": "Downloading video..."})
        print(f"[{job_id}] Downloading video...")
        
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
        
        print(f"[{job_id}] ✓ Downloaded: {video_path}")
        
        # Extract frames
        jobs[job_id].update({"status": "extracting", "progress": 30, "message": "Extracting frames..."})
        print(f"[{job_id}] Extracting frames...")
        
        frames = []
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps)  # 1 frame per second
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % frame_interval == 0:
                frames.append(frame)
            frame_count += 1
        
        cap.release()
        print(f"[{job_id}] ✓ Extracted {len(frames)} frames")
        
        # Detect unique frames
        jobs[job_id].update({"status": "detecting", "progress": 50, "message": "Detecting unique slides..."})
        print(f"[{job_id}] Detecting unique slides...")
        
        import imagehash
        from PIL import Image
        
        unique_frames = []
        last_hash = None
        threshold = 10
        
        for frame in frames:
            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_hash = imagehash.phash(pil_img, hash_size=8)
            
            if last_hash is None or (frame_hash - last_hash) > threshold:
                unique_frames.append(frame)
                last_hash = frame_hash
        
        print(f"[{job_id}] ✓ Found {len(unique_frames)} unique slides")
        
        # Generate PDF
        jobs[job_id].update({"status": "generating", "progress": 80, "message": "Generating PDF..."})
        print(f"[{job_id}] Generating PDF...")
        
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Spacer, PageBreak, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        
        pdf_path = OUTPUT_DIR / f"{job_id}.pdf"
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Save frames as images
        for i, frame in enumerate(unique_frames):
            img_path = job_dir / f"slide_{i}.jpg"
            cv2.imwrite(str(img_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            # Add to PDF
            title = Paragraph(f"<b>Slide {i+1} of {len(unique_frames)}</b>", styles['Heading2'])
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            img = RLImage(str(img_path), width=7*inch, height=5.25*inch)
            story.append(img)
            
            if i < len(unique_frames) - 1:
                story.append(PageBreak())
        
        doc.build(story)
        print(f"[{job_id}] ✓ PDF created: {pdf_path}")
        
        # Complete
        jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Extracted {len(unique_frames)} slides",
            "pdf_path": str(pdf_path),
            "pdf_url": f"/api/download/{job_id}"
        })
        
        print(f"[{job_id}] ✅ COMPLETE!")
        
        # Cleanup
        import shutil
        if job_dir.exists():
            shutil.rmtree(job_dir)
        
    except Exception as e:
        print(f"[{job_id}] ❌ ERROR: {e}")
        traceback.print_exc()
        jobs[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": "Extraction failed",
            "error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  YouTube Notes Extractor - NO OCR VERSION")
    print("="*60)
    print("  Server: http://localhost:8000")
    print("  ")
    print("  Features:")
    print("  ✅ Video download")
    print("  ✅ Frame extraction")
    print("  ✅ Slide detection")
    print("  ✅ PDF generation")
    print("  ⚠️ NO OCR (Tesseract not required)")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
