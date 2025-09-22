from flask import render_template
from flask_login import login_required
from app.profiles import profiles_bp

@profiles_bp.route('/profile')
@login_required
def profile_view():
    return render_template('profiles/profile_view.html')
