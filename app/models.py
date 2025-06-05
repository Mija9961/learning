from .extensions import db
from flask_login import UserMixin

# Define Models
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    session_token = db.Column(db.String(255))

class Conversation(db.Model, UserMixin):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    conversation_id = db.Column(db.String(255))
    conversation_type = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
