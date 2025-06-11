from flask import Blueprint

autogen_bp = Blueprint('autogen', __name__, template_folder='templates')

from . import routes
