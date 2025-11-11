from app.api import api_bp as auth_bp
from flask import request, jsonify, url_for, current_app
from app.auth.helpers import (
    validate_email, validate_password, validate_phone, validate_url,
    validate_required_fields, validate_number, validate_integer,
    sanitize_string, build_error_response, build_success_response
)
from app.extensions import db
from flask_login import login_user
from app.models import User, Vendor
from app.auth.activity_log import (
    log_registration, log_vendor_profile_creation, log_error
)


@auth_bp.route('/auth/register/vendor', methods=['POST'])
def api_register_vendor():
    """
    API endpoint for vendor registration
    
    Expected JSON payload:
    {
        "email": "vendor@example.com",
        "password": "SecurePass123",
        "confirm_password": "SecurePass123",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
        "business_name": "Adventure Tours Ltd",
        "business_type": "transportation",
        "description": "Premium travel services...",
        "contact_email": "business@example.com",
        "contact_phone": "+1234567891",
        "website": "https://example.com",  # Optional
        "address_line1": "123 Main St",  # Optional
        "address_line2": "Suite 100",  # Optional
        "city": "New York",
        "state": "NY",  # Optional
        "postal_code": "10001",  # Optional
        "country": "USA",
        "license_number": "LIC123",  # Optional
        "insurance_details": "Insurance info...",  # Optional
        "capacity": 50,  # Optional
        "specializations": ["school trips", "sports events"],  # Optional
        "base_price": 100.00,  # Optional
        "price_per_person": 25.00,  # Optional
        "pricing_notes": "Pricing details..."  # Optional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify(build_error_response('No data provided')[0]), 400
        
        # Validate required user fields
        required_user_fields = ['email', 'password', 'confirm_password', 
                               'first_name', 'last_name', 'phone']
        is_valid_user, missing_user_fields = validate_required_fields(data, required_user_fields)
        
        # Validate required vendor fields
        required_vendor_fields = ['business_name', 'business_type', 'contact_email', 
                                 'contact_phone', 'city', 'country']
        is_valid_vendor, missing_vendor_fields = validate_required_fields(data, required_vendor_fields)
        
        missing_fields = missing_user_fields + missing_vendor_fields
        if missing_fields:
            return jsonify(build_error_response(
                f'Missing required fields: {", ".join(missing_fields)}'
            )[0]), 400
        
        # Sanitize inputs
        email = sanitize_string(data['email']).lower()
        first_name = sanitize_string(data['first_name'])
        last_name = sanitize_string(data['last_name'])
        phone = sanitize_string(data['phone'])
        business_name = sanitize_string(data['business_name'])
        contact_email = sanitize_string(data['contact_email']).lower()
        contact_phone = sanitize_string(data['contact_phone'])
        
        # Validate email formats
        if not validate_email(email):
            return jsonify(build_error_response('Invalid user email format')[0]), 400
        
        if not validate_email(contact_email):
            return jsonify(build_error_response('Invalid business email format')[0]), 400
        
        # Check if user email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify(build_error_response('Email already registered')[0]), 400
        
        # Validate password
        password = data['password']
        if not validate_password(password):
            return jsonify(build_error_response(
                'Password must be at least 8 characters with uppercase, lowercase, and number'
            )[0]), 400
        
        # Check password confirmation
        if password != data['confirm_password']:
            return jsonify(build_error_response('Passwords do not match')[0]), 400
        
        # Validate phone numbers
        if not validate_phone(phone):
            return jsonify(build_error_response('Invalid phone number format')[0]), 400
        
        if not validate_phone(contact_phone):
            return jsonify(build_error_response('Invalid business phone number format')[0]), 400
        
        # Validate business type
        valid_business_types = ['transportation', 'accommodation', 'activities', 
                               'catering', 'equipment', 'other']
        business_type = sanitize_string(data['business_type']).lower()
        if business_type not in valid_business_types:
            return jsonify(build_error_response(
                f'Invalid business type. Must be one of: {", ".join(valid_business_types)}'
            )[0]), 400
        
        # Validate description
        description = sanitize_string(data.get('description', ''))
        if len(description) < 20:
            return jsonify(build_error_response(
                'Business description must be at least 20 characters'
            )[0]), 400
        
        # Validate website if provided
        website = sanitize_string(data.get('website', ''))
        if website and not validate_url(website):
            return jsonify(build_error_response('Invalid website URL format')[0]), 400
        
        # Validate capacity if provided
        capacity = None
        if data.get('capacity'):
            is_valid_capacity, capacity_error, capacity = validate_integer(
                data['capacity'], min_value=1, max_value=10000
            )
            if not is_valid_capacity:
                return jsonify(build_error_response(
                    capacity_error or 'Invalid capacity value'
                )[0]), 400
        
        # Validate pricing if provided
        base_price = None
        if data.get('base_price'):
            is_valid_price, price_error, base_price = validate_number(
                data['base_price'], min_value=0
            )
            if not is_valid_price:
                return jsonify(build_error_response(
                    price_error or 'Invalid base price value'
                )[0]), 400
        
        price_per_person = None
        if data.get('price_per_person'):
            is_valid_ppp, ppp_error, price_per_person = validate_number(
                data['price_per_person'], min_value=0
            )
            if not is_valid_ppp:
                return jsonify(build_error_response(
                    ppp_error or 'Invalid price per person value'
                )[0]), 400
        
        # Parse specializations
        specializations = []
        if data.get('specializations'):
            if isinstance(data['specializations'], list):
                specializations = [s.strip() for s in data['specializations'] if s.strip()]
            elif isinstance(data['specializations'], str):
                specializations = [s.strip() for s in data['specializations'].split(',') if s.strip()]
        
        # Create new vendor user
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='vendor',
            is_active=True,
            is_verified=False
        )
        new_user.password = password
        
        db.session.add(new_user)
        db.session.flush()  # Get the user ID
        
        # Create vendor profile
        vendor_profile = Vendor(
            user_id=new_user.id,
            business_name=business_name,
            business_type=business_type,
            description=description,
            contact_email=contact_email,
            contact_phone=contact_phone,
            website=website if website else None,
            address_line1=sanitize_string(data.get('address_line1', '')),
            address_line2=sanitize_string(data.get('address_line2', '')),
            city=sanitize_string(data['city']),
            state=sanitize_string(data.get('state', '')),
            postal_code=sanitize_string(data.get('postal_code', '')),
            country=sanitize_string(data['country']),
            license_number=sanitize_string(data.get('license_number', '')),
            insurance_details=sanitize_string(data.get('insurance_details', '')),
            capacity=capacity,
            specializations=specializations if specializations else None,
            base_price=base_price,
            price_per_person=price_per_person,
            pricing_notes=sanitize_string(data.get('pricing_notes', '')),
            is_verified=False,
            is_active=True
        )
        
        db.session.add(vendor_profile)
        db.session.commit()
        
        # Log the registration
        try:
            additional_data = {
                'business_name': business_name,
                'business_type': business_type,
                'city': vendor_profile.city,
                'country': vendor_profile.country,
                'has_website': bool(website),
                'has_specializations': bool(specializations)
            }
            log_registration(new_user, 'vendor', additional_data=additional_data)
        except Exception as log_error_ex:
            current_app.logger.error(f'Activity log error (user): {str(log_error_ex)}')
        
        # Log vendor profile creation
        try:
            log_vendor_profile_creation(vendor_profile, new_user)
        except Exception as log_error_ex:
            current_app.logger.error(f'Activity log error (vendor): {str(log_error_ex)}')
        
        # Log the user in
        login_user(new_user)
        
        # Build success response
        response_data = {
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'full_name': new_user.full_name,
                'role': new_user.role
            },
            'vendor': {
                'id': vendor_profile.id,
                'business_name': vendor_profile.business_name,
                'business_type': vendor_profile.business_type
            }
        }
        
        return jsonify(build_success_response(
            'Vendor account created successfully',
            data=response_data,
            redirect_url=url_for('vendor.dashboard'),
            status_code=201
        )[0]), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Vendor registration error: {str(e)}')
        
        # Log the error
        try:
            log_error('vendor_registration', str(e))
        except Exception:
            pass
        
        return jsonify(build_error_response(
            'An unexpected error occurred. Please try again.',
            status_code=500
        )[0]), 500


@auth_bp.route('/auth/business-types', methods=['GET'])
def get_business_types():
    """Get list of valid business types"""
    try:
        business_types = [
            {'value': 'transportation', 'label': 'Transportation'},
            {'value': 'accommodation', 'label': 'Accommodation'},
            {'value': 'activities', 'label': 'Activities & Excursions'},
            {'value': 'catering', 'label': 'Catering'},
            {'value': 'equipment', 'label': 'Equipment Rental'},
            {'value': 'other', 'label': 'Other Services'}
        ]
        
        return jsonify({
            'success': True,
            'business_types': business_types
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Business types error: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error fetching business types'
        }), 500