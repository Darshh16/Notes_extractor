from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import uuid
import time
from pathlib import Path

app = FastAPI(title="YouTube Notes Extractor - Simplified")

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
    return {
        "message": "YouTube Notes Extractor API (Simplified Mode)",
        "status": "running",
        "version": "1.0.0-simple"
    }

@app.post("/api/extract")
async def extract_notes(request: VideoRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Job queued",
        "url": request.url
    }
    
    print(f"\n{'='*60}")
    print(f"New extraction job: {job_id}")
    print(f"URL: {request.url}")
    print(f"Quality: {request.quality}")
    print(f"{'='*60}\n")
    
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

@app.get("/api/download/{job_id}")
async def download_pdf(job_id: str):
    """Placeholder for PDF download"""
    return {
        "message": "PDF download not implemented in simplified mode",
        "job_id": job_id
    }

def process_video_simple(job_id: str, url: str, quality: str):
    """Simplified processing for testing - simulates the full pipeline"""
    
    try:
        # Simulate processing stages with realistic timing
        stages = [
            (10, "downloading", "Downloading video...", 3),
            (25, "extracting", "Extracting frames...", 2),
            (40, "detecting", "Detecting unique pages...", 2),
            (60, "cleaning", "Cleaning 5 frames...", 3),
            (80, "ocr", "Extracting text from frames...", 2),
            (90, "generating", "Generating PDF...", 2),
            (100, "completed", "Successfully extracted 5 pages!", 0)
        ]
        
        for progress, status, message, delay in stages:
            jobs[job_id].update({
                "status": status,
                "progress": progress,
                "message": message
            })
            print(f"[{job_id}] {progress:3d}% - {status:12s} - {message}")
            
            if delay > 0:
                time.sleep(delay)
        
        print(f"\n{'='*60}")
        print(f"[{job_id}] ✅ EXTRACTION COMPLETE!")
        print(f"{'='*60}\n")
            
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[{job_id}] ❌ ERROR: {str(e)}")
        print(f"{'='*60}\n")
        
        jobs[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": "Extraction failed",
            "error": str(e)
        })

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  YouTube Notes Extractor - Simplified Test Server")
    print("="*60)
    print("  Mode: SIMPLIFIED (for testing)")
    print("  Server: http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print("  ")
    print("  This server simulates the extraction process")
    print("  Use this to test the Chrome extension")
    print("  ")
    print("  Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
