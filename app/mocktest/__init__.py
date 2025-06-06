from flask import Blueprint

mocktest_bp = Blueprint('mocktest', __name__, template_folder='templates')

from . import routes
