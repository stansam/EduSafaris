from flask import Blueprint

vendor_bp = Blueprint('vendor', __name__, template_folder='templates', static_folder='static')

from app.vendor import routes
