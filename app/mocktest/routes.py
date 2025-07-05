from flask import render_template, jsonify, request, flash, session, redirect, url_for
from flask_login import login_required, current_user
from . import mocktest_bp
from app import db, limiter
from .util.llm_response import LLMResponse
from .util.shared_state import mock_questions, mock_answers
from datetime import datetime

@mocktest_bp.route('/')
@login_required
def index():
    return render_template('mocktest/index.html')

# @mocktest_bp.route('/test/<topic>', methods=['GET', 'POST'])
# @login_required
# def test(topic):
#     global mock_questions
#     global mock_answers
#     mock_questions, mock_answers = LLMResponse.get_question_paper(topic)
#     questions = mock_questions.get(topic.lower())
#     if not questions:
#         return redirect(url_for('mocktest.index'))
#     return render_template('mocktest/test.html', topic=topic, questions=questions)

# ALLOWED_TOPICS = ['python', 'dsa', 'java']

# @mocktest_bp.route('/test/<topic>', methods=['GET', 'POST'])
# @login_required
# def test(topic):
#     topic = topic.lower()
#     if topic not in ALLOWED_TOPICS:
#         return redirect(url_for('mocktest.index'))

#     # Check if the user is revisiting the same topic
#     current_topic = session.get('current_topic')
#     if current_topic == topic and 'mock_questions' in session:
#         questions = session['mock_questions']
#     else:
#         # New topic selected; generate new questions
#         mock_questions, mock_answers = LLMResponse.get_question_paper(topic)
#         questions = mock_questions.get(topic)
#         if not questions:
#             return redirect(url_for('mocktest.index'))

#         # Store in session for refreshes
#         session['current_topic'] = topic
#         session['mock_questions'] = questions

#     return render_template('mocktest/test.html', topic=topic, questions=questions)

# @mocktest_bp.route('/test/<topic>', methods=['GET', 'POST'])
# @login_required
# def test(topic):
#     global mock_questions
#     global mock_answers

#     if 'mock_questions' not in session or session.get('current_topic') != topic:
#         mock_questions, mock_answers = LLMResponse.get_question_paper(topic)
#         session['mock_questions'] = mock_questions
#         session['mock_answers'] = mock_answers
#         session['current_topic'] = topic
#         session['start_time'] = datetime.utcnow().isoformat()
#     else:
#         mock_questions = session.get('mock_questions')
#         mock_answers = session.get('mock_answers')

#     questions = mock_questions.get(topic.lower())
#     if not questions:
#         return redirect(url_for('mocktest.index'))

#     # Calculate remaining time
#     start_time = datetime.fromisoformat(session.get('start_time'))
#     elapsed_time = (datetime.utcnow() - start_time).total_seconds()
#     remaining_time = max(0, 1800 - elapsed_time)  # 10 min limit

#     return render_template(
#         'mocktest/test.html',
#         topic=topic,
#         questions=questions,
#         remaining_time=remaining_time
#     )

@mocktest_bp.route('/test/<topic>', methods=['GET', 'POST'])
@login_required
def test(topic):
    global mock_questions
    global mock_answers
    mock_questions, mock_answers = LLMResponse.get_question_paper(topic)
    questions = mock_questions.get(topic.lower())
    if not questions:
        return redirect(url_for('mocktest.index'))

    # Load current question index from session (default 0)
    current_question_index = session.get('current_question_index', 0)
    
    # (Optional) Load remaining time if you also want to persist timer
    remaining_time = session.get('remaining_time', 5 * 60)  # 5 minutes in seconds
    saved_answers = session.get('saved_answers', {})

    return render_template(
        'mocktest/test.html',
        topic=topic,
        questions=questions,
        current_question_index=current_question_index,
        remaining_time=remaining_time,
        saved_answers=saved_answers
    )

@mocktest_bp.route('/save_progress', methods=['POST'])
@login_required
def save_progress():
    data = request.get_json()
    current_question_index = data.get('current_question_index', 0)
    remaining_time = data.get('remaining_time')
    answers = data.get('answers', {})  # dictionary of saved answers

    session['current_question_index'] = current_question_index
    if remaining_time is not None:
        session['remaining_time'] = remaining_time
    session['saved_answers'] = answers  # store answers in session

    return jsonify({"status": "success"})


@mocktest_bp.route('/result')
@login_required
def result():
    summary = session.pop('summary', [])
    score = session.pop('score', 0)
    total = session.pop('total', 0)
    return render_template('mocktest/result.html', score=score, total=total, summary=summary)


@mocktest_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    data = request.get_json()
    answers = data.get('answers', {})
    topic = data.get('topic', '').lower()
    questions = mock_questions.get(topic, [])
    correct_answers = mock_answers.get(topic, [])

    score = 0
    summary = []

    for idx, correct in enumerate(correct_answers):
        user_answer = answers.get(f'q{idx}')
        question_text = questions[idx]['question'] if idx < len(questions) else ''
        is_correct = user_answer and user_answer.strip().lower() == correct.strip().lower()
        if is_correct:
            score += 1
        summary.append({
            'question': question_text,
            'selected_answer': user_answer,
            'correct_answer': correct,
            'is_correct': is_correct
        })

    # Store in session
    session['summary'] = summary
    session['score'] = score
    session['total'] = len(correct_answers)

    session.pop('mock_questions', None)
    session.pop('mock_answers', None)
    session.pop('current_topic', None)
    session.pop('start_time', None)
    session.pop('remaining_time', None)
    session.pop('save_answers', None)


    return jsonify({'redirect_url': url_for('mocktest.result')})
