from flask import render_template, jsonify, request, flash, session, redirect, url_for
from flask_login import login_required, current_user
from . import chat_bp
from .util.llm_response import LLMResponse
from .util.shared_state import global_chat_sessions
import re, asyncio
from app import limiter
from flask_limiter.errors import RateLimitExceeded


@chat_bp.route('/chat-global', methods=['POST'])
@limiter.limit("2 per minute")
def chat_global():
    data = request.get_json()
    user_input = data.get('message', '')

    reply = asyncio.run(LLMResponse.get_response_chat(user_input))
    print(reply)

    # Append user input and bot response to chat history
    if current_user.is_authenticated:
        session_id = LLMResponse.get_session_id()
        global_chat_sessions.setdefault(session_id, [{"user": None, "bot": "Hi there! This is Alexi. How can I help you?"}]) \
            .append({"user": user_input, "bot": re.sub(r'<.*?>', '', reply)})
    else:
        print("Anonymous user - not storing chat history")

    return jsonify({'response': reply})


@chat_bp.route('/chat-history')
# @login_required
def get_chat_history():
    print("current user: ",current_user)
    chat_history = [{"user": None, "bot": "Hi there! This is Alexi. How can I help you?"}]
    if current_user.is_authenticated:
        """If user logged in"""
        session_id = LLMResponse.get_session_id()
        chat_history = global_chat_sessions.get(session_id, [{"bot": "Hi there! This is Alexi. How can I help you?"}])
    return jsonify(chat_history)


@chat_bp.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    return jsonify({
        "response": "❌Warning! You can ask two questions/minute"
    }), 200