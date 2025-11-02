from app.api import api_bp as auth_bp
from flask import request, jsonify, url_for, current_app
from app.auth.helpers import validate_email, validate_password, validate_phone
from app.extensions import db
from flask_login import login_user
from app.models import User, Vendor
from app.auth.activity_log import (
    log_registration, log_vendor_profile_creation
)


@auth_bp.route('/auth/register/vendor', methods=['POST'])
def api_register_vendor():
    """API endpoint for vendor registration"""
    try:
        data = request.get_json()
        
        # Validate required user fields
        required_user_fields = ['email', 'password', 'confirm_password', 
                               'first_name', 'last_name', 'phone']
        missing_fields = [field for field in required_user_fields if not data.get(field)]
        
        # Validate required vendor fields
        required_vendor_fields = ['business_name', 'business_type', 'contact_email', 
                                 'contact_phone', 'city', 'country']
        missing_fields.extend([field for field in required_vendor_fields if not data.get(field)])
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Validate email formats
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': 'Invalid user email format'
            }), 400
        
        if not validate_email(data['contact_email']):
            return jsonify({
                'success': False,
                'message': 'Invalid business email format'
            }), 400
        
        # Check if email already exists
        if User.query.filter_by(email=data['email'].lower()).first():
            return jsonify({
                'success': False,
                'message': 'Email already registered'
            }), 400
        
        # Validate password
        if not validate_password(data['password']):
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters with uppercase, lowercase, and number'
            }), 400
        
        # Check password confirmation
        if data['password'] != data['confirm_password']:
            return jsonify({
                'success': False,
                'message': 'Passwords do not match'
            }), 400
        
        # Validate phone numbers
        if not validate_phone(data['phone']):
            return jsonify({
                'success': False,
                'message': 'Invalid phone number format'
            }), 400
        
        if not validate_phone(data['contact_phone']):
            return jsonify({
                'success': False,
                'message': 'Invalid business phone number format'
            }), 400
        
        # Validate capacity if provided
        if data.get('capacity'):
            try:
                capacity = int(data['capacity'])
                if capacity <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'message': 'Capacity must be a positive number'
                }), 400
        
        # Validate pricing if provided
        if data.get('base_price'):
            try:
                base_price = float(data['base_price'])
                if base_price < 0:
                    raise ValueError
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'message': 'Base price must be a valid number'
                }), 400
        
        if data.get('price_per_person'):
            try:
                price_per_person = float(data['price_per_person'])
                if price_per_person < 0:
                    raise ValueError
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'message': 'Price per person must be a valid number'
                }), 400
        
        # Create new vendor user
        new_user = User(
            email=data['email'].lower(),
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            phone=data['phone'].strip(),
            role='vendor',
            is_active=True,
            is_verified=False
        )
        new_user.password = data['password']
        
        db.session.add(new_user)
        db.session.flush()  # Get the user ID
        
        # Parse specializations
        specializations = []
        if data.get('specializations'):
            if isinstance(data['specializations'], list):
                specializations = data['specializations']
            else:
                specializations = [s.strip() for s in data['specializations'].split(',') if s.strip()]
        
        # Create vendor profile
        vendor_profile = Vendor(
            user_id=new_user.id,
            business_name=data['business_name'].strip(),
            business_type=data['business_type'].strip(),
            description=data.get('description', '').strip(),
            contact_email=data['contact_email'].lower(),
            contact_phone=data['contact_phone'].strip(),
            website=data.get('website', '').strip(),
            address_line1=data.get('address_line1', '').strip(),
            address_line2=data.get('address_line2', '').strip(),
            city=data['city'].strip(),
            state=data.get('state', '').strip(),
            postal_code=data.get('postal_code', '').strip(),
            country=data['country'].strip(),
            license_number=data.get('license_number', '').strip(),
            insurance_details=data.get('insurance_details', '').strip(),
            capacity=int(data['capacity']) if data.get('capacity') else None,
            specializations=specializations,
            base_price=float(data['base_price']) if data.get('base_price') else None,
            price_per_person=float(data['price_per_person']) if data.get('price_per_person') else None,
            pricing_notes=data.get('pricing_notes', '').strip(),
            is_verified=False,
            is_active=True
        )
        
        db.session.add(vendor_profile)
        db.session.commit()
        
        try:
            log_registration(
                new_user,
                'vendor',
                additional_data={
                    'business_name': data['business_name'],
                    'business_type': data['business_type']
                }
            )
        except Exception as log_error:
            current_app.logger.error(f'Activity log error (user): {str(log_error)}')
        
        try:
            log_vendor_profile_creation(vendor_profile, new_user)
        except Exception as log_error:
            current_app.logger.error(f'Activity log error (vendor): {str(log_error)}')
        
        # Log the user in
        login_user(new_user)
        
        return jsonify({
            'success': True,
            'message': 'Vendor account created successfully',
            'redirect_url': url_for('vendor.dashboard')
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@auth_bp.route('/auth/check-email', methods=['POST'])
def check_email():
    """Check if email is already registered"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower()
        
        if not email:
            return jsonify({'available': False, 'message': 'Email is required'}), 400
        
        if not validate_email(email):
            return jsonify({'available': False, 'message': 'Invalid email format'}), 400
        
        exists = User.query.filter_by(email=email).first() is not None
        
        return jsonify({
            'available': not exists,
            'message': 'Email already registered' if exists else 'Email available'
        }), 200
        
    except Exception as e:
        return jsonify({
            'available': False,
            'message': f'Error checking email: {str(e)}'
        }), 500