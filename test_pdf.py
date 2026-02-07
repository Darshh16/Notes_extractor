"""
Test PDF generation to verify it works
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from pathlib import Path

# Create test PDF
pdf_path = Path("backend/output/test.pdf")
pdf_path.parent.mkdir(exist_ok=True)

doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
story = []
styles = getSampleStyleSheet()

# Add content
story.append(Paragraph("<b>Test PDF</b>", styles['Heading1']))
story.append(Spacer(1, 0.5*inch))
story.append(Paragraph("This is a test PDF to verify generation works.", styles['Normal']))

# Build PDF
doc.build(story)

print(f"✓ Test PDF created: {pdf_path}")
print(f"✓ File size: {pdf_path.stat().st_size} bytes")

# Verify it's a valid PDF
with open(pdf_path, 'rb') as f:
    header = f.read(5)
    if header == b'%PDF-':
        print("✓ Valid PDF header")
    else:
        print(f"✗ Invalid header: {header}")
