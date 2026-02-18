import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app
import os

def init_cloudinary(app):
    """
    Initialize Cloudinary configuration from app config.
    Call this once in create_app() after other extensions are initialized.
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

def _ensure_cloudinary_configured():
    """
    Safety net: if Cloudinary wasn't initialized at startup (e.g. during
    testing or a missed init call), try to configure it from env vars directly.
    Returns True if Cloudinary is ready to use.
    """
    # Check if already configured
    if cloudinary.config().cloud_name:
        return True

    # Try to configure from environment variables directly as a fallback
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    api_key = os.environ.get('CLOUDINARY_API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')

    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        print("⚠️  Cloudinary configured from env vars (fallback) — add init_cloudinary(app) to app.py")
        return True

    return False

def upload_image(file, folder='skillverse/skills'):
    """
    Upload image to Cloudinary.

    Args:
        file: File object from request.files
        folder: Cloudinary folder path

    Returns:
        str: Secure URL of uploaded image or None if failed
    """
    try:
        # Ensure Cloudinary is configured before attempting upload
        if not _ensure_cloudinary_configured():
            print("Cloudinary upload skipped: credentials not configured")
            return None

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type="image"
        )

        return upload_result.get('secure_url')

    except Exception as e:
        print(f"Cloudinary upload error: {str(e)}")
        return None