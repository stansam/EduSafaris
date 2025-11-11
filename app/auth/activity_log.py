from flask import request
from app.models import ActivityLog

def get_request_metadata():
    """Extract request metadata for activity logging"""
    return {
        'ip_address': request.remote_addr if request else None,
        'user_agent': request.user_agent.string if request and request.user_agent else None,
        'request_method': request.method if request else None,
        'request_url': request.url if request else None
    }

def log_registration(user, role_type, additional_data=None):
    """
    Log user registration activity
    
    Args:
        user: User object that was created
        role_type: 'parent', 'teacher', or 'vendor'
        additional_data: Additional metadata to store
    """
    try:
        metadata = get_request_metadata()
        
        new_values = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name
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
            ip_address=metadata.get('ip_address'),
            user_agent=metadata.get('user_agent'),
            request_method=metadata.get('request_method'),
            request_url=metadata.get('request_url'),
            status='success'
        )
    except Exception as e:
        print(f"Error logging registration: {str(e)}")
        return None

def log_login(user, success=True, error_message=None):
    """
    Log user login attempt
    
    Args:
        user: User object (or None if login failed)
        success: Whether login was successful
        error_message: Error message if login failed
    """
    try:
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
                ip_address=metadata.get('ip_address'),
                user_agent=metadata.get('user_agent'),
                request_method=metadata.get('request_method'),
                request_url=metadata.get('request_url'),
                status='success'
            )
        else:
            # Log failed login attempt (without user_id for security)
            email = 'unknown'
            if request:
                try:
                    if request.form:
                        email = request.form.get('email', 'unknown')
                    elif request.get_json():
                        email = request.get_json().get('email', 'unknown')
                except Exception:
                    pass
            
            return ActivityLog.log_action(
                action='login_failed',
                user_id=None,
                entity_type='user',
                entity_id=None,
                description=f"Failed login attempt for: {email}",
                category='security',
                metadata={'attempted_email': email},
                ip_address=metadata.get('ip_address'),
                user_agent=metadata.get('user_agent'),
                request_method=metadata.get('request_method'),
                request_url=metadata.get('request_url'),
                status='failed',
                error_message=error_message or 'Invalid credentials'
            )
    except Exception as e:
        print(f"Error logging login: {str(e)}")
        return None

def log_logout(user):
    """Log user logout"""
    try:
        metadata = get_request_metadata()
        
        return ActivityLog.log_action(
            action='logout',
            user_id=user.id,
            entity_type='user',
            entity_id=user.id,
            description=f"User logged out: {user.email}",
            category='security',
            ip_address=metadata.get('ip_address'),
            user_agent=metadata.get('user_agent'),
            request_method=metadata.get('request_method'),
            request_url=metadata.get('request_url'),
            status='success'
        )
    except Exception as e:
        print(f"Error logging logout: {str(e)}")
        return None

def log_password_reset_request(user):
    """Log password reset request"""
    try:
        metadata = get_request_metadata()
        
        return ActivityLog.log_action(
            action='password_reset_requested',
            user_id=user.id if user else None,
            entity_type='user',
            entity_id=user.id if user else None,
            description=f"Password reset requested for: {user.email if user else 'unknown'}",
            category='security',
            ip_address=metadata.get('ip_address'),
            user_agent=metadata.get('user_agent'),
            request_method=metadata.get('request_method'),
            request_url=metadata.get('request_url'),
            status='success'
        )
    except Exception as e:
        print(f"Error logging password reset request: {str(e)}")
        return None

def log_password_reset_completed(user):
    """Log successful password reset"""
    try:
        metadata = get_request_metadata()
        
        return ActivityLog.log_action(
            action='password_reset_completed',
            user_id=user.id,
            entity_type='user',
            entity_id=user.id,
            description=f"Password reset completed for: {user.email}",
            category='security',
            ip_address=metadata.get('ip_address'),
            user_agent=metadata.get('user_agent'),
            request_method=metadata.get('request_method'),
            request_url=metadata.get('request_url'),
            status='success'
        )
    except Exception as e:
        print(f"Error logging password reset completion: {str(e)}")
        return None

def log_email_verification(user):
    """Log email verification"""
    try:
        metadata = get_request_metadata()
        
        return ActivityLog.log_action(
            action='email_verified',
            user_id=user.id,
            entity_type='user',
            entity_id=user.id,
            description=f"Email verified for: {user.email}",
            category='user',
            new_values={'is_verified': True},
            ip_address=metadata.get('ip_address'),
            user_agent=metadata.get('user_agent'),
            request_method=metadata.get('request_method'),
            request_url=metadata.get('request_url'),
            status='success'
        )
    except Exception as e:
        print(f"Error logging email verification: {str(e)}")
        return None

def log_vendor_profile_creation(vendor, user):
    """Log vendor profile creation"""
    try:
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
                'country': vendor.country,
                'is_verified': vendor.is_verified,
                'is_active': vendor.is_active
            },
            ip_address=metadata.get('ip_address'),
            user_agent=metadata.get('user_agent'),
            request_method=metadata.get('request_method'),
            request_url=metadata.get('request_url'),
            status='success'
        )
    except Exception as e:
        print(f"Error logging vendor profile creation: {str(e)}")
        return None

def log_profile_update(user, old_values, new_values, update_type='profile'):
    """
    Log user profile updates
    
    Args:
        user: User object
        old_values: Dictionary of old values
        new_values: Dictionary of new values
        update_type: Type of update (profile, settings, etc.)
    """
    try:
        metadata = get_request_metadata()
        
        return ActivityLog.log_action(
            action='profile_updated',
            user_id=user.id,
            entity_type='user',
            entity_id=user.id,
            description=f"User profile updated: {update_type}",
            category='user',
            old_values=old_values,
            new_values=new_values,
            metadata={'update_type': update_type},
            ip_address=metadata.get('ip_address'),
            user_agent=metadata.get('user_agent'),
            request_method=metadata.get('request_method'),
            request_url=metadata.get('request_url'),
            status='success'
        )
    except Exception as e:
        print(f"Error logging profile update: {str(e)}")
        return None

def log_error(action, error_message, user_id=None, entity_type=None, entity_id=None):
    """
    Log application errors
    
    Args:
        action: Action being performed when error occurred
        error_message: Error message
        user_id: User ID if applicable
        entity_type: Entity type if applicable
        entity_id: Entity ID if applicable
    """
    try:
        metadata = get_request_metadata()
        
        return ActivityLog.log_action(
            action=action,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            description=f"Error during {action}",
            category='error',
            ip_address=metadata.get('ip_address'),
            user_agent=metadata.get('user_agent'),
            request_method=metadata.get('request_method'),
            request_url=metadata.get('request_url'),
            status='failed',
            error_message=error_message
        )
    except Exception as e:
        print(f"Error logging error: {str(e)}")
        return None