from flask import Blueprint

teacher_bp = Blueprint('teacher', __name__, static_folder='static', template_folder='templates', static_url_path='/teacher/static/')

from app.teacher import routes
from app.teacher.api import dash, trips, participants, notifications
