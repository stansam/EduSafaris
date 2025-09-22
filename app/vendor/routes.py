from flask import render_template
from flask_login import login_required
from app.vendor import vendor_bp

@vendor_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('vendor/dashboard.html')
