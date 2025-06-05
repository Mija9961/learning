
from flask import session, flash, redirect, url_for
from app.models import User
from app.extensions import db

def check_session_validity():
    if 'username' in session:
        user = db.session.query(User).filter_by(username=session['username']).first()
        if user:
            db_token = user.session_token
            if db_token != session.get('session_token'):
                # Invalidate session
                session.clear()
                flash("Your session has expired or was logged in elsewhere.", "danger")
                return redirect(url_for('auth.login'))  # Adjust to your login endpoint
