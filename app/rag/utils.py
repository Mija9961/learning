import os
from werkzeug.utils import secure_filename
from flask import current_app
import uuid

def get_unique_filename(filename, user_id):
    """Generate a unique filename with user ID and UUID."""
    ext = filename.rsplit('.', 1)[1].lower()
    unique_id = str(uuid.uuid4())[:8]
    return secure_filename(f"{user_id}_{unique_id}_{filename}")

def get_upload_path(filename):
    """Get the full path for uploading a file."""
    return os.path.join(current_app.config['UPLOAD_FOLDER'], filename)