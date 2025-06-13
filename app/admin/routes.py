from flask import render_template, flash, redirect, url_for
from flask_login import login_required
from . import admin_bp
from ..models import User
from ..extensions import db
import os
from .util.decorators import admin_required

@admin_bp.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/index.html')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/users')
@admin_required
@login_required
def users():
    # Sample: users = User.query.all()
    users = User.query.order_by(User.id).all()

    return render_template('admin/users.html', users=users)

@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.active = not user.active
    if not user.active:
        user.session_token = os.urandom(24).hex()
    db.session.commit()
    flash(f"User '{user.username}' status updated to {'Active' if user.active else 'Inactive'}.", "success")
    return redirect(url_for("admin.users"))
