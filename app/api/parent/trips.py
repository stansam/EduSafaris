from flask import request, jsonify, current_app
from flask_login import current_user
from sqlalchemy import and_, or_, func
from datetime import datetime, date
from decimal import Decimal

from app.extensions import db
from app.models import Trip, Participant, ActivityLog, TripRegistration
from app.utils.utils import roles_required
from app.api import api_bp as parent_trips_bp 

def error_response(message, status_code=400, errors=None):
    """Standardized error response"""
    response = {
        'success': False,
        'message': message,
        'data': None
    }
    if errors:
        response['errors'] = errors
    return jsonify(response), status_code

def success_response(data=None, message='Success', status_code=200):
    """Standardized success response"""
    return jsonify({
        'success': True,
        'message': message,
        'data': data
    }), status_code


@parent_trips_bp.route('/parents/trips', methods=['GET'])
@roles_required('admin', 'parent')
def browse_trips():
    """
    Browse and search trips with pagination and filters
    Combines browsing and searching into one endpoint
    Query params: page, per_page, q, destination, category, grade_level, 
                  min_price, max_price, start_date_from, start_date_to, 
                  sort_by, sort_order
    """
    try:
        user_id = current_user.id
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 9, type=int)
        
        # Validate pagination
        if page < 1:
            return error_response('Page number must be greater than 0', 400)
        if per_page < 1 or per_page > 100:
            return error_response('Per page must be between 1 and 100', 400)
        
        # Build base query - only active/published trips
        query = Trip.query.filter(
            Trip.status.in_(['published', 'registration_open']),
            Trip.is_published == True
        )
        
        # Search query (title, description, destination)
        search_query = request.args.get('q', '').strip()
        if search_query:
            search_filter = or_(
                Trip.title.ilike(f'%{search_query}%'),
                Trip.description.ilike(f'%{search_query}%'),
                Trip.destination.ilike(f'%{search_query}%')
            )
            query = query.filter(search_filter)
        
        # Filter by destination
        destination = request.args.get('destination', '').strip()
        if destination:
            query = query.filter(Trip.destination.ilike(f'%{destination}%'))
        
        # Filter by category
        category = request.args.get('category', '').strip()
        if category:
            query = query.filter(Trip.category == category)
        
        # Filter by grade level
        grade_level = request.args.get('grade_level', '').strip()
        if grade_level:
            query = query.filter(Trip.grade_level == grade_level)
        
        # Filter by price range
        try:
            min_price = request.args.get('min_price', type=float)
            if min_price is not None:
                if min_price < 0:
                    return error_response('Minimum price cannot be negative', 400)
                query = query.filter(Trip.price_per_student >= min_price)
            
            max_price = request.args.get('max_price', type=float)
            if max_price is not None:
                if max_price < 0:
                    return error_response('Maximum price cannot be negative', 400)
                query = query.filter(Trip.price_per_student <= max_price)
            
            if min_price is not None and max_price is not None and min_price > max_price:
                return error_response('Minimum price cannot be greater than maximum price', 400)
        except ValueError:
            return error_response('Invalid price format', 400)
        
        # Filter by date range
        try:
            start_date_from = request.args.get('start_date_from')
            if start_date_from:
                start_date_from = datetime.strptime(start_date_from, '%Y-%m-%d').date()
                query = query.filter(Trip.start_date >= start_date_from)
            
            start_date_to = request.args.get('start_date_to')
            if start_date_to:
                start_date_to = datetime.strptime(start_date_to, '%Y-%m-%d').date()
                query = query.filter(Trip.start_date <= start_date_to)
            
            if start_date_from and start_date_to and start_date_from > start_date_to:
                return error_response('Start date from cannot be after start date to', 400)
        except ValueError:
            return error_response('Invalid date format. Use YYYY-MM-DD', 400)
        
        # Only show trips with future dates by default
        show_past = request.args.get('show_past', False, type=bool)
        if not show_past:
            today = date.today()
            query = query.filter(Trip.start_date > today)
        
        # Sort options
        sort_by = request.args.get('sort_by', 'start_date')
        sort_order = request.args.get('sort_order', 'asc')
        
        if sort_by == 'price':
            order_column = Trip.price_per_student
        elif sort_by == 'title':
            order_column = Trip.title
        elif sort_by == 'created_at':
            order_column = Trip.created_at
        else:
            order_column = Trip.start_date
        
        if sort_order == 'desc':
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        trips_data = []
        for trip in pagination.items:
            trip_dict = trip.serialize()
            
            # Add registration status for current user's children
            user_registrations = TripRegistration.query.filter_by(
                trip_id=trip.id,
                parent_id=user_id
            ).filter(
                TripRegistration.status.in_(['pending', 'confirmed', 'waitlisted'])
            ).all()
            
            trip_dict['user_registrations_count'] = len(user_registrations)
            trip_dict['user_registered_children'] = [
                {
                    'participant_id': reg.participant_id,
                    'participant_name': reg.participant.full_name,
                    'status': reg.status
                } for reg in user_registrations
            ]
            
            # Add availability info
            trip_dict['spots_remaining'] = trip.available_spots
            trip_dict['is_full'] = trip.is_full
            trip_dict['can_register'] = trip.registration_is_open and not trip.is_full
            
            trips_data.append(trip_dict)
        
        return success_response({
            'trips': trips_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error browsing trips: {str(e)}", exc_info=True)
        return error_response('An error occurred while fetching trips', 500)


@parent_trips_bp.route('/parent/trips/<int:trip_id>', methods=['GET'])
@roles_required('admin', 'parent')
def get_parent_trip_details(trip_id):
    """Get detailed information about a specific trip"""
    try:
        user_id = current_user.id
        
        # Get trip
        trip = Trip.query.get(trip_id)
        if not trip:
            return error_response('Trip not found', 404)
        
        # Get trip details with full information
        trip_data = trip.serialize(include_details=True)
        
        # Add participant information for current user
        user_registrations = TripRegistration.query.filter_by(
            trip_id=trip_id,
            parent_id=user_id
        ).all()
        
        trip_data['user_registrations'] = [reg.serialize() for reg in user_registrations]
        trip_data['user_has_registrations'] = len(user_registrations) > 0
        
        # Add availability information
        trip_data['spots_remaining'] = trip.available_spots
        trip_data['is_full'] = trip.is_full
        trip_data['can_register'] = trip.registration_is_open and not trip.is_full
        
        # Log activity
        try:
            ActivityLog.log_action(
                action='trip_viewed',
                user_id=user_id,
                entity_type='trip',
                entity_id=trip_id,
                description=f"Viewed trip details: {trip.title}",
                category='trip',
                trip_id=trip_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        except Exception as log_error:
            current_app.logger.warning(f"Failed to log activity: {str(log_error)}")
        
        return success_response(trip_data)
        
    except Exception as e:
        current_app.logger.error(f"Error getting trip details: {str(e)}", exc_info=True)
        return error_response('An error occurred while fetching trip details', 500)


@parent_trips_bp.route('/parent/trips/<int:trip_id>/itinerary', methods=['GET'])
@roles_required('admin', 'parent')
def get_trip_itinerary(trip_id):
    """Get detailed itinerary for a specific trip"""
    try:
        # Get trip
        trip = Trip.query.get(trip_id)
        if not trip:
            return error_response('Trip not found', 404)
        
        # Get itinerary
        itinerary_data = {
            'trip_id': trip.id,
            'trip_title': trip.title,
            'destination': trip.destination,
            'start_date': trip.start_date.isoformat() if trip.start_date else None,
            'end_date': trip.end_date.isoformat() if trip.end_date else None,
            'duration_days': trip.duration_days,
            'itinerary': trip.itinerary or []
        }
        
        return success_response(itinerary_data)
        
    except Exception as e:
        current_app.logger.error(f"Error getting trip itinerary: {str(e)}", exc_info=True)
        return error_response('An error occurred while fetching trip itinerary', 500)


@parent_trips_bp.route('/parent/registrations/<int:registration_id>/cancel', methods=['POST'])
@roles_required('admin', 'parent')
def cancel_registration(registration_id):
    """Cancel a child's registration for a trip"""
    try:
        user_id = current_user.id
        data = request.get_json() or {}

        # Get registration
        registration = TripRegistration.query.get(registration_id)
        if not registration:
            return error_response('Registration not found', 404)
        
        # Verify ownership
        if registration.parent_id != user_id:
            return error_response('You do not have permission to cancel this registration', 403)
        
        # Check if already cancelled
        if registration.status == 'cancelled':
            return error_response('Registration is already cancelled', 400)
        
        # Check if trip has started
        trip = registration.trip
        if trip.start_date <= date.today():
            return error_response('Cannot cancel registration for a trip that has already started', 400)
        
        # Cancel registration
        registration.cancel_registration(data.get('cancellation_reason'))
        
        # Log activity
        try:
            ActivityLog.log_trip_registration(registration, user_id, 'cancelled')
        except Exception as log_error:
            current_app.logger.warning(f"Failed to log activity: {str(log_error)}")
        
        return success_response(
            registration.serialize(),
            'Registration cancelled successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error cancelling registration: {str(e)}", exc_info=True)
        return error_response('An error occurred while cancelling registration', 500)


@parent_trips_bp.route('/parent/registrations/<int:registration_id>/requirements', methods=['PUT'])
@roles_required('admin', 'parent')
def update_special_requirements(registration_id):
    """Add or update special requirements for a participant"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        if not data:
            return error_response('No data provided', 400)

        registration = TripRegistration.query.get(registration_id)
        if not registration:
            return error_response('Registration not found', 404)
        
        # Verify ownership
        if registration.parent_id != user_id:
            return error_response('You do not have permission to update this registration', 403)
        
        # Update participant details
        participant = registration.participant
        
        # Store old values for logging
        old_values = {
            'special_requirements': participant.special_requirements,
            'dietary_restrictions': participant.dietary_restrictions,
            'medical_conditions': participant.medical_conditions,
            'medications': participant.medications,
            'allergies': participant.allergies
        }
        
        # Update fields if provided
        if 'special_requirements' in data:
            participant.special_requirements = data['special_requirements'].strip() if data['special_requirements'] else None
        
        if 'dietary_restrictions' in data:
            participant.dietary_restrictions = data['dietary_restrictions'].strip() if data['dietary_restrictions'] else None
        
        if 'medical_conditions' in data:
            participant.medical_conditions = data['medical_conditions'].strip() if data['medical_conditions'] else None
        
        if 'medications' in data:
            participant.medications = data['medications'].strip() if data['medications'] else None
        
        if 'allergies' in data:
            participant.allergies = data['allergies'].strip() if data['allergies'] else None
        
        if 'emergency_medical_info' in data:
            participant.emergency_medical_info = data['emergency_medical_info'].strip() if data['emergency_medical_info'] else None
        
        db.session.commit()
        
        # Log activity
        try:
            ActivityLog.log_action(
                action='participant_updated',
                user_id=user_id,
                entity_type='participant',
                entity_id=participant.id,
                description=f"Updated requirements for {participant.full_name}",
                category='trip',
                trip_id=registration.trip_id,
                old_values=old_values,
                new_values={
                    'special_requirements': participant.special_requirements,
                    'dietary_restrictions': participant.dietary_restrictions,
                    'medical_conditions': participant.medical_conditions,
                    'medications': participant.medications,
                    'allergies': participant.allergies
                },
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        except Exception as log_error:
            current_app.logger.warning(f"Failed to log activity: {str(log_error)}")
        
        return success_response(
            participant.serialize(include_sensitive=True),
            'Special requirements updated successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating special requirements: {str(e)}", exc_info=True)
        return error_response('An error occurred while updating special requirements', 500)


@parent_trips_bp.route('/parent/trips/categories', methods=['GET'])
@roles_required('admin', 'parent')
def get_trip_categories():
    """Get all available trip categories and grade levels for filtering"""
    try:
        categories = db.session.query(Trip.category).distinct().filter(
            Trip.category.isnot(None),
            Trip.status.in_(['published', 'registration_open']),
            Trip.is_published == True
        ).all()
        
        grade_levels = db.session.query(Trip.grade_level).distinct().filter(
            Trip.grade_level.isnot(None),
            Trip.status.in_(['published', 'registration_open']),
            Trip.is_published == True
        ).all()
        
        return success_response({
            'categories': sorted([cat[0] for cat in categories if cat[0]]),
            'grade_levels': sorted([level[0] for level in grade_levels if level[0]])
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting trip categories: {str(e)}", exc_info=True)
        return error_response('An error occurred while fetching categories', 500)


@parent_trips_bp.route('/parent/registrations', methods=['GET'])
@roles_required('admin', 'parent')
def get_all_registrations():
    """Get all registrations for the current parent across all trips"""
    try:
        user_id = current_user.id
        
        # Get all registrations by this parent
        registrations = TripRegistration.query.filter_by(
            parent_id=user_id
        ).order_by(TripRegistration.created_at.desc()).all()
        
        registrations_data = []
        for reg in registrations:
            reg_dict = reg.serialize()
            # Add additional trip info for display
            if reg.trip:
                reg_dict['trip_id'] = reg.trip.id
                reg_dict['trip_title'] = reg.trip.title
                reg_dict['destination'] = reg.trip.destination
                reg_dict['start_date'] = reg.trip.start_date.isoformat() if reg.trip.start_date else None
                reg_dict['duration_days'] = reg.trip.duration_days
                reg_dict['price_per_student'] = float(reg.trip.price_per_student)
            
            # Add participant info
            if reg.participant:
                reg_dict['participant_name'] = reg.participant.full_name
                reg_dict['participant_status'] = reg.status
            
            registrations_data.append(reg_dict)
        
        # Separate by status
        active_registrations = [r for r in registrations_data if r['status'] in ['pending', 'confirmed', 'waitlisted']]
        cancelled_registrations = [r for r in registrations_data if r['status'] == 'cancelled']
        completed_registrations = [r for r in registrations_data if r['status'] == 'completed']
        
        return success_response({
            'registrations': registrations_data,
            'active_registrations': active_registrations,
            'cancelled_registrations': cancelled_registrations,
            'completed_registrations': completed_registrations,
            'total_count': len(registrations_data),
            'active_count': len(active_registrations),
            'cancelled_count': len(cancelled_registrations),
            'completed_count': len(completed_registrations)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting registrations: {str(e)}", exc_info=True)
        return error_response('An error occurred while fetching registrations', 500)