from .extensions import db
from flask_login import UserMixin
from sqlalchemy.dialects.mysql import JSON

# Define Models
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    session_token = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=False, nullable=False)  # 👈 Added field
    is_admin = db.Column(db.Boolean, default=False)  # 👈 This determines admin access


class Conversation(db.Model, UserMixin):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    conversation_id = db.Column(db.String(255))
    conversation_name = db.Column(db.String(255))
    conversation_type = db.Column(db.String(255))
    subject = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())


class MockTestData(db.Model, UserMixin):
    __tablename__ = 'mock_test_questions'

    id = db.Column(db.Integer, primary_key=True)
    question_set_no = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    data = db.Column(JSON, nullable=False)

    def __repr__(self):
        return f"<MockTestData(id={self.id}, question_set_no={self.question_set_no}, subject={self.subject})>"
    

class UserAIModel(db.Model, UserMixin):
    __tablename__ = 'users_ai_model'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100), unique=True, nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)



class AIModel(db.Model, UserMixin):
    __tablename__ = 'ai_models'
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)