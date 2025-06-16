from flask import render_template, jsonify, request, flash, session, redirect, url_for
from flask_login import login_required, current_user
from . import python_bp
from app import db, limiter, chromadb_client
from app.models import User, Conversation
from .util.llm_response import LLMResponse
from .util.shared_state import chat_sessions
import asyncio, re
from uuid import uuid4
from flask_limiter.errors import RateLimitExceeded

from .test import get_data
from .util.validity_check import is_valid_uuid

@python_bp.route('/')
@login_required
def index():
    return render_template('python/index.html', user=current_user)


@python_bp.route('/interview')
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
            return redirect(url_for('python.interview', conversation_id=conversation_id))
        if not is_valid_uuid(conversation_id):
            flash(f'Conversation not found. Starting a new conversation', 'danger')
            return redirect(url_for('python.interview', conversation_id=None))
        
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

    return render_template('python/interview.html', messages=conversation_history, user=current_user)


@python_bp.route('/learn')
@login_required
def learn():
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
            return redirect(url_for('python.learn', conversation_id=conversation_id))
        if not is_valid_uuid(conversation_id):
            flash(f'Conversation not found. Starting a new conversation', 'danger')
            return redirect(url_for('python.learn', conversation_id=None))


        conversations = (
            Conversation.query
            .filter_by(user_email=user_email, conversation_type='learn', subject='python', conversation_id=conversation_id)
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
    return render_template('python/learn.html', messages=conversation_history, conversation_id=conversation_id, user=current_user)


@python_bp.route('/ask/interview', methods=['POST'])
@limiter.limit("20 per minute")
@login_required
def ask():
    user_input = request.form.get('message', '').strip()
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    user_email = current_user.email
    conversation_id = request.args.get('conversation_id', str(uuid4()))

    try:
        response = asyncio.run(LLMResponse.get_response(user_input))

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



@python_bp.route('/ask/learn', methods=['POST'])
@limiter.limit("20 per minute")
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

        new_convo = Conversation(
            user_email=user_email,
            user_message=user_input,
            bot_response=response,
            conversation_id=conversation_id,
            conversation_type='learn',
            subject='python'
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


@python_bp.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    return jsonify({
        "response": e.description
    }), 200


@python_bp.route('/test', methods=['GET'])
def test():
    res = get_data()
    return res


@python_bp.route('/delete_conversation/learn/<conversation_id>', methods=['POST'])
@login_required
def delete_conversation(conversation_id):
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('auth.login'))

    try:
        deleted = Conversation.query.filter_by(
            user_email=user.email,
            conversation_id=conversation_id,
            conversation_type='learn',
            subject='python'
        ).delete()
        db.session.commit()
        flash(f"Deleted conversation ({deleted} messages).", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting conversation: {e}", "danger")

    return redirect(url_for('python.learn_select'))

@python_bp.route('/learn/select')
@login_required
def learn_select():
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
            .filter_by(user_email=user_email, conversation_type='learn', subject='python')
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
                subject='python'
            ).order_by(Conversation.timestamp.asc()).all()
        else:
            conversations = []

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
        'python/learn_select.html',
        messages=conversation_history,
        conversation_summaries=conversation_summaries,
        conversation_id=selected_conversation_id,
        user=current_user
    )


@python_bp.route('/rename/learn', methods=['POST'])
def rename_conversation():
    conversation_id = request.form.get('conversation_id')
    new_name = request.form.get('new_name')
    
    conversation = Conversation.query.filter_by(conversation_id=conversation_id).first()
    if conversation:
        conversation.conversation_name = new_name
        db.session.commit()
        flash("Conversation renamed successfully.", "success")
    else:
        flash("Conversation not found.", "danger")
        
    return redirect(url_for('python.learn_select', conversation_id=conversation_id))




# Interview

@python_bp.route('/delete_conversation/interview/<conversation_id>', methods=['POST'])
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

    return redirect(url_for('python.interview_select'))

@python_bp.route('/interview/select')
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
        'python/interview_select.html',
        messages=conversation_history,
        conversation_summaries=conversation_summaries,
        conversation_id=selected_conversation_id,
        user=current_user
    )


@python_bp.route('/rename/interview', methods=['POST'])
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
        
    return redirect(url_for('python.interview_select', conversation_id=conversation_id))
