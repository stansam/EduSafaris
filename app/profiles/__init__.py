from flask import Blueprint

profiles_bp = Blueprint('profiles', __name__, template_folder='templates', static_folder='static')

from app.profiles import routes
