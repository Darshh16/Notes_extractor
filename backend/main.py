from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
import os
from pathlib import Path
from typing import Optional
import uuid
from datetime import datetime
import asyncio

from services.video_processor import VideoProcessor
from services.frame_cleaner import FrameCleaner
from services.page_detector import PageDetector
from services.ocr_engine import OCREngine
from services.pdf_generator import PDFGenerator

app = FastAPI(
    title="YouTube Notes Extractor API",
    description="Extract clean study notes from YouTube videos",
    version="1.0.0"
)

# CORS middleware for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your extension ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
video_processor = VideoProcessor()
frame_cleaner = FrameCleaner()
page_detector = PageDetector()
ocr_engine = OCREngine()
pdf_generator = PDFGenerator()

# Storage paths
BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# In-memory job storage (use Redis in production)
jobs = {}


class VideoRequest(BaseModel):
    url: HttpUrl
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
        "message": "YouTube Notes Extractor API",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/api/extract", response_model=JobStatus)
async def extract_notes(request: VideoRequest, background_tasks: BackgroundTasks):
    """
    Start the extraction process for a YouTube video.
    Returns a job ID for tracking progress.
    """
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Job queued",
        "created_at": datetime.now(),
        "url": str(request.url)
    }
    
    # Add background task
    background_tasks.add_task(
        process_video,
        job_id=job_id,
        url=str(request.url),
        quality=request.quality
    )
    
    return JobStatus(
        job_id=job_id,
        status="queued",
        progress=0,
        message="Extraction job started"
    )


@app.get("/api/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of an extraction job."""
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
    """Download the generated PDF."""
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


async def process_video(job_id: str, url: str, quality: str):
    """
    Main processing pipeline for video extraction.
    This is the agentic core that self-corrects and adapts.
    """
    print(f"\n{'='*60}")
    print(f"Starting extraction for job: {job_id}")
    print(f"URL: {url}")
    print(f"Quality: {quality}")
    print(f"{'='*60}\n")
    
    try:
        # Update status: Downloading
        jobs[job_id].update({
            "status": "downloading",
            "progress": 10,
            "message": "Downloading video..."
        })
        print(f"[{job_id}] Status: Downloading video...")
        
        video_path = await video_processor.download_video(url, quality, TEMP_DIR / job_id)
        print(f"[{job_id}] ✓ Video downloaded: {video_path}")
        
        # Update status: Extracting frames
        jobs[job_id].update({
            "status": "extracting",
            "progress": 25,
            "message": "Extracting frames..."
        })
        print(f"[{job_id}] Status: Extracting frames...")
        
        frames = await video_processor.extract_frames(video_path)
        print(f"[{job_id}] ✓ Extracted {len(frames)} frames")
        
        # Update status: Detecting pages
        jobs[job_id].update({
            "status": "detecting",
            "progress": 40,
            "message": "Detecting unique pages..."
        })
        print(f"[{job_id}] Status: Detecting unique pages...")
        
        unique_frames = await page_detector.detect_unique_pages(frames)
        print(f"[{job_id}] ✓ Detected {len(unique_frames)} unique pages")
        
        # Update status: Cleaning frames
        jobs[job_id].update({
            "status": "cleaning",
            "progress": 60,
            "message": f"Cleaning {len(unique_frames)} frames..."
        })
        print(f"[{job_id}] Status: Cleaning {len(unique_frames)} frames...")
        
        cleaned_frames = []
        for i, frame in enumerate(unique_frames):
            # Self-correction: Check frame quality before cleaning
            if frame_cleaner.is_low_quality(frame):
                jobs[job_id]["message"] = f"Skipping low-quality frame {i+1}/{len(unique_frames)}"
                print(f"[{job_id}] ⚠ Skipping low-quality frame {i+1}")
                continue
            
            cleaned_frame = await frame_cleaner.remove_obstructions(frame)
            
            # Self-correction: Verify cleaning didn't corrupt the frame
            if frame_cleaner.is_valid_cleaned_frame(cleaned_frame):
                cleaned_frames.append(cleaned_frame)
                print(f"[{job_id}] ✓ Cleaned frame {i+1}/{len(unique_frames)}")
            else:
                # Fallback to original if cleaning failed
                cleaned_frames.append(frame)
                print(f"[{job_id}] ⚠ Cleaning failed for frame {i+1}, using original")
        
        print(f"[{job_id}] ✓ Cleaned {len(cleaned_frames)} frames total")
        
        # Update status: OCR processing
        jobs[job_id].update({
            "status": "ocr",
            "progress": 80,
            "message": "Extracting text from frames..."
        })
        print(f"[{job_id}] Status: Extracting text (OCR)...")
        
        frames_with_text = []
        for i, frame in enumerate(cleaned_frames):
            text = await ocr_engine.extract_text(frame)
            frames_with_text.append({
                "image": frame,
                "text": text
            })
            print(f"[{job_id}] ✓ OCR processed frame {i+1}/{len(cleaned_frames)}")
        
        # Update status: Generating PDF
        jobs[job_id].update({
            "status": "generating",
            "progress": 90,
            "message": "Generating PDF..."
        })
        print(f"[{job_id}] Status: Generating PDF...")
        
        pdf_path = OUTPUT_DIR / f"{job_id}.pdf"
        await pdf_generator.create_searchable_pdf(frames_with_text, pdf_path)
        print(f"[{job_id}] ✓ PDF generated: {pdf_path}")
        
        # Update status: Completed
        jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Successfully extracted {len(cleaned_frames)} pages",
            "pdf_path": str(pdf_path),
            "pdf_url": f"/api/download/{job_id}"
        })
        
        print(f"\n{'='*60}")
        print(f"[{job_id}] ✅ EXTRACTION COMPLETE!")
        print(f"Pages extracted: {len(cleaned_frames)}")
        print(f"PDF location: {pdf_path}")
        print(f"{'='*60}\n")
        
        # Cleanup temporary files
        video_processor.cleanup(TEMP_DIR / job_id)
        print(f"[{job_id}] ✓ Cleaned up temporary files")
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[{job_id}] ❌ ERROR: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        jobs[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": "Extraction failed",
            "error": str(e)
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
