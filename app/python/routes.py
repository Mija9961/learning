from flask import render_template, jsonify, request, flash, session, redirect, url_for
from flask_login import login_required, current_user
from . import python_bp
from app import db, limiter
from app.models import User, Conversation
from .util.llm_response import LLMResponse
import asyncio
from uuid import uuid4
from flask_limiter.errors import RateLimitExceeded


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
        conversations = (
            Conversation.query
            .filter_by(user_email=user_email, conversation_type='interview')
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
    LLMResponse.chat_sessions[(session_id, 'interview')] = conversation_history[-20:]  # Send last 20 conversations to LLM

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
        conversations = (
            Conversation.query
            .filter_by(user_email=user_email, conversation_type='learn')
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
    LLMResponse.chat_sessions[(session_id, 'learn')] = conversation_history[-20:]  # Send last 20 conversations to LLM

    return render_template('python/learn.html', messages=conversation_history, user=current_user)


@python_bp.route('/ask/interview', methods=['POST'])
@limiter.limit("20 per minute")
@login_required
def ask():
    user_input = request.form.get('message', '').strip()
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    user_email = current_user.email
    conversation_id = str(uuid4())

    try:
        response = asyncio.run(LLMResponse.get_response(user_input, conversation_id))

        new_convo = Conversation(
            user_email=user_email,
            user_message=user_input,
            bot_response=response,
            conversation_id=conversation_id,
            conversation_type='interview'
        )
        db.session.add(new_convo)
        db.session.commit()

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
    conversation_id = str(uuid4())

    try:
        response = asyncio.run(LLMResponse.get_response_learn(user_input, conversation_id))

        new_convo = Conversation(
            user_email=user_email,
            user_message=user_input,
            bot_response=response,
            conversation_id=conversation_id,
            conversation_type='learn'
        )
        db.session.add(new_convo)
        db.session.commit()

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