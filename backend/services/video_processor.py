import cv2
import yt_dlp
import os
from pathlib import Path
from typing import List, Tuple
import numpy as np
import shutil


class VideoProcessor:
    """Service for downloading and processing YouTube videos."""
    
    def __init__(self, fps: int = 1):
        """
        Initialize video processor.
        
        Args:
            fps: Frames per second to extract (default: 1 frame per second)
        """
        self.fps = fps
        
    async def download_video(
        self, url: str, quality: str, output_dir: Path
    ) -> Path:
        """
        Download YouTube video using yt-dlp.
        
        Args:
            url: YouTube video URL
            quality: Video quality (e.g., '720p', '1080p')
            output_dir: Directory to save the video
            
        Returns:
            Path to downloaded video file
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure yt-dlp options
        # Try to merge video+audio, but fallback to single format if FFmpeg not available
        ydl_opts = {
            'format': f'bestvideo[height<={quality[:-1]}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality[:-1]}][ext=mp4]/best',
            'outtmpl': str(output_dir / 'video.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'merge_output_format': 'mp4',
            # Don't abort if FFmpeg is missing, just use best single format
            'ignoreerrors': False,
            'no_abort_on_error': True,
        }
        
        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        return Path(filename)
    
    async def extract_frames(
        self, video_path: Path
    ) -> List[Tuple[np.ndarray, float]]:
        """
        Extract frames from video at specified FPS.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of (frame, timestamp) tuples
        """
        frames = []
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame interval
        frame_interval = int(video_fps / self.fps)
        
        frame_count = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Extract frame at specified interval
            if frame_count % frame_interval == 0:
                timestamp = frame_count / video_fps
                frames.append((frame, timestamp))
                extracted_count += 1
            
            frame_count += 1
        
        cap.release()
        
        return frames
    
    def cleanup(self, directory: Path):
        """Clean up temporary files."""
        if directory.exists():
            shutil.rmtree(directory)
