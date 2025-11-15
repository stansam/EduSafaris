from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import or_, and_, func
from datetime import datetime, timedelta
import secrets
from werkzeug.security import generate_password_hash
from app.models import Trip
from app.extensions import db
from app.models import User, ActivityLog, Participant, TripRegistration, School, Vendor
from app.api.admin.users.email_service import send_password_reset_email, send_email_verification
from app.api.admin.users.helpers import log_admin_action, validate_user_data, get_user_statistics
from app.utils.utils import roles_required
from app.api import api_bp as admin_users_bp 


@admin_users_bp.route('/admin/user', methods=['GET'])
@login_required
@roles_required('admin')
def list_users():
    """
    Get paginated list of users with search and filter capabilities
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    - search: Search term (searches email, first_name, last_name)
    - role: Filter by role (parent, teacher, vendor, admin)
    - status: Filter by status (active, inactive)
    - verified: Filter by verification status (true, false)
    - school_id: Filter by school (for teachers)
    - sort_by: Sort field (created_at, last_login, email, name)
    - sort_order: Sort order (asc, desc)
    """
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Build query
        query = User.query
        
        # Search
        search_term = request.args.get('search', '').strip()
        if search_term:
            search_filter = or_(
                User.email.ilike(f'%{search_term}%'),
                User.first_name.ilike(f'%{search_term}%'),
                User.last_name.ilike(f'%{search_term}%'),
                func.concat(User.first_name, ' ', User.last_name).ilike(f'%{search_term}%')
            )
            query = query.filter(search_filter)
        
        # Filters
        role = request.args.get('role')
        if role and role in ['parent', 'teacher', 'vendor', 'admin']:
            query = query.filter(User.role == role)
        
        status = request.args.get('status')
        if status == 'active':
            query = query.filter(User.is_active == True)
        elif status == 'inactive':
            query = query.filter(User.is_active == False)
        
        verified = request.args.get('verified')
        if verified == 'true':
            query = query.filter(User.is_verified == True)
        elif verified == 'false':
            query = query.filter(User.is_verified == False)
        
        school_id = request.args.get('school_id', type=int)
        if school_id:
            query = query.filter(User.school_id == school_id)
        
        # Sorting
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if sort_by == 'name':
            sort_column = User.first_name
        elif sort_by == 'email':
            sort_column = User.email
        elif sort_by == 'last_login':
            sort_column = User.last_login
        else:
            sort_column = User.created_at
        
        if sort_order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Execute pagination
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialize users
        users_data = []
        for user in pagination.items:
            user_dict = user.serialize()
            user_dict['statistics'] = get_user_statistics(user)
            users_data.append(user_dict)
        
        # Log this action
        log_admin_action(
            action='users_list_viewed',
            target_user_id=current_user.id,
            description=f"Admin viewed users list (page {page}, filters: {request.args.to_dict()})"
        )
        
        return jsonify({
            'success': True,
            'data': {
                'users': users_data,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total_pages': pagination.pages,
                    'total_items': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                },
                'filters_applied': {
                    'search': search_term,
                    'role': role,
                    'status': status,
                    'verified': verified,
                    'school_id': school_id
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve users',
            'message': str(e),
            'code': 'USERS_FETCH_ERROR'
        }), 500


@admin_users_bp.route('/admin/user/<int:user_id>', methods=['GET'])
@login_required
@roles_required('admin')
def get_user_details(user_id):
    """
    Get detailed information about a specific user
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # Get comprehensive user data
        user_data = user.serialize(include_sensitive=True)
        user_data['statistics'] = get_user_statistics(user)
        
        # Add role-specific details
        if user.is_parent():
            children = [child.serialize() for child in user.children.filter_by(status='active').all()]
            user_data['children'] = children
            user_data['active_registrations'] = [
                reg.serialize() for reg in user.get_active_registrations()
            ]
        
        elif user.is_teacher():
            user_data['upcoming_trips'] = [
                trip.serialize() for trip in user.get_upcoming_trips()[:5]
            ]
        
        elif user.is_vendor() and user.vendor_profile:
            user_data['vendor_details'] = user.vendor_profile.serialize()
        
        # Log this action
        log_admin_action(
            action='user_details_viewed',
            target_user_id=user_id,
            description=f"Admin viewed details for user: {user.email}"
        )
        
        return jsonify({
            'success': True,
            'data': user_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve user details',
            'message': str(e),
            'code': 'USER_DETAILS_ERROR'
        }), 500


@admin_users_bp.route('/admin/user/<int:user_id>', methods=['PUT', 'PATCH'])
@login_required
@roles_required('admin')
def update_user(user_id):
    """
    Update user information
    
    Request Body:
    - first_name: User's first name
    - last_name: User's last name
    - email: User's email
    - phone: User's phone number
    - school_id: School ID (for teachers)
    - bio: User biography
    - address_line1, address_line2, city, state, postal_code, country: Address fields
    - department, specialization, years_of_experience: Teacher-specific fields
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # Prevent admins from modifying their own accounts through this endpoint
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'Cannot modify your own account through this endpoint',
                'code': 'SELF_MODIFICATION_DENIED'
            }), 403
        
        data = request.get_json()
        
        # Validate input
        validation_errors = validate_user_data(data, is_update=True)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'validation_errors': validation_errors,
                'code': 'VALIDATION_ERROR'
            }), 400
        
        # Check for email uniqueness if email is being changed
        if 'email' in data and data['email'] != user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({
                    'success': False,
                    'error': 'Email already in use',
                    'code': 'EMAIL_EXISTS'
                }), 409
        
        # Store old values for audit log
        old_values = {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'school_id': user.school_id
        }
        
        # Update fields
        updateable_fields = [
            'first_name', 'last_name', 'email', 'phone', 'bio',
            'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country', 'school_id', 'department',
            'specialization', 'years_of_experience', 'teacher_id'
        ]
        
        new_values = {}
        for field in updateable_fields:
            if field in data:
                setattr(user, field, data[field])
                new_values[field] = data[field]
        
        # If email changed, mark as unverified
        if 'email' in data and data['email'] != old_values['email']:
            user.is_verified = False
            new_values['is_verified'] = False
        
        db.session.commit()
        
        # Log this action
        log_admin_action(
            action='user_updated',
            target_user_id=user_id,
            description=f"Admin updated user: {user.email}",
            old_values=old_values,
            new_values=new_values
        )
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'data': user.serialize(include_sensitive=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update user',
            'message': str(e),
            'code': 'USER_UPDATE_ERROR'
        }), 500


@admin_users_bp.route('/admin/user/<int:user_id>/activate', methods=['POST'])
@login_required
@roles_required('admin')
def activate_user(user_id):
    """Activate a user account"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'Cannot modify your own account status',
                'code': 'SELF_MODIFICATION_DENIED'
            }), 403
        
        if user.is_active:
            return jsonify({
                'success': False,
                'error': 'User is already active',
                'code': 'ALREADY_ACTIVE'
            }), 400
        
        user.is_active = True
        db.session.commit()
        
        # Log this action
        log_admin_action(
            action='user_activated',
            target_user_id=user_id,
            description=f"Admin activated user: {user.email}",
            old_values={'is_active': False},
            new_values={'is_active': True}
        )
        
        return jsonify({
            'success': True,
            'message': 'User activated successfully',
            'data': user.serialize()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to activate user',
            'message': str(e),
            'code': 'USER_ACTIVATION_ERROR'
        }), 500


@admin_users_bp.route('/admin/user/<int:user_id>/deactivate', methods=['POST'])
@login_required
@roles_required('admin')
def deactivate_user(user_id):
    """
    Deactivate a user account
    
    Request Body (optional):
    - reason: Reason for deactivation
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'Cannot deactivate your own account',
                'code': 'SELF_MODIFICATION_DENIED'
            }), 403
        
        if not user.is_active:
            return jsonify({
                'success': False,
                'error': 'User is already inactive',
                'code': 'ALREADY_INACTIVE'
            }), 400
        
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')
        
        user.is_active = False
        db.session.commit()
        
        # Log this action
        log_admin_action(
            action='user_deactivated',
            target_user_id=user_id,
            description=f"Admin deactivated user: {user.email}. Reason: {reason}",
            old_values={'is_active': True},
            new_values={'is_active': False},
            metadata={'reason': reason}
        )
        
        return jsonify({
            'success': True,
            'message': 'User deactivated successfully',
            'data': user.serialize()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to deactivate user',
            'message': str(e),
            'code': 'USER_DEACTIVATION_ERROR'
        }), 500


@admin_users_bp.route('/admin/user/<int:user_id>/role', methods=['PUT'])
@login_required
@roles_required('admin')
def change_user_role(user_id):
    """
    Change user's role
    
    Request Body:
    - role: New role (parent, teacher, vendor, admin)
    - reason: Reason for role change (optional)
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'Cannot change your own role',
                'code': 'SELF_MODIFICATION_DENIED'
            }), 403
        
        data = request.get_json()
        
        if not data or 'role' not in data:
            return jsonify({
                'success': False,
                'error': 'Role is required',
                'code': 'ROLE_REQUIRED'
            }), 400
        
        new_role = data['role']
        
        if new_role not in ['parent', 'teacher', 'vendor', 'admin']:
            return jsonify({
                'success': False,
                'error': 'Invalid role',
                'code': 'INVALID_ROLE'
            }), 400
        
        if user.role == new_role:
            return jsonify({
                'success': False,
                'error': f'User already has role: {new_role}',
                'code': 'SAME_ROLE'
            }), 400
        
        old_role = user.role
        reason = data.get('reason', 'No reason provided')
        
        # Role-specific validations
        if new_role == 'vendor':
            # Check if user has vendor profile
            if not user.vendor_profile:
                return jsonify({
                    'success': False,
                    'error': 'User must have a vendor profile to be assigned vendor role',
                    'code': 'VENDOR_PROFILE_REQUIRED'
                }), 400
        
        user.role = new_role
        db.session.commit()
        
        # Log this action
        log_admin_action(
            action='user_role_changed',
            target_user_id=user_id,
            description=f"Admin changed user role from {old_role} to {new_role}. Reason: {reason}",
            old_values={'role': old_role},
            new_values={'role': new_role},
            metadata={'reason': reason}
        )
        
        return jsonify({
            'success': True,
            'message': f'User role changed from {old_role} to {new_role}',
            'data': user.serialize()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to change user role',
            'message': str(e),
            'code': 'ROLE_CHANGE_ERROR'
        }), 500


@admin_users_bp.route('/admin/user/<int:user_id>/reset-password', methods=['POST'])
@login_required
@roles_required('admin')
def reset_user_password(user_id):
    """
    Reset user's password and send reset email
    
    Request Body (optional):
    - send_email: Boolean to send password reset email (default: true)
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        data = request.get_json() or {}
        send_email_notification = data.get('send_email', True)
        
        # Generate password reset token
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expires = datetime.now() + timedelta(hours=24)
        
        db.session.commit()
        
        # Send password reset email
        email_sent = False
        if send_email_notification:
            try:
                send_password_reset_email(user.email, token)
                email_sent = True
            except Exception as email_error:
                print(f"Failed to send password reset email: {str(email_error)}")
        
        # Log this action
        log_admin_action(
            action='password_reset_initiated',
            target_user_id=user_id,
            description=f"Admin initiated password reset for user: {user.email}",
            new_values={'email_sent': email_sent}
        )
        
        return jsonify({
            'success': True,
            'message': 'Password reset initiated',
            'data': {
                'email_sent': email_sent,
                'reset_token': token if not email_sent else None,
                'expires_at': user.password_reset_expires.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to reset password',
            'message': str(e),
            'code': 'PASSWORD_RESET_ERROR'
        }), 500


@admin_users_bp.route('/admin/user/<int:user_id>/verify-email', methods=['POST'])
@login_required
@roles_required('admin')
def verify_user_email(user_id):
    """
    Manually verify user's email or send verification email
    
    Request Body (optional):
    - force_verify: Boolean to manually verify without email (default: false)
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        data = request.get_json() or {}
        force_verify = data.get('force_verify', False)
        
        if force_verify:
            # Manually verify email
            if user.is_verified:
                return jsonify({
                    'success': False,
                    'error': 'Email already verified',
                    'code': 'ALREADY_VERIFIED'
                }), 400
            
            user.is_verified = True
            user.email_verification_token = None
            db.session.commit()
            
            # Log this action
            log_admin_action(
                action='email_manually_verified',
                target_user_id=user_id,
                description=f"Admin manually verified email for user: {user.email}",
                new_values={'is_verified': True}
            )
            
            return jsonify({
                'success': True,
                'message': 'Email verified successfully',
                'data': user.serialize()
            }), 200
        
        else:
            # Send verification email
            if user.is_verified:
                return jsonify({
                    'success': False,
                    'error': 'Email already verified',
                    'code': 'ALREADY_VERIFIED'
                }), 400
            
            # Generate verification token
            token = secrets.token_urlsafe(32)
            user.email_verification_token = token
            user.email_verification_sent_at = datetime.now()
            
            db.session.commit()
            
            # Send verification email
            email_sent = False
            try:
                send_email_verification(user.email, token)
                email_sent = True
            except Exception as email_error:
                print(f"Failed to send verification email: {str(email_error)}")
            
            # Log this action
            log_admin_action(
                action='verification_email_sent',
                target_user_id=user_id,
                description=f"Admin sent verification email to user: {user.email}",
                new_values={'email_sent': email_sent}
            )
            
            return jsonify({
                'success': True,
                'message': 'Verification email sent' if email_sent else 'Verification token generated',
                'data': {
                    'email_sent': email_sent,
                    'verification_token': token if not email_sent else None
                }
            }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to verify email',
            'message': str(e),
            'code': 'EMAIL_VERIFICATION_ERROR'
        }), 500

@admin_users_bp.route('/admin/user/<int:user_id>/activity', methods=['GET'])
@login_required
@roles_required('admin')
def get_user_activity(user_id):
    """
    Get activity log for a specific user
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 200)
    - action: Filter by action type
    - category: Filter by action category
    - status: Filter by status (success, failed, warning)
    - date_from: Filter activities from this date (ISO format)
    - date_to: Filter activities until this date (ISO format)
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)
        
        # Build query
        query = ActivityLog.query.filter_by(user_id=user_id)
        
        # Filters
        action = request.args.get('action')
        if action:
            query = query.filter(ActivityLog.action == action)
        
        category = request.args.get('category')
        if category:
            query = query.filter(ActivityLog.action_category == category)
        
        status = request.args.get('status')
        if status:
            query = query.filter(ActivityLog.status == status)
        
        # Date filters
        date_from = request.args.get('date_from')
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from)
                query = query.filter(ActivityLog.created_at >= date_from_obj)
            except ValueError:
                pass
        
        date_to = request.args.get('date_to')
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to)
                query = query.filter(ActivityLog.created_at <= date_to_obj)
            except ValueError:
                pass
        
        # Order by most recent
        query = query.order_by(ActivityLog.created_at.desc())
        
        # Execute pagination
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialize activity logs
        activities = [activity.serialize() for activity in pagination.items]
        
        # Get activity summary
        activity_summary = {
            'total_actions': ActivityLog.query.filter_by(user_id=user_id).count(),
            'failed_actions': ActivityLog.query.filter_by(user_id=user_id, status='failed').count(),
            'last_30_days': ActivityLog.query.filter(
                ActivityLog.user_id == user_id,
                ActivityLog.created_at >= datetime.now() - timedelta(days=30)
            ).count()
        }
        
        # Log this action
        log_admin_action(
            action='user_activity_viewed',
            target_user_id=user_id,
            description=f"Admin viewed activity log for user: {user.email}"
        )
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name
                },
                'activities': activities,
                'summary': activity_summary,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total_pages': pagination.pages,
                    'total_items': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve user activity',
            'message': str(e),
            'code': 'ACTIVITY_FETCH_ERROR'
        }), 500


@admin_users_bp.route('/admin/user/<int:user_id>/delete', methods=['DELETE'])
@login_required
@roles_required('admin')
def delete_user(user_id):
    """
    Delete a user account (soft delete by deactivating)
    Use with extreme caution - consider data retention policies
    
    Request Body:
    - confirm: Must be true
    - reason: Reason for deletion (required)
    - hard_delete: Boolean for permanent deletion (default: false)
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'Cannot delete your own account',
                'code': 'SELF_DELETION_DENIED'
            }), 403
        
        data = request.get_json()
        
        if not data or not data.get('confirm'):
            return jsonify({
                'success': False,
                'error': 'Deletion must be confirmed',
                'code': 'CONFIRMATION_REQUIRED'
            }), 400
        
        if not data.get('reason'):
            return jsonify({
                'success': False,
                'error': 'Reason for deletion is required',
                'code': 'REASON_REQUIRED'
            }), 400
        
        reason = data['reason']
        hard_delete = data.get('hard_delete', False)
        
        # Check for active dependencies
        warnings = []
        
        if user.is_teacher():
            active_trips = user.organized_trips.filter(
                Trip.status.in_(['published', 'registration_open', 'in_progress'])
            ).count()
            if active_trips > 0:
                warnings.append(f'User has {active_trips} active trips')
        
        if user.is_parent():
            active_registrations = len(user.get_active_registrations())
            if active_registrations > 0:
                warnings.append(f'User has {active_registrations} active trip registrations')
            
            if user.get_outstanding_balance() > 0:
                warnings.append(f'User has outstanding balance of {user.get_outstanding_balance()}')
        
        if warnings and not data.get('force', False):
            return jsonify({
                'success': False,
                'error': 'User has active dependencies',
                'warnings': warnings,
                'code': 'ACTIVE_DEPENDENCIES',
                'message': 'Set force=true to proceed anyway'
            }), 400
        
        if hard_delete:
            # Permanent deletion - use with extreme caution
            # Log before deletion
            log_admin_action(
                action='user_permanently_deleted',
                target_user_id=user_id,
                description=f"Admin permanently deleted user: {user.email}. Reason: {reason}",
                old_values={'email': user.email, 'role': user.role},
                metadata={'reason': reason, 'warnings': warnings},
                status='warning'
            )
            
            db.session.delete(user)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'User permanently deleted',
                'warnings': warnings
            }), 200
        else:
            # Soft delete (deactivate)
            user.is_active = False
            db.session.commit()
            
            # Log this action
            log_admin_action(
                action='user_soft_deleted',
                target_user_id=user_id,
                description=f"Admin soft deleted (deactivated) user: {user.email}. Reason: {reason}",
                old_values={'is_active': True},
                new_values={'is_active': False},
                metadata={'reason': reason, 'warnings': warnings}
            )
            
            return jsonify({
                'success': True,
                'message': 'User deactivated (soft delete)',
                'data': user.serialize(),
                'warnings': warnings
            }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete user',
            'message': str(e),
            'code': 'USER_DELETE_ERROR'
        }), 500


@admin_users_bp.route('/admin/user/statistics', methods=['GET'])
@login_required
@roles_required('admin')
def get_users_statistics():
    """
    Get overall user statistics for the platform
    """
    try:
        # Basic counts
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        verified_users = User.query.filter_by(is_verified=True).count()
        
        # Role breakdown
        role_stats = {
            'parents': User.query.filter_by(role='parent').count(),
            'teachers': User.query.filter_by(role='teacher').count(),
            'vendors': User.query.filter_by(role='vendor').count(),
            'admins': User.query.filter_by(role='admin').count()
        }
        
        # Recent activity
        last_24h = User.query.filter(
            User.created_at >= datetime.now() - timedelta(days=1)
        ).count()
        
        last_7d = User.query.filter(
            User.created_at >= datetime.now() - timedelta(days=7)
        ).count()
        
        last_30d = User.query.filter(
            User.created_at >= datetime.now() - timedelta(days=30)
        ).count()
        
        # Login activity
        recent_logins = ActivityLog.query.filter(
            ActivityLog.action == 'login',
            ActivityLog.created_at >= datetime.now() - timedelta(days=7)
        ).count()
        
        # Get top active users
        top_active_users = db.session.query(
            ActivityLog.user_id,
            func.count(ActivityLog.id).label('action_count')
        ).filter(
            ActivityLog.created_at >= datetime.now() - timedelta(days=30)
        ).group_by(ActivityLog.user_id)\
         .order_by(func.count(ActivityLog.id).desc())\
         .limit(10).all()
        
        top_users = []
        for user_id, count in top_active_users:
            user = User.query.get(user_id)
            if user:
                top_users.append({
                    'user': user.serialize(),
                    'action_count': count
                })
        
        return jsonify({
            'success': True,
            'data': {
                'overview': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'inactive_users': total_users - active_users,
                    'verified_users': verified_users,
                    'unverified_users': total_users - verified_users,
                    'verification_rate': round((verified_users / total_users * 100), 2) if total_users > 0 else 0
                },
                'by_role': role_stats,
                'new_users': {
                    'last_24_hours': last_24h,
                    'last_7_days': last_7d,
                    'last_30_days': last_30d
                },
                'activity': {
                    'logins_last_7_days': recent_logins
                },
                'top_active_users': top_users
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve statistics',
            'message': str(e),
            'code': 'STATISTICS_ERROR'
        }), 500


@admin_users_bp.route('/admin/user/bulk-action', methods=['POST'])
@login_required
@roles_required('admin')
def bulk_user_action():
    """
    Perform bulk actions on multiple users
    
    Request Body:
    - user_ids: Array of user IDs
    - action: Action to perform (activate, deactivate, verify_email, send_reset)
    - reason: Reason for bulk action (optional)
    """
    try:
        data = request.get_json()
        
        if not data or 'user_ids' not in data or 'action' not in data:
            return jsonify({
                'success': False,
                'error': 'user_ids and action are required',
                'code': 'MISSING_PARAMETERS'
            }), 400
        
        user_ids = data['user_ids']
        action = data['action']
        reason = data.get('reason', 'Bulk action')
        
        if not isinstance(user_ids, list) or len(user_ids) == 0:
            return jsonify({
                'success': False,
                'error': 'user_ids must be a non-empty array',
                'code': 'INVALID_USER_IDS'
            }), 400
        
        if action not in ['activate', 'deactivate', 'verify_email', 'send_reset']:
            return jsonify({
                'success': False,
                'error': 'Invalid action',
                'code': 'INVALID_ACTION'
            }), 400
        
        # Prevent self-modification
        if current_user.id in user_ids:
            return jsonify({
                'success': False,
                'error': 'Cannot perform bulk actions on your own account',
                'code': 'SELF_MODIFICATION_DENIED'
            }), 403
        
        # Limit bulk action size
        if len(user_ids) > 100:
            return jsonify({
                'success': False,
                'error': 'Cannot perform bulk action on more than 100 users at once',
                'code': 'BULK_LIMIT_EXCEEDED'
            }), 400
        
        # Get users
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        if not users:
            return jsonify({
                'success': False,
                'error': 'No valid users found',
                'code': 'NO_USERS_FOUND'
            }), 404
        
        results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        
        for user in users:
            try:
                if action == 'activate':
                    if user.is_active:
                        results['skipped'].append({
                            'user_id': user.id,
                            'email': user.email,
                            'reason': 'Already active'
                        })
                    else:
                        user.is_active = True
                        results['success'].append({
                            'user_id': user.id,
                            'email': user.email
                        })
                
                elif action == 'deactivate':
                    if not user.is_active:
                        results['skipped'].append({
                            'user_id': user.id,
                            'email': user.email,
                            'reason': 'Already inactive'
                        })
                    else:
                        user.is_active = False
                        results['success'].append({
                            'user_id': user.id,
                            'email': user.email
                        })
                
                elif action == 'verify_email':
                    if user.is_verified:
                        results['skipped'].append({
                            'user_id': user.id,
                            'email': user.email,
                            'reason': 'Already verified'
                        })
                    else:
                        user.is_verified = True
                        user.email_verification_token = None
                        results['success'].append({
                            'user_id': user.id,
                            'email': user.email
                        })
                
                elif action == 'send_reset':
                    token = secrets.token_urlsafe(32)
                    user.password_reset_token = token
                    user.password_reset_expires = datetime.now() + timedelta(hours=24)
                    
                    try:
                        send_password_reset_email(user.email, token)
                        results['success'].append({
                            'user_id': user.id,
                            'email': user.email
                        })
                    except Exception as e:
                        results['failed'].append({
                            'user_id': user.id,
                            'email': user.email,
                            'reason': f'Email send failed: {str(e)}'
                        })
            
            except Exception as e:
                results['failed'].append({
                    'user_id': user.id,
                    'email': user.email,
                    'reason': str(e)
                })
        
        # Commit all changes
        db.session.commit()
        
        # Log bulk action
        log_admin_action(
            action=f'bulk_{action}',
            target_user_id=current_user.id,
            description=f"Admin performed bulk {action} on {len(results['success'])} users. Reason: {reason}",
            new_values={
                'success_count': len(results['success']),
                'failed_count': len(results['failed']),
                'skipped_count': len(results['skipped']),
                'user_ids': user_ids
            },
            metadata={'reason': reason}
        )
        
        return jsonify({
            'success': True,
            'message': f'Bulk action completed: {len(results["success"])} succeeded, {len(results["failed"])} failed, {len(results["skipped"])} skipped',
            'data': results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to perform bulk action',
            'message': str(e),
            'code': 'BULK_ACTION_ERROR'
        }), 500


@admin_users_bp.route('/admin/user/export', methods=['GET'])
@login_required
@roles_required('admin')
def export_users():
    """
    Export user data to CSV
    
    Query Parameters:
    - role: Filter by role
    - status: Filter by status (active, inactive)
    - verified: Filter by verification status
    """
    try:
        import csv
        from io import StringIO
        
        # Build query with filters
        query = User.query
        
        role = request.args.get('role')
        if role:
            query = query.filter(User.role == role)
        
        status = request.args.get('status')
        if status == 'active':
            query = query.filter(User.is_active == True)
        elif status == 'inactive':
            query = query.filter(User.is_active == False)
        
        verified = request.args.get('verified')
        if verified == 'true':
            query = query.filter(User.is_verified == True)
        elif verified == 'false':
            query = query.filter(User.is_verified == False)
        
        users = query.all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'ID', 'Email', 'First Name', 'Last Name', 'Role',
            'Phone', 'City', 'Country', 'Is Active', 'Is Verified',
            'Created At', 'Last Login'
        ])
        
        # Write data
        for user in users:
            writer.writerow([
                user.id,
                user.email,
                user.first_name,
                user.last_name,
                user.role,
                user.phone or '',
                user.city or '',
                user.country or '',
                'Yes' if user.is_active else 'No',
                'Yes' if user.is_verified else 'No',
                user.created_at.isoformat() if user.created_at else '',
                user.last_login.isoformat() if user.last_login else ''
            ])
        
        # Log export
        log_admin_action(
            action='users_exported',
            target_user_id=current_user.id,
            description=f"Admin exported {len(users)} users to CSV",
            new_values={'count': len(users)}
        )
        
        # Prepare response
        output.seek(0)
        response = jsonify({
            'success': True,
            'data': {
                'csv_content': output.getvalue(),
                'filename': f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                'total_records': len(users)
            }
        })
        
        return response, 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to export users',
            'message': str(e),
            'code': 'EXPORT_ERROR'
        }), 500

