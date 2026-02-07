"""
Production YouTube Notes Extractor Server
Minimal version without Mediapipe/TensorFlow dependencies
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
import asyncio
import traceback

# Import only the services we need (without Mediapipe)
from services.video_processor import VideoProcessor
from services.page_detector import PageDetector
from services.ocr_engine import OCREngine
from services.pdf_generator import PDFGenerator

# Simplified frame cleaner without face detection
import cv2
import numpy as np

app = FastAPI(
    title="YouTube Notes Extractor API",
    description="Extract clean study notes from YouTube videos",
    version="1.0.0-production"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
video_processor = VideoProcessor()
page_detector = PageDetector()
ocr_engine = OCREngine()
pdf_generator = PDFGenerator()

# Storage paths
BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Job storage
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
        "message": "YouTube Notes Extractor API",
        "version": "1.0.0-production",
        "status": "running",
        "mode": "minimal (no Mediapipe)"
    }

@app.post("/api/extract", response_model=JobStatus)
async def extract_notes(request: VideoRequest, background_tasks: BackgroundTasks):
    """Start extraction process"""
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
    print(f"Quality: {request.quality}")
    print(f"{'='*60}\n")
    
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
    """Get job status"""
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
    """Download generated PDF"""
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
    """
    Main processing pipeline - runs in background thread
    No async needed since it runs in background
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
        
        # Create job directory
        job_dir = TEMP_DIR / job_id
        job_dir.mkdir(exist_ok=True)
        
        # Download video with latest yt-dlp configuration
        import yt_dlp
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': str(job_dir / 'video.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'age_limit': None,
            # Critical: Use latest extractor args to bypass 403
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"[{job_id}] Downloading from: {url}")
                info = ydl.extract_info(url, download=True)
                video_path = Path(ydl.prepare_filename(info))
        except Exception as download_error:
            print(f"[{job_id}] Download failed, trying alternative method...")
            # Fallback: Try with different client
            ydl_opts['extractor_args']['youtube']['player_client'] = ['android']
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = Path(ydl.prepare_filename(info))
        
        print(f"[{job_id}] ✓ Video downloaded: {video_path}")
        
        # Update status: Extracting frames
        jobs[job_id].update({
            "status": "extracting",
            "progress": 25,
            "message": "Extracting frames..."
        })
        print(f"[{job_id}] Status: Extracting frames...")
        
        # Extract frames
        frames = []
        cap = cv2.VideoCapture(str(video_path))
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(video_fps / 1)  # 1 frame per second
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                timestamp = frame_count / video_fps
                frames.append((frame, timestamp))
            
            frame_count += 1
        
        cap.release()
        print(f"[{job_id}] ✓ Extracted {len(frames)} frames")
        
        # Update status: Detecting pages
        jobs[job_id].update({
            "status": "detecting",
            "progress": 40,
            "message": "Detecting unique pages..."
        })
        print(f"[{job_id}] Status: Detecting unique pages...")
        
        # Detect unique pages using perceptual hashing
        import imagehash
        from PIL import Image
        
        unique_frames = []
        last_hash = None
        hash_threshold = 10
        
        for frame, timestamp in frames:
            # Convert to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_hash = imagehash.phash(pil_image, hash_size=8)
            
            if last_hash is None or (frame_hash - last_hash) > hash_threshold:
                unique_frames.append(frame)
                last_hash = frame_hash
        
        print(f"[{job_id}] ✓ Detected {len(unique_frames)} unique pages")
        
        # Update status: OCR processing
        jobs[job_id].update({
            "status": "ocr",
            "progress": 70,
            "message": f"Extracting text from {len(unique_frames)} frames..."
        })
        print(f"[{job_id}] Status: Extracting text (OCR)...")
        
        # OCR processing
        frames_with_text = []
        for i, frame in enumerate(unique_frames):
            # Preprocess for OCR
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Extract text
            import pytesseract
            text = pytesseract.image_to_string(denoised)
            
            frames_with_text.append({
                "image": frame,
                "text": text
            })
            print(f"[{job_id}] ✓ OCR processed frame {i+1}/{len(unique_frames)}")
        
        # Update status: Generating PDF
        jobs[job_id].update({
            "status": "generating",
            "progress": 90,
            "message": "Generating PDF..."
        })
        print(f"[{job_id}] Status: Generating PDF...")
        
        # Generate PDF
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_LEFT
        import io
        
        pdf_path = OUTPUT_DIR / f"{job_id}.pdf"
        
        # Create PDF with proper settings
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Create custom style for OCR text
        ocr_style = ParagraphStyle(
            'OCRText',
            parent=styles['Normal'],
            fontSize=8,
            textColor='grey',
            alignment=TA_LEFT
        )
        
        # Save all frames as images first
        temp_images = []
        for i, item in enumerate(frames_with_text):
            temp_img = job_dir / f"frame_{i}.jpg"
            # Save with high quality
            cv2.imwrite(str(temp_img), item["image"], [cv2.IMWRITE_JPEG_QUALITY, 95])
            temp_images.append(temp_img)
        
        # Build PDF content
        for i, item in enumerate(frames_with_text):
            try:
                # Add page number
                page_num = Paragraph(f"<b>Page {i+1} of {len(frames_with_text)}</b>", styles['Heading2'])
                story.append(page_num)
                story.append(Spacer(1, 0.2*inch))
                
                # Add image
                img_path = str(temp_images[i])
                img = RLImage(img_path, width=7*inch, height=5.25*inch)
                story.append(img)
                story.append(Spacer(1, 0.3*inch))
                
                # Add OCR text if available
                if item["text"].strip():
                    # Clean text for PDF
                    clean_text = item["text"].replace('\x00', '').strip()
                    if clean_text:
                        text_para = Paragraph(f"<i>Extracted Text:</i><br/>{clean_text[:500]}", ocr_style)
                        story.append(text_para)
                
                # Add page break except for last page
                if i < len(frames_with_text) - 1:
                    story.append(PageBreak())
                    
            except Exception as e:
                print(f"[{job_id}] ⚠ Error adding page {i+1}: {e}")
                continue
        
        # Build PDF
        try:
            doc.build(story)
            print(f"[{job_id}] ✓ PDF generated: {pdf_path}")
        except Exception as e:
            print(f"[{job_id}] ❌ PDF build error: {e}")
            raise
        
        # Update status: Completed
        jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Successfully extracted {len(unique_frames)} pages",
            "pdf_path": str(pdf_path),
            "pdf_url": f"/api/download/{job_id}"
        })
        
        print(f"\n{'='*60}")
        print(f"[{job_id}] ✅ EXTRACTION COMPLETE!")
        print(f"Pages extracted: {len(unique_frames)}")
        print(f"PDF location: {pdf_path}")
        print(f"{'='*60}\n")
        
        # Cleanup temporary files
        import shutil
        if job_dir.exists():
            shutil.rmtree(job_dir)
        print(f"[{job_id}] ✓ Cleaned up temporary files")
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[{job_id}] ❌ ERROR: {str(e)}")
        print(f"Error type: {type(e).__name__}")
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
    print("\n" + "="*60)
    print("  YouTube Notes Extractor - Production Server")
    print("="*60)
    print("  Mode: PRODUCTION (Minimal - No Mediapipe)")
    print("  Server: http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print("  ")
    print("  Features:")
    print("  ✅ Real video download (yt-dlp)")
    print("  ✅ Frame extraction (OpenCV)")
    print("  ✅ Page detection (perceptual hashing)")
    print("  ✅ OCR (Tesseract)")
    print("  ✅ PDF generation (ReportLab)")
    print("  ⚠️ No face detection (Mediapipe disabled)")
    print("  ")
    print("  Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
