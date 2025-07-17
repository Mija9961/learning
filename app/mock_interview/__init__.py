from flask import Blueprint

mock_interview_bp = Blueprint('mock_interview', __name__, template_folder='templates')

from . import routes
