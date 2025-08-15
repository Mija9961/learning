from flask import render_template, flash, redirect, url_for, request, jsonify, current_app, send_from_directory, abort, session
from flask_login import current_user, login_required
from . import rag_bp
from ..models import User, Document, UserAIModel
from ..extensions import db
import os, asyncio, uuid
from .util.doc_modifier import extract_text_from_pdf
from ..util.chromadb import ChromaMemory
from .util.llm_response import LLMResponse
from werkzeug.utils import secure_filename

memory = ChromaMemory()

def allowed_file(filename):
    """Check if the file extension is allowed."""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@rag_bp.route('/upload_doc', methods=['GET', 'POST'])
@login_required
def upload_doc():
    results = []
    formatted_answer = None
    documents = Document.query.filter_by(user_email=current_user.email).order_by(Document.created_at.desc()).all()
    # Set AI model
    user_model = UserAIModel.query.filter_by(user_email=current_user.email).first()
    selected_provider = user_model.provider if user_model else os.environ.get("DEFAULT_AI_PROVIDER", None)
    selected_model = user_model.model_name if user_model else os.environ.get("DEFAULT_AI_MODEL", None)
    session['ai_provider'] = selected_provider.lower()
    session['ai_model'] = selected_model.lower()
    if request.method == 'POST':
        # Handle memory reset
        if 'reset' in request.form:
            memory.client.delete_collection(name="agent_memory")
            memory.__init__()
            flash('Memory has been reset successfully', 'success')
            return redirect(url_for('rag.upload_doc'))

        # Handle file upload
        if 'document' in request.files:
            file = request.files['document']
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                try:
                    # Generate document_id
                    document_id = str(uuid.uuid4())
                    
                    # Create unique filename
                    filename = secure_filename(f"{file.filename}")
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER_DOC'], filename)
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    
                    # Save file
                    file.save(filepath)

                    # Create document record
                    document = Document(
                        document_id=document_id,
                        filename=filename,
                        filepath=filepath,
                        user_email=current_user.email
                    )
                    db.session.add(document)
                    db.session.commit()

                    # Extract text based on file type
                    if filename.endswith('.pdf'):
                        text = extract_text_from_pdf(file)
                    else:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            text = f.read()

                    # Add to memory with metadata
                    memory.add(
                        text=text,
                        metadata={
                            'doc_id': document.id,
                            'filename': filename,
                            'user_email': current_user.email,
                            'created_at': document.created_at.isoformat()
                        }
                    )

                    flash('Document uploaded and processed successfully!', 'success')
                    return redirect(url_for('rag.upload_doc'))

                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error processing document: {str(e)}")
                    flash('Error processing document. Please try again.', 'danger')
                    return redirect(request.url)

            flash('Invalid file type', 'danger')
            return redirect(request.url)

        # Handle query
        if 'query' in request.form:
            query = request.form.get('query')
            results = memory.search(query)
            
            # Format results via LLM
            if results:
                try:
                    prompt = (
                        f"Based on the following context, please answer the query:\n\n"
                        f"Context:\n{[r['text'] for r in results]}\n\n"
                        f"Query:\n{query}"
                    )
                    print(f"prompt::{prompt}")
                    formatted_answer = asyncio.run(LLMResponse.get_formatted_response_from_llm(prompt))
                except Exception as e:
                    current_app.logger.error(f"Error formatting response: {str(e)}")
                    formatted_answer = "Error processing response"

    return render_template(
        'rag/upload_doc.html',
        documents=documents,
        results=results,
        formatted_answer=formatted_answer,
        user=current_user
    )

@rag_bp.route('/upload', methods=['POST'])
@login_required
def upload_document():
    if 'document' not in request.files:
        flash('No file selected', 'danger')
        return redirect(request.url)
        
    file = request.files['document']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(request.url)
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER_DOC'], filename)
        file.save(filepath)
        
        # Create document record in database
        document = Document(
            filename=filename,
            filepath=filepath,
            user_email=current_user.email
        )
        db.session.add(document)
        db.session.commit()
        
        # Process document for RAG
        process_document_for_rag(filepath, document.id)
        
        flash('Document uploaded successfully!', 'success')
        return redirect(url_for('rag.upload_doc'))
        
    flash('Invalid file type', 'danger')
    return redirect(request.url)

async def get_rag_answer(doc_id, question):
    """Get answer for a question using RAG approach."""
    try:
        # Get document from database
        document = Document.query.get_or_404(doc_id)
        
        # Search in memory with metadata filter
        results = memory.search(
            query=question,
            filter_metadata={"doc_id": int(doc_id)}  # Ensure doc_id is an integer
        )
        
        if not results:
            return "I couldn't find relevant information in the document to answer your question."
        
        # Construct prompt with context
        context_texts = [r["text"] for r in results]
        prompt = (
            f"Based on the following context from the document '{document.filename}', "
            f"please answer this question: {question}\n\n"
            f"Context:\n{context_texts}\n\n"
            "Please provide a clear and concise answer using only the information "
            "from the given context. If the answer cannot be found in the context, "
            "say so explicitly."
        )
        
        # Get formatted response from LLM
        answer = await LLMResponse.get_formatted_response_from_llm(prompt)
        return answer
        
    except Exception as e:
        current_app.logger.error(f"RAG answer error: {str(e)}")
        raise

# Update the ask_question route to use asyncio
@rag_bp.route('/ask', methods=['POST'])
@login_required
def ask_question():
    data = request.get_json()
    doc_id = data.get('doc_id')
    question = data.get('question')
    
    if not doc_id or not question:
        return jsonify({'error': 'Missing required parameters'}), 400
        
    try:
        # Run async function in sync context
        answer = asyncio.run(get_rag_answer(doc_id, question))
        return jsonify({'answer': answer})
    except Exception as e:
        current_app.logger.error(f"Error in RAG Q&A: {str(e)}")
        return jsonify({'error': 'Failed to process question'}), 500

@rag_bp.route('/preview/<doc_id>')
@login_required
def preview_document(doc_id):
    """Preview document endpoint."""
    try:
        # Get document and verify ownership
        document = Document.query.filter_by(
            document_id=doc_id, 
            user_email=current_user.email
        ).first_or_404()
        
        # Get file extension
        file_ext = document.filename.rsplit('.', 1)[1].lower()
        
        # For PDFs and text files, serve directly
        if file_ext in {'pdf'}:
            return send_from_directory(
                current_app.config['UPLOAD_FOLDER_DOC'],
                document.filename,
                as_attachment=False
            )
        else:
            flash(f"Unsupported documents",'danger')
    except Exception as e:
        current_app.logger.error(f"Error previewing document: {str(e)}")
        abort(404)