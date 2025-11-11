from app.api import api_bp as auth_bp
from flask import request, jsonify, url_for, current_app
from app.auth.helpers import (
    validate_email, validate_password, validate_phone, validate_date_of_birth,
    validate_required_fields, sanitize_string, build_error_response, build_success_response
)
from app.extensions import db
from flask_login import login_user
from app.models import User, School
from app.auth.activity_log import log_registration, log_error


@auth_bp.route('/auth/register/teacher', methods=['POST'])
def api_register_teacher():
    """
    API endpoint for teacher registration
    
    Expected JSON payload:
    {
        "email": "teacher@example.com",
        "password": "SecurePass123",
        "confirm_password": "SecurePass123",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
        "school_id": 1,  # Optional: existing school ID
        "school_name": "Example School",  # Optional: if creating new school
        "teacher_id": "TCH12345",  # Optional
        "department": "Science",  # Optional
        "specialization": "Biology",  # Optional
        "years_of_experience": 5,  # Optional
        "bio": "Experienced teacher...",  # Optional
        "date_of_birth": "1985-05-15",  # Optional
        "emergency_contact": "Jane Doe",  # Optional
        "emergency_phone": "+0987654321"  # Optional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify(build_error_response('No data provided')[0]), 400
        
        # Validate required fields
        required_fields = ['email', 'password', 'confirm_password', 'first_name', 
                          'last_name', 'phone']
        is_valid, missing_fields = validate_required_fields(data, required_fields)
        
        if not is_valid:
            return jsonify(build_error_response(
                f'Missing required fields: {", ".join(missing_fields)}'
            )[0]), 400
        
        # Sanitize inputs
        email = sanitize_string(data['email']).lower()
        first_name = sanitize_string(data['first_name'])
        last_name = sanitize_string(data['last_name'])
        phone = sanitize_string(data['phone'])
        
        # Validate email format
        if not validate_email(email):
            return jsonify(build_error_response('Invalid email format')[0]), 400
        
        # Check if email already exists
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
        
        # Validate phone
        if not validate_phone(phone):
            return jsonify(build_error_response('Invalid phone number format')[0]), 400
        
        # Validate emergency contact phone if provided
        emergency_phone = sanitize_string(data.get('emergency_phone', ''))
        if emergency_phone and not validate_phone(emergency_phone):
            return jsonify(build_error_response(
                'Invalid emergency contact phone number'
            )[0]), 400
        
        # Validate date of birth if provided
        dob = None
        if data.get('date_of_birth'):
            dob, dob_error = validate_date_of_birth(data['date_of_birth'])
            if dob_error:
                return jsonify(build_error_response(dob_error)[0]), 400
        
        # Handle school association
        school_id = data.get('school_id')
        school = None
        
        if school_id:
            # Verify school exists
            school = School.query.get(school_id)
            if not school:
                return jsonify(build_error_response(
                    f'School with ID {school_id} not found'
                )[0]), 400
            
            if not school.is_active:
                return jsonify(build_error_response(
                    'Selected school is not active'
                )[0]), 400
        
        # Validate optional integer fields
        years_of_experience = data.get('years_of_experience')
        if years_of_experience:
            try:
                years_of_experience = int(years_of_experience)
                if years_of_experience < 0 or years_of_experience > 60:
                    return jsonify(build_error_response(
                        'Years of experience must be between 0 and 60'
                    )[0]), 400
            except (ValueError, TypeError):
                return jsonify(build_error_response(
                    'Invalid years of experience value'
                )[0]), 400
        
        # Create new teacher user
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='teacher',
            is_active=True,
            is_verified=False
        )
        new_user.password = password
        
        # Set optional fields
        if school:
            new_user.school_id = school.id
        
        if dob:
            new_user.date_of_birth = dob
        
        if data.get('bio'):
            new_user.bio = sanitize_string(data['bio'])
        
        if data.get('emergency_contact'):
            new_user.emergency_contact = sanitize_string(data['emergency_contact'])
        
        if emergency_phone:
            new_user.emergency_phone = emergency_phone
        
        if data.get('teacher_id'):
            new_user.teacher_id = sanitize_string(data['teacher_id'])
        
        if data.get('department'):
            new_user.department = sanitize_string(data['department'])
        
        if data.get('specialization'):
            new_user.specialization = sanitize_string(data['specialization'])
        
        if years_of_experience is not None:
            new_user.years_of_experience = years_of_experience
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        # Log the registration
        try:
            additional_data = {
                'school_id': school.id if school else None,
                'school_name': school.name if school else None,
                'has_emergency_contact': bool(data.get('emergency_contact')),
                'department': data.get('department'),
                'specialization': data.get('specialization')
            }
            log_registration(new_user, 'teacher', additional_data=additional_data)
        except Exception as log_error:
            current_app.logger.error(f'Activity log error: {str(log_error)}')
        
        # Log the user in
        login_user(new_user)
        
        # Build success response
        response_data = {
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'full_name': new_user.full_name,
                'role': new_user.role
            }
        }
        
        return jsonify(build_success_response(
            'Teacher account created successfully',
            data=response_data,
            redirect_url=url_for('teacher.dashboard'),
            status_code=201
        )[0]), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Teacher registration error: {str(e)}')
        
        # Log the error
        try:
            log_error('teacher_registration', str(e))
        except Exception:
            pass
        
        return jsonify(build_error_response(
            'An unexpected error occurred. Please try again.',
            status_code=500
        )[0]), 500


@auth_bp.route('/auth/checks-email', methods=['POST'])
def checks_email():
    """
    Check if email is already registered
    
    Expected JSON payload:
    {
        "email": "user@example.com"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'available': False, 'message': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        
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
        current_app.logger.error(f'Email check error: {str(e)}')
        return jsonify({
            'available': False,
            'message': 'Error checking email availability'
        }), 500


@auth_bp.route('/auth/schools/search', methods=['GET'])
def search_schools():
    """
    Search for schools by name
    
    Query parameters:
    - q: Search query
    - limit: Maximum results (default: 10)
    """
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if not query or len(query) < 2:
            return jsonify({
                'success': True,
                'schools': []
            }), 200
        
        schools = School.query.filter(
            School.is_active == True,
            db.or_(
                School.name.ilike(f'%{query}%'),
                School.short_name.ilike(f'%{query}%')
            )
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'schools': [{
                'id': school.id,
                'name': school.name,
                'short_name': school.short_name,
                'city': school.city,
                'country': school.country,
                'is_verified': school.is_verified
            } for school in schools]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'School search error: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error searching schools'
        }), 500