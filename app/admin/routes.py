from flask import render_template
from flask_login import login_required
from app.admin import admin_bp
from app.utils.utils import roles_required

@admin_bp.route('/dashboard')
@roles_required('admin')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')
