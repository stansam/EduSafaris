from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.main import main_bp

@main_bp.route('/')
def index():
    """Home page"""
    return render_template('main/index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - redirect to appropriate dashboard based on role"""
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'vendor':
        return redirect(url_for('vendor.dashboard'))
    elif current_user.role == 'teacher':
        return redirect(url_for('trips.list_trips'))
    else:
        return render_template('main/dashboard.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('main/about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('main/contact.html')
