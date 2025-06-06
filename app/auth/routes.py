from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user
from . import auth_bp
from ..models import User
from ..extensions import db
from .forms import LoginForm, SignupForm
import uuid

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for('user.dashboard'))
    if form.validate_on_submit():
        username_or_email = form.username.data
        password = form.password.data

        # Look up the user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user:
            if check_password_hash(user.password, password):
                if user.session_token:
                    flash("You are already logged in on another device.", "warning")
                    # Store pending session token in session for confirmation
                    session['pending_token'] = str(uuid.uuid4())
                    session['username_pending'] = user.username
                    session['user_id_pending'] = user.id
                    return redirect(url_for('auth.confirm_session'))
                else:
                    # First login, generate a new session token
                    session_token = str(uuid.uuid4())
                    user.session_token = session_token
                    db.session.commit()

                    session['username'] = user.username
                    session['session_token'] = session_token

                    flash(f"Login successful. Welcome, {user.username}!", 'success')
                    login_user(user)

                    return redirect(url_for('user.dashboard'))  # or 'home' if that's your route
            else:
                flash("Invalid password.", "danger")
        else:
            flash("User not found.", "danger")
    elif 'username' in session:
        return redirect(url_for('user.dashboard'))  # or 'home'

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    if 'username' in session and 'session_token' in session:
        username = session['username']
        session_token = session['session_token']

        # Find the user with this session_token using SQLAlchemy
        user = User.query.filter_by(username=username, session_token=session_token).first()
        if user:
            user.session_token = None  # Invalidate the session token in the DB
            db.session.commit()

    # Log out the user using Flask-Login
    logout_user()

    # Clear the Flask session (cookies)
    session.clear()

    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.signup'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.signup'))

        hashed_password = generate_password_hash(password)

        try:
            # Check if email is already registered
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered. Please use a different email.', 'danger')
                return redirect(url_for('auth.signup'))

            # Check if username is already registered
            existing_user_name = User.query.filter_by(username=username).first()
            if existing_user_name:
                flash('Username already registered. Please use a different username.', 'danger')
                return redirect(url_for('auth.signup'))

            # Create new user
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('auth.signup'))

    # If user already logged in, redirect
    if 'username' in session:
        return redirect(url_for('home'))

    return render_template('auth/signup.html', form=form)



# @auth_bp.route('/confirm_session', methods=['GET', 'POST'])
# def confirm_session():
#     if request.method == 'POST':
#         action = request.form.get('action')
#         if action == 'confirm':
#             # User chose to logout other sessions
#             session_token = session.pop('pending_token', None)
#             username = session.pop('username_pending', None)
#             user_id = session.pop('user_id_pending', None)

#             if session_token and username and user_id:
#                 # Update the session token in the database using SQLAlchemy
#                 user = db.session.query(User).filter_by(id=user_id).first()
#                 if user:
#                     user.session_token = session_token
#                     db.session.commit()

#                     # Set active session data
#                     session['username'] = username
#                     session['session_token'] = session_token

#                     flash("Logged in and other sessions are now logged out.", "success")
#                     return redirect(url_for('index'))
#                 else:
#                     flash("User not found.", "danger")
#                     return redirect(url_for('auth.login'))
#             else:
#                 flash("Session confirmation failed.", "danger")
#                 return redirect(url_for('auth.login'))
#         else:
#             # Cancel and go back to login
#             session.pop('pending_token', None)
#             session.pop('username_pending', None)
#             session.pop('user_id_pending', None)
#             flash("Login cancelled.", "info")
#             return redirect(url_for('auth.login'))

#     return render_template('auth/confirm_session.html')

@auth_bp.route('/confirm_session', methods=['GET', 'POST'])
def confirm_session():
    """
    Confirms a pending session after the user is detected as already logged in elsewhere.
    Offers the user the choice to logout other sessions and continue, or cancel.
    """
    # Ensure pending session data exists
    pending_token = session.get('pending_token')
    username_pending = session.get('username_pending')
    user_id_pending = session.get('user_id_pending')

    if not (pending_token and username_pending and user_id_pending):
        flash("No pending session to confirm. Please log in again.", "warning")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'confirm':
            # User chose to log out other sessions and proceed
            user = User.query.filter_by(id=user_id_pending).first()
            if user:
                # Overwrite previous session token to invalidate old sessions
                user.session_token = pending_token
                db.session.commit()

                # Store new session data
                session['username'] = username_pending
                session['session_token'] = pending_token

                # Clean up pending session keys
                session.pop('pending_token', None)
                session.pop('username_pending', None)
                session.pop('user_id_pending', None)

                flash("You have successfully confirmed your session. Other sessions have been logged out.", "success")
                login_user(user)
                return redirect(url_for('user.dashboard'))  # or wherever you'd like to land

            else:
                flash("User not found. Please log in again.", "danger")
                return redirect(url_for('auth.login'))

        elif action == 'cancel':
            # User cancelled session confirmation
            session.pop('pending_token', None)
            session.pop('username_pending', None)
            session.pop('user_id_pending', None)

            flash("Session confirmation cancelled. Please log in again.", "info")
            return redirect(url_for('auth.login'))

        else:
            flash("Invalid action.", "danger")
            return redirect(url_for('auth.confirm_session'))

    return render_template('auth/confirm_session.html', username=username_pending)
