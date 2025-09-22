from flask import render_template
from flask_login import login_required
from app.admin import admin_bp

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')
