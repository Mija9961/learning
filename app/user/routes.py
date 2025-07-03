from flask import render_template, jsonify, request, flash, session, redirect, url_for
from flask_login import login_required, current_user
from . import user_bp
from app import db, limiter
from app.models import User, AIModel, UserAIModel
from dotenv import load_dotenv
import os

load_dotenv()

@user_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('user/dashboard.html', user=current_user)

@user_bp.route('/profile')
@login_required
def profile():
    return render_template('user/profile.html', user=current_user)



# Model provider to models mapping
# MODEL_REGISTRY = {
#     "OpenAI": ["gpt-3.5-turbo", "gpt-4", "gpt-4o"],
#     "Anthropic": ["claude-3-sonnet", "claude-3-haiku"],
#     "Gemini": ["gemini-pro", "gemini-1.5-pro"]
# }
# @user_bp.route('/settings', methods=['GET', 'POST'])
# @login_required
# def settings():
#     if request.method == 'POST':
#         provider = request.form.get('provider')
#         model = request.form.get('model')

#         if provider not in MODEL_REGISTRY or model not in MODEL_REGISTRY[provider]:
#             flash("Invalid provider or model selection.", "danger")
#             return redirect(url_for('user.settings'))

#         session['selected_provider'] = provider
#         session['selected_model'] = model
#         flash("Settings saved successfully.", "success")
#         return redirect(url_for('user.settings'))

#     return render_template('user/settings.html',
#                            selected_provider=session.get('selected_provider'),
#                            selected_model=session.get('selected_model'),
#                            model_registry=MODEL_REGISTRY)



# @login_required
# @user_bp.route('/get-models/<provider>', methods=['GET'])
# def get_models(provider):
#     if provider in MODEL_REGISTRY:
#         return jsonify(MODEL_REGISTRY[provider])
#     return jsonify([]), 404


@user_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        provider = request.form.get('provider')
        model = request.form.get('model')

        # Save or update user settings in DB
        user_model = UserAIModel.query.filter_by(user_email=current_user.email).first()
        if user_model:
            user_model.provider = provider
            user_model.model_name = model
        else:
            user_model = UserAIModel(
                user_email=current_user.email,
                provider=provider,
                model_name=model
            )
            db.session.add(user_model)

        db.session.commit()
        flash("Settings updated successfully.", "success")
        return redirect(url_for('user.settings'))

    # Fetch user's existing settings
    user_model = UserAIModel.query.filter_by(user_email=current_user.email).first()
    selected_provider = user_model.provider if user_model else os.environ.get("DEFAULT_AI_PROVIDER", None)
    selected_model = user_model.model_name if user_model else os.environ.get("DEFAULT_AI_MODEL", None)

    # Fetch providers and models from the database instead of hardcoding
    providers = db.session.query(AIModel.provider).distinct().all()
    model_registry = {
        provider[0]: [m.model_name for m in AIModel.query.filter_by(provider=provider[0]).all()]
        for provider in providers
    }

    return render_template(
        'user/settings.html',
        selected_provider=selected_provider,
        selected_model=selected_model,
        model_registry=model_registry
    )

@user_bp.route('/get-models/<provider>')
@login_required
def get_models(provider):
    models = [m.model_name for m in AIModel.query.filter_by(provider=provider).all()]
    return jsonify(models)