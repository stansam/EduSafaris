from flask import request, jsonify, current_app
from flask_login import current_user, login_required
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import os
from decimal import Decimal

from app.extensions import db
from app.models.participant import Participant
from app.models.consent import Consent
from app.models.document import Document
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.models.trip import Trip
from app.config import BaseConfig

from app.api import api_bp as parent_bp 


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in BaseConfig.ALLOWED_EXTENSIONS


def get_current_user():
    """Get current authenticated user"""
    try:
        # user_id = get_jwt_identity()
        user = User.query.get(current_user.id)
        if not user:
            return None, {'error': 'User not found'}, 404
        roles = ['admin', 'parent']
        if user.role not in roles:
            return None, {'error': 'User not Authorised'}, 404
        return user, None, None
    except Exception as e:
        return None, {'error': 'Authentication failed'}, 401


def verify_parent_child_access(parent_id, child_id):
    """Verify that the parent has access to the child"""
    child = Participant.query.get(child_id)
    if not child:
        return None, {'error': 'Child not found'}, 404
    
    if child.parent_id != parent_id:
        return None, {'error': 'Unauthorized access to this child'}, 403
    
    return child, None, None


def validate_child_data(data, is_update=False):
    """Validate child/participant data"""
    errors = []
    
    if not is_update:
        # Required fields for creation
        if not data.get('first_name'):
            errors.append('First name is required')
        if not data.get('last_name'):
            errors.append('Last name is required')
        if not data.get('trip_id'):
            errors.append('Trip ID is required')
    
    # Validate email if provided
    if data.get('email'):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            errors.append('Invalid email format')
    
    # Validate phone if provided
    if data.get('phone'):
        phone = data['phone'].replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        if not phone.isdigit() or len(phone) < 10:
            errors.append('Invalid phone number format')
    
    # Validate date of birth if provided
    if data.get('date_of_birth'):
        try:
            dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            if dob > datetime.now().date():
                errors.append('Date of birth cannot be in the future')
        except ValueError:
            errors.append('Invalid date of birth format. Use YYYY-MM-DD')
    
    return errors


# ============================================================================
# ROUTES - CHILDREN LIST & PROFILE
# ============================================================================

@parent_bp.route('/parent/children', methods=['GET'])
# @jwt_required()
def get_children_list():
    """
    Get list of all children registered by the parent
    
    Query Parameters:
        - status: Filter by participant status (optional)
        - trip_id: Filter by specific trip (optional)
        - payment_status: Filter by payment status (optional)
    
    Returns:
        200: List of children with summary information
        401: Unauthorized
        500: Server error
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code
        
        # Build query
        query = Participant.query.filter_by(parent_id=user.id)
        
        # Apply filters
        status_filter = request.args.get('status')
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        trip_id = request.args.get('trip_id', type=int)
        if trip_id:
            query = query.filter_by(trip_id=trip_id)
        
        payment_status = request.args.get('payment_status')
        if payment_status:
            query = query.filter_by(payment_status=payment_status)
        
        # Get children
        children = query.order_by(Participant.created_at.desc()).all()
        
        # Serialize with trip information
        children_data = []
        for child in children:
            child_dict = child.serialize()
            if child.trip:
                child_dict['trip'] = {
                    'id': child.trip.id,
                    'title': child.trip.title,
                    'destination': child.trip.destination,
                    'start_date': child.trip.start_date.isoformat() if child.trip.start_date else None,
                    'end_date': child.trip.end_date.isoformat() if child.trip.end_date else None,
                    'status': child.trip.status
                }
            children_data.append(child_dict)
        
        return jsonify({
            'success': True,
            'count': len(children_data),
            'children': children_data
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500


@parent_bp.route('/parent/children/<int:child_id>', methods=['GET'])
# @jwt_required()
def get_child_profile(child_id):
    """
    Get detailed profile of a specific child including trip history
    
    Parameters:
        - child_id: ID of the child/participant
    
    Returns:
        200: Child profile with complete details
        403: Unauthorized access
        404: Child not found
        500: Server error
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code
        
        # Verify access
        child, error, status_code = verify_parent_child_access(user.id, child_id)
        if error:
            return jsonify(error), status_code
        
        # Get child details
        child_data = child.serialize()
        
        # Add current trip details
        if child.trip:
            child_data['current_trip'] = {
                'id': child.trip.id,
                'title': child.trip.title,
                'description': child.trip.description,
                'destination': child.trip.destination,
                'start_date': child.trip.start_date.isoformat() if child.trip.start_date else None,
                'end_date': child.trip.end_date.isoformat() if child.trip.end_date else None,
                'status': child.trip.status,
                'price': float(child.trip.price_per_student) if child.trip.price_per_student else 0
            }
        
        # Get trip history (all trips this child participated in)
        trip_history = Participant.query.filter_by(
            first_name=child.first_name,
            last_name=child.last_name,
            parent_id=user.id
        ).all()
        
        child_data['trip_history'] = []
        for participant in trip_history:
            if participant.trip:
                child_data['trip_history'].append({
                    'id': participant.id,
                    'trip_id': participant.trip_id,
                    'trip_title': participant.trip.title,
                    'destination': participant.trip.destination,
                    'start_date': participant.trip.start_date.isoformat() if participant.trip.start_date else None,
                    'end_date': participant.trip.end_date.isoformat() if participant.trip.end_date else None,
                    'status': participant.status,
                    'payment_status': participant.payment_status,
                    'amount_paid': float(participant.amount_paid) if participant.amount_paid else 0
                })
        
        # Get documents
        documents = Document.get_participant_documents(child_id)
        child_data['documents'] = [doc.serialize() for doc in documents]
        
        # Get consent forms
        consents = child.consents.all()
        child_data['consents'] = [consent.serialize() for consent in consents]
        
        # Get latest location if available
        latest_location = child.get_latest_location()
        if latest_location:
            child_data['latest_location'] = latest_location.serialize()
        
        return jsonify({
            'success': True,
            'child': child_data
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500


# ============================================================================
# ROUTES - ADD CHILD
# ============================================================================

@parent_bp.route('/parent/children', methods=['POST'])
# @jwt_required()
def add_child():
    """
    Register a new child for a trip
    
    Required JSON fields:
        - first_name: Child's first name
        - last_name: Child's last name
        - trip_id: ID of the trip to register for
    
    Optional fields:
        - date_of_birth: YYYY-MM-DD format
        - grade_level: Grade or class
        - email: Child's email
        - phone: Contact number
        - student_id: School student ID
        - special_requirements: Any special needs
    
    Returns:
        201: Child successfully registered
        400: Validation error
        404: Trip not found
        500: Server error
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate data
        validation_errors = validate_child_data(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'validation_errors': validation_errors
            }), 400
        
        # Verify trip exists and is accepting registrations
        trip = Trip.query.get(data['trip_id'])
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found'
            }), 404
        
        if trip.status == 'cancelled':
            return jsonify({
                'success': False,
                'error': 'Cannot register for cancelled trip'
            }), 400
        
        # Check if trip is full
        if trip.max_participants:
            current_participants = Participant.query.filter_by(
                trip_id=trip.id,
                status='confirmed'
            ).count()
            if current_participants >= trip.max_participants:
                return jsonify({
                    'success': False,
                    'error': 'Trip is full'
                }), 400
        
        # Create participant
        child = Participant(
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date() if data.get('date_of_birth') else None,
            grade_level=data.get('grade_level'),
            student_id=data.get('student_id'),
            email=data.get('email'),
            phone=data.get('phone'),
            special_requirements=data.get('special_requirements'),
            trip_id=data['trip_id'],
            parent_id=user.id,
            status='registered',
            payment_status='pending',
            registration_date=datetime.now()
        )
        
        db.session.add(child)
        db.session.commit()
        
        # Log activity
        ActivityLog.log_action(
            action='child_registered',
            user_id=user.id,
            entity_type='participant',
            entity_id=child.id,
            description=f"Registered {child.full_name} for {trip.title}",
            category='participant',
            trip_id=trip.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'success': True,
            'message': 'Child registered successfully',
            'child': child.serialize()
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'Invalid data format',
            'details': str(e)
        }), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500


# ============================================================================
# ROUTES - UPDATE CHILD PROFILE
# ============================================================================

@parent_bp.route('/parent/children/<int:child_id>', methods=['PUT', 'PATCH'])
# @jwt_required()
def update_child_profile(child_id):
    """
    Update child profile information
    
    Parameters:
        - child_id: ID of the child to update
    
    Allowed JSON fields:
        - first_name, last_name
        - date_of_birth, grade_level, student_id
        - email, phone
        - medical_conditions, medications, allergies
        - dietary_restrictions, emergency_medical_info
        - emergency_contact_1_*, emergency_contact_2_*
        - special_requirements
    
    Returns:
        200: Profile updated successfully
        400: Validation error
        403: Unauthorized access
        404: Child not found
        500: Server error
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code
        
        # Verify access
        child, error, status_code = verify_parent_child_access(user.id, child_id)
        if error:
            return jsonify(error), status_code
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate data
        validation_errors = validate_child_data(data, is_update=True)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'validation_errors': validation_errors
            }), 400
        
        # Store old values for logging
        old_values = {}
        updated_fields = []
        
        # Update basic information
        basic_fields = ['first_name', 'last_name', 'grade_level', 'student_id', 
                       'email', 'phone', 'special_requirements']
        for field in basic_fields:
            if field in data:
                old_values[field] = getattr(child, field)
                setattr(child, field, data[field])
                updated_fields.append(field)
        
        # Update date of birth
        if 'date_of_birth' in data:
            old_values['date_of_birth'] = child.date_of_birth.isoformat() if child.date_of_birth else None
            child.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            updated_fields.append('date_of_birth')
        
        # Update medical information
        medical_fields = ['medical_conditions', 'medications', 'allergies', 
                         'dietary_restrictions', 'emergency_medical_info']
        for field in medical_fields:
            if field in data:
                old_values[field] = getattr(child, field)
                setattr(child, field, data[field])
                updated_fields.append(field)
        
        # Update emergency contacts
        emergency_fields = [
            'emergency_contact_1_name', 'emergency_contact_1_phone', 'emergency_contact_1_relationship',
            'emergency_contact_2_name', 'emergency_contact_2_phone', 'emergency_contact_2_relationship'
        ]
        for field in emergency_fields:
            if field in data:
                old_values[field] = getattr(child, field)
                setattr(child, field, data[field])
                updated_fields.append(field)
        
        if not updated_fields:
            return jsonify({
                'success': False,
                'error': 'No valid fields to update'
            }), 400
        
        db.session.commit()
        
        # Log activity
        ActivityLog.log_action(
            action='child_profile_updated',
            user_id=user.id,
            entity_type='participant',
            entity_id=child.id,
            description=f"Updated profile for {child.full_name}",
            category='participant',
            trip_id=child.trip_id,
            old_values=old_values,
            new_values={field: getattr(child, field) for field in updated_fields},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'updated_fields': updated_fields,
            'child': child.serialize()
        }), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Invalid data format',
            'details': str(e)
        }), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500


# ============================================================================
# ROUTES - DOCUMENT MANAGEMENT
# ============================================================================

@parent_bp.route('/parent/children/<int:child_id>/documents', methods=['POST'])
# @jwt_required()
def upload_child_document(child_id):
    """
    Upload a document for a child (medical forms, etc.)
    
    Parameters:
        - child_id: ID of the child
    
    Form Data:
        - file: Document file (required)
        - title: Document title (required)
        - document_type: Type of document (required)
        - description: Document description (optional)
        - expiry_date: Expiry date in YYYY-MM-DD format (optional)
    
    Returns:
        201: Document uploaded successfully
        400: Invalid file or data
        403: Unauthorized access
        404: Child not found
        413: File too large
        500: Server error
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code
        
        # Verify access
        child, error, status_code = verify_parent_child_access(user.id, child_id)
        if error:
            return jsonify(error), status_code
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(BaseConfig.ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Get form data
        title = request.form.get('title')
        document_type = request.form.get('document_type')
        
        if not title or not document_type:
            return jsonify({
                'success': False,
                'error': 'Title and document_type are required'
            }), 400
        
        # Secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{child_id}_{timestamp}_{filename}"
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join('uploads', 'participants', str(child_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Check file size
        if file_size > BaseConfig.MAX_CONTENT_LENGTH:
            os.remove(file_path)
            return jsonify({
                'success': False,
                'error': f'File too large. Maximum size is {BaseConfig.MAX_CONTENT_LENGTH / (1024*1024)}MB'
            }), 413
        
        # Create document record
        document = Document(
            title=title,
            description=request.form.get('description'),
            file_name=filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file.content_type,
            document_type=document_type,
            uploaded_by=user.id,
            participant_id=child_id,
            trip_id=child.trip_id,
            is_active=True
        )
        
        # Set expiry date if provided
        expiry_date = request.form.get('expiry_date')
        if expiry_date:
            try:
                document.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        db.session.add(document)
        db.session.commit()
        
        # Log activity
        ActivityLog.log_action(
            action='document_uploaded',
            user_id=user.id,
            entity_type='document',
            entity_id=document.id,
            description=f"Uploaded document '{title}' for {child.full_name}",
            category='document',
            trip_id=child.trip_id,
            new_values={
                'document_type': document_type,
                'file_name': filename
            },
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'success': True,
            'message': 'Document uploaded successfully',
            'document': document.serialize()
        }), 201
        
    except OSError as e:
        return jsonify({
            'success': False,
            'error': 'File system error',
            'details': str(e)
        }), 500
    except SQLAlchemyError as e:
        db.session.rollback()
        # Clean up file if database operation fails
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500


@parent_bp.route('/parent/children/<int:child_id>/documents', methods=['GET'])
# @jwt_required()
def get_child_documents(child_id):
    """
    Get all documents for a child
    
    Parameters:
        - child_id: ID of the child
    
    Query Parameters:
        - document_type: Filter by document type (optional)
    
    Returns:
        200: List of documents
        403: Unauthorized access
        404: Child not found
        500: Server error
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code
        
        # Verify access
        child, error, status_code = verify_parent_child_access(user.id, child_id)
        if error:
            return jsonify(error), status_code
        
        # Get documents
        document_type = request.args.get('document_type')
        documents = Document.get_participant_documents(child_id, document_type)
        
        return jsonify({
            'success': True,
            'count': len(documents),
            'documents': [doc.serialize() for doc in documents]
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500


# ============================================================================
# ROUTES - CONSENT MANAGEMENT
# ============================================================================

@parent_bp.route('/parent/children/<int:child_id>/consents', methods=['GET'])
# @jwt_required()
def get_child_consents(child_id):
    """
    Get all consent forms for a child
    
    Parameters:
        - child_id: ID of the child
    
    Query Parameters:
        - status: Filter by signed status (signed/unsigned) (optional)
    
    Returns:
        200: List of consent forms
        403: Unauthorized access
        404: Child not found
        500: Server error
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code
        
        # Verify access
        child, error, status_code = verify_parent_child_access(user.id, child_id)
        if error:
            return jsonify(error), status_code
        
        # Get consents
        query = child.consents
        
        status_filter = request.args.get('status')
        if status_filter == 'signed':
            query = query.filter_by(is_signed=True)
        elif status_filter == 'unsigned':
            query = query.filter_by(is_signed=False)
        
        consents = query.order_by(Consent.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'count': len(consents),
            'consents': [consent.serialize() for consent in consents]
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500


@parent_bp.route('/parent/children/<int:child_id>/consents/<int:consent_id>', methods=['GET'])
# @jwt_required()
def get_consent_details(child_id, consent_id):
    """
    Get detailed information about a specific consent form
    
    Parameters:
        - child_id: ID of the child
        - consent_id: ID of the consent form
    
    Returns:
        200: Consent form details
        403: Unauthorized access
        404: Consent not found
        500: Server error
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code
        
        # Verify access
        child, error, status_code = verify_parent_child_access(user.id, child_id)
        if error:
            return jsonify(error), status_code
        
        # Get consent
        consent = Consent.query.get(consent_id)
        if not consent or consent.participant_id != child_id:
            return jsonify({
                'success': False,
                'error': 'Consent form not found'
            }), 404
        
        return jsonify({
            'success': True,
            'consent': consent.serialize()
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500


@parent_bp.route('/parent/children/<int:child_id>/consents/<int:consent_id>/sign', methods=['POST'])
# @jwt_required()
def sign_consent_form(child_id, consent_id):
    """
    Sign a consent form for a child
    
    Parameters:
        - child_id: ID of the child
        - consent_id: ID of the consent form
    
    Required JSON fields:
        - signer_name: Name of person signing
        - signer_relationship: Relationship to child (e.g., "Parent", "Guardian")
    
    Optional fields:
        - signature_data: Digital signature data (base64)
        - notes: Additional notes
    
    Returns:
        200: Consent signed successfully
        400: Validation error or already signed
        403: Unauthorized access
        404: Consent not found
        500: Server error
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code
        
        # Verify access
        child, error, status_code = verify_parent_child_access(user.id, child_id)
        if error:
            return jsonify(error), status_code
        
        # Get consent
        consent = Consent.query.get(consent_id)
        if not consent or consent.participant_id != child_id:
            return jsonify({
                'success': False,
                'error': 'Consent form not found'
            }), 404
        
        return jsonify({
            'success': True,
            'consent': consent.serialize()
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500


@parent_bp.route('/parent/children/<int:child_id>/emergency-contacts', methods=['PUT'])
# @jwt_required()
def update_emergency_contacts(child_id):
    """
    Update emergency contact information for a child
    
    Parameters:
        - child_id: ID of the child
    
    JSON fields:
        - emergency_contact_1_name
        - emergency_contact_1_phone
        - emergency_contact_1_relationship
        - emergency_contact_2_name
        - emergency_contact_2_phone
        - emergency_contact_2_relationship
    
    Returns:
        200: Emergency contacts updated
        400: Validation error
        403: Unauthorized access
        404: Child not found
        500: Server error
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code
        
        # Verify access
        child, error, status_code = verify_parent_child_access(user.id, child_id)
        if error:
            return jsonify(error), status_code
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate at least one emergency contact
        has_contact_1 = data.get('emergency_contact_1_name') and data.get('emergency_contact_1_phone')
        has_contact_2 = data.get('emergency_contact_2_name') and data.get('emergency_contact_2_phone')
        
        if not has_contact_1 and not has_contact_2:
            return jsonify({
                'success': False,
                'error': 'At least one emergency contact is required'
            }), 400
        
        # Store old values
        old_values = {
            'emergency_contact_1_name': child.emergency_contact_1_name,
            'emergency_contact_1_phone': child.emergency_contact_1_phone,
            'emergency_contact_2_name': child.emergency_contact_2_name,
            'emergency_contact_2_phone': child.emergency_contact_2_phone
        }
        
        # Update emergency contacts
        emergency_fields = [
            'emergency_contact_1_name', 'emergency_contact_1_phone', 'emergency_contact_1_relationship',
            'emergency_contact_2_name', 'emergency_contact_2_phone', 'emergency_contact_2_relationship'
        ]
        
        for field in emergency_fields:
            if field in data:
                setattr(child, field, data[field])
        
        db.session.commit()
        
        # Log activity
        ActivityLog.log_action(
            action='emergency_contacts_updated',
            user_id=user.id,
            entity_type='participant',
            entity_id=child.id,
            description=f"Updated emergency contacts for {child.full_name}",
            category='participant',
            trip_id=child.trip_id,
            old_values=old_values,
            new_values={field: getattr(child, field) for field in emergency_fields if field in data},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'success': True,
            'message': 'Emergency contacts updated successfully',
            'emergency_contacts': {
                'contact_1': {
                    'name': child.emergency_contact_1_name,
                    'phone': child.emergency_contact_1_phone,
                    'relationship': child.emergency_contact_1_relationship
                },
                'contact_2': {
                    'name': child.emergency_contact_2_name,
                    'phone': child.emergency_contact_2_phone,
                    'relationship': child.emergency_contact_2_relationship
                }
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500


# ============================================================================
# ROUTES - MEDICAL INFORMATION
# ============================================================================

@parent_bp.route('/parent/children/<int:child_id>/medical-info', methods=['PUT'])
# @jwt_required()
def update_medical_info(child_id):
    """
    Update medical information for a child
    
    Parameters:
        - child_id: ID of the child
    
    JSON fields:
        - medical_conditions: Medical conditions/history
        - medications: Current medications
        - allergies: Known allergies
        - dietary_restrictions: Dietary needs/restrictions
        - emergency_medical_info: Critical medical information
    
    Returns:
        200: Medical information updated
        400: No data provided
        403: Unauthorized access
        404: Child not found
        500: Server error
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code
        
        # Verify access
        child, error, status_code = verify_parent_child_access(user.id, child_id)
        if error:
            return jsonify(error), status_code
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Store old values
        old_values = {
            'medical_conditions': child.medical_conditions,
            'medications': child.medications,
            'allergies': child.allergies,
            'dietary_restrictions': child.dietary_restrictions,
            'emergency_medical_info': child.emergency_medical_info
        }
        
        # Update medical information
        medical_fields = ['medical_conditions', 'medications', 'allergies', 
                         'dietary_restrictions', 'emergency_medical_info']
        
        updated_fields = []
        for field in medical_fields:
            if field in data:
                setattr(child, field, data[field])
                updated_fields.append(field)
        
        if not updated_fields:
            return jsonify({
                'success': False,
                'error': 'No valid medical fields to update'
            }), 400
        
        db.session.commit()
        
        # Log activity
        ActivityLog.log_action(
            action='medical_info_updated',
            user_id=user.id,
            entity_type='participant',
            entity_id=child.id,
            description=f"Updated medical information for {child.full_name}",
            category='participant',
            trip_id=child.trip_id,
            old_values=old_values,
            new_values={field: getattr(child, field) for field in updated_fields},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'success': True,
            'message': 'Medical information updated successfully',
            'updated_fields': updated_fields,
            'medical_info': {
                'medical_conditions': child.medical_conditions,
                'medications': child.medications,
                'allergies': child.allergies,
                'dietary_restrictions': child.dietary_restrictions,
                'emergency_medical_info': child.emergency_medical_info
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@parent_bp.route('/parent/trips', methods=['GET'])
# @jwt_required()
def get_parent_trips():
    """
    Fetch available trips for filtering by parents.
    Only return trips that are active, not full, and open for registration.
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code

        # Base query: only trips open for registration
        trips_query = Trip.query.filter(Trip.status.in_(['active', 'in_progress']))

        # Optional: Only include trips that are upcoming or registration is open
        trips = [t for t in trips_query.all() if t.registration_open]

        # Serialize minimal fields for filter dropdown
        trip_data = [{
            'id': trip.id,
            'title': trip.title,
            'destination': trip.destination,
            'start_date': trip.start_date.isoformat() if trip.start_date else None,
            'end_date': trip.end_date.isoformat() if trip.end_date else None
        } for trip in trips]

        return jsonify({'success': True, 'trips': trip_data}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] /api/parent/trips: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch trips'}), 500