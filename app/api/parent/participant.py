from flask import request, jsonify, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.extensions import db
from app.models import Participant, ActivityLog, Trip, TripRegistration
from app.api.parent.children import get_current_user
from app.api import api_bp as parent_bp 
from app.utils.utils import roles_required
from app.api.parent.validator import validate_participant_data

@parent_bp.route('/parent/children', methods=['POST'])
@roles_required('parent', 'admin')
def create_child():
    """
    Create a new child/participant profile
    
    Expected JSON:
    {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "2015-05-15",
        "gender": "male",
        "grade_level": "4th Grade",
        "school_name": "Springfield Elementary",
        "blood_type": "A+",
        "medical_conditions": "Asthma",
        "medications": "Albuterol inhaler",
        "allergies": "Peanuts, shellfish",
        "dietary_restrictions": "Vegetarian",
        "emergency_contact_1_name": "Jane Doe",
        "emergency_contact_1_phone": "+254712345678",
        "emergency_contact_1_relationship": "Mother",
        "emergency_contact_1_email": "jane@example.com",
        "special_requirements": "Needs assistance with stairs"
    }
    """
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required',
                'code': 'MISSING_DATA'
            }), 400
        
        # Validate data
        validation_errors = validate_participant_data(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'code': 'VALIDATION_ERROR',
                'details': validation_errors
            }), 400
        
        # Check if child with same name and DOB already exists for this parent
        existing_child = Participant.query.filter_by(
            parent_id=current_user.id,
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        ).first()
        
        if existing_child:
            return jsonify({
                'success': False,
                'error': 'A child with the same name and date of birth already exists',
                'code': 'DUPLICATE_CHILD',
                'child_id': existing_child.id
            }), 409
        
        # Create participant
        participant = Participant(
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date(),
            gender=data['gender'],
            grade_level=data.get('grade_level', '').strip() if data.get('grade_level') else None,
            school_name=data.get('school_name', '').strip() if data.get('school_name') else None,
            student_id=data.get('student_id', '').strip() if data.get('student_id') else None,
            email=data.get('email', '').strip() if data.get('email') else None,
            phone=data.get('phone', '').strip() if data.get('phone') else None,
            blood_type=data.get('blood_type'),
            medical_conditions=data.get('medical_conditions', '').strip() if data.get('medical_conditions') else None,
            medications=data.get('medications', '').strip() if data.get('medications') else None,
            allergies=data.get('allergies', '').strip() if data.get('allergies') else None,
            dietary_restrictions=data.get('dietary_restrictions', '').strip() if data.get('dietary_restrictions') else None,
            emergency_medical_info=data.get('emergency_medical_info', '').strip() if data.get('emergency_medical_info') else None,
            doctor_name=data.get('doctor_name', '').strip() if data.get('doctor_name') else None,
            doctor_phone=data.get('doctor_phone', '').strip() if data.get('doctor_phone') else None,
            emergency_contact_1_name=data['emergency_contact_1_name'].strip(),
            emergency_contact_1_phone=data['emergency_contact_1_phone'].strip(),
            emergency_contact_1_relationship=data['emergency_contact_1_relationship'].strip(),
            emergency_contact_1_email=data.get('emergency_contact_1_email', '').strip() if data.get('emergency_contact_1_email') else None,
            emergency_contact_2_name=data.get('emergency_contact_2_name', '').strip() if data.get('emergency_contact_2_name') else None,
            emergency_contact_2_phone=data.get('emergency_contact_2_phone', '').strip() if data.get('emergency_contact_2_phone') else None,
            emergency_contact_2_relationship=data.get('emergency_contact_2_relationship', '').strip() if data.get('emergency_contact_2_relationship') else None,
            emergency_contact_2_email=data.get('emergency_contact_2_email', '').strip() if data.get('emergency_contact_2_email') else None,
            special_requirements=data.get('special_requirements', '').strip() if data.get('special_requirements') else None,
            photo_url=data.get('photo_url'),
            parent_id=current_user.id,
            created_by=current_user.id,
            status='active'
        )
        
        db.session.add(participant)
        db.session.flush()  # Get participant ID without committing
        
        # Log activity
        ActivityLog.log_action(
            action='participant_created',
            user_id=current_user.id,
            entity_type='participant',
            entity_id=participant.id,
            description=f"Parent created child profile: {participant.full_name}",
            category='user',
            new_values={
                'full_name': participant.full_name,
                'date_of_birth': data['date_of_birth'],
                'grade_level': participant.grade_level
            }
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Child profile created successfully',
            'data': participant.serialize(include_sensitive=True)
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Invalid data format',
            'code': 'INVALID_FORMAT',
            'details': str(e)
        }), 400
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500

@parent_bp.route('/parent/children/<int:child_id>', methods=['PUT', 'PATCH'])
@roles_required('parent', 'admin')
def update_child(child_id):
    """Update child profile"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required',
                'code': 'MISSING_DATA'
            }), 400
        
        # Get child
        child = Participant.query.filter_by(
            id=child_id,
            parent_id=current_user.id
        ).first()
        
        if not child:
            return jsonify({
                'success': False,
                'error': 'Child not found or access denied',
                'code': 'NOT_FOUND'
            }), 404
        
        # Validate data
        validation_errors = validate_participant_data(data, is_update=True)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'code': 'VALIDATION_ERROR',
                'details': validation_errors
            }), 400
        
        # Store old values for logging
        old_values = {}
        new_values = {}
        
        # Update fields
        updatable_fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'grade_level',
            'school_name', 'student_id', 'email', 'phone', 'blood_type',
            'medical_conditions', 'medications', 'allergies', 'dietary_restrictions',
            'emergency_medical_info', 'doctor_name', 'doctor_phone',
            'emergency_contact_1_name', 'emergency_contact_1_phone',
            'emergency_contact_1_relationship', 'emergency_contact_1_email',
            'emergency_contact_2_name', 'emergency_contact_2_phone',
            'emergency_contact_2_relationship', 'emergency_contact_2_email',
            'special_requirements', 'photo_url'
        ]
        
        for field in updatable_fields:
            if field in data:
                old_value = getattr(child, field)
                
                # Handle date conversion
                if field == 'date_of_birth' and data[field]:
                    new_value = datetime.strptime(data[field], '%Y-%m-%d').date()
                else:
                    new_value = data[field].strip() if isinstance(data[field], str) else data[field]
                
                if old_value != new_value:
                    old_values[field] = str(old_value) if old_value else None
                    new_values[field] = str(new_value) if new_value else None
                    setattr(child, field, new_value)
        
        if old_values:
            # Log activity
            ActivityLog.log_action(
                action='participant_updated',
                user_id=current_user.id,
                entity_type='participant',
                entity_id=child.id,
                description=f"Parent updated child profile: {child.full_name}",
                category='user',
                old_values=old_values,
                new_values=new_values
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Child profile updated successfully',
            'data': child.serialize(include_sensitive=True)
        }), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Invalid data format',
            'code': 'INVALID_FORMAT',
            'details': str(e)
        }), 400
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500
    
@parent_bp.route('/parent/children/trips/<int:trip_id>/register', methods=['POST'])
@roles_required('parent', 'admin')
def register_for_trip(trip_id):
    """
    Register a child for a trip
    
    Expected JSON:
    {
        "participant_id": 123,
        "payment_plan": "full",
        "parent_notes": "Please note my child has a nut allergy"
    }
    """
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data or 'participant_id' not in data:
            return jsonify({
                'success': False,
                'error': 'participant_id is required',
                'code': 'MISSING_DATA'
            }), 400
        
        participant_id = data['participant_id']
        
        # Verify trip exists and is available
        trip = Trip.query.get(trip_id)
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found',
                'code': 'TRIP_NOT_FOUND'
            }), 404
        
        if not trip.registration_is_open:
            return jsonify({
                'success': False,
                'error': 'Registration is not open for this trip',
                'code': 'REGISTRATION_CLOSED',
                'details': {
                    'status': trip.status,
                    'is_full': trip.is_full,
                    'available_spots': trip.available_spots
                }
            }), 400
        
        # Verify participant belongs to parent
        participant = Participant.query.filter_by(
            id=participant_id,
            parent_id=current_user.id,
            status='active'
        ).first()
        
        if not participant:
            return jsonify({
                'success': False,
                'error': 'Participant not found or access denied',
                'code': 'PARTICIPANT_NOT_FOUND'
            }), 404
        
        # Check if already registered
        existing_registration = TripRegistration.query.filter_by(
            trip_id=trip_id,
            participant_id=participant_id
        ).filter(
            TripRegistration.status.in_(['pending', 'confirmed', 'waitlisted'])
        ).first()
        
        if existing_registration:
            return jsonify({
                'success': False,
                'error': 'Participant is already registered for this trip',
                'code': 'ALREADY_REGISTERED',
                'registration_id': existing_registration.id,
                'status': existing_registration.status
            }), 409
        
        # Check age restrictions
        if trip.min_age and participant.age < trip.min_age:
            return jsonify({
                'success': False,
                'error': f'Participant must be at least {trip.min_age} years old',
                'code': 'AGE_RESTRICTION',
                'participant_age': participant.age,
                'required_age': trip.min_age
            }), 400
        
        if trip.max_age and participant.age > trip.max_age:
            return jsonify({
                'success': False,
                'error': f'Participant must be at most {trip.max_age} years old',
                'code': 'AGE_RESTRICTION',
                'participant_age': participant.age,
                'required_age': trip.max_age
            }), 400
        
        # Check if medical info is required and complete
        if trip.medical_info_required and not participant.has_complete_medical_info:
            return jsonify({
                'success': False,
                'error': 'Complete medical information is required for this trip',
                'code': 'INCOMPLETE_MEDICAL_INFO',
                'message': 'Please update the participant profile with complete medical information'
            }), 400
        
        # Determine registration status based on capacity
        if trip.is_full:
            registration_status = 'waitlisted'
        else:
            registration_status = 'pending'
        
        # Create registration
        registration = TripRegistration(
            trip_id=trip_id,
            participant_id=participant_id,
            parent_id=current_user.id,
            status=registration_status,
            total_amount=trip.price_per_student,
            amount_paid=0,
            payment_status='unpaid',
            payment_plan=data.get('payment_plan', 'full'),
            payment_deadline=trip.registration_deadline,
            consent_signed=False,
            medical_form_submitted=participant.has_complete_medical_info,
            parent_notes=data.get('parent_notes', '').strip() if data.get('parent_notes') else None
        )
        
        registration.generate_registration_number()
        
        db.session.add(registration)
        db.session.flush()
        
        # Log activity
        ActivityLog.log_trip_registration(
            registration=registration,
            user_id=current_user.id,
            action_type='created'
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Registration {"waitlisted" if registration_status == "waitlisted" else "created"} successfully',
            'data': registration.serialize(),
            'next_steps': {
                'payment_required': True,
                'amount_due': float(trip.price_per_student),
                'payment_deadline': trip.registration_deadline.isoformat() if trip.registration_deadline else None,
                'consent_required': trip.consent_required,
                'documents_required': not registration.is_documentation_complete
            }
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Invalid data',
            'code': 'INVALID_DATA',
            'details': str(e)
        }), 400
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500
