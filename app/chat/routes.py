from flask import render_template, jsonify, request, flash, session, redirect, url_for
from flask_login import login_required, current_user
from . import chat_bp
from .util.llm_response import LLMResponse
from .util.shared_state import global_chat_sessions, anything_chat_sessions
import re, asyncio
from app import limiter
from flask_limiter.errors import RateLimitExceeded
import time

@chat_bp.route('/chat-global', methods=['POST'])
@limiter.limit("5 per minute")
def chat_global():
    data = request.get_json()
    user_input = data.get('message', '')

    reply = asyncio.run(LLMResponse.get_response_chat(user_input))

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
    chat_history = [{"user": None, "bot": "Hi there! This is Alexi. How can I help you?"}]
    if current_user.is_authenticated:
        """If user logged in"""
        session_id = LLMResponse.get_session_id()
        chat_history = global_chat_sessions.get(session_id, [{"bot": "Hi there! This is Alexi. How can I help you?"}])
    return jsonify(chat_history)


@chat_bp.route('/chat-history-anything')
# @login_required
def get_chat_history_anything():
    chat_history = []
    if current_user.is_authenticated:
        """If user logged in"""
        session_id = LLMResponse.get_session_id()
        chat_history = anything_chat_sessions.get(session_id, [])
    print("Chat history: ", chat_history)
    return jsonify(chat_history)

@chat_bp.route('/anything', methods=['GET','POST'])
@login_required
@limiter.limit("5 per minute")
def chat_anything():
    chat_history = []
    if request.method == "POST":
        data = request.get_json()
        user_input = data.get('message', '')
        reply = asyncio.run(LLMResponse.get_response_chat_anything(user_input))

        # Append user input and bot response to chat history
        if current_user.is_authenticated:
            session_id = LLMResponse.get_session_id()
            anything_chat_sessions.setdefault(session_id, []).append({"user": user_input, "bot": re.sub(r'<.*?>', '', reply)})
            chat_history = anything_chat_sessions.get(session_id, [])

        else:
            print("Anonymous user - not storing chat history")
        return jsonify({'response': reply})

    else:
        if current_user.is_authenticated:
            session_id = LLMResponse.get_session_id()
            chat_history = anything_chat_sessions.get(session_id, [])

    return render_template(
        'chat/ask_anything.html',
        chat_history = chat_history,
        user=current_user
    )



@chat_bp.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    return jsonify({
        "response": "❌Warning! You can ask 5 questions/minute"
    }), 200