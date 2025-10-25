from flask import Blueprint

parent_comm_bp = Blueprint(
    'parent_comm', 
    __name__, 
    template_folder='templates',
    static_folder='static'
)

from app.parent_comm import routes