
from flask import session, flash, redirect, url_for
from app.models import User
from app.extensions import db
from flask_login import current_user, logout_user

def check_session_validity():
    if 'username' in session:
        user = db.session.query(User).filter_by(username=session['username']).first()
        if user:
            if not user.active:
                session.clear()
                flash("Your account has been deactivated. Please contact administrator.", "danger")

                return redirect(url_for('auth.login'))
            db_token = user.session_token
            if db_token != session.get('session_token'):
                # Invalidate session
                session.clear()
                flash("Your session has expired or was logged in elsewhere.", "danger")
                return redirect(url_for('auth.login'))  # Adjust to your login endpoint
            
def check_user_active_status():
    if current_user.is_authenticated:
        # Check if account is active
        if not current_user.active:
            logout_user()
            flash("Your account has been deactivated.", "danger")
            return redirect(url_for("login"))

        # Check if session token is valid
        if session.get("session_token") != current_user.session_token:
            logout_user()
            flash("Your session has expired.", "warning")
            return redirect(url_for("login"))
