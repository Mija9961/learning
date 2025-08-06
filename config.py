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
    RATELIMIT_STORAGE_URL = "redis://localhost:6379"
    RATELIMIT_HEADERS_ENABLED = True

    # Upload Folder
    UPLOAD_FOLDER = os.environ['UPLOAD_FOLDER']


