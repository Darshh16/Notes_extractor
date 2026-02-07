import pytesseract
import cv2
import numpy as np
from typing import Optional
import re


class OCREngine:
    """Service for extracting text from images using Tesseract OCR."""
    
    def __init__(self, lang: str = 'eng'):
        """
        Initialize OCR engine.
        
        Args:
            lang: Language code for OCR (default: 'eng' for English)
        """
        self.lang = lang
        
        # Configure Tesseract (you may need to set the path on Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    async def extract_text(self, frame: np.ndarray) -> str:
        """
        Extract text from a frame using OCR.
        
        Args:
            frame: Input image frame
            
        Returns:
            Extracted text
        """
        # Preprocess image for better OCR results
        processed = self._preprocess_for_ocr(frame)
        
        # Extract text using Tesseract
        custom_config = r'--oem 3 --psm 6'  # LSTM OCR Engine, assume uniform block of text
        text = pytesseract.image_to_string(
            processed,
            lang=self.lang,
            config=custom_config
        )
        
        # Clean up extracted text
        text = self._clean_text(text)
        
        return text
    
    def _preprocess_for_ocr(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy.
        Applies grayscale conversion, denoising, and thresholding.
        """
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(denoised)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    
    def _clean_text(self, text: str) -> str:
        """Clean up extracted text by removing noise and formatting."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[|\\]', '', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    async def extract_text_with_confidence(
        self, frame: np.ndarray
    ) -> tuple[str, float]:
        """
        Extract text with confidence score.
        
        Returns:
            Tuple of (text, confidence_score)
        """
        processed = self._preprocess_for_ocr(frame)
        
        # Get detailed OCR data
        data = pytesseract.image_to_data(
            processed,
            lang=self.lang,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract text and calculate average confidence
        text_parts = []
        confidences = []
        
        for i, conf in enumerate(data['conf']):
            if int(conf) > 0:  # Filter out low confidence
                text_parts.append(data['text'][i])
                confidences.append(int(conf))
        
        text = ' '.join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return self._clean_text(text), avg_confidence / 100.0
