from app.models import ActivityLog, School
from flask import request
from flask_login import current_user
from datetime import datetime
from app.api.admin.users.validators import validate_email, validate_phone

def log_admin_action(action, target_user_id, description, old_values=None, new_values=None, status='success'):
    """Log admin actions for audit trail"""
    try:
        ActivityLog.log_action(
            action=action,
            user_id=current_user.id,
            entity_type='user',
            entity_id=target_user_id,
            description=description,
            category='user',
            old_values=old_values,
            new_values=new_values,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            request_method=request.method,
            request_url=request.url,
            status=status
        )
    except Exception as e:
        # Log the error but don't fail the main operation
        print(f"Error logging admin action: {str(e)}")


def validate_user_data(data, is_update=False):
    """Validate user data with detailed error messages"""
    errors = {}
    
    if not is_update or 'email' in data:
        if not data.get('email'):
            errors['email'] = 'Email is required'
        elif not validate_email(data['email']):
            errors['email'] = 'Invalid email format'
    
    if not is_update:
        if not data.get('first_name'):
            errors['first_name'] = 'First name is required'
        if not data.get('last_name'):
            errors['last_name'] = 'Last name is required'
        if not data.get('role'):
            errors['role'] = 'Role is required'
        elif data['role'] not in ['parent', 'teacher', 'vendor', 'admin']:
            errors['role'] = 'Invalid role. Must be parent, teacher, vendor, or admin'
    
    if 'role' in data and data['role'] not in ['parent', 'teacher', 'vendor', 'admin']:
        errors['role'] = 'Invalid role'
    
    if 'phone' in data and data['phone'] and not validate_phone(data['phone']):
        errors['phone'] = 'Invalid phone format'
    
    if 'school_id' in data and data['school_id']:
        school = School.query.get(data['school_id'])
        if not school:
            errors['school_id'] = 'School not found'
    
    return errors


def get_user_statistics(user):
    """Get comprehensive statistics for a user"""
    stats = {
        'total_logins': ActivityLog.query.filter_by(
            user_id=user.id, 
            action='login'
        ).count(),
        'last_activity': None,
        'account_age_days': (datetime.now() - user.created_at).days if user.created_at else 0
    }
    
    # Get last activity
    last_activity = ActivityLog.query.filter_by(user_id=user.id)\
        .order_by(ActivityLog.created_at.desc()).first()
    if last_activity:
        stats['last_activity'] = last_activity.created_at.isoformat()
    
    # Role-specific statistics
    if user.is_teacher():
        stats.update({
            'total_trips': user.organized_trips.count(),
            'active_trips': user.get_active_trips_count(),
            'total_students': user.get_total_students()
        })
    elif user.is_parent():
        stats.update({
            'total_children': user.get_children_count(),
            'active_registrations': len(user.get_active_registrations()),
            'total_spent': float(user.get_total_spent()),
            'outstanding_balance': float(user.get_outstanding_balance())
        })
    elif user.is_vendor():
        if user.vendor_profile:
            stats.update({
                'total_bookings': user.vendor_profile.service_bookings.count(),
                'average_rating': user.vendor_profile.average_rating,
                'total_reviews': user.vendor_profile.total_reviews
            })
    
    return stats
