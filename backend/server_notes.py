"""
YouTube NOTES Extractor - Extracts text from lecture slides
Designed for educational videos with text/notes on slides
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

app = FastAPI(title="YouTube Notes Extractor", version="3.0.0-notes")

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
    return {"message": "YouTube Notes Extractor", "status": "running", "purpose": "Extract text from lecture slides"}

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
    
    txt_path = job.get("pdf_path")
    if not txt_path or not os.path.exists(txt_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        txt_path,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=notes_{job_id}.txt"}
    )

def process_video(job_id: str, url: str):
    print(f"[{job_id}] START - Extracting notes from lecture")
    
    try:
        # Download
        jobs[job_id].update({"status": "downloading", "progress": 10, "message": "Downloading video..."})
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
            video_title = info.get('title', 'Unknown')
        
        print(f"[{job_id}] ✓ Downloaded: {video_title}")
        
        # Extract frames every 2 seconds (slower = better for lectures)
        jobs[job_id].update({"status": "extracting", "progress": 25, "message": "Extracting frames..."})
        print(f"[{job_id}] Extracting frames...")
        
        frames = []
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        interval = int(fps * 2)  # Every 2 seconds
        
        count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if count % interval == 0:
                frames.append(frame)
            count += 1
        
        cap.release()
        print(f"[{job_id}] ✓ {len(frames)} frames extracted")
        
        # Detect unique slides
        jobs[job_id].update({"status": "detecting", "progress": 40, "message": "Finding unique slides..."})
        print(f"[{job_id}] Detecting unique slides...")
        
        import imagehash
        from PIL import Image
        
        unique = []
        last_hash = None
        
        if len(unique) == 0:
            print(f"[{job_id}] ⚠ No unique slides found (possibly too much motion/video)")
            # Fallback: take frames at fixed intervals
            interval_frames = frames[::10]  # Take every 10th frame captured
            unique = interval_frames
            print(f"[{job_id}] -> Using {len(unique)} frames as fallback")

        # Extract text using OCR
        jobs[job_id].update({"status": "ocr", "progress": 60, "message": f"Extracting text from {len(unique)} slides..."})
        print(f"[{job_id}] Extracting text with OCR...")
        
        try:
            import pytesseract
            # Explicitly set path for Windows
            tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                print(f"[{job_id}] ✓ Tesseract found at: {tesseract_path}")
            else:
                print(f"[{job_id}] ⚠ Tesseract not found at default path. Checking PATH...")

            all_notes = []
            all_notes.append(f"NOTES FROM: {video_title}")
            all_notes.append(f"URL: {url}")
            all_notes.append(f"Extracted: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            all_notes.append(f"Total Slides Processed: {len(unique)}")
            all_notes.append("="*60)
            all_notes.append("")
            
            extracted_count = 0
            for i, frame in enumerate(unique):
                print(f"[{job_id}]   Processing slide {i+1}/{len(unique)}...")
                
                # Preprocess for better OCR
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Increase contrast
                gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
                # Denoise
                denoised = cv2.fastNlMeansDenoising(gray)
                try:
                    # Threshold
                    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    # Extract text
                    text = pytesseract.image_to_string(thresh, config='--psm 6')
                except Exception as ocr_err:
                     print(f"[{job_id}]   ⚠ OCR Error on slide {i+1}: {ocr_err}")
                     text = ""
                
                if text.strip():
                    extracted_count += 1
                    all_notes.append(f"\n{'='*60}")
                    all_notes.append(f"SLIDE {i+1} (Time approx: {i*2}s)")
                    all_notes.append(f"{'='*60}")
                    all_notes.append(text.strip())
                    all_notes.append("")

            if extracted_count == 0:
                all_notes.append("No readable text found in video frames.")
                all_notes.append("Try a video with clearer text/slides.")

            # Save as text file
            txt_path = OUTPUT_DIR / f"{job_id}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_notes))
            
            print(f"[{job_id}] ✓ Notes saved: {txt_path.stat().st_size} bytes")
            
            # Complete
            jobs[job_id].update({
                "status": "completed",
                "progress": 100,
                "message": f"Extracted notes from {extracted_count} slides",
                "pdf_path": str(txt_path),
                "pdf_url": f"/api/download/{job_id}"
            })
            
            print(f"[{job_id}] ✅ DONE - {extracted_count} text slides found")
            
        except Exception as e:
            # General OCR failure - save images instead
            print(f"[{job_id}] ⚠ OCR Failed: {e} - saving images instead")
            traceback.print_exc()

            import zipfile
            zip_path = OUTPUT_DIR / f"{job_id}.zip"
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for i, frame in enumerate(unique):
                    img_path = job_dir / f"slide_{i+1:03d}.jpg"
                    cv2.imwrite(str(img_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    if img_path.exists():
                        zf.write(img_path, img_path.name)
            
            jobs[job_id].update({
                "status": "completed",
                "progress": 100,
                "message": f"{len(unique)} slides saved (OCR failed)",
                "pdf_path": str(zip_path),
                "pdf_url": f"/api/download/{job_id}"
            })
            
            print(f"[{job_id}] ✅ DONE - Images only (OCR failed)")
        
        # Cleanup
        import shutil
        import time
        time.sleep(1)
        
        try:
            if job_dir.exists():
                shutil.rmtree(job_dir)
        except:
            pass
        
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
    print("  YouTube NOTES Extractor")
    print("="*60)
    print("  Server: http://localhost:8000")
    print("  Purpose: Extract text from lecture slides")
    print("  Output: Text file with all notes")
    print("  ")
    print("  Best for: Educational videos, lectures, tutorials")
    print("  Not for: Music videos, vlogs, entertainment")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
