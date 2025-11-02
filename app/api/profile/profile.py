from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.utils.utils import roles_required
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.exceptions import BadRequest
import re
from app.auth.helpers import validate_email, validate_date_of_birth, validate_phone
from app.extensions import db
from app.models.user import User
from app.api import api_bp as profile_bp

@profile_bp.route('/profile', methods=['GET'])
@login_required
@roles_required('parent', 'teacher')
def get_profile():
    """
    Get user profile data for authenticated parent or teacher
    
    Returns:
        JSON response with user profile data
    """
    try:
        user = User.query.get(current_user.id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Build profile data
        profile_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'phone': user.phone,
            'role': user.role,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'school': user.school,
            'bio': user.bio,
            'profile_picture': user.profile_picture,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'emergency_contact': user.emergency_contact,
            'emergency_phone': user.emergency_phone,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }
        
        # Add role-specific statistics
        if user.is_teacher():
            profile_data['statistics'] = {
                'total_trips': user.organized_trips.count() if user.organized_trips else 0,
                'total_students': user.get_total_students()
            }
        elif user.is_parent():
            profile_data['statistics'] = {
                'children_count': user.get_children_count(),
                'upcoming_trips': user.get_upcoming_trips_count()
            }
        
        return jsonify({
            'success': True,
            'data': profile_data
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Database error occurred: {str(e)}'
            # 'details': str(e) if request.args.get('debug') else None
        }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
            # 'details': str(e) if request.args.get('debug') else None
        }), 500


@profile_bp.route('/profile/update', methods=['PUT', 'PATCH'])
@login_required
@roles_required('parent', 'teacher')
def update_profile():
    """
    Update user profile data for authenticated parent or teacher
    
    Accepts JSON body with fields to update
    
    Returns:
        JSON response with updated profile data
    """
    try:
        # Get request data
        try:
            data = request.get_json()
        except BadRequest:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON data'
            }), 400
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Get user
        user = User.query.get(current_user.id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Track changes for response
        updated_fields = []
        validation_errors = []
        
        # Define allowed fields for update
        allowed_fields = {
            'first_name', 'last_name', 'phone', 'school', 
            'bio', 'date_of_birth', 'emergency_contact', 'emergency_phone'
        }
        
        # Email update (requires special validation)
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if not validate_email(new_email):
                validation_errors.append('Invalid email format')
            elif new_email != user.email:
                # Check if email already exists
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user:
                    validation_errors.append('Email already in use')
                else:
                    user.email = new_email
                    user.is_verified = False  # Require re-verification
                    updated_fields.append('email')
        
        # First name
        if 'first_name' in data:
            first_name = data['first_name'].strip()
            if not first_name or len(first_name) < 2:
                validation_errors.append('First name must be at least 2 characters')
            elif len(first_name) > 50:
                validation_errors.append('First name must not exceed 50 characters')
            else:
                user.first_name = first_name
                updated_fields.append('first_name')
        
        # Last name
        if 'last_name' in data:
            last_name = data['last_name'].strip()
            if not last_name or len(last_name) < 2:
                validation_errors.append('Last name must be at least 2 characters')
            elif len(last_name) > 50:
                validation_errors.append('Last name must not exceed 50 characters')
            else:
                user.last_name = last_name
                updated_fields.append('last_name')
        
        # Phone
        if 'phone' in data:
            phone = data['phone'].strip() if data['phone'] else None
            if phone and not validate_phone(phone):
                validation_errors.append('Invalid phone number format')
            elif phone and len(phone) > 20:
                validation_errors.append('Phone number must not exceed 20 characters')
            else:
                user.phone = phone
                updated_fields.append('phone')
        
        # School
        if 'school' in data:
            school = data['school'].strip() if data['school'] else None
            if school and len(school) > 100:
                validation_errors.append('School name must not exceed 100 characters')
            else:
                user.school = school
                updated_fields.append('school')
        
        # Bio
        if 'bio' in data:
            bio = data['bio'].strip() if data['bio'] else None
            if bio and len(bio) > 1000:
                validation_errors.append('Bio must not exceed 1000 characters')
            else:
                user.bio = bio
                updated_fields.append('bio')
        
        # Date of birth
        if 'date_of_birth' in data:
            if data['date_of_birth']:
                dob, error = validate_date_of_birth(data['date_of_birth'])
                if error:
                    validation_errors.append(error)
                else:
                    user.date_of_birth = dob
                    updated_fields.append('date_of_birth')
            else:
                user.date_of_birth = None
                updated_fields.append('date_of_birth')
        
        # Emergency contact
        if 'emergency_contact' in data:
            emergency_contact = data['emergency_contact'].strip() if data['emergency_contact'] else None
            if emergency_contact and len(emergency_contact) > 100:
                validation_errors.append('Emergency contact name must not exceed 100 characters')
            else:
                user.emergency_contact = emergency_contact
                updated_fields.append('emergency_contact')
        
        # Emergency phone
        if 'emergency_phone' in data:
            emergency_phone = data['emergency_phone'].strip() if data['emergency_phone'] else None
            if emergency_phone and not validate_phone(emergency_phone):
                validation_errors.append('Invalid emergency phone number format')
            elif emergency_phone and len(emergency_phone) > 20:
                validation_errors.append('Emergency phone must not exceed 20 characters')
            else:
                user.emergency_phone = emergency_phone
                updated_fields.append('emergency_phone')
        
        # Check for validation errors
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'validation_errors': validation_errors
            }), 400
        
        # Check if any valid fields were provided
        if not updated_fields:
            return jsonify({
                'success': False,
                'error': 'No valid fields provided for update'
            }), 400
        
        # Update timestamp
        user.updated_at = datetime.utcnow()
        
        # Commit changes
        db.session.commit()
        
        # Build updated profile data
        profile_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'phone': user.phone,
            'role': user.role,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'school': user.school,
            'bio': user.bio,
            'profile_picture': user.profile_picture,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'emergency_contact': user.emergency_contact,
            'emergency_phone': user.emergency_phone,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'updated_fields': updated_fields,
            'data': profile_data
        }), 200
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Data integrity error. Email may already exist.',
            'details': str(e) if request.args.get('debug') else None
        }), 409
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e) if request.args.get('debug') else None
        }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e) if request.args.get('debug') else None
        }), 500