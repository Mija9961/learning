from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required
from . import admin_bp
from ..models import User
from ..extensions import db
import os, asyncio
from .util.decorators import admin_required
from .util.doc_modifier import extract_text_from_pdf
from ..util.chromadb import memory
from .util.llm_response import LLMResponse
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


@admin_bp.route('/upload_doc', methods=['GET', 'POST'])
@login_required
@admin_required
def upload_doc():
    results = []
    formatted_answer = None
    if request.method == 'POST':
        # ✅ Check if user wants to reset
        if 'reset' in request.form:
            memory.client.delete_collection(name="agent_memory")  # Delete the existing collection
            memory.__init__()  # Reinitialize to create an empty one

        # ✅ Upload and Extract Text
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file.filename != '':
                text = extract_text_from_pdf(pdf_file)
                # Add the whole text (splitting handled by your `memory.add()` method)
                memory.add(text)

        # ✅ Handle the Query
        if 'query' in request.form:
            query = request.form.get('query')
            results = memory.search(query)
            # 🐍 Format Results via OpenAI
            combined_results = " ".join(results) if results else "No relevant information found."
            prompt = (
                f"Data: \n{combined_results}\n\n"
                f"Query:\n{query}"
            )
            formatted_answer = asyncio.run(LLMResponse.get_formatted_response_from_llm(prompt))

    return render_template('admin/upload_doc.html', results=results, formatted_answer=formatted_answer)
