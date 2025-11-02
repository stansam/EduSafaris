from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.participant import Participant
from app.models.trip import Trip
from app.models.activity_log import ActivityLog

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


@teacher_participants_bp.route('/participants/trip/<int:trip_id>', methods=['GET'])
@login_required
@roles_required('teacher')
def get_trip_participants(trip_id):
    """
    Get all participants for a specific trip organized by the teacher
    
    Query Parameters:
    - status: Filter by participant status (registered, confirmed, cancelled, completed)
    - payment_status: Filter by payment status (pending, partial, paid, refunded)
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
        
        # Validate parameters
        valid_statuses = ['registered', 'confirmed', 'cancelled', 'completed']
        valid_payment_statuses = ['pending', 'partial', 'paid', 'refunded']
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
        
        # Build query
        query = Participant.query.filter_by(trip_id=trip_id)
        
        # Apply filters
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        if payment_status_filter:
            query = query.filter_by(payment_status=payment_status_filter)
        
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
            sort_column = Participant.registration_date
        elif sort_by == 'payment_status':
            sort_column = Participant.payment_status
        elif sort_by == 'amount_paid':
            sort_column = Participant.amount_paid
        
        if order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Paginate results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Calculate statistics
        total_participants = Participant.query.filter_by(trip_id=trip_id).count()
        confirmed_count = Participant.query.filter_by(trip_id=trip_id, status='confirmed').count()
        paid_count = Participant.query.filter_by(trip_id=trip_id, payment_status='paid').count()
        
        # Serialize participants
        participants_data = []
        for participant in pagination.items:
            data = participant.serialize()
            # Add additional calculated fields
            data['latest_location'] = participant.get_latest_location().serialize() if participant.get_latest_location() else None
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
                metadata={
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
                    'trip_capacity': trip.max_participants if hasattr(trip, 'max_participants') else None
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
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'An error occurred while fetching participants'
        }), 500
    
    except Exception as e:
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
        
        # Verify trip ownership
        trip, error_response, status_code = verify_trip_ownership(participant.trip_id)
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
                'emergency_info': participant.emergency_medical_info
            },
            
            # Emergency Contacts
            'emergency_contacts': [
                {
                    'name': participant.emergency_contact_1_name,
                    'phone': participant.emergency_contact_1_phone,
                    'relationship': participant.emergency_contact_1_relationship
                } if participant.emergency_contact_1_name else None,
                {
                    'name': participant.emergency_contact_2_name,
                    'phone': participant.emergency_contact_2_phone,
                    'relationship': participant.emergency_contact_2_relationship
                } if participant.emergency_contact_2_name else None
            ],
            
            # Status and Registration
            'status': participant.status,
            'registration_date': participant.registration_date.isoformat() if participant.registration_date else None,
            'confirmation_date': participant.confirmation_date.isoformat() if participant.confirmation_date else None,
            
            # Payment Information
            'payment': {
                'status': participant.payment_status,
                'amount_paid': float(participant.amount_paid) if participant.amount_paid else 0,
                'outstanding_balance': participant.outstanding_balance,
                'total_paid': participant.total_paid,
                'payment_history': [
                    {
                        'id': payment.id,
                        'amount': float(payment.amount),
                        'date': payment.created_at.isoformat() if payment.created_at else None,
                        'status': payment.status,
                        'payment_method': payment.payment_method if hasattr(payment, 'payment_method') else None
                    }
                    for payment in participant.payments.order_by(db.desc('created_at')).all()
                ]
            },
            
            # Consent Forms
            'consents': {
                'has_all_required': participant.has_all_consents(),
                'forms': [
                    {
                        'id': consent.id,
                        'title': consent.title if hasattr(consent, 'title') else None,
                        'is_signed': consent.is_signed,
                        'signed_date': consent.signed_at.isoformat() if hasattr(consent, 'signed_at') and consent.signed_at else None,
                        'signer_name': consent.signer_name if hasattr(consent, 'signer_name') else None
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
            'internal_notes': participant.internal_notes,
            
            # Trip Information
            'trip': {
                'id': trip.id,
                'title': trip.title,
                'start_date': trip.start_date.isoformat() if trip.start_date else None,
                'end_date': trip.end_date.isoformat() if trip.end_date else None,
                'price_per_student': float(trip.price_per_student) if hasattr(trip, 'price_per_student') and trip.price_per_student else None
            },
            
            # Parent Information
            'parent': participant.parent.serialize() if participant.parent else None,
            
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
                trip_id=participant.trip_id,
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
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'An error occurred while fetching participant details'
        }), 500
    
    except Exception as e:
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
    Delete a participant from a trip
    
    Notes:
    - This will also delete associated consents, payments, and locations due to cascade rules
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
        
        # Verify trip ownership
        trip, error_response, status_code = verify_trip_ownership(participant.trip_id)
        if error_response:
            return jsonify(error_response), status_code
        
        # Check if force delete is requested for confirmed participants
        force_delete = request.args.get('force', 'false').lower() == 'true'
        
        if participant.status == 'confirmed' and not force_delete:
            return jsonify({
                'success': False,
                'error': 'Confirmation required',
                'message': 'This participant is confirmed. Use force=true to delete.',
                'data': {
                    'participant_id': participant_id,
                    'status': participant.status,
                    'requires_force': True
                }
            }), 400
        
        # Store participant data for logging before deletion
        participant_data = {
            'id': participant.id,
            'full_name': participant.full_name,
            'email': participant.email,
            'status': participant.status,
            'payment_status': participant.payment_status,
            'amount_paid': float(participant.amount_paid) if participant.amount_paid else 0,
            'trip_id': participant.trip_id,
            'trip_title': trip.title
        }
        
        # Delete participant (cascades to related records)
        db.session.delete(participant)
        db.session.commit()
        
        # Log the deletion
        try:
            ActivityLog.log_action(
                action='participant_deleted',
                user_id=current_user.id,
                entity_type='participant',
                entity_id=participant_id,
                description=f'Deleted participant: {participant_data["full_name"]} from trip: {trip.title}',
                category='user',
                trip_id=participant.trip_id,
                old_values=participant_data,
                metadata={
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
            'message': 'Participant deleted successfully',
            'data': {
                'deleted_participant': participant_data,
                'timestamp': db.func.now()
            }
        }), 200
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'An error occurred while deleting the participant'
        }), 500
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500


