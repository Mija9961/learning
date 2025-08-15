from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from . import auth_bp
from ..models import User, UserMessage
from ..extensions import db
from .forms import LoginForm, SignupForm, SendMessageForm
import uuid
from datetime import datetime, timedelta
from ..util.email.email_content import GetEmailContent
from ..util.email.send_email import sync_send_email, email_exists, check_email_exists_and_send_email


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
                if not user.active:
                    flash("Your account is deactivated, please check your email or contact administrator", "danger")
                    return render_template('auth/login.html', form=form)
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
                    if user.is_admin:
                        return redirect(url_for('admin.index'))
                    return redirect(url_for('user.dashboard'))
            else:
                flash("Invalid password.", "danger")
        else:
            flash("User not found.", "danger")
    elif 'username' in session:
        return redirect(url_for('user.dashboard'))

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
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for('user.dashboard'))
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

            # Send Registration Email

            # Generate activation token
            activation_token = str(uuid.uuid4())
            
            # Create activation link
            activation_link = url_for('auth.activate_account', 
                                    token=activation_token, 
                                    _external=True)
            
            # Generate email content
            email_content = GetEmailContent.get_welcome_email_html(
                username=username,
                activation_link=activation_link
            )
            
            # Send email
            sync_send_email(
                subject="Welcome to LearnAnythingWithAI - Activate Your Account",
                receiver_email=email,
                html_content=email_content
            )
        
            # Create new user
            new_user = User(username=username, email=email, password=hashed_password, activation_token=activation_token)
            db.session.add(new_user)
            db.session.commit()
            
            
            flash('Registration successful! Please check your email and activate account to log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('auth.signup'))

    # If user already logged in, redirect
    if 'username' in session:
        return redirect(url_for('index'))

    return render_template('auth/signup.html', form=form)



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
                if not user.active:
                    flash("Your account has been deactivated. Please contact administrator.", "danger")
                    # Log out the user using Flask-Login
                    logout_user()

                    # Clear the Flask session (cookies)
                    session.clear()
                    return redirect(url_for('auth.login'))

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


@auth_bp.route('/activate/<token>')
def activate_account(token):
    """
    Activates a user account using the provided activation token.
    Token expires after 24 hours.
    """
    try:
        # Find user with matching activation token
        user = User.query.filter_by(activation_token=token).first()
        print(f"Activation token: {token} ")
        if not user:
            flash('Invalid activation link.', 'danger')
            return redirect(url_for('auth.login'))
            
        # Check if token is expired (24 hours)
        token_age = datetime.utcnow() - user.activation_token_created_at
        if token_age > timedelta(hours=24):
            flash('Activation link has expired. Please request a new one.', 'warning')
            return redirect(url_for('auth.resend_activation'))
            
        # Activate account
        user.active = True
        user.activation_token = None
        user.activation_token_created_at = None
        user.email_verified = True
        user.email_verified_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Your account has been successfully activated! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while activating your account.', 'danger')
        print(f"An error occurred while activating your account. {e}")
        return redirect(url_for('auth.login'))


@auth_bp.route('/resend-activation', methods=['GET', 'POST'])
def resend_activation():
    """
    Allows users to request a new activation link if the original expired.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Please provide your email address.', 'danger')
            return render_template('auth/resend_activation.html')
            
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('No account found with that email address.', 'danger')
            return render_template('auth/resend_activation.html')
            
        if user.active:
            flash('This account is already activated.', 'info')
            return redirect(url_for('auth.login'))
            
        # Generate new activation token
        new_token = str(uuid.uuid4())
        user.activation_token = new_token
        user.activation_token_created_at = datetime.utcnow()
        print("")
        try:
            # Create activation link
            activation_link = url_for('auth.activate_account', 
                                    token=new_token, 
                                    _external=True)
            
            # Generate email content
            email_content = GetEmailContent.get_welcome_email_html(
                username=user.username,
                activation_link=activation_link
            )
            
            # Send email
            sync_send_email(
                subject="LearnAnythingWithAI - New Account Activation Link",
                receiver_email=user.email,
                html_content=email_content
            )
            
            db.session.commit()
            flash('A new activation link has been sent to your email address.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while sending the activation link.', 'danger')
            print(f"An error occurred while sending the activation link.{e}")
            return render_template('auth/resend_activation.html')
    
    return render_template('auth/resend_activation.html')

@auth_bp.route('/send_message', methods=['POST'])
# @login_required
def send_message():
    form = SendMessageForm()
    try:
        if form.validate_on_submit():
            # Get client IP address
            if request.headers.get('X-Forwarded-For'):
                client_ip = request.headers.get('X-Forwarded-For').split(',')[0]
            else:
                client_ip = request.remote_addr
            name = form.name.data.strip()
            email = form.email.data.strip().lower()
            message = form.message.data.strip()

            # Check if the email actually exists
            #TODO uncomment this code when you have server email, noreply@<company_name>.com
            # if not email_exists(email):
            #     flash('The provided email does not exist. Please enter a valid email.', 'danger')
            #     return redirect(url_for('index'))

            # Generate email content
            email_content = GetEmailContent.get_thanks_email_html()

            #TODO uncomment this code when you have server email, noreply@<company_name>.com
            # Send email
            sync_send_email(
                subject="Thanks For Your Message",
                receiver_email=email,
                html_content=email_content
            )

            #TODO comment/remove this code when you have server email, noreply@<company_name>.com
            # Send email
            res = check_email_exists_and_send_email(
                subject="Thanks For Your Message",
                receiver_email=email,
                html_content=email_content
            )

            if not res:
                flash(f'Unable to send your message, please check your email and ensure it really exists', 'danger')
                return redirect(url_for('index'))

            # Save to DB
            new_user = UserMessage(name=name, email=email, message=message, client_ip=client_ip)
            db.session.add(new_user)
            db.session.commit()

            flash('Message sent successfully! Please check your email.', 'success')
            return redirect(url_for('index'))
        else:
            flash(f'Please correct the errors in the form and try again. {form.errors}', 'danger')
            return redirect(url_for('index'))

    except Exception as e:
        db.session.rollback()
        print(f"Error in send_message(): {e}")
        flash('Error sending your message. Please try again.', 'danger')
        return redirect(url_for('index'))
