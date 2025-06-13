from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
db = SQLAlchemy()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from app.models import User  # move import inside the function
    return User.query.get(int(user_id))


migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)


chromadb_client = Config.get_chroma_client()
