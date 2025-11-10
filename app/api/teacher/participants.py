from flask import request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models import Participant, Trip, ActivityLog, TripRegistration, RegistrationPayment

from app.api import api_bp as teacher_participants_bp 
from app.utils.utils import roles_required


def verify_trip_ownership(trip_id):
    """Verify that the current teacher owns/organizes the trip"""
    try:
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return None, {
                'success': False,
                'error': 'Trip not found',
                'message': f'No trip found with ID {trip_id}'
            }, 404
        
        if trip.organizer_id != current_user.id:
            return None, {
                'success': False,
                'error': 'Unauthorized',
                'message': 'You do not have permission to access this trip'
            }, 403
        
        return trip, None, None
    
    except SQLAlchemyError as e:
        return None, {
            'success': False,
            'error': 'Database error',
            'message': 'An error occurred while verifying trip ownership'
        }, 500


# @teacher_participants_bp.route('/participants/teacher/trips', methods=['GET'])
# @login_required
# @roles_required('teacher')
# def get_teachers_trips():
#     """
#     Get all trips for the current teacher with participant statistics
#     """
#     try:
#         include_stats = request.args.get('include_stats', 'false').lower() == 'true'
        
#         # Get all trips organized by the teacher
#         trips = Trip.query.filter_by(organizer_id=current_user.id).all()
        
#         trips_data = []
#         for trip in trips:
#             trip_data = {
#                 'id': trip.id,
#                 'title': trip.title,
#                 'start_date': trip.start_date.isoformat() if trip.start_date else None,
#                 'end_date': trip.end_date.isoformat() if trip.end_date else None,
#                 'status': trip.status
#             }
            
#             if include_stats:
#                 # Get registration statistics
#                 registrations = TripRegistration.query.filter_by(trip_id=trip.id).all()
#                 confirmed_registrations = [r for r in registrations if r.status == 'confirmed']
#                 paid_registrations = [r for r in registrations if r.payment_status == 'paid']
                
#                 trip_data['participant_count'] = len(registrations)
#                 trip_data['confirmed_count'] = len(confirmed_registrations)
#                 trip_data['paid_count'] = len(paid_registrations)
            
#             trips_data.append(trip_data)
        
#         return jsonify({
#             'success': True,
#             'data': {
#                 'trips': trips_data
#             }
#         }), 200
    
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': 'Internal server error',
#             'message': 'An unexpected error occurred'
#         }), 500


@teacher_participants_bp.route('/participants/trip/<int:trip_id>', methods=['GET'])
@login_required
@roles_required('teacher')
def get_trip_participants(trip_id):
    """
    Get all participants for a specific trip organized by the teacher
    
    Query Parameters:
    - status: Filter by registration status (pending, confirmed, waitlisted, cancelled, completed)
    - payment_status: Filter by payment status (unpaid, partial, paid, refunded)
    - search: Search by participant name
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    - sort_by: Sort field (name, registration_date, payment_status)
    - order: Sort order (asc, desc)
    """
    try:
        # Verify trip ownership
        trip, error_response, status_code = verify_trip_ownership(trip_id)
        if error_response:
            return jsonify(error_response), status_code
        
        # Get query parameters
        status_filter = request.args.get('status', type=str)
        payment_status_filter = request.args.get('payment_status', type=str)
        search_query = request.args.get('search', type=str)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        sort_by = request.args.get('sort_by', 'registration_date', type=str)
        order = request.args.get('order', 'desc', type=str)
        
        # Validate parameters - Use TripRegistration statuses
        valid_statuses = ['pending', 'confirmed', 'waitlisted', 'cancelled', 'completed']
        valid_payment_statuses = ['unpaid', 'partial', 'paid', 'refunded']
        valid_sort_fields = ['name', 'registration_date', 'payment_status', 'amount_paid']
        
        if status_filter and status_filter not in valid_statuses:
            return jsonify({
                'success': False,
                'error': 'Invalid parameter',
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        if payment_status_filter and payment_status_filter not in valid_payment_statuses:
            return jsonify({
                'success': False,
                'error': 'Invalid parameter',
                'message': f'Invalid payment status. Must be one of: {", ".join(valid_payment_statuses)}'
            }), 400
        
        if sort_by not in valid_sort_fields:
            return jsonify({
                'success': False,
                'error': 'Invalid parameter',
                'message': f'Invalid sort field. Must be one of: {", ".join(valid_sort_fields)}'
            }), 400
        
        # Build query - Join TripRegistration with Participant
        query = db.session.query(TripRegistration, Participant)\
            .join(Participant, TripRegistration.participant_id == Participant.id)\
            .filter(TripRegistration.trip_id == trip_id)
        
        # Apply filters on TripRegistration
        if status_filter:
            query = query.filter(TripRegistration.status == status_filter)
        
        if payment_status_filter:
            query = query.filter(TripRegistration.payment_status == payment_status_filter)
        
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Participant.first_name.ilike(search_pattern),
                    Participant.last_name.ilike(search_pattern),
                    Participant.email.ilike(search_pattern)
                )
            )
        
        # Apply sorting
        if sort_by == 'name':
            sort_column = Participant.first_name
        elif sort_by == 'registration_date':
            sort_column = TripRegistration.registration_date
        elif sort_by == 'payment_status':
            sort_column = TripRegistration.payment_status
        elif sort_by == 'amount_paid':
            sort_column = TripRegistration.amount_paid
        
        if order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Paginate results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Calculate statistics
        all_registrations = TripRegistration.query.filter_by(trip_id=trip_id).all()
        total_participants = len(all_registrations)
        confirmed_count = len([r for r in all_registrations if r.status == 'confirmed'])
        paid_count = len([r for r in all_registrations if r.payment_status == 'paid'])
        
        # Serialize participants with registration data
        participants_data = []
        for registration, participant in pagination.items:
            # Get basic participant data
            data = {
                'id': participant.id,
                'full_name': participant.full_name,
                'first_name': participant.first_name,
                'last_name': participant.last_name,
                'email': participant.email,
                'age': participant.age,
                'grade_level': participant.grade_level,
                'photo_url': participant.photo_url,
                
                # Registration data from TripRegistration
                'status': registration.status,
                'payment_status': registration.payment_status,
                'registration_date': registration.registration_date.isoformat() if registration.registration_date else None,
                'registration_number': registration.registration_number,
                'amount_paid': float(registration.amount_paid or 0),
                'total_amount': float(registration.total_amount),
                'outstanding_balance': registration.outstanding_balance,
                
                # Consent status
                'has_all_consents': registration.consent_signed,
                'consent_signed': registration.consent_signed,
                'medical_form_submitted': registration.medical_form_submitted,
                
                # Parent info
                'parent': {
                    'id': participant.parent.id,
                    'full_name': participant.parent.full_name,
                    'email': participant.parent.email,
                    'phone': participant.parent.phone
                } if participant.parent else None
            }
            
            # Add latest location if available
            latest_location = participant.get_latest_location()
            data['latest_location'] = latest_location.serialize() if latest_location else None
            
            participants_data.append(data)
        
        # Log activity
        try:
            ActivityLog.log_action(
                action='view_participants',
                user_id=current_user.id,
                entity_type='trip',
                entity_id=trip_id,
                description=f'Viewed participants list for trip: {trip.title}',
                category='trip',
                trip_id=trip_id,
                meta_data={
                    'filters': {
                        'status': status_filter,
                        'payment_status': payment_status_filter,
                        'search': search_query
                    },
                    'page': page,
                    'per_page': per_page
                },
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                request_method=request.method,
                request_url=request.url
            )
        except Exception as log_error:
            # Don't fail the request if logging fails
            print(f"Logging error: {str(log_error)}")
        
        return jsonify({
            'success': True,
            'data': {
                'participants': participants_data,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                },
                'statistics': {
                    'total_participants': total_participants,
                    'confirmed_participants': confirmed_count,
                    'fully_paid': paid_count,
                    'trip_capacity': trip.max_participants
                },
                'trip': {
                    'id': trip.id,
                    'title': trip.title,
                    'start_date': trip.start_date.isoformat() if trip.start_date else None,
                    'end_date': trip.end_date.isoformat() if trip.end_date else None
                }
            }
        }), 200
    
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'An error occurred while fetching participants'
        }), 500
    
    except Exception as e:
        import traceback
        print("Unexpected Error:", str(e))
        traceback.print_exc() 

        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500


@teacher_participants_bp.route('/participant/<int:participant_id>', methods=['GET'])
@login_required
@roles_required('teacher')
def get_participant_details(participant_id):
    """
    Get detailed information about a specific participant
    
    Includes:
    - Basic participant information
    - Medical information
    - Emergency contacts
    - Payment history
    - Consent forms status
    - Location history
    """
    try:
        # Get participant
        participant = Participant.query.get(participant_id)
        
        if not participant:
            return jsonify({
                'success': False,
                'error': 'Participant not found',
                'message': f'No participant found with ID {participant_id}'
            }), 404
        
        # Get the registration for this participant (assuming single active registration)
        # registration = TripRegistration.query.filter_by(
        #     participant_id=participant_id
        # ).order_by(TripRegistration.registration_date.desc()).first()
        registration = (
            TripRegistration.query
            .join(Trip)  # join with the Trip model
            .filter(
                TripRegistration.participant_id == participant_id,
                Trip.organizer_id == current_user.id  
            )
            .order_by(TripRegistration.registration_date.desc())
            .first()
        )
        
        if not registration:
            return jsonify({
                'success': False,
                'error': 'Registration not found',
                'message': 'No registration found for this participant'
            }), 404
        
        # Verify trip ownership
        trip, error_response, status_code = verify_trip_ownership(registration.trip_id)
        if error_response:
            return jsonify(error_response), status_code
        
        # Build detailed participant data
        participant_data = {
            'id': participant.id,
            'full_name': participant.full_name,
            'first_name': participant.first_name,
            'last_name': participant.last_name,
            'date_of_birth': participant.date_of_birth.isoformat() if participant.date_of_birth else None,
            'age': participant.age,
            'grade_level': participant.grade_level,
            'student_id': participant.student_id,
            'gender': participant.gender,
            'school_name': participant.school_name,
            
            # Contact Information
            'contact': {
                'email': participant.email,
                'phone': participant.phone
            },
            
            # Medical Information
            'medical': {
                'conditions': participant.medical_conditions,
                'medications': participant.medications,
                'allergies': participant.allergies,
                'dietary_restrictions': participant.dietary_restrictions,
                'emergency_info': participant.emergency_medical_info,
                'blood_type': participant.blood_type,
                'doctor_name': participant.doctor_name,
                'doctor_phone': participant.doctor_phone
            },
            
            # Emergency Contacts
            'emergency_contacts': participant.emergency_contacts_list,
            
            # Status and Registration
            'status': registration.status,
            'registration_date': registration.registration_date.isoformat() if registration.registration_date else None,
            'registration_number': registration.registration_number,
            'confirmed_date': registration.confirmed_date.isoformat() if registration.confirmed_date else None,
            'cancelled_date': registration.cancelled_date.isoformat() if registration.cancelled_date else None,
            'cancellation_reason': registration.cancellation_reason,
            
            # Payment Information
            'payment': {
                'status': registration.payment_status,
                'amount_paid': float(registration.amount_paid or 0),
                'total_amount': float(registration.total_amount),
                'outstanding_balance': registration.outstanding_balance,
                'currency': registration.currency,
                'payment_plan': registration.payment_plan,
                'payment_deadline': registration.payment_deadline.isoformat() if registration.payment_deadline else None,
                'payment_history': [
                    {
                        'id': payment.id,
                        'amount': float(payment.amount),
                        'date': payment.payment_date.isoformat() if payment.payment_date else None,
                        'status': payment.status,
                        'payment_method': payment.payment_method,
                        'reference_number': payment.reference_number,
                        'transaction_id': payment.transaction_id
                    }
                    for payment in registration.payments.order_by(RegistrationPayment.payment_date.desc()).all()
                ]
            },
            
            # Consent Forms
            'consents': {
                'has_all_required': registration.is_documentation_complete,
                'consent_signed': registration.consent_signed,
                'medical_form_submitted': registration.medical_form_submitted,
                'forms': [
                    {
                        'id': consent.id,
                        'title': consent.title,
                        'is_signed': consent.is_signed,
                        'signed_date': consent.signed_date.isoformat() if consent.signed_at else None,
                        'signer_name': consent.signer_name,
                        'signer_relationship': consent.signer_relationship
                    }
                    for consent in participant.consents.all()
                ]
            },
            
            # Location Information
            'location': {
                'latest': participant.get_latest_location().serialize() if participant.get_latest_location() else None,
                'history_count': participant.locations.filter_by(is_valid=True).count()
            },
            
            # Special Requirements
            'special_requirements': participant.special_requirements,
            'behavioral_notes': participant.behavioral_notes,
            
            # Registration Notes
            'parent_notes': registration.parent_notes,
            'admin_notes': registration.admin_notes,
            
            # Trip Information
            'trip': {
                'id': trip.id,
                'title': trip.title,
                'start_date': trip.start_date.isoformat() if trip.start_date else None,
                'end_date': trip.end_date.isoformat() if trip.end_date else None,
                'price_per_student': float(trip.price_per_student)
            },
            
            # Parent Information
            'parent': {
                'id': participant.parent.id,
                'full_name': participant.parent.full_name,
                'email': participant.parent.email,
                'phone': participant.parent.phone
            } if participant.parent else None,
            
            # Timestamps
            'created_at': participant.created_at.isoformat() if participant.created_at else None,
            'updated_at': participant.updated_at.isoformat() if participant.updated_at else None
        }
        
        # Log activity
        try:
            ActivityLog.log_action(
                action='view_participant_details',
                user_id=current_user.id,
                entity_type='participant',
                entity_id=participant_id,
                description=f'Viewed details for participant: {participant.full_name}',
                category='user',
                trip_id=registration.trip_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                request_method=request.method,
                request_url=request.url
            )
        except Exception as log_error:
            print(f"Logging error: {str(log_error)}")
        
        return jsonify({
            'success': True,
            'data': participant_data
        }), 200
    
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'An error occurred while fetching participant details'
        }), 500
    
    except Exception as e:
        import traceback
        print("Unexpected Error:", str(e))
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500


@teacher_participants_bp.route('/participant/<int:participant_id>', methods=['DELETE'])
@login_required
@roles_required('teacher')
def delete_participant(participant_id):
    """
    Delete a participant registration from a trip
    
    Notes:
    - Deletes the TripRegistration record, not the Participant itself
    - Cannot delete confirmed participants without confirmation
    - Logs the deletion for audit purposes
    """
    try:
        # Get participant
        participant = Participant.query.get(participant_id)
        
        if not participant:
            return jsonify({
                'success': False,
                'error': 'Participant not found',
                'message': f'No participant found with ID {participant_id}'
            }), 404
        
        # Get the registration
        registration = TripRegistration.query.filter_by(
            participant_id=participant_id
        ).order_by(TripRegistration.registration_date.desc()).first()
        
        if not registration:
            return jsonify({
                'success': False,
                'error': 'Registration not found',
                'message': 'No registration found for this participant'
            }), 404
        
        # Verify trip ownership
        trip, error_response, status_code = verify_trip_ownership(registration.trip_id)
        if error_response:
            return jsonify(error_response), status_code
        
        # Check if force delete is requested for confirmed participants
        force_delete = request.args.get('force', 'false').lower() == 'true'
        
        if registration.status == 'confirmed' and not force_delete:
            return jsonify({
                'success': False,
                'error': 'Confirmation required',
                'message': 'This participant is confirmed. Use force=true to delete.',
                'data': {
                    'participant_id': participant_id,
                    'status': registration.status,
                    'requires_force': True
                }
            }), 400
        
        # Store data for logging before deletion
        participant_data = {
            'id': participant.id,
            'full_name': participant.full_name,
            'email': participant.email,
            'registration_id': registration.id,
            'registration_number': registration.registration_number,
            'status': registration.status,
            'payment_status': registration.payment_status,
            'amount_paid': float(registration.amount_paid or 0),
            'trip_id': registration.trip_id,
            'trip_title': trip.title
        }
        
        # Delete registration (this will cascade to payments)
        # Note: We're deleting the registration, not the participant
        # The participant record remains for historical purposes
        db.session.delete(registration)
        db.session.commit()
        
        # Log the deletion
        try:
            ActivityLog.log_action(
                action='participant_registration_deleted',
                user_id=current_user.id,
                entity_type='trip_registration',
                entity_id=registration.id,
                description=f'Deleted registration for participant: {participant_data["full_name"]} from trip: {trip.title}',
                category='booking',
                trip_id=registration.trip_id,
                old_values=participant_data,
                meta_data={
                    'force_delete': force_delete,
                    'deleted_by': current_user.full_name
                },
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                request_method=request.method,
                request_url=request.url
            )
        except Exception as log_error:
            # Don't fail the deletion if logging fails
            print(f"Logging error: {str(log_error)}")
        
        return jsonify({
            'success': True,
            'message': 'Participant registration deleted successfully',
            'data': {
                'deleted_registration': participant_data,
                'timestamp': db.func.now()
            }
        }), 200
    
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'An error occurred while deleting the participant registration'
        }), 500
    
    except Exception as e:
        db.session.rollback()
        import traceback
        print("Unexpected Error:", str(e))
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500