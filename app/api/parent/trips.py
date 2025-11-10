from flask import request, jsonify, current_app
from flask_login import current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import and_, or_, func
from datetime import datetime, date
from decimal import Decimal

from app.extensions import db
from app.models import Trip, Participant, ActivityLog, TripRegistration
from app.utils.utils import roles_required
from app.api import api_bp as parent_trips_bp 

# Helper function for error responses
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

# Helper function for success responses
def success_response(data=None, message='Success', status_code=200):
    """Standardized success response"""
    return jsonify({
        'success': True,
        'message': message,
        'data': data
    }), status_code


# 1. Browse Available Trips
@parent_trips_bp.route('/parents/trips', methods=['GET'])
@roles_required('admin', 'parent')
def browse_trips():
    """
    Browse all available trips with pagination
    Query params: page, per_page, status, featured
    """
    try:
        user_id = current_user.id
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination
        if page < 1:
            return error_response('Page number must be greater than 0', 400)
        if per_page < 1 or per_page > 100:
            return error_response('Per page must be between 1 and 100', 400)
        
        # Build query
        query = Trip.query
        
        # Filter by status (default to active trips)
        status = request.args.get('status', 'active')
        if status:
            query = query.filter(Trip.status == status)
        
        # Filter by featured
        featured = request.args.get('featured', type=bool)
        if featured is not None:
            query = query.filter(Trip.featured == featured)
        
        # Only show trips with open registration
        show_all = request.args.get('show_all', False, type=bool)
        if not show_all:
            today = date.today()
            query = query.filter(
                and_(
                    Trip.status == 'active',
                    or_(
                        Trip.registration_deadline.is_(None),
                        Trip.registration_deadline >= today
                    ),
                    Trip.start_date > today
                )
            )
        
        # Order by start date
        query = query.order_by(Trip.start_date.asc())
        
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
            trip_dict['children_registered'] = Participant.query.filter_by(
                trip_id=trip.id,
                parent_id=user_id,
                status='confirmed'
            ).count()
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


# 2. Search and Filter Trips
@parent_trips_bp.route('/parent/trips/search', methods=['GET'])
@roles_required('admin', 'parent')
def search_trips():
    """
    Search and filter trips with multiple criteria
    Query params: q, destination, category, grade_level, min_price, max_price, 
                  start_date_from, start_date_to, page, per_page
    """
    try:
        user_id = current_user.id
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination
        if page < 1:
            return error_response('Page number must be greater than 0', 400)
        if per_page < 1 or per_page > 100:
            return error_response('Per page must be between 1 and 100', 400)
        
        # Build query
        query = Trip.query.filter(Trip.status == 'active')
        
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
        
        # Filter out full trips unless specified
        include_full = request.args.get('include_full', False, type=bool)
        if not include_full:
            # This requires a subquery to count participants
            query = query.filter(
                Trip.max_participants > (
                    db.session.query(func.count(Participant.id))
                    .filter(
                        Participant.trip_id == Trip.id,
                        Participant.status == 'confirmed'
                    )
                    .correlate(Trip)
                    .scalar_subquery()
                )
            )
        
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
            trip_dict['children_registered'] = Participant.query.filter_by(
                trip_id=trip.id,
                parent_id=user_id,
                status='confirmed'
            ).count()
            trips_data.append(trip_dict)
        
        return success_response({
            'trips': trips_data,
            'search_params': {
                'query': search_query,
                'destination': destination,
                'category': category,
                'grade_level': grade_level,
                'min_price': min_price,
                'max_price': max_price,
                'start_date_from': start_date_from.isoformat() if start_date_from else None,
                'start_date_to': start_date_to.isoformat() if start_date_to else None
            },
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
        current_app.logger.error(f"Error searching trips: {str(e)}", exc_info=True)
        return error_response('An error occurred while searching trips', 500)


# 3. View Trip Details
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
        
        # Get trip details
        trip_data = trip.serialize()
        
        # Add participant information for current user
        user_participants = Participant.query.filter_by(
            trip_id=trip_id,
            parent_id=user_id
        ).all()
        
        trip_data['user_participants'] = [p.serialize() for p in user_participants]
        trip_data['user_has_registrations'] = len(user_participants) > 0
        
        # Add availability information
        trip_data['spots_remaining'] = trip.available_spots
        trip_data['is_full'] = trip.is_full
        trip_data['can_register'] = trip.registration_open and not trip.is_full
        
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


# 4. View Trip Itinerary
@parent_trips_bp.route('/parent/trips/<int:trip_id>/itinerary', methods=['GET'])
@roles_required('admin', 'parent')
def get_trip_itinerary(trip_id):
    """Get detailed itinerary for a specific trip"""
    try:
        user_id = current_user.id
        
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


# 6. Cancel Trip Registration
@parent_trips_bp.route('/parent/trips/<int:trip_id>/registrations/<int:registration_id>/cancel', methods=['POST'])
@roles_required('admin', 'parent')
def cancel_registration(trip_id, registration_id):
    """Cancel a child's registration for a trip"""
    try:
        user_id = current_user.id
        data = request.get_json() or {}
        
        # Get participant
        # participant = Participant.query.get(participant_id)
        # if not participant:
        #     return error_response('Participant not found', 404)
        
        # # Verify ownership
        # if participant.parent_id != user_id:
        #     return error_response('You do not have permission to cancel this registration', 403)
        
        # # Verify trip match
        # if participant.trip_id != trip_id:
        #     return error_response('Participant does not belong to this trip', 400)
        
        # # Check if already cancelled
        # if participant.status == 'cancelled':
        #     return error_response('Registration is already cancelled', 400)
        
        # # Check if trip has already started or completed
        # trip = participant.trip
        # if trip.start_date <= date.today():
        #     return error_response('Cannot cancel registration for a trip that has already started', 400)
        
        # # Store old status for logging
        # old_status = participant.status
        
        # # Cancel registration
        # participant.cancel_participation()
        
        # # Add cancellation reason if provided
        # if data.get('cancellation_reason'):
        #     participant.internal_notes = f"Cancellation reason: {data['cancellation_reason']}"
        #     db.session.commit()

        # Get registration
        registration = TripRegistration.query.get(registration_id)
        if not registration:
            return error_response('Registration not found', 404)
        
        # Verify ownership
        if registration.parent_id != user_id:
            return error_response('You do not have permission to cancel this registration', 403)
        
        # Verify trip match
        if registration.trip_id != trip_id:
            return error_response('Registration does not belong to this trip', 400)
        
        # Check if already cancelled
        if registration.status == 'cancelled':
            return error_response('Registration is already cancelled', 400)
        
        # Check if trip has started
        trip = registration.trip
        if trip.start_date <= date.today():
            return error_response('Cannot cancel registration for a trip that has already started', 400)
        
        # Cancel registration
        old_status = registration.status
        registration.cancel_registration(data.get('cancellation_reason'))
        
        # Log activity
        try:
            # ActivityLog.log_action(
            #     action='participant_cancelled',
            #     user_id=user_id,
            #     entity_type='participant',
            #     entity_id=participant_id,
            #     description=f"Cancelled registration for {participant.full_name} from trip: {trip.title}",
            #     category='trip',
            #     trip_id=trip_id,
            #     old_values={'status': old_status},
            #     new_values={'status': 'cancelled'},
            #     metadata={'reason': data.get('cancellation_reason')},
            #     ip_address=request.remote_addr,
            #     user_agent=request.headers.get('User-Agent')
            # )
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


# 7. View Registration Status
@parent_trips_bp.route('/parent/trips/<int:trip_id>/participants', methods=['GET'])
@roles_required('admin', 'parent')
def get_trip_registrations(trip_id):
    """Get all participant registrations for a trip (for current parent)"""
    try:
        user_id = current_user.id
        
        # Verify trip exists
        trip = Trip.query.get(trip_id)
        if not trip:
            return error_response('Trip not found', 404)
        
        # Get all participants registered by this parent for this trip
        # participants = Participant.query.filter_by(
        #     trip_id=trip_id,
        #     parent_id=user_id
        # ).order_by(Participant.created_at.desc()).all()
        registrations = TripRegistration.query.filter_by(
            trip_id=trip_id,
            parent_id=user_id
        ).order_by(TripRegistration.created_at.desc()).all()
        registrations_data = [reg.serialize() for reg in registrations]

        
        # participants_data = []
        # for participant in participants:
        #     p_data = participant.serialize()
        #     # Add additional registration details
        #     p_data['has_medical_info'] = bool(
        #         participant.medical_conditions or 
        #         participant.medications or 
        #         participant.allergies
        #     )
        #     p_data['has_emergency_contacts'] = bool(
        #         participant.emergency_contact_1_name and 
        #         participant.emergency_contact_1_phone
        #     )
        #     participants_data.append(p_data)
        
        return success_response({
            'trip': trip.serialize(),
            'registrations': registrations_data,
            'total_registrations': len(registrations),
            'confirmed_count': len([p for p in registrations if p.status == 'confirmed']),
            'pending_count': len([p for p in registrations if p.status == 'pending']),
            'cancelled_count': len([p for p in registrations if p.status == 'cancelled'])
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting trip registrations: {str(e)}", exc_info=True)
        return error_response('An error occurred while fetching registrations', 500)


# 8. Add/Update Special Requirements
@parent_trips_bp.route('/parent/trips/<int:trip_id>/registrations/<int:registration_id>/requirements', methods=['PUT'])
@roles_required('admin', 'parent')
def update_special_requirements(trip_id, registration_id):
    """Add or update special requirements for a participant"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        if not data:
            return error_response('No data provided', 400)
        
        # Get participant
        # participant = Participant.query.get(participant_id)
        # if not participant:
        #     return error_response('Participant not found', 404)
        
        # # Verify ownership
        # if participant.parent_id != user_id:
        #     return error_response('You do not have permission to update this participant', 403)
        
        # # Verify trip match
        # if participant.trip_id != trip_id:
        #     return error_response('Participant does not belong to this trip', 400)

        registration = TripRegistration.query.get(registration_id)
        if not registration:
            return error_response('Registration not found', 404)
        
        # Verify ownership and trip match
        if registration.parent_id != user_id:
            return error_response('You do not have permission to update this registration', 403)
        
        if registration.trip_id != trip_id:
            return error_response('Registration does not belong to this trip', 400)
        
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
        
        # Update fields
        if 'special_requirements' in data:
            participant.special_requirements = data['special_requirements'].strip()
        
        if 'dietary_restrictions' in data:
            participant.dietary_restrictions = data['dietary_restrictions'].strip()
        
        if 'medical_conditions' in data:
            participant.medical_conditions = data['medical_conditions'].strip()
        
        if 'medications' in data:
            participant.medications = data['medications'].strip()
        
        if 'allergies' in data:
            participant.allergies = data['allergies'].strip()
        
        if 'emergency_medical_info' in data:
            participant.emergency_medical_info = data['emergency_medical_info'].strip()
        
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
                trip_id=trip_id,
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
            participant.serialize(),
            'Special requirements updated successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating special requirements: {str(e)}", exc_info=True)
        return error_response('An error occurred while updating special requirements', 500)


# 9. Get Trip Categories (Helper endpoint)
@parent_trips_bp.route('/parent/trips/categories', methods=['GET'])
@roles_required('admin', 'parent')
def get_trip_categories():
    """Get all available trip categories for filtering"""
    try:
        categories = db.session.query(Trip.category).distinct().filter(
            Trip.category.isnot(None),
            Trip.status == 'active'
        ).all()
        
        grade_levels = db.session.query(Trip.grade_level).distinct().filter(
            Trip.grade_level.isnot(None),
            Trip.status == 'active'
        ).all()
        
        return success_response({
            'categories': [cat[0] for cat in categories if cat[0]],
            'grade_levels': [level[0] for level in grade_levels if level[0]]
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
        
        # # Get all participants registered by this parent
        # participants = Participant.query.filter_by(
        #     parent_id=user_id
        # ).order_by(Participant.created_at.desc()).all()
        
        # registrations_data = []
        # for participant in participants:
        #     trip = participant.trip
        #     if not trip:
        #         continue
                
        #     registration = {
        #         'participant_id': participant.id,
        #         'participant_name': participant.full_name,
        #         'participant_status': participant.status,
        #         'trip_id': trip.id,
        #         'trip_title': trip.title,
        #         'destination': trip.destination,
        #         'start_date': trip.start_date.isoformat() if trip.start_date else None,
        #         'end_date': trip.end_date.isoformat() if trip.end_date else None,
        #         'duration_days': trip.duration_days,
        #         'price_per_student': float(trip.price_per_student) if trip.price_per_student else 0,
        #         'registration_date': participant.created_at.isoformat() if participant.created_at else None,
        #         'has_medical_info': bool(
        #             participant.medical_conditions or 
        #             participant.medications or 
        #             participant.allergies
        #         ),
        #         'has_dietary_info': bool(participant.dietary_restrictions),
        #         'has_special_requirements': bool(participant.special_requirements)
        #     }
        #     registrations_data.append(registration)
        
        # # Separate by status
        # active_registrations = [r for r in registrations_data if r['participant_status'] in ['registered', 'confirmed']]
        # cancelled_registrations = [r for r in registrations_data if r['participant_status'] == 'cancelled']
        
        # return success_response({
        #     'registrations': registrations_data,
        #     'active_registrations': active_registrations,
        #     'cancelled_registrations': cancelled_registrations,
        #     'total_count': len(registrations_data),
        #     'active_count': len(active_registrations),
        #     'cancelled_count': len(cancelled_registrations)
        # })

        registrations = TripRegistration.query.filter_by(
            parent_id=user_id
        ).order_by(TripRegistration.created_at.desc()).all()
        
        registrations_data = [reg.serialize() for reg in registrations]
        
        # Separate by status
        active_registrations = [r for r in registrations_data if r['status'] in ['pending', 'confirmed']]
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


