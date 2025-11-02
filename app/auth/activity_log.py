from flask import request
from app.models import ActivityLog

def get_request_metadata():
    """Extract request metadata for activity logging"""
    return {
        'ip_address': request.remote_addr,
        'user_agent': request.user_agent.string if request.user_agent else None,
        'request_method': request.method,
        'request_url': request.url
    }

def log_registration(user, role_type, additional_data=None):
    """
    Log user registration activity
    
    Args:
        user: User object that was created
        role_type: 'parent', 'teacher', or 'vendor'
        additional_data: Additional metadata to store
    """
    metadata = get_request_metadata()
    
    new_values = {
        'user_id': user.id,
        'email': user.email,
        'role': user.role,
        'first_name': user.first_name,
        'last_name': user.last_name
    }
    
    if additional_data:
        new_values.update(additional_data)
    
    return ActivityLog.log_action(
        action='user_registered',
        user_id=user.id,
        entity_type='user',
        entity_id=user.id,
        description=f"New {role_type} account registered: {user.email}",
        category='user',
        new_values=new_values,
        metadata={'registration_type': role_type},
        ip_address=metadata['ip_address'],
        user_agent=metadata['user_agent'],
        request_method=metadata['request_method'],
        request_url=metadata['request_url'],
        status='success'
    )

def log_login(user, success=True, error_message=None):
    """
    Log user login attempt
    
    Args:
        user: User object (or None if login failed)
        success: Whether login was successful
        error_message: Error message if login failed
    """
    metadata = get_request_metadata()
    
    if success and user:
        return ActivityLog.log_action(
            action='login_success',
            user_id=user.id,
            entity_type='user',
            entity_id=user.id,
            description=f"User logged in: {user.email}",
            category='security',
            new_values={'role': user.role, 'email': user.email},
            ip_address=metadata['ip_address'],
            user_agent=metadata['user_agent'],
            request_method=metadata['request_method'],
            request_url=metadata['request_url'],
            status='success'
        )
    else:
        # Log failed login attempt (without user_id for security)
        email = request.form.get('email') or request.get_json().get('email', 'unknown')
        return ActivityLog.log_action(
            action='login_failed',
            user_id=None,
            entity_type='user',
            entity_id=None,
            description=f"Failed login attempt for: {email}",
            category='security',
            metadata={'attempted_email': email},
            ip_address=metadata['ip_address'],
            user_agent=metadata['user_agent'],
            request_method=metadata['request_method'],
            request_url=metadata['request_url'],
            status='failed',
            error_message=error_message or 'Invalid credentials'
        )

def log_logout(user):
    """Log user logout"""
    metadata = get_request_metadata()
    
    return ActivityLog.log_action(
        action='logout',
        user_id=user.id,
        entity_type='user',
        entity_id=user.id,
        description=f"User logged out: {user.email}",
        category='security',
        ip_address=metadata['ip_address'],
        user_agent=metadata['user_agent'],
        request_method=metadata['request_method'],
        request_url=metadata['request_url'],
        status='success'
    )

def log_password_reset_request(user):
    """Log password reset request"""
    metadata = get_request_metadata()
    
    return ActivityLog.log_action(
        action='password_reset_requested',
        user_id=user.id if user else None,
        entity_type='user',
        entity_id=user.id if user else None,
        description=f"Password reset requested for: {user.email if user else 'unknown'}",
        category='security',
        ip_address=metadata['ip_address'],
        user_agent=metadata['user_agent'],
        request_method=metadata['request_method'],
        request_url=metadata['request_url'],
        status='success'
    )

def log_password_reset_completed(user):
    """Log successful password reset"""
    metadata = get_request_metadata()
    
    return ActivityLog.log_action(
        action='password_reset_completed',
        user_id=user.id,
        entity_type='user',
        entity_id=user.id,
        description=f"Password reset completed for: {user.email}",
        category='security',
        ip_address=metadata['ip_address'],
        user_agent=metadata['user_agent'],
        request_method=metadata['request_method'],
        request_url=metadata['request_url'],
        status='success'
    )

def log_email_verification(user):
    """Log email verification"""
    metadata = get_request_metadata()
    
    return ActivityLog.log_action(
        action='email_verified',
        user_id=user.id,
        entity_type='user',
        entity_id=user.id,
        description=f"Email verified for: {user.email}",
        category='user',
        new_values={'is_verified': True},
        ip_address=metadata['ip_address'],
        user_agent=metadata['user_agent'],
        request_method=metadata['request_method'],
        request_url=metadata['request_url'],
        status='success'
    )

def log_vendor_profile_creation(vendor, user):
    """Log vendor profile creation"""
    metadata = get_request_metadata()
    
    return ActivityLog.log_action(
        action='vendor_profile_created',
        user_id=user.id,
        entity_type='vendor',
        entity_id=vendor.id,
        description=f"Vendor profile created: {vendor.business_name}",
        category='user',
        new_values={
            'business_name': vendor.business_name,
            'business_type': vendor.business_type,
            'city': vendor.city,
            'country': vendor.country
        },
        ip_address=metadata['ip_address'],
        user_agent=metadata['user_agent'],
        request_method=metadata['request_method'],
        request_url=metadata['request_url'],
        status='success'
    )