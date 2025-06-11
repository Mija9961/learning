from flask import render_template, jsonify, request, flash, session, redirect, url_for
from flask_login import login_required, current_user
from . import autogen_bp
from app import db, limiter
from app.models import User, Conversation
from .util.llm_response import LLMResponse
from .util.shared_state import chat_sessions
import asyncio, re
from uuid import uuid4
from flask_limiter.errors import RateLimitExceeded



@autogen_bp.route('/interview')
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
        conversations = (
            Conversation.query
            .filter_by(user_email=user_email, conversation_type='interview', subject='autogen')
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

    return render_template('autogen/interview.html', messages=conversation_history, user=current_user)


@autogen_bp.route('/learn')
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
        conversations = (
            Conversation.query
            .filter_by(user_email=user_email, conversation_type='learn', subject='autogen')
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
    return render_template('autogen/learn.html', messages=conversation_history, user=current_user)


@autogen_bp.route('/ask/interview', methods=['POST'])
@limiter.limit("20 per minute")
@login_required
def ask():
    user_input = request.form.get('message', '').strip()
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    user_email = current_user.email
    conversation_id = str(uuid4())

    try:
        response = asyncio.run(LLMResponse.get_response(user_input))

        new_convo = Conversation(
            user_email=user_email,
            user_message=user_input,
            bot_response=response,
            conversation_id=conversation_id,
            conversation_type='interview',
            subject='autogen'
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



@autogen_bp.route('/ask/learn', methods=['POST'])
@limiter.limit("20 per minute")
@login_required
def ask_learn():
    user_input = request.form.get('message', '').strip()
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    user_email = current_user.email
    conversation_id = str(uuid4())

    try:
        response = asyncio.run(LLMResponse.get_response_learn(user_input))

        new_convo = Conversation(
            user_email=user_email,
            user_message=user_input,
            bot_response=response,
            conversation_id=conversation_id,
            conversation_type='learn',
            subject='autogen'
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


@autogen_bp.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    return jsonify({
        "response": e.description
    }), 200