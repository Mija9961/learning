from flask import render_template, jsonify, request, flash, session, redirect, url_for, current_app
from flask_login import login_required, current_user
from . import mock_interview_bp
from app import db, limiter
from app.models import User, Conversation, AIModel, UserAIModel, Subject, Resume
from .util.llm_response import LLMResponse
from .util.shared_state import chat_sessions, subjects_storage, current_subject_dict
import asyncio, re, os
from datetime import datetime, timezone
from uuid import uuid4
from flask_limiter.errors import RateLimitExceeded
from uuid import uuid4
from .util.validity_check import is_valid_uuid
from werkzeug.utils import secure_filename
import PyPDF2

# Store subjects in memory for now (replace with DB later)


# Upload settings
UPLOAD_FOLDER = 'static/resumes/uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 500 * 1024  # 500 KB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_sensitive_info(text):
    # Remove email addresses
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '', text)

    # Remove phone numbers (simple patterns like 123-456-7890, (123) 456-7890, +91 98765 43210)
    text = re.sub(r'(\+?\d{1,3})?[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}', '', text)

    # Remove social media links (facebook, twitter, linkedin, instagram, etc.)
    text = re.sub(r'https?:\/\/(?:www\.)?(facebook|twitter|linkedin|instagram|t\.me|youtube)\.[^\s]+', '', text, flags=re.IGNORECASE)

    return text.strip()

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''
        for page in reader.pages:
            text += page.extract_text() or ''
    return text

@mock_interview_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    resume_id = uuid4()
    if request.method == 'POST':
        file = request.files.get('resume')
        if file and allowed_file(file.filename):
            resume_filename = f"{resume_id}_{file.filename}"
            resume_path = os.path.join(UPLOAD_FOLDER, resume_filename)

            filename = secure_filename(resume_filename)
            resume_folder = os.path.join(current_app.static_folder, 'resumes', 'uploads')
            os.makedirs(resume_folder, exist_ok=True)
            resume_path = os.path.join(resume_folder, filename)
            file.save(resume_path)
            resume_content = extract_text_from_pdf(resume_path)
            resume_content = clean_sensitive_info(resume_content)
            print(resume_content)
            resume = Resume(user_email=current_user.email,
                            resume_id=resume_id,
                            filename=file.filename,
                            filepath=filename,
                            resume_content=resume_content)
            db.session.add(resume)
            db.session.commit()
            flash('Resume uploaded successfully.', 'success')
            return redirect(url_for("mock_interview.index"))
        else:
            flash("Invalid file. Please upload a PDF file.", "danger")
            return redirect(request.url)

    resumes = Resume.query.filter_by(user_email=current_user.email).all()
    
    return render_template("mock_interview/index.html", resumes=resumes, user=current_user)



@mock_interview_bp.route('/interview/select/<resume_id>')
@login_required
def mock_interview_select(resume_id):
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    user_email = user.email # needed to fetch data from database
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    user_email = user.email
    selected_conversation_id = request.args.get('conversation_id')

    try:
        resume = Resume.query.filter_by(resume_id=resume_id).first()
        if not resume:
            flash("Resume not found with the given ID.", "danger")
            return redirect(url_for('mock_interview.index'))
    
        
        if resume.resume_content is None:
            flash("Resume content not found with the given ID.", "danger")
            return redirect(url_for('mock_interview.index'))
        # Fetch grouped conversations (distinct conversation_ids)
        
        all_conversations = (
            db.session.query(Conversation.conversation_id, Conversation.conversation_name, db.func.min(Conversation.timestamp))
            .filter_by(user_email=user_email, conversation_type='interview', subject_id=resume.resume_id)
            .group_by(Conversation.conversation_id)
            .order_by(db.func.min(Conversation.timestamp).desc())
            .all()
        )
        conversation_summaries = [(conv_id, conv_name, ts) for conv_id, conv_name, ts in all_conversations]
        print(f"Conversation summary::{conversation_summaries}")
        # Get conversation history for selected conversation_id or start new
        if selected_conversation_id:
            conversations = Conversation.query.filter_by(
                user_email=user_email,
                conversation_id=selected_conversation_id,
                conversation_type='interview',
            ).order_by(Conversation.timestamp.asc()).all()
        else:
            conversations = []

        # Set AI model
        user_model = UserAIModel.query.filter_by(user_email=current_user.email).first()
        selected_provider = user_model.provider if user_model else os.environ.get("DEFAULT_AI_PROVIDER", None)
        selected_model = user_model.model_name if user_model else os.environ.get("DEFAULT_AI_MODEL", None)
        session['ai_provider'] = selected_provider.lower()
        session['ai_model'] = selected_model.lower()

    except Exception as e:
        flash(f"Error loading conversations: {e}", "danger")
        conversations = []
        conversation_summaries = []

    # Format conversation history
    conversation_history = [
        {"user": conv.user_message, "bot": conv.bot_response}
        for conv in conversations
    ]

    # Save session to LLM
    session_id = LLMResponse.get_session_id()
    chat_sessions[session_id] = conversation_history[-20:]
        

    return render_template(
        'mock_interview/mock_interview_select.html',
        resume=resume,
        resume_id=resume_id,
        conversation_id=selected_conversation_id,
        messages=conversation_history,
        conversation_summaries=conversation_summaries,
        user=current_user,
    )
   

@mock_interview_bp.route('/interview/<resume_id>')
@login_required
def mock_interview(resume_id):
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        resume = Resume.query.filter_by(resume_id=resume_id).first()
        if not resume:
            flash("Resume not found with the given ID.", "danger")
            return redirect(url_for('mock_interview.index'))
    

        # Fetch user email from User model
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.login'))

        user_email = user.email

        # Fetch conversations for this user and conversation_type
        # Get conversation_id from URL or generate a new one
        session['subject_id'] = resume_id
        session['resume_content'] = resume.resume_content
        conversation_id = request.args.get('conversation_id')
        if not conversation_id:
            conversation_id = str(uuid4())
            return redirect(url_for('mock_interview.mock_interview', resume_id=resume_id, conversation_id=conversation_id))
        if not is_valid_uuid(conversation_id):
            flash(f'Conversation not found. Starting a new conversation', 'danger')
            return redirect(url_for('mock_interview.mock_interview', resume_id=resume_id, conversation_id=conversation_id))


        conversations = (
            Conversation.query
            .filter_by(user_email=user_email, conversation_type='interview', conversation_id=conversation_id)
            .order_by(Conversation.timestamp.asc())
            .all()
        )

    except Exception as e:
        flash(f"Error loading conversation history: {e}", 'danger')
        conversations = []

    # Format conversation for prompt input
    conversation_history = [
        {"user": conv.user_message, "bot": conv.bot_response}
        for conv in conversations
    ]
    print("Conversation History:: ",conversation_history)
    session_id = LLMResponse.get_session_id()
    chat_sessions[session_id] = conversation_history[-20:]  # Send last 20 conversations to LLM
    return render_template('mock_interview/mock_interview.html', resume_id=resume_id, messages=conversation_history, conversation_id=conversation_id, user=current_user)


@mock_interview_bp.route('/ask/interview', methods=['POST'])
@limiter.limit("3 per minute")
@login_required
def ask():
    user_input = request.form.get('message', '').strip()
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    user_email = current_user.email
    conversation_id = request.args.get('conversation_id', str(uuid4()))

    try:
        response = asyncio.run(LLMResponse.get_response_interview(user_input))

        new_convo = Conversation(
            user_email=user_email,
            user_message=user_input,
            bot_response=response,
            conversation_id=conversation_id,
            conversation_type='interview',
            subject='Resume based mock interview',
            subject_id=session['subject_id']

        )
        db.session.add(new_convo)
        db.session.commit()
        # Append user input and bot response to chat history
        session_id = LLMResponse.get_session_id()

        chat_sessions.setdefault(session_id, []).append({"user": user_input, "bot": response})
        return jsonify({"response": response})
    except Exception as e:
        db.session.rollback()
        print(f"error: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@mock_interview_bp.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    return jsonify({
        "response": "❌Warning! You can ask three questions/minute"
    }), 200



@mock_interview_bp.route('/delete_conversation/interview/<resume_id>/<conversation_id>', methods=['POST'])
@login_required
def delete_conversation_interview(resume_id,conversation_id):
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('auth.login'))
    
    resume = Resume.query.filter_by(resume_id=resume_id).first()
    if not resume:
        flash("Resume not found with the given ID.", "danger")
        return redirect(url_for('mock_interview.index'))

    
    if resume.resume_content is None:
        flash("Resume content not found with the given ID.", "danger")
        return redirect(url_for('mock_interview.index'))

    try:
        deleted = Conversation.query.filter_by(
            user_email=user.email,
            conversation_id=conversation_id,
            conversation_type='interview',
        ).delete()
        db.session.commit()
        flash(f"Deleted conversation ({deleted} messages).", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting conversation: {e}", "danger")

    return redirect(url_for('mock_interview.mock_interview_select', resume_id=resume_id))


@mock_interview_bp.route('/rename/interview/<resume_id>', methods=['POST'])
def rename_conversation_interview(resume_id):
    resume = Resume.query.filter_by(resume_id=resume_id).first()
    if not resume:
        flash("Resume not found with the given ID.", "danger")
        return redirect(url_for('mock_interview.index'))

    
    if resume.resume_content is None:
        flash("Resume content not found with the given ID.", "danger")
        return redirect(url_for('mock_interview.index'))
    conversation_id = request.form.get('conversation_id')
    new_name = request.form.get('new_name')
    
    conversation = Conversation.query.filter_by(conversation_id=conversation_id).first()
    if conversation:
        conversation.conversation_name = new_name
        db.session.commit()
        flash("Conversation renamed successfully.", "success")
    else:
        flash("Conversation not found.", "danger")
        
    return redirect(url_for('mock_interview.mock_interview_select', resume_id=resume_id, conversation_id=conversation_id))
