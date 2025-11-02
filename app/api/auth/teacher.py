from app.api import api_bp as auth_bp
from flask import request, jsonify,url_for, current_app
from app.auth.helpers import validate_email, validate_password, validate_phone
from app.extensions import db
from flask_login import login_user
from app.models import User
from datetime import datetime
from app.auth.activity_log import log_registration

@auth_bp.route('/auth/register/teacher', methods=['POST'])
def api_register_teacher():
    """API endpoint for teacher registration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'confirm_password', 'first_name', 
                          'last_name', 'phone', 'school']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
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
        
        # Validate phone
        if not validate_phone(data['phone']):
            return jsonify({
                'success': False,
                'message': 'Invalid phone number format'
            }), 400
        
        # Validate emergency contact phone if provided
        if data.get('emergency_phone') and not validate_phone(data['emergency_phone']):
            return jsonify({
                'success': False,
                'message': 'Invalid emergency contact phone number'
            }), 400
        
        # Create new teacher user
        new_user = User(
            email=data['email'].lower(),
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            phone=data['phone'].strip(),
            role='teacher',
            school=data['school'].strip(),
            bio=data.get('bio', '').strip(),
            emergency_contact=data.get('emergency_contact', '').strip(),
            emergency_phone=data.get('emergency_phone', '').strip(),
            is_active=True,
            is_verified=False
        )
        new_user.password = data['password']
        
        # Parse date of birth if provided
        if data.get('date_of_birth'):
            try:
                new_user.date_of_birth = datetime.strptime(
                    data['date_of_birth'], '%Y-%m-%d'
                ).date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format'
                }), 400
        
        db.session.add(new_user)
        db.session.commit()
        
        try:
            log_registration(
                new_user, 
                'teacher',
                additional_data={
                    'school': data['school'],
                    'has_emergency_contact': bool(data.get('emergency_contact'))
                }
            )
        except Exception as log_error:
            current_app.logger.error(f'Activity log error: {str(log_error)}')
        

        # Log the user in
        login_user(new_user)
        
        return jsonify({
            'success': True,
            'message': 'Teacher account created successfully',
            'redirect_url': url_for('teacher.dashboard')
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500