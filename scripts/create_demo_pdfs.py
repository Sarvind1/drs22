#!/usr/bin/env python3
"""Generate sample PDF files for demo purposes."""

import os
from pathlib import Path
import shutil
import sys
import tempfile
from PIL import Image, ImageDraw, ImageFont
import io

def create_sample_pdf(output_path, doc_type, batch, version, status):
    """Create a sample PDF with basic information."""
    # Calculate dimensions for an A4 size at 72 DPI
    width, height = 595, 842
    
    # Create a white background image
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a system font, fallback to default if not available
    try:
        font_large = ImageFont.truetype('Arial', 36)
        font_medium = ImageFont.truetype('Arial', 24)
        font_small = ImageFont.truetype('Arial', 18)
    except IOError:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large
    
    # Draw borders
    draw.rectangle([(20, 20), (width-20, height-20)], outline='black', width=2)
    
    # Draw header
    draw.text((width//2, 50), f"{doc_type} Document", font=font_large, fill='black', anchor='mt')
    draw.text((width//2, 100), f"Batch: {batch}", font=font_medium, fill='black', anchor='mt')
    
    # Draw content
    y_position = 150
    draw.text((width//2, y_position), f"Version: {version}", font=font_medium, fill='black', anchor='mt')
    y_position += 40
    draw.text((width//2, y_position), f"Status: {status}", font=font_medium, fill='black', anchor='mt')
    y_position += 40
    
    # Draw some content lines
    for i in range(10):
        y_position += 30
        draw.text((40, y_position), f"Sample content line {i+1} for demonstration purposes", 
                 font=font_small, fill='black')
    
    # Draw footer
    draw.text((width//2, height-50), "This is a sample document for demo purposes", 
             font=font_small, fill='gray', anchor='mt')
    
    # Save as PDF
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path, 'PDF')

def main():
    """Generate sample PDFs for the demo."""
    base_dir = Path(__file__).parent.parent
    static_dir = base_dir / 'static' / 'documents'
    
    # Ensure the directory exists
    os.makedirs(static_dir, exist_ok=True)
    
    # Sample data
    batches = ['B001', 'B002', 'B003']
    doc_types = ['CI', 'PL']
    statuses = ['Pending', 'Accepted', 'Rejected', 'In Review']
    
    for batch_idx, batch in enumerate(batches):
        for doc_type in doc_types:
            # Create 2 versions for each batch and document type
            for version in range(1, 3):
                status = statuses[(batch_idx + version) % len(statuses)]
                output_path = static_dir / doc_type / batch / f"{batch}_{version}.pdf"
                print(f"Creating sample PDF: {output_path}")
                create_sample_pdf(output_path, doc_type, batch, version, status)

if __name__ == "__main__":
    main()
    print("Sample PDFs created successfully!") 