from flask import Blueprint

api_bp = Blueprint('api', __name__)

from app.api import routes
from app.api.main import trip_details, dash, trips
from app.api.auth import teacher, vendor
from app.api.profile import profile
from app.api.teacher import trip, participants, vendors
from app.api.teacher.participant import fetch
from app.api.parent import children, trips, payment, extra_payment
from app.api.vendor import booking, financials, dash, profile
