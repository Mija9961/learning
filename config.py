import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", os.environ['SECRET_KEY'])

    # Database
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.environ['MYSQL_USER']}:{os.environ['MYSQL_PASSWORD']}"
        f"@{os.environ['MYSQL_HOST']}/{os.environ['MYSQL_DB']}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Rate limiting
    REDIS_HOST=os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT=int(os.getenv("REDIS_PORT", 6379))
    RATELIMIT_STORAGE_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
    RATELIMIT_HEADERS_ENABLED = True

    # Upload Folder
    UPLOAD_FOLDER_DOC = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static', 'documents', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf'}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size


