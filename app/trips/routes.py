from flask import render_template
from flask_login import login_required
from app.trips import trips_bp

@trips_bp.route('/')
@login_required
def list_trips():
    return render_template('trips/list.html')
