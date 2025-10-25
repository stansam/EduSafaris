from flask import Blueprint

safety_bp = Blueprint('safety', __name__, 
                     template_folder='templates', 
                     static_folder='static')

from app.safety import routes, socket_handlers