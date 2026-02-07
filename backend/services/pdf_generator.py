from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfgen import canvas
from PIL import Image as PILImage
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict
import io
from datetime import datetime


class PDFGenerator:
    """Service for generating searchable PDFs from extracted frames and text."""
    
    def __init__(self, page_size=A4):
        """
        Initialize PDF generator.
        
        Args:
            page_size: Page size for PDF (default: A4)
        """
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        
        # Create custom style for OCR text
        self.ocr_style = ParagraphStyle(
            'OCRText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor='white',  # Invisible text for searchability
            leading=10,
            alignment=TA_LEFT
        )
    
    async def create_searchable_pdf(
        self, frames_with_text: List[Dict], output_path: Path
    ):
        """
        Create a searchable PDF from frames and extracted text.
        
        Args:
            frames_with_text: List of dicts with 'image' and 'text' keys
            output_path: Path to save the PDF
        """
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=self.page_size,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Build content
        story = []
        
        # Add title page
        story.extend(self._create_title_page())
        story.append(PageBreak())
        
        # Add each frame with its text
        for i, item in enumerate(frames_with_text):
            frame = item['image']
            text = item['text']
            
            # Add frame image
            img_element = self._create_image_element(frame)
            if img_element:
                story.append(img_element)
            
            # Add invisible searchable text
            if text:
                # Split text into paragraphs for better searchability
                paragraphs = text.split('\n')
                for para in paragraphs:
                    if para.strip():
                        story.append(Paragraph(para, self.ocr_style))
                        story.append(Spacer(1, 0.1*inch))
            
            # Add page break between slides
            if i < len(frames_with_text) - 1:
                story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
    
    def _create_title_page(self) -> List:
        """Create a title page for the PDF."""
        elements = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor='#2196F3',
            spaceAfter=30,
            alignment=TA_LEFT
        )
        
        elements.append(Paragraph("YouTube Study Notes", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Metadata
        meta_style = self.styles['Normal']
        elements.append(
            Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style)
        )
        elements.append(Spacer(1, 0.2*inch))
        
        # Description
        desc_style = ParagraphStyle(
            'Description',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14
        )
        
        description = """
        This PDF contains automatically extracted slides from a YouTube video.
        All text has been extracted using OCR and is searchable.
        Obstructions such as facecams and overlays have been intelligently removed.
        """
        
        elements.append(Paragraph(description, desc_style))
        
        return elements
    
    def _create_image_element(self, frame: np.ndarray) -> Image:
        """
        Convert OpenCV frame to ReportLab Image element.
        
        Args:
            frame: OpenCV frame (BGR format)
            
        Returns:
            ReportLab Image element
        """
        # Convert BGR to RGB
        if len(frame.shape) == 3:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            frame_rgb = frame
        
        # Convert to PIL Image
        pil_image = PILImage.fromarray(frame_rgb)
        
        # Save to bytes buffer
        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Calculate dimensions to fit page
        page_width, page_height = self.page_size
        max_width = page_width - 1*inch
        max_height = page_height - 2*inch
        
        # Get image dimensions
        img_width, img_height = pil_image.size
        
        # Calculate scaling
        width_ratio = max_width / img_width
        height_ratio = max_height / img_height
        scale = min(width_ratio, height_ratio)
        
        final_width = img_width * scale
        final_height = img_height * scale
        
        # Create ReportLab Image
        img_element = Image(img_buffer, width=final_width, height=final_height)
        
        return img_element
    
    async def create_simple_pdf(
        self, frames: List[np.ndarray], output_path: Path
    ):
        """
        Create a simple PDF without OCR text (faster, non-searchable).
        
        Args:
            frames: List of frames
            output_path: Path to save the PDF
        """
        frames_with_text = [{'image': frame, 'text': ''} for frame in frames]
        await self.create_searchable_pdf(frames_with_text, output_path)
