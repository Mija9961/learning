from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from . import admin_bp
from ..models import User, AIModel, UserMessage
from ..extensions import db
import os
from .util.decorators import admin_required

@admin_bp.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/index.html', user=current_user)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html', user=current_user)

@admin_bp.route('/users')
@admin_required
@login_required
def users():
    # Sample: users = User.query.all()
    users = User.query.order_by(User.id).all()

    return render_template('admin/users.html', users=users, user=current_user)

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


@admin_bp.route('/ai-models', methods=["GET", "POST"])
@login_required
@admin_required
def ai_models():
    if request.method == "POST":
        model_name = request.form.get("model_name")
        provider = request.form.get("provider")
        if model_name and provider:
            new_model = AIModel(model_name=model_name, provider=provider)
            db.session.add(new_model)
            db.session.commit()
            flash("AI Model added successfully.", "success")
        else:
            flash("Model Name and Provider are required.", "danger")
        return redirect(url_for('admin.ai_models'))

    models = AIModel.query.order_by(AIModel.id).all()
    return render_template("admin/ai_models.html", models=models, user=current_user)


@admin_bp.route("/ai-models/<int:model_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_ai_model(model_id):
    model = AIModel.query.get_or_404(model_id)
    if request.method == "POST":
        model.model_name = request.form.get("model_name")
        model.provider = request.form.get("provider")
        db.session.commit()
        flash("AI Model updated successfully.", "success")
        return redirect(url_for("admin.ai_models"))
    return render_template("admin/edit_ai_model.html", model=model, user=current_user)



@admin_bp.route("/ai-models/<int:model_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_ai_model(model_id):
    model = AIModel.query.get_or_404(model_id)
    db.session.delete(model)
    db.session.commit()
    flash("AI Model deleted.", "success")
    return redirect(url_for("admin.ai_models"))



@admin_bp.route('/messages')
@login_required
@admin_required
def view_messages():
    messages = UserMessage.query.order_by(UserMessage.received_at.desc()).all()
    return render_template('admin/messages.html', messages_list=messages, user=current_user)

@admin_bp.route("/toggle-read/<int:msg_id>", methods=["POST"])
@login_required
def toggle_read(msg_id):
    message = UserMessage.query.get_or_404(msg_id)
    message.is_read_message = not message.is_read_message
    db.session.commit()
    return jsonify({
        "success": True,
        "is_read": message.is_read_message
    })