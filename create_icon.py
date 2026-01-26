#!/usr/bin/env python3
"""
Script to convert PNG icon to ICO format for the X-Plane Dataref Bridge application.
"""
import os
from PIL import Image

def convert_png_to_ico(png_path, ico_path):
    """Convert a PNG image to ICO format."""
    try:
        img = Image.open(png_path)
        
        # Convert RGBA to RGB if necessary (ICO doesn't support alpha in all cases)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Save as ICO with multiple sizes
        img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        print(f"Successfully converted {png_path} to {ico_path}")
        return True
    except Exception as e:
        print(f"Error converting image: {e}")
        return False

if __name__ == "__main__":
    # Define paths
    png_path = "resources/Gemini_Generated_Image_5v3gkv5v3gkv5v3g-removebg-preview.png"
    ico_path = "resources/icon.ico"
    
    # Create resources directory if it doesn't exist
    os.makedirs("resources", exist_ok=True)
    
    # Check if PNG exists
    if os.path.exists(png_path):
        success = convert_png_to_ico(png_path, ico_path)
        if success:
            print("Icon conversion completed successfully!")
        else:
            print("Icon conversion failed.")
    else:
        print(f"PNG file not found at {png_path}")