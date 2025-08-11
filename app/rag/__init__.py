from flask import Blueprint

rag_bp = Blueprint('rag', __name__, template_folder='templates')

from . import routes
