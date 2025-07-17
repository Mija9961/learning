from flask import render_template, jsonify, request, flash, session, redirect, url_for
from flask_login import login_required, current_user
from . import custom_subject_bp
from app import db, limiter
from app.models import User, Conversation, AIModel, UserAIModel, Subject
from .util.llm_response import LLMResponse
from .util.shared_state import chat_sessions, subjects_storage, current_subject_dict
import asyncio, re, os
from datetime import datetime, timezone
from uuid import uuid4
from flask_limiter.errors import RateLimitExceeded
from uuid import uuid4
from .util.validity_check import is_valid_uuid

# Store subjects in memory for now (replace with DB later)


@custom_subject_bp.route('/', methods=["GET","POST"])
@login_required
def index():
    # Handle form submission
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))
    try:
        # Fetch user email from User model
        subjects_storage = None
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.login'))

        user_email = user.email
        if request.method == "POST":
            subject = request.form.get("subject")
            syllabus = request.form.get("syllabus")
            if subject:
                subject_id = str(uuid4())
                # Create new subject and save to database
                new_subject = Subject(subject=subject, subject_id=subject_id, syllabus=syllabus, user_email=user_email)
                db.session.add(new_subject)
                db.session.commit()
                flash("Subject added successfully!", "success")
            else:
                flash("Subject is required.", "danger")
            return redirect(url_for("custom_subject.index"))
        subjects_storage = (
                Subject.query
                .filter_by(user_email=user_email)
                .order_by(Subject.added_at.asc())
                .all()
            )
    except Exception as e:
        print(f"Error in custom_subjec.index, {e}")
        flash("Something went wrong try again. If face the issue again contact administrator","danger")
    
    # Example conversation summaries
    return render_template("custom_subject/index.html",
                           user=current_user,
                           subjects=subjects_storage,
                           conversation_summaries=[])


@custom_subject_bp.route('/<subject>/<subject_id>')
def subject(subject,subject_id):
    subject_obj = Subject.query.filter_by(subject_id=subject_id).first()
    if not subject_obj:
        flash("Subject not found with the given ID.", "danger")
        return redirect(url_for('custom_subject.index'))
    
    subject = subject_obj.subject

    return render_template("custom_subject/subject.html",
                           subject=subject, subject_id=subject_id, user=current_user)


@custom_subject_bp.route('/<subject>/learn/select/<subject_id>')
@login_required
def subject_learn_select(subject, subject_id):
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
        subject = None
        subject_obj = Subject.query.filter_by(subject_id=subject_id).first()
        if not subject_obj:
            flash("Subject not found with the given ID.", "danger")
            return redirect(url_for('custom_subject.index'))
    
        subject = subject_obj.subject
        session['subject'] = subject
        session['subject_id'] = subject_id
        session['syllabus'] = subject_obj.syllabus
        if subject is None:
            flash("Subject not found with the given ID.", "danger")
            return redirect(url_for('custom_subject.index'))
        # Fetch grouped conversations (distinct conversation_ids)
        
        all_conversations = (
            db.session.query(Conversation.conversation_id, Conversation.conversation_name, db.func.min(Conversation.timestamp))
            .filter_by(user_email=user_email, conversation_type='learn', subject=subject, subject_id=subject_id)
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
                conversation_type='learn',
                subject=subject
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
        'custom_subject/subject_learn_select.html',
        subject=subject,
        subject_id=subject_id,
        conversation_id=selected_conversation_id,
        messages=conversation_history,
        conversation_summaries=conversation_summaries,
        user=current_user,
    )
   


@custom_subject_bp.route('/interview')
@login_required
def interview():
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))
    try:
        # Fetch user email from User model
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.login'))

        user_email = user.email

        # Fetch conversations for this user and conversation_type
         # Get conversation_id from URL or generate a new one
        conversation_id = request.args.get('conversation_id')
        if not conversation_id:
            conversation_id = str(uuid4())
            return redirect(url_for('custom_subject.interview', conversation_id=conversation_id))
        if not is_valid_uuid(conversation_id):
            flash(f'Conversation not found. Starting a new conversation', 'danger')
            return redirect(url_for('custom_subject.interview', conversation_id=None))
        
        conversations = (
            Conversation.query
            .filter_by(user_email=user_email, conversation_type='interview', subject='python', conversation_id=conversation_id)
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

    session_id = LLMResponse.get_session_id()
    chat_sessions[session_id] = conversation_history[-20:]  # Send last 20 conversations to LLM

    return render_template('custom_subject/interview.html', messages=conversation_history, user=current_user)


@custom_subject_bp.route('/learn/<subject_id>')
@login_required
def learn(subject_id):
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        subject = None
        subject_obj = Subject.query.filter_by(subject_id=subject_id).first()
        if not subject_obj:
            flash("Subject not found with the given ID.", "danger")
            return redirect(url_for('custom_subject.index'))
    
        subject = subject_obj.subject
        
        if subject is None:
            flash("Subject not found with the given ID.", "danger")
            return redirect(url_for('custom_subject.index'))
        # Fetch user email from User model
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.login'))

        user_email = user.email

        # Fetch conversations for this user and conversation_type
        # Get conversation_id from URL or generate a new one
        conversation_id = request.args.get('conversation_id')
        if not conversation_id:
            conversation_id = str(uuid4())
            return redirect(url_for('custom_subject.learn', subject_id=subject_id, subject=subject, conversation_id=conversation_id))
        if not is_valid_uuid(conversation_id):
            flash(f'Conversation not found. Starting a new conversation', 'danger')
            return redirect(url_for('custom_subject.learn', subject_id=subject_id, subject=subject, conversation_id=conversation_id))


        conversations = (
            Conversation.query
            .filter_by(user_email=user_email, conversation_type='learn', conversation_id=conversation_id)
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
    return render_template('custom_subject/learn.html', messages=conversation_history, subject_id=subject_id, subject=subject, conversation_id=conversation_id, user=current_user)


@custom_subject_bp.route('/ask/interview', methods=['POST'])
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
            subject='python'
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



@custom_subject_bp.route('/ask/learn', methods=['POST'])
@limiter.limit("3 per minute")
@login_required
def ask_learn():
    user_input = request.form.get('message', '').strip()
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    user_email = current_user.email
    # conversation_id = str(uuid4())
    conversation_id = request.args.get('conversation_id', str(uuid4()))

    try:
        response = asyncio.run(LLMResponse.get_response_learn(user_input))
        print(f"Response:: {response}")
        response = re.sub(r"^```html\n?|```$", "", response).strip() # Remove code block
        response = f"<div>{response}</div>"

        new_convo = Conversation(
            user_email=user_email,
            user_message=user_input,
            bot_response=response,
            conversation_id=conversation_id,
            conversation_type='learn',
            subject=session['subject'],
            subject_id=session['subject_id']
        )
        db.session.add(new_convo)
        db.session.commit()
        
        # Append user input and bot response to chat history
        session_id = LLMResponse.get_session_id()

        chat_sessions.setdefault(session_id, []).append({"user": user_input, "bot": re.sub(r'<.*?>', '', response)})
        return jsonify({"response": response})
    except Exception as e:
        db.session.rollback()
        print(f"error: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@custom_subject_bp.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    return jsonify({
        "response": "❌Warning! You can ask three questions/minute"
    }), 200



@custom_subject_bp.route('/delete_conversation/<subject>/learn/<subject_id>/<conversation_id>', methods=['POST'])
@login_required
def delete_conversation(subject, subject_id, conversation_id):
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('auth.login'))

    try:
        deleted = Conversation.query.filter_by(
            user_email=user.email,
            conversation_id=conversation_id,
            conversation_type='learn'
            # subject='python'
        ).delete()
        db.session.commit()
        flash(f"Deleted conversation ({deleted} messages).", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting conversation: {e}", "danger")

    return redirect(url_for('custom_subject.subject_learn_select', subject=subject, subject_id=subject_id))

@custom_subject_bp.route('/learn/select/<subject_id>')
@login_required
def learn_select(subject_id):
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    user_email = user.email
    selected_conversation_id = request.args.get('conversation_id')

    try:
        subject = None
        subject_obj = Subject.query.filter_by(subject_id=subject_id).first()
        if not subject_obj:
            flash("Subject not found with the given ID.", "danger")
            return redirect(url_for('custom_subject.index'))
    
        subject = subject_obj.subject
        
        if subject is None:
            flash("Subject not found with the given ID.", "danger")
            return redirect(url_for('custom_subject.index'))
        # Fetch grouped conversations (distinct conversation_ids)
        all_conversations = (
            db.session.query(Conversation.conversation_id, Conversation.conversation_name, db.func.min(Conversation.timestamp))
            .filter_by(user_email=user_email, conversation_type='learn', subject=subject)
            .group_by(Conversation.conversation_id)
            .order_by(db.func.min(Conversation.timestamp).desc())
            .all()
        )

        conversation_summaries = [(conv_id, conv_name, ts) for conv_id, conv_name, ts in all_conversations]

        # Get conversation history for selected conversation_id or start new
        if selected_conversation_id:
            conversations = Conversation.query.filter_by(
                user_email=user_email,
                conversation_id=selected_conversation_id,
                conversation_type='learn',
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
        'custom_subject/learn_select.html',
        messages=conversation_history,
        conversation_summaries=conversation_summaries,
        conversation_id=selected_conversation_id,
        subject_id = subject_id,
        user=current_user,
    )


@custom_subject_bp.route('/rename/<subject>/learn/<subject_id>', methods=['POST'])
def rename_conversation(subject, subject_id):
    conversation_id = request.form.get('conversation_id')
    new_name = request.form.get('new_name')
    
    conversation = Conversation.query.filter_by(conversation_id=conversation_id).first()
    if conversation:
        conversation.conversation_name = new_name
        db.session.commit()
        flash("Conversation renamed successfully.", "success")
    else:
        flash("Conversation not found.", "danger")
        
    return redirect(url_for('custom_subject.subject_learn_select', subject=subject, subject_id=subject_id, conversation_id=conversation_id))




# Interview

@custom_subject_bp.route('/delete_conversation/interview/<conversation_id>', methods=['POST'])
@login_required
def delete_conversation_interview(conversation_id):
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('auth.login'))

    try:
        deleted = Conversation.query.filter_by(
            user_email=user.email,
            conversation_id=conversation_id,
            conversation_type='interview',
            subject='python'
        ).delete()
        db.session.commit()
        flash(f"Deleted conversation ({deleted} messages).", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting conversation: {e}", "danger")

    return redirect(url_for('custom_subject.interview_select'))

@custom_subject_bp.route('/interview/select')
@login_required
def interview_select():
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    user_email = user.email
    selected_conversation_id = request.args.get('conversation_id')

    try:
        # Fetch grouped conversations (distinct conversation_ids)
        all_conversations = (
            db.session.query(Conversation.conversation_id, Conversation.conversation_name, db.func.min(Conversation.timestamp))
            .filter_by(user_email=user_email, conversation_type='interview', subject='python')
            .group_by(Conversation.conversation_id)
            .order_by(db.func.min(Conversation.timestamp).desc())
            .all()
        )

        conversation_summaries = [(conv_id, conv_name, ts) for conv_id, conv_name, ts in all_conversations]

        # Get conversation history for selected conversation_id or start new
        if selected_conversation_id:
            conversations = Conversation.query.filter_by(
                user_email=user_email,
                conversation_id=selected_conversation_id,
                conversation_type='interview',
                subject='python'
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
        'custom_subject/interview_select.html',
        messages=conversation_history,
        conversation_summaries=conversation_summaries,
        conversation_id=selected_conversation_id,
        user=current_user
    )


@custom_subject_bp.route('/rename/interview', methods=['POST'])
def rename_conversation_interview():
    conversation_id = request.form.get('conversation_id')
    new_name = request.form.get('new_name')
    
    conversation = Conversation.query.filter_by(conversation_id=conversation_id).first()
    if conversation:
        conversation.conversation_name = new_name
        db.session.commit()
        flash("Conversation renamed successfully.", "success")
    else:
        flash("Conversation not found.", "danger")
        
    return redirect(url_for('custom_subject.interview_select', conversation_id=conversation_id))
