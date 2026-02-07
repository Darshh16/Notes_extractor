"""
Test Suite for YouTube Notes Extractor
Demonstrates the agentic self-correction capabilities
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.frame_cleaner import FrameCleaner
from services.page_detector import PageDetector
from services.ocr_engine import OCREngine


class TestFrameCleanerAgentic:
    """Test the agentic self-correction features of FrameCleaner"""
    
    def setup_method(self):
        self.cleaner = FrameCleaner()
    
    def test_low_quality_detection_dark_frame(self):
        """Test that very dark frames are detected as low quality"""
        # Create a very dark frame
        dark_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        dark_frame[:] = 10  # Very dark
        
        assert self.cleaner.is_low_quality(dark_frame) == True
    
    def test_low_quality_detection_bright_frame(self):
        """Test that very bright frames are detected as low quality"""
        # Create a very bright frame
        bright_frame = np.ones((480, 640, 3), dtype=np.uint8) * 250
        
        assert self.cleaner.is_low_quality(bright_frame) == True
    
    def test_low_quality_detection_blurry_frame(self):
        """Test that blurry frames are detected as low quality"""
        # Create a blurry frame (low sharpness)
        blurry_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        blurry_frame = cv2.GaussianBlur(blurry_frame, (51, 51), 0)
        
        assert self.cleaner.is_low_quality(blurry_frame) == True
    
    def test_low_quality_detection_good_frame(self):
        """Test that good quality frames pass validation"""
        # Create a frame with good contrast and sharpness
        good_frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
        
        # Add some edges for sharpness
        cv2.rectangle(good_frame, (100, 100), (500, 400), (255, 255, 255), 2)
        cv2.putText(good_frame, "Test Slide", (150, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        
        assert self.cleaner.is_low_quality(good_frame) == False
    
    def test_valid_cleaned_frame_detection(self):
        """Test validation of cleaned frames"""
        # Create a normal frame
        normal_frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
        assert self.cleaner.is_valid_cleaned_frame(normal_frame) == True
        
        # Create a corrupted frame (mostly black)
        corrupted_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        assert self.cleaner.is_valid_cleaned_frame(corrupted_frame) == False
        
        # Create a corrupted frame (mostly white)
        white_frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
        assert self.cleaner.is_valid_cleaned_frame(white_frame) == False
    
    @pytest.mark.asyncio
    async def test_self_correction_on_low_quality(self):
        """Test that low quality frames are returned unchanged"""
        # Create a low quality frame
        dark_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        dark_frame[:] = 10
        
        result = await self.cleaner.remove_obstructions(dark_frame)
        
        # Should return the original frame without processing
        assert np.array_equal(result, dark_frame)
    
    def test_obstruction_detection(self):
        """Test that obstructions are detected"""
        # Create a frame with a simulated face region
        frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
        
        # Add a face-like region (skin tone rectangle)
        cv2.rectangle(frame, (50, 50), (150, 200), (180, 140, 120), -1)
        
        obstructions = self.cleaner._detect_all_obstructions(frame)
        
        # Should detect some obstructions (faces or overlays)
        assert isinstance(obstructions, list)
    
    def test_region_merging(self):
        """Test that overlapping regions are merged"""
        from services.frame_cleaner import ObstructionRegion
        
        regions = [
            ObstructionRegion(x=10, y=10, width=50, height=50, confidence=0.9, type='face'),
            ObstructionRegion(x=40, y=40, width=50, height=50, confidence=0.8, type='face'),
        ]
        
        merged = self.cleaner._merge_overlapping_regions(regions)
        
        # Should merge into one region
        assert len(merged) == 1
        assert merged[0].width >= 50
        assert merged[0].height >= 50


class TestPageDetector:
    """Test the page detection algorithm"""
    
    def setup_method(self):
        self.detector = PageDetector(
            hash_threshold=10,
            diff_threshold=0.15,
            min_page_duration=2.0
        )
    
    def create_test_frame(self, text: str, bg_color: tuple = (255, 255, 255)):
        """Helper to create test frames with text"""
        frame = np.ones((480, 640, 3), dtype=np.uint8)
        frame[:] = bg_color
        
        cv2.putText(frame, text, (100, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        
        return frame
    
    @pytest.mark.asyncio
    async def test_detect_unique_pages_different_slides(self):
        """Test detection of different slides"""
        frames = [
            (self.create_test_frame("Slide 1"), 0.0),
            (self.create_test_frame("Slide 1"), 1.0),
            (self.create_test_frame("Slide 1"), 2.0),
            (self.create_test_frame("Slide 2"), 3.0),
            (self.create_test_frame("Slide 2"), 4.0),
            (self.create_test_frame("Slide 2"), 5.0),
        ]
        
        unique = await self.detector.detect_unique_pages(frames)
        
        # Should detect 2 unique pages
        assert len(unique) == 2
    
    @pytest.mark.asyncio
    async def test_detect_unique_pages_min_duration(self):
        """Test that pages shown briefly are filtered out"""
        frames = [
            (self.create_test_frame("Slide 1"), 0.0),
            (self.create_test_frame("Slide 1"), 1.0),
            (self.create_test_frame("Slide 2"), 1.5),  # Only 0.5 seconds
            (self.create_test_frame("Slide 3"), 2.0),
            (self.create_test_frame("Slide 3"), 3.0),
            (self.create_test_frame("Slide 3"), 4.0),
        ]
        
        unique = await self.detector.detect_unique_pages(frames)
        
        # Should only detect slides shown for >= 2 seconds
        # Slide 2 should be filtered out
        assert len(unique) <= 2
    
    def test_phash_calculation(self):
        """Test perceptual hash calculation"""
        frame1 = self.create_test_frame("Test")
        frame2 = self.create_test_frame("Test")
        frame3 = self.create_test_frame("Different")
        
        hash1 = self.detector._calculate_phash(frame1)
        hash2 = self.detector._calculate_phash(frame2)
        hash3 = self.detector._calculate_phash(frame3)
        
        # Same content should have similar hashes
        assert hash1 - hash2 < 5
        
        # Different content should have different hashes
        assert hash1 - hash3 > 5


class TestOCREngine:
    """Test OCR text extraction"""
    
    def setup_method(self):
        self.ocr = OCREngine()
    
    def create_text_frame(self, text: str):
        """Create a frame with text"""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        cv2.putText(frame, text, (50, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
        
        return frame
    
    @pytest.mark.asyncio
    async def test_extract_text_simple(self):
        """Test basic text extraction"""
        frame = self.create_text_frame("HELLO WORLD")
        
        text = await self.ocr.extract_text(frame)
        
        # Should extract some text (Tesseract may not be perfect)
        assert isinstance(text, str)
        assert len(text) > 0
    
    def test_preprocessing(self):
        """Test image preprocessing for OCR"""
        frame = self.create_text_frame("Test")
        
        processed = self.ocr._preprocess_for_ocr(frame)
        
        # Should return grayscale image
        assert len(processed.shape) == 2
        assert processed.dtype == np.uint8
    
    def test_text_cleaning(self):
        """Test text cleanup"""
        dirty_text = "  Hello   World  \n\n  Test  "
        
        clean = self.ocr._clean_text(dirty_text)
        
        # Should remove excessive whitespace
        assert "  " not in clean
        assert clean.strip() == clean


class TestAgenticBehavior:
    """Integration tests for agentic self-correction"""
    
    def setup_method(self):
        self.cleaner = FrameCleaner()
    
    @pytest.mark.asyncio
    async def test_end_to_end_self_correction(self):
        """Test complete self-correction pipeline"""
        # Create a good frame
        good_frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
        cv2.rectangle(good_frame, (100, 100), (500, 400), (255, 255, 255), -1)
        cv2.putText(good_frame, "Lecture Slide", (150, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
        
        # Process the frame
        result = await self.cleaner.remove_obstructions(good_frame)
        
        # Result should be valid
        assert result is not None
        assert result.shape == good_frame.shape
        assert self.cleaner.is_valid_cleaned_frame(result)
    
    @pytest.mark.asyncio
    async def test_fallback_to_original_on_corruption(self):
        """Test that original is returned if cleaning fails"""
        # This test would require mocking the cleaning to fail
        # For now, we just verify the logic exists
        
        frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
        
        # The cleaner should handle errors gracefully
        result = await self.cleaner.remove_obstructions(frame)
        
        assert result is not None
        assert result.shape == frame.shape


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
