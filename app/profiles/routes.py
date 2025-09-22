import os
from flask import render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
from app.profiles import profiles_bp
from app.profiles.forms import ProfileForm, ChangePasswordForm
from app.models import User
from app.extensions import db
from app.utils import roles_required
import uuid

# Allowed file extensions for profile pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image_path, max_size=(300, 300)):
    """Resize uploaded image to maximum dimensions"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(image_path, optimize=True, quality=85)
    except Exception as e:
        current_app.logger.error(f"Error resizing image: {e}")

@profiles_bp.route('/profile')
@login_required
def profile_view():
    """Display current user's profile with role-specific sections"""
    return render_template('profiles/profile_view.html', user=current_user)

@profiles_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def profile_edit():
    """Edit profile fields, phone, school, profile picture upload"""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Update basic profile fields
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        current_user.school = form.school.data
        current_user.bio = form.bio.data
        current_user.emergency_contact = form.emergency_contact.data
        current_user.emergency_phone = form.emergency_phone.data
        
        # Handle profile picture upload
        if form.profile_picture.data:
            file = form.profile_picture.data
            if file and allowed_file(file.filename):
                # Generate unique filename
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                
                # Create uploads directory if it doesn't exist
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'profiles')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save file
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                
                # Resize image
                resize_image(file_path)
                
                # Remove old profile picture if it exists
                if current_user.profile_picture and current_user.profile_picture != 'default.png':
                    old_path = os.path.join(upload_folder, current_user.profile_picture)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass
                
                current_user.profile_picture = unique_filename
            else:
                flash('Invalid file type. Please upload PNG, JPG, JPEG, or GIF files only.', 'error')
                return render_template('profiles/profile_edit.html', form=form)
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profiles.profile_view'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating profile: {e}")
            flash('An error occurred while updating your profile. Please try again.', 'error')
    
    return render_template('profiles/profile_edit.html', form=form)

@profiles_bp.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Authenticated password change using current password confirmation"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.verify_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return render_template('profiles/change_password.html', form=form)
        
        # Update password
        current_user.password = form.new_password.data
        
        try:
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profiles.profile_view'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error changing password: {e}")
            flash('An error occurred while changing your password. Please try again.', 'error')
    
    return render_template('profiles/change_password.html', form=form)

@profiles_bp.route('/users/<int:user_id>')
@login_required
@roles_required('admin')
def admin_user_view(user_id):
    """Admin-only view of any user"""
    user = User.query.get_or_404(user_id)
    return render_template('profiles/admin_user_view.html', user=user)

@profiles_bp.route('/users')
@login_required
@roles_required('admin')
def admin_users_list():
    """Admin-only list of all users"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    role_filter = request.args.get('role', '', type=str)
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.first_name.contains(search)) |
            (User.last_name.contains(search)) |
            (User.email.contains(search))
        )
    
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('profiles/admin_users_list.html', 
                         users=users, search=search, role_filter=role_filter)

@profiles_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@roles_required('admin')
def toggle_user_status(user_id):
    """Admin-only toggle user active status"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('profiles.admin_user_view', user_id=user_id))
    
    user.is_active = not user.is_active
    status = 'activated' if user.is_active else 'deactivated'
    
    try:
        db.session.commit()
        flash(f'User {user.email} has been {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling user status: {e}")
        flash('An error occurred while updating user status.', 'error')
    
    return redirect(url_for('profiles.admin_user_view', user_id=user_id))