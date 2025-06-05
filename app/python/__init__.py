from flask import Blueprint

python_bp = Blueprint('python', __name__, template_folder='templates')

from . import routes
