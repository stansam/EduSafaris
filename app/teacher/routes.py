from flask import render_template, jsonify
from flask_login import login_required, current_user
from app.teacher import teacher_bp

@teacher_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_teacher():
        return jsonify({'error': 'Unauthorized'}), 403
    return render_template('teacher/dashboard.html')