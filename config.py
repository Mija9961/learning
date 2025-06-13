import os
from dotenv import load_dotenv
import chromadb

load_dotenv()

class Config:
    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "f8b2e22e57d64d08a7b0c20e3dcf8472")

    # Database
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.environ['MYSQL_USER']}:{os.environ['MYSQL_PASSWORD']}"
        f"@{os.environ['MYSQL_HOST']}/{os.environ['MYSQL_DB']}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Rate limiting
    RATELIMIT_STORAGE_URL = "redis://localhost:6379"
    RATELIMIT_HEADERS_ENABLED = True

    # ChromaDB
    CHROMADB_HOST = os.environ.get("CHROMADB_HOST", "localhost")
    CHROMADB_PORT = int(os.environ.get("CHROMADB_PORT", 8000))
    CHROMADB_COLLECTION = os.environ.get("CHROMADB_COLLECTION", "default_memory")

    @staticmethod
    def get_chroma_client():
        return chromadb.HttpClient(
            host=Config.CHROMADB_HOST,
            port=Config.CHROMADB_PORT
        )
