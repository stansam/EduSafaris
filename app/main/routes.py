from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.main import main_bp

@main_bp.route('/')
def index():
    """Home page"""
    return render_template('main/index.html')

# @main_bp.route('/dashboard')
# @login_required
# def dashboard():
#     """User dashboard - redirect to appropriate dashboard based on role"""
#     if current_user.role == 'admin':
#         return redirect(url_for('admin.dashboard'))
#     elif current_user.role == 'vendor':
#         return redirect(url_for('vendor.vendor_directory'))
#     elif current_user.role == 'teacher':
#         return redirect(url_for('trips.list_trips'))
#     elif current_user.role == 'parent':
#             return redirect(url_for('parent_comm.parent_trips'))
#     else:
#         return render_template('main/index.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('main/about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('main/contact.html')

@main_bp.route('/explore-trips')
def trips():
    """trips page"""
    return render_template('main/trips.html')

@main_bp.route('/for-schools')
def for_schools():
    """trips page"""
    return render_template('main/schools.html')

@main_bp.route('/for-providers')
def for_providers():
    """trips page"""
    return render_template('main/providers.html')

# @main_bp.route('/trip/name')
@main_bp.route('/trip/<int:trip_id>')
def trip_details(trip_id):
    return render_template('main/trip_details.html', trip_id=trip_id)