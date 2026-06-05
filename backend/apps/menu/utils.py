import os
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile

def process_image(image_field, max_width=800, max_height=800, quality=80):
    """
    Compresses and converts any uploaded image to WebP format.
    Reduces physical size to fit within max_width x max_height while maintaining aspect ratio.
    """
    if not image_field:
        return image_field
    
    try:
        # Ensure we read from the beginning
        image_field.seek(0)
        img = Image.open(image_field)
        
        # Check transparency and convert modes
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')
            
        # Resize using Lanczos resampling (high quality)
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Save to WebP memory stream
        buffer = BytesIO()
        img.save(buffer, format='WEBP', quality=quality, method=4)
        buffer.seek(0)
        
        # Format the file name
        original_name = image_field.name
        base_name = os.path.splitext(os.path.basename(original_name))[0]
        new_filename = f"{base_name}.webp"
        
        # Return a Django UploadedFile equivalent
        return InMemoryUploadedFile(
            buffer,
            'ImageField',
            new_filename,
            'image/webp',
            buffer.getbuffer().nbytes,
            None
        )
    except Exception as e:
        # Fallback to the original file if conversion fails
        print(f"Error converting image to WebP: {e}")
        return image_field
