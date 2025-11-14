from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.exceptions import BadRequest
from decimal import Decimal
from app.extensions import db
from app.models import ActivityLog
from app.api import api_bp as vendor_profile_bp 
from app.api.vendor.profile_validator import VendorProfileValidator
from app.utils.utils import roles_required


@vendor_profile_bp.route('/vendor/profile', methods=['GET'])
@login_required
@roles_required('vendor')
def get_vendor_profile_data():
    """
    Get vendor profile information
    
    Returns:
        200: Vendor profile data
        404: Profile not found
        500: Server error
    """
    try:
        vendor = current_user.vendor_profile
        
        # Get additional statistics
        total_bookings = vendor.service_bookings.count()
        active_bookings = vendor.service_bookings.filter_by(status='confirmed').count()
        
        profile_data = vendor.serialize()
        profile_data.update({
            'user_info': {
                'email': current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'full_name': current_user.full_name,
                'phone': current_user.phone,
                'profile_picture': current_user.profile_picture
            },
            'statistics': {
                'total_bookings': total_bookings,
                'active_bookings': active_bookings,
                'average_rating': vendor.average_rating,
                'total_reviews': vendor.total_reviews
            }
        })
        
        return jsonify({
            'success': True,
            'data': profile_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching vendor profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': 'An error occurred while fetching profile'
        }), 500


@vendor_profile_bp.route('/vendor/profile', methods=['PUT'])
@login_required
@roles_required('vendor')
def update_vendor_profile():
    """
    Update vendor profile information
    
    Request Body:
        {
            "business_name": str (optional),
            "business_type": str (optional),
            "description": str (optional),
            "contact_email": str (optional),
            "contact_phone": str (optional),
            "website": str (optional),
            "address_line1": str (optional),
            "address_line2": str (optional),
            "city": str (optional),
            "state": str (optional),
            "postal_code": str (optional),
            "country": str (optional),
            "capacity": int (optional),
            "specializations": list (optional),
            "base_price": float (optional),
            "price_per_person": float (optional),
            "pricing_notes": str (optional),
            "license_number": str (optional),
            "insurance_details": str (optional)
        }
    
    Returns:
        200: Profile updated successfully
        400: Validation error
        404: Profile not found
        500: Server error
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Bad request',
                'message': 'No data provided'
            }), 400
        
        vendor = current_user.vendor_profile
        validator = VendorProfileValidator()
        
        # Store old values for activity log
        old_values = {
            'business_name': vendor.business_name,
            'business_type': vendor.business_type,
            'contact_email': vendor.contact_email,
            'contact_phone': vendor.contact_phone
        }
        
        # Validate and update fields
        errors = {}
        
        # Business name
        if 'business_name' in data:
            is_valid, error_msg = validator.validate_business_name(data['business_name'])
            if not is_valid:
                errors['business_name'] = error_msg
            else:
                vendor.business_name = data['business_name'].strip()
        
        # Business type
        if 'business_type' in data:
            is_valid, error_msg = validator.validate_business_type(data['business_type'])
            if not is_valid:
                errors['business_type'] = error_msg
            else:
                vendor.business_type = data['business_type']
        
        # Contact email
        if 'contact_email' in data:
            is_valid, error_msg = validator.validate_email(data['contact_email'])
            if not is_valid:
                errors['contact_email'] = error_msg
            else:
                vendor.contact_email = data['contact_email'].strip().lower()
        
        # Contact phone
        if 'contact_phone' in data:
            is_valid, error_msg = validator.validate_phone(data['contact_phone'])
            if not is_valid:
                errors['contact_phone'] = error_msg
            else:
                vendor.contact_phone = data['contact_phone'].strip()
        
        # Website
        if 'website' in data:
            is_valid, error_msg = validator.validate_url(data['website'])
            if not is_valid:
                errors['website'] = error_msg
            else:
                vendor.website = data['website'].strip() if data['website'] else None
        
        # Base price
        if 'base_price' in data:
            is_valid, error_msg = validator.validate_price(data['base_price'], "Base price")
            if not is_valid:
                errors['base_price'] = error_msg
            else:
                vendor.base_price = Decimal(str(data['base_price'])) if data['base_price'] else None
        
        # Price per person
        if 'price_per_person' in data:
            is_valid, error_msg = validator.validate_price(data['price_per_person'], "Price per person")
            if not is_valid:
                errors['price_per_person'] = error_msg
            else:
                vendor.price_per_person = Decimal(str(data['price_per_person'])) if data['price_per_person'] else None
        
        # Capacity
        if 'capacity' in data:
            is_valid, error_msg = validator.validate_capacity(data['capacity'])
            if not is_valid:
                errors['capacity'] = error_msg
            else:
                vendor.capacity = int(data['capacity']) if data['capacity'] else None
        
        # Specializations
        if 'specializations' in data:
            if isinstance(data['specializations'], list):
                vendor.specializations = data['specializations']
            else:
                errors['specializations'] = "Specializations must be a list"
        
        # Text fields (no special validation needed)
        text_fields = [
            'description', 'address_line1', 'address_line2', 
            'city', 'state', 'postal_code', 'country',
            'pricing_notes', 'license_number', 'insurance_details'
        ]
        
        for field in text_fields:
            if field in data:
                value = data[field].strip() if isinstance(data[field], str) else data[field]
                setattr(vendor, field, value if value else None)
        
        # Return validation errors if any
        if errors:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'errors': errors
            }), 400
        
        # Save changes
        db.session.commit()
        
        # Log the activity
        new_values = {
            'business_name': vendor.business_name,
            'business_type': vendor.business_type,
            'contact_email': vendor.contact_email,
            'contact_phone': vendor.contact_phone
        }
        
        try:
            ActivityLog.log_action(
                action='vendor_profile_updated',
                user_id=current_user.id,
                entity_type='vendor',
                entity_id=vendor.id,
                description=f"Vendor profile updated for {vendor.business_name}",
                category='vendor',
                old_values=old_values,
                new_values=new_values,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                request_method=request.method,
                request_url=request.url
            )
        except Exception as log_error:
            # Log error but don't fail the request
            current_app.logger.error(f"Failed to log activity: {str(log_error)}")
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'data': vendor.serialize()
        }), 200
        
    except BadRequest as e:
        return jsonify({
            'success': False,
            'error': 'Bad request',
            'message': 'Invalid JSON data'
        }), 400
        
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"Database integrity error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'A constraint violation occurred. Please check your data.'
        }), 400
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error updating vendor profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'An error occurred while updating profile'
        }), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error updating vendor profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': 'An unexpected error occurred'
        }), 500


@vendor_profile_bp.route('/vendor/profile/user', methods=['PUT'])
@login_required
@roles_required('vendor')
def update_user_profile():
    """
    Update vendor user information (name, phone, etc.)
    
    Request Body:
        {
            "first_name": str (optional),
            "last_name": str (optional),
            "phone": str (optional),
            "bio": str (optional),
            "language_preference": str (optional),
            "timezone": str (optional)
        }
    
    Returns:
        200: User profile updated successfully
        400: Validation error
        500: Server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Bad request',
                'message': 'No data provided'
            }), 400
        
        user = current_user
        validator = VendorProfileValidator()
        errors = {}
        
        # Store old values
        old_values = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone
        }
        
        # First name
        if 'first_name' in data:
            first_name = data['first_name'].strip() if data['first_name'] else None
            if not first_name:
                errors['first_name'] = "First name is required"
            elif len(first_name) < 2:
                errors['first_name'] = "First name must be at least 2 characters"
            elif len(first_name) > 50:
                errors['first_name'] = "First name must be less than 50 characters"
            else:
                user.first_name = first_name
        
        # Last name
        if 'last_name' in data:
            last_name = data['last_name'].strip() if data['last_name'] else None
            if not last_name:
                errors['last_name'] = "Last name is required"
            elif len(last_name) < 2:
                errors['last_name'] = "Last name must be at least 2 characters"
            elif len(last_name) > 50:
                errors['last_name'] = "Last name must be less than 50 characters"
            else:
                user.last_name = last_name
        
        # Phone
        if 'phone' in data and data['phone']:
            is_valid, error_msg = validator.validate_phone(data['phone'])
            if not is_valid:
                errors['phone'] = error_msg
            else:
                user.phone = data['phone'].strip()
        
        # Bio
        if 'bio' in data:
            bio = data['bio'].strip() if data['bio'] else None
            if bio and len(bio) > 1000:
                errors['bio'] = "Bio must be less than 1000 characters"
            else:
                user.bio = bio
        
        # Language preference
        if 'language_preference' in data:
            valid_languages = ['en', 'es', 'fr', 'de', 'sw']  # Add your supported languages
            if data['language_preference'] not in valid_languages:
                errors['language_preference'] = f"Invalid language. Supported: {', '.join(valid_languages)}"
            else:
                user.language_preference = data['language_preference']
        
        # Timezone
        if 'timezone' in data:
            user.timezone = data['timezone']
        
        # Return validation errors if any
        if errors:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'errors': errors
            }), 400
        
        # Save changes
        db.session.commit()
        
        # Log the activity
        new_values = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone
        }
        
        try:
            ActivityLog.log_action(
                action='user_profile_updated',
                user_id=user.id,
                entity_type='user',
                entity_id=user.id,
                description=f"User profile updated for {user.full_name}",
                category='user',
                old_values=old_values,
                new_values=new_values,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                request_method=request.method,
                request_url=request.url
            )
        except Exception as log_error:
            current_app.logger.error(f"Failed to log activity: {str(log_error)}")
        
        return jsonify({
            'success': True,
            'message': 'User profile updated successfully',
            'data': user.serialize()
        }), 200
        
    except BadRequest:
        return jsonify({
            'success': False,
            'error': 'Bad request',
            'message': 'Invalid JSON data'
        }), 400
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error updating user profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'An error occurred while updating profile'
        }), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error updating user profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': 'An unexpected error occurred'
        }), 500





