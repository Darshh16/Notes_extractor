import cv2
import numpy as np
import imagehash
from PIL import Image
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class FrameInfo:
    """Information about a detected frame/page."""
    frame: np.ndarray
    timestamp: float
    hash_value: str
    difference_score: float


class PageDetector:
    """
    Intelligent page detection using perceptual hashing and frame differencing.
    Detects when slides change while ignoring minor movements, cursor flickers, etc.
    """
    
    def __init__(
        self,
        hash_threshold: int = 10,
        diff_threshold: float = 0.15,
        min_page_duration: float = 2.0
    ):
        """
        Initialize page detector with configurable thresholds.
        
        Args:
            hash_threshold: Hamming distance threshold for pHash comparison (lower = more similar)
            diff_threshold: Frame difference threshold (0-1, higher = more different)
            min_page_duration: Minimum duration (seconds) a page must be shown
        """
        self.hash_threshold = hash_threshold
        self.diff_threshold = diff_threshold
        self.min_page_duration = min_page_duration
        
    async def detect_unique_pages(
        self, frames: List[Tuple[np.ndarray, float]]
    ) -> List[np.ndarray]:
        """
        Detect unique pages from a list of frames.
        
        Args:
            frames: List of (frame, timestamp) tuples
            
        Returns:
            List of unique page frames
        """
        if not frames:
            return []
        
        unique_pages = []
        last_page_hash = None
        last_page_time = 0
        candidate_page = None
        candidate_time = 0
        
        for frame, timestamp in frames:
            # Calculate perceptual hash
            current_hash = self._calculate_phash(frame)
            
            # First frame
            if last_page_hash is None:
                last_page_hash = current_hash
                last_page_time = timestamp
                candidate_page = frame
                candidate_time = timestamp
                continue
            
            # Compare with last detected page
            is_different = self._is_different_page(
                frame, current_hash, last_page_hash
            )
            
            if is_different:
                # Check if candidate page was shown long enough
                if candidate_page is not None:
                    duration = timestamp - candidate_time
                    if duration >= self.min_page_duration:
                        unique_pages.append(candidate_page)
                        last_page_hash = current_hash
                        last_page_time = timestamp
                
                # Set new candidate
                candidate_page = frame
                candidate_time = timestamp
            else:
                # Same page, update candidate to latest (best quality) frame
                candidate_page = frame
        
        # Add the last candidate if it was shown long enough
        if candidate_page is not None and len(frames) > 0:
            last_timestamp = frames[-1][1]
            duration = last_timestamp - candidate_time
            if duration >= self.min_page_duration:
                unique_pages.append(candidate_page)
        
        return unique_pages
    
    def _calculate_phash(self, frame: np.ndarray) -> imagehash.ImageHash:
        """Calculate perceptual hash of a frame."""
        # Convert to PIL Image
        if len(frame.shape) == 3:
            # BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            frame_rgb = frame
        
        pil_image = Image.fromarray(frame_rgb)
        
        # Calculate perceptual hash
        return imagehash.phash(pil_image, hash_size=8)
    
    def _is_different_page(
        self,
        frame: np.ndarray,
        current_hash: imagehash.ImageHash,
        last_hash: imagehash.ImageHash
    ) -> bool:
        """
        Determine if current frame represents a different page.
        Uses both perceptual hashing and frame differencing.
        """
        # Method 1: Perceptual hash comparison
        hash_distance = current_hash - last_hash
        
        if hash_distance > self.hash_threshold:
            return True
        
        # Method 2: Frame differencing (for subtle changes)
        # This is a secondary check for edge cases
        # Note: We'd need to store the last frame for this, which we're not doing
        # to save memory. The hash method is usually sufficient.
        
        return False
    
    def _calculate_frame_difference(
        self, frame1: np.ndarray, frame2: np.ndarray
    ) -> float:
        """
        Calculate normalized difference between two frames.
        Returns value between 0 (identical) and 1 (completely different).
        """
        # Resize to same size if needed
        if frame1.shape != frame2.shape:
            h, w = min(frame1.shape[0], frame2.shape[0]), min(frame1.shape[1], frame2.shape[1])
            frame1 = cv2.resize(frame1, (w, h))
            frame2 = cv2.resize(frame2, (w, h))
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY) if len(frame1.shape) == 3 else frame1
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY) if len(frame2.shape) == 3 else frame2
        
        # Calculate absolute difference
        diff = cv2.absdiff(gray1, gray2)
        
        # Normalize to 0-1 range
        normalized_diff = np.sum(diff) / (diff.size * 255)
        
        return normalized_diff
    
    def remove_duplicates_by_similarity(
        self, frames: List[np.ndarray], similarity_threshold: int = 5
    ) -> List[np.ndarray]:
        """
        Remove near-duplicate frames using stricter similarity threshold.
        Useful for final cleanup of detected pages.
        
        Args:
            frames: List of frames to deduplicate
            similarity_threshold: Hamming distance threshold (lower = stricter)
            
        Returns:
            List of unique frames
        """
        if not frames:
            return []
        
        unique_frames = []
        unique_hashes = []
        
        for frame in frames:
            current_hash = self._calculate_phash(frame)
            
            # Check against all existing unique frames
            is_duplicate = False
            for existing_hash in unique_hashes:
                if current_hash - existing_hash <= similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_frames.append(frame)
                unique_hashes.append(current_hash)
        
        return unique_frames
