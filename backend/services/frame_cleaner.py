import cv2
import numpy as np
# import mediapipe as mp  # Temporarily disabled due to protobuf conflicts
from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class ObstructionRegion:
    """Represents a detected obstruction in the frame."""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    type: str  # 'face', 'overlay', 'watermark'


class FrameCleaner:
    """
    Intelligent frame cleaning service that removes obstructions like facecams,
    overlays, and watermarks using AI-powered detection and inpainting.
    
    This is the core "agentic" component that self-corrects and validates its work.
    """
    
    def __init__(self):
        # Initialize Mediapipe Face Detection
        # TEMPORARILY DISABLED due to protobuf conflicts
        # self.mp_face_detection = mp.solutions.face_detection
        # self.face_detection = self.mp_face_detection.FaceDetection(
        #     model_selection=1,  # Full range model
        #     min_detection_confidence=0.5
        # )
        self.face_detection = None  # Disabled
        
        # Initialize Haar Cascade as primary method
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Quality thresholds for self-correction
        self.MIN_BRIGHTNESS = 20
        self.MAX_BRIGHTNESS = 235
        self.MIN_SHARPNESS = 50
        self.MIN_FRAME_SIZE = (320, 240)
        
    def is_low_quality(self, frame: np.ndarray) -> bool:
        """
        Agentic quality check: Determine if frame is too low quality to process.
        Returns True if frame should be skipped.
        """
        if frame is None or frame.size == 0:
            return True
        
        # Check minimum dimensions
        h, w = frame.shape[:2]
        if h < self.MIN_FRAME_SIZE[1] or w < self.MIN_FRAME_SIZE[0]:
            return True
        
        # Check brightness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        if mean_brightness < self.MIN_BRIGHTNESS or mean_brightness > self.MAX_BRIGHTNESS:
            return True
        
        # Check sharpness using Laplacian variance
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < self.MIN_SHARPNESS:
            return True
        
        return False
    
    def is_valid_cleaned_frame(self, frame: np.ndarray) -> bool:
        """
        Agentic validation: Verify that cleaning didn't corrupt the frame.
        Returns True if the cleaned frame is valid.
        """
        if frame is None or frame.size == 0:
            return False
        
        # Check for excessive black/white areas (sign of bad inpainting)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        black_pixels = np.sum(gray < 10)
        white_pixels = np.sum(gray > 245)
        total_pixels = gray.size
        
        # If more than 80% is pure black or white, cleaning likely failed
        if (black_pixels + white_pixels) / total_pixels > 0.8:
            return False
        
        return True
    
    async def remove_obstructions(self, frame: np.ndarray) -> np.ndarray:
        """
        Main cleaning function: Detects and removes obstructions from frame.
        Uses multiple detection methods and self-corrects if needed.
        """
        if self.is_low_quality(frame):
            return frame
        
        # Detect all obstructions
        obstructions = self._detect_all_obstructions(frame)
        
        if not obstructions:
            return frame
        
        # Create a copy for cleaning
        cleaned_frame = frame.copy()
        
        # Remove each obstruction
        for obstruction in obstructions:
            cleaned_frame = self._remove_obstruction(cleaned_frame, obstruction)
        
        # Self-correction: Validate the result
        if not self.is_valid_cleaned_frame(cleaned_frame):
            # If cleaning failed, try a more conservative approach
            cleaned_frame = self._conservative_clean(frame, obstructions)
            
            # If still invalid, return original
            if not self.is_valid_cleaned_frame(cleaned_frame):
                return frame
        
        return cleaned_frame
    
    def _detect_all_obstructions(self, frame: np.ndarray) -> List[ObstructionRegion]:
        """Detect all types of obstructions in the frame."""
        obstructions = []
        
        # 1. Detect faces using Mediapipe (DISABLED)
        # obstructions.extend(self._detect_faces_mediapipe(frame))
        
        # 2. Use Haar Cascade as primary method
        obstructions.extend(self._detect_faces_haar(frame))
        
        # 3. Detect common overlay regions (corners, bottom)
        obstructions.extend(self._detect_overlays(frame))
        
        # 4. Merge overlapping regions
        obstructions = self._merge_overlapping_regions(obstructions)
        
        return obstructions
    
    def _detect_faces_mediapipe(self, frame: np.ndarray) -> List[ObstructionRegion]:
        """Detect faces using Mediapipe Face Detection (DISABLED)."""
        # Disabled due to protobuf conflicts
        return []
    
    def _detect_faces_haar(self, frame: np.ndarray) -> List[ObstructionRegion]:
        """Fallback face detection using Haar Cascade."""
        obstructions = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        
        for (x, y, w, h) in faces:
            # Expand to include body
            expansion = 0.3
            x = max(0, int(x - w * expansion))
            y = max(0, int(y - h * expansion))
            w = int(w * (1 + 2 * expansion))
            h = int(h * (1 + 2 * expansion))
            
            obstructions.append(ObstructionRegion(
                x=x, y=y, width=w, height=h,
                confidence=0.7,
                type='face'
            ))
        
        return obstructions
    
    def _detect_overlays(self, frame: np.ndarray) -> List[ObstructionRegion]:
        """
        Detect common overlay regions like social media handles, logos.
        These are typically in corners or bottom of frame.
        """
        obstructions = []
        h, w = frame.shape[:2]
        
        # Define common overlay regions (relative to frame size)
        overlay_regions = [
            # Bottom center (common for social media handles)
            (int(w * 0.3), int(h * 0.85), int(w * 0.4), int(h * 0.1)),
            # Bottom right
            (int(w * 0.75), int(h * 0.85), int(w * 0.2), int(h * 0.1)),
            # Top right (logo area)
            (int(w * 0.8), int(h * 0.05), int(w * 0.15), int(h * 0.1)),
        ]
        
        for x, y, width, height in overlay_regions:
            roi = frame[y:y+height, x:x+width]
            
            # Check if region has text/graphics (high edge density)
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray_roi, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # If edge density is high, likely an overlay
            if edge_density > 0.1:
                obstructions.append(ObstructionRegion(
                    x=x, y=y, width=width, height=height,
                    confidence=edge_density,
                    type='overlay'
                ))
        
        return obstructions
    
    def _merge_overlapping_regions(
        self, regions: List[ObstructionRegion]
    ) -> List[ObstructionRegion]:
        """Merge overlapping obstruction regions."""
        if len(regions) <= 1:
            return regions
        
        merged = []
        sorted_regions = sorted(regions, key=lambda r: r.x)
        
        current = sorted_regions[0]
        
        for next_region in sorted_regions[1:]:
            # Check if regions overlap
            if self._regions_overlap(current, next_region):
                # Merge regions
                current = self._merge_two_regions(current, next_region)
            else:
                merged.append(current)
                current = next_region
        
        merged.append(current)
        return merged
    
    def _regions_overlap(self, r1: ObstructionRegion, r2: ObstructionRegion) -> bool:
        """Check if two regions overlap."""
        return not (r1.x + r1.width < r2.x or
                   r2.x + r2.width < r1.x or
                   r1.y + r1.height < r2.y or
                   r2.y + r2.height < r1.y)
    
    def _merge_two_regions(
        self, r1: ObstructionRegion, r2: ObstructionRegion
    ) -> ObstructionRegion:
        """Merge two overlapping regions."""
        x = min(r1.x, r2.x)
        y = min(r1.y, r2.y)
        width = max(r1.x + r1.width, r2.x + r2.width) - x
        height = max(r1.y + r1.height, r2.y + r2.height) - y
        
        return ObstructionRegion(
            x=x, y=y, width=width, height=height,
            confidence=max(r1.confidence, r2.confidence),
            type=r1.type if r1.confidence > r2.confidence else r2.type
        )
    
    def _remove_obstruction(
        self, frame: np.ndarray, obstruction: ObstructionRegion
    ) -> np.ndarray:
        """Remove a single obstruction using intelligent inpainting."""
        # Create mask for the obstruction
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        mask[
            obstruction.y:obstruction.y + obstruction.height,
            obstruction.x:obstruction.x + obstruction.width
        ] = 255
        
        # Use Telea inpainting algorithm (fast and good for text/graphics)
        result = cv2.inpaint(frame, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        
        return result
    
    def _conservative_clean(
        self, frame: np.ndarray, obstructions: List[ObstructionRegion]
    ) -> np.ndarray:
        """
        Conservative cleaning approach: Replace obstructions with blurred background.
        Used as fallback when aggressive inpainting fails.
        """
        cleaned = frame.copy()
        
        for obstruction in obstructions:
            # Extract surrounding region for background estimation
            padding = 20
            y1 = max(0, obstruction.y - padding)
            y2 = min(frame.shape[0], obstruction.y + obstruction.height + padding)
            x1 = max(0, obstruction.x - padding)
            x2 = min(frame.shape[1], obstruction.x + obstruction.width + padding)
            
            surrounding = frame[y1:y2, x1:x2]
            
            # Get dominant color from surrounding area
            avg_color = cv2.mean(surrounding)[:3]
            
            # Fill obstruction with averaged color
            cleaned[
                obstruction.y:obstruction.y + obstruction.height,
                obstruction.x:obstruction.x + obstruction.width
            ] = avg_color
            
            # Apply slight blur to blend
            roi = cleaned[
                obstruction.y:obstruction.y + obstruction.height,
                obstruction.x:obstruction.x + obstruction.width
            ]
            blurred = cv2.GaussianBlur(roi, (15, 15), 0)
            cleaned[
                obstruction.y:obstruction.y + obstruction.height,
                obstruction.x:obstruction.x + obstruction.width
            ] = blurred
        
        return cleaned
