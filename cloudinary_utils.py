import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app
import os

def init_cloudinary(app):
    """
    Initialize Cloudinary configuration from app config
    """
    cloud_name = app.config.get('CLOUDINARY_CLOUD_NAME')
    api_key = app.config.get('CLOUDINARY_API_KEY')
    api_secret = app.config.get('CLOUDINARY_API_SECRET')

    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        return True
    return False

def upload_image(file, folder='skillverse/skills'):
    """
    Upload image to Cloudinary
    
    Args:
        file: File object from request.files
        folder: Cloudinary folder path
        
    Returns:
        str: Secure URL of uploaded image or None if failed
    """
    try:
        # Check if Cloudinary is configured
        if not current_app.config.get('CLOUDINARY_CLOUD_NAME'):
            return None
            
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type="image"
        )
        
        # Return secure URL
        return upload_result.get('secure_url')
        
    except Exception as e:
        print(f"Cloudinary upload error: {str(e)}")
        return None
