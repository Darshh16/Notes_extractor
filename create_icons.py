"""
Quick script to create placeholder icons for the Chrome extension
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory if it doesn't exist
os.makedirs('extension/icons', exist_ok=True)

def create_icon(size):
    """Create a simple gradient icon with YN text"""
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background (purple)
    for y in range(size):
        # Gradient from #667eea to #764ba2
        r = int(102 + (118 - 102) * y / size)
        g = int(126 + (75 - 126) * y / size)
        b = int(234 + (162 - 234) * y / size)
        draw.rectangle([(0, y), (size, y+1)], fill=(r, g, b, 255))
    
    # Draw rounded corners
    corner_radius = size // 8
    draw.rectangle([(0, 0), (corner_radius, corner_radius)], fill=(0, 0, 0, 0))
    draw.rectangle([(size-corner_radius, 0), (size, corner_radius)], fill=(0, 0, 0, 0))
    draw.rectangle([(0, size-corner_radius), (corner_radius, size)], fill=(0, 0, 0, 0))
    draw.rectangle([(size-corner_radius, size-corner_radius), (size, size)], fill=(0, 0, 0, 0))
    
    # Draw play button symbol (white triangle)
    if size >= 48:
        triangle_size = size // 3
        center_x, center_y = size // 2, size // 2
        points = [
            (center_x - triangle_size//3, center_y - triangle_size//2),
            (center_x - triangle_size//3, center_y + triangle_size//2),
            (center_x + triangle_size//2, center_y)
        ]
        draw.polygon(points, fill=(255, 255, 255, 255))
    
    # For 16px, just draw a simple white dot
    if size == 16:
        draw.ellipse([(size//3, size//3), (2*size//3, 2*size//3)], fill=(255, 255, 255, 255))
    
    return img

# Create all three icon sizes
sizes = [16, 48, 128]
for size in sizes:
    icon = create_icon(size)
    icon.save(f'extension/icons/icon{size}.png', 'PNG')
    print(f'Created icon{size}.png')

print('\n✓ All icons created successfully!')
print('You can now load the extension in Chrome.')
