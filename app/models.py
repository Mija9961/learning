from .extensions import db
from flask_login import UserMixin
from sqlalchemy.dialects.mysql import JSON
from datetime import datetime

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
    profile_image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    activation_token = db.Column(db.String(255))
    activation_token_created_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verified_at = db.Column(db.DateTime)

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
    subject_id = db.Column(db.String(255))
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


class Subject(db.Model, UserMixin):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(50), nullable=False)
    subject_id = db.Column(db.String(50), unique=True, nullable=False)
    syllabus = db.Column(db.Text, nullable=False)
    added_at = db.Column(db.DateTime, server_default=db.func.now())
    user_email = db.Column(db.String(100), nullable=False)


class Resume(db.Model, UserMixin):
    __tablename__ = 'resume'
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.String(50), unique=True, nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    added_at = db.Column(db.DateTime, server_default=db.func.now())
    resume_content = db.Column(db.Text, nullable=False)



class Document(db.Model, UserMixin):
    __tablename__ = 'document'
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.String(50), unique=True, nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class UserMessage(db.Model, UserMixin):
    __tablename__ = 'user_message'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    received_at = db.Column(db.DateTime, server_default=db.func.now())
    is_read_message = db.Column(db.Boolean, default=False)
    client_ip = db.Column(db.String(50), nullable=True)

