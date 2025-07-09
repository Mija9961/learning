from flask import Blueprint

custom_subject_bp = Blueprint('custom_subject', __name__, template_folder='templates')

from . import routes
