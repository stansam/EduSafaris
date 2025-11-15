from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date, timedelta
from sqlalchemy import func, case, extract, and_, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from decimal import Decimal, InvalidOperation
import traceback

from app.extensions import db
from app.models import (
    Trip, TripRegistration, User, ActivityLog, 
    ServiceBooking, Participant
)
from app.api import api_bp as admin_trips_bp 
from app.utils.utils import roles_required
from app.api.admin.trip.helpers import log_admin_action, build_trip_filters, get_request_metadata, apply_trip_sorting

# ============================================================================
# DECORATOR
# ============================================================================

def validate_pagination(f):
    """Decorator to validate and set pagination parameters"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            if page < 1:
                return jsonify({
                    'success': False,
                    'error': 'Page number must be greater than 0',
                    'code': 'INVALID_PAGINATION'
                }), 400
            
            if per_page < 1 or per_page > 100:
                return jsonify({
                    'success': False,
                    'error': 'Items per page must be between 1 and 100',
                    'code': 'INVALID_PAGINATION'
                }), 400
            
            kwargs['page'] = page
            kwargs['per_page'] = per_page
            return f(*args, **kwargs)
        except (ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': 'Invalid pagination parameters',
                'code': 'INVALID_PAGINATION'
            }), 400
    return decorated_function


@admin_trips_bp.route('/admin/trips', methods=['GET'])
@roles_required('admin')
@validate_pagination
def get_trips_list(page, per_page):
    """
    Get paginated list of trips with filtering and search
    
    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
        - status: Filter by status (comma-separated)
        - category: Filter by category (comma-separated)
        - destination: Filter by destination (partial match)
        - organizer_id: Filter by organizer
        - start_date_from: Filter trips starting from date (YYYY-MM-DD)
        - start_date_to: Filter trips starting until date (YYYY-MM-DD)
        - min_price: Minimum price filter
        - max_price: Maximum price filter
        - featured: Filter featured trips (true/false)
        - is_published: Filter published trips (true/false)
        - search: Search in title, description, destination
        - has_available_spots: Filter trips with available spots (true/false)
        - sort_by: Sort field (title, start_date, price, etc.)
        - sort_order: Sort order (asc/desc)
    """
    try:
        # Build base query
        query = Trip.query
        
        # Apply filters
        filters = request.args.to_dict()
        query = build_trip_filters(query, filters)
        
        # Apply sorting
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        query = apply_trip_sorting(query, sort_by, sort_order)
        
        # Execute pagination
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialize trips
        trips = [trip.serialize(include_details=False) for trip in pagination.items]
        
        # Add additional stats for each trip
        for trip_data in trips:
            trip = Trip.query.get(trip_data['id'])
            if trip:
                trip_data.update({
                    'pending_registrations': trip.pending_registrations_count,
                    'total_revenue': trip.get_total_revenue(),
                    'total_expenses': trip.get_total_expenses(),
                    'days_until_trip': trip.days_until_trip
                })
        
        return jsonify({
            'success': True,
            'data': {
                'trips': trips,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total_pages': pagination.pages,
                    'total_items': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                },
                'filters_applied': {
                    k: v for k, v in filters.items() 
                    if k not in ['page', 'per_page', 'sort_by', 'sort_order']
                }
            }
        }), 200
        
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in get_trips_list: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in get_trips_list: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


# ============================================================================
# TRIP DETAILS
# ============================================================================

@admin_trips_bp.route('/admin/trips/<int:trip_id>', methods=['GET'])
@roles_required('admin')
def get_admin_trip_details(trip_id):
    """
    Get detailed information about a specific trip
    """
    try:
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found',
                'code': 'TRIP_NOT_FOUND'
            }), 404
        
        # Get registrations with details
        registrations = TripRegistration.query.filter_by(trip_id=trip_id).all()
        registrations_data = [reg.serialize() for reg in registrations]
        
        # Get service bookings
        service_bookings = ServiceBooking.query.filter_by(trip_id=trip_id).all()
        bookings_data = [booking.serialize() for booking in service_bookings]
        
        # Get recent activity logs
        activity_logs = ActivityLog.get_trip_activity(trip_id, limit=20)
        activity_data = [log.serialize() for log in activity_logs]
        
        # Calculate financial summary
        financial_summary = {
            'total_revenue': trip.get_total_revenue(),
            'expected_revenue': trip.get_expected_revenue(),
            'total_expenses': trip.get_total_expenses(),
            'profit_estimate': trip.get_profit_estimate(),
            'currency': 'KES'
        }
        
        # Get registration statistics
        registration_stats = {
            'confirmed': trip.current_participants_count,
            'pending': trip.pending_registrations_count,
            'waitlisted': trip.registrations.filter_by(status='waitlisted').count(),
            'cancelled': trip.registrations.filter_by(status='cancelled').count(),
            'completed': trip.registrations.filter_by(status='completed').count(),
            'total': trip.registrations.count()
        }
        
        # Payment statistics
        payment_stats = {
            'fully_paid': trip.registrations.filter_by(payment_status='paid').count(),
            'partial': trip.registrations.filter_by(payment_status='partial').count(),
            'unpaid': trip.registrations.filter_by(payment_status='unpaid').count()
        }
        
        return jsonify({
            'success': True,
            'data': {
                'trip': trip.serialize(include_details=True),
                'registrations': registrations_data,
                'registration_stats': registration_stats,
                'payment_stats': payment_stats,
                'service_bookings': bookings_data,
                'financial_summary': financial_summary,
                'recent_activity': activity_data
            }
        }), 200
        
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in get_trip_details: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in get_trip_details: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


# ============================================================================
# UPDATE TRIP
# ============================================================================

@admin_trips_bp.route('/admin/trips/<int:trip_id>', methods=['PUT', 'PATCH'])
@roles_required('admin')
def update_trip_admin(trip_id):
    """
    Update trip information
    Admin can update any field
    """
    try:
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found',
                'code': 'TRIP_NOT_FOUND'
            }), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'code': 'NO_DATA'
            }), 400
        
        # Store old values for logging
        old_values = {}
        new_values = {}
        
        # Updatable fields with validation
        updatable_fields = {
            'title': str,
            'description': str,
            'destination': str,
            'destination_country': str,
            'category': str,
            'grade_level': str,
            'meeting_point': str,
            'max_participants': int,
            'min_participants': int,
            'price_per_student': Decimal,
            'deposit_amount': Decimal,
            'medical_info_required': bool,
            'consent_required': bool,
            'featured': bool,
            'is_published': bool,
            'transportation_included': bool,
            'meals_included': bool,
            'accommodation_included': bool,
            'insurance_required': bool,
            'allows_installments': bool,
            'cover_image_url': str,
            'refund_policy': str,
            'vaccination_requirements': str,
            'special_equipment_needed': str,
            'physical_requirements': str,
            'min_age': int,
            'max_age': int
        }
        
        # Date fields
        date_fields = {
            'start_date': 'start_date',
            'end_date': 'end_date',
            'registration_start_date': 'registration_start_date',
            'registration_deadline': 'registration_deadline',
            'deposit_deadline': 'deposit_deadline'
        }
        
        # JSON fields
        json_fields = ['itinerary', 'tags', 'learning_objectives', 
                      'subjects_covered', 'gallery_images', 'meals_provided']
        
        # Update simple fields
        for field, field_type in updatable_fields.items():
            if field in data:
                try:
                    old_values[field] = getattr(trip, field)
                    
                    if field_type == bool:
                        new_value = bool(data[field])
                    elif field_type == int:
                        new_value = int(data[field])
                    elif field_type == Decimal:
                        new_value = Decimal(str(data[field]))
                    else:
                        new_value = str(data[field])
                    
                    setattr(trip, field, new_value)
                    new_values[field] = new_value
                except (ValueError, TypeError, InvalidOperation) as e:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid value for field {field}: {str(e)}',
                        'code': 'INVALID_FIELD_VALUE'
                    }), 400
        
        # Update date fields
        for field, db_field in date_fields.items():
            if field in data:
                try:
                    old_values[field] = getattr(trip, db_field).isoformat() if getattr(trip, db_field) else None
                    
                    if data[field]:
                        date_value = datetime.strptime(data[field], '%Y-%m-%d').date()
                        setattr(trip, db_field, date_value)
                        new_values[field] = data[field]
                    else:
                        setattr(trip, db_field, None)
                        new_values[field] = None
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid date format for {field}. Use YYYY-MM-DD',
                        'code': 'INVALID_DATE_FORMAT'
                    }), 400
        
        # Update JSON fields
        for field in json_fields:
            if field in data:
                old_values[field] = getattr(trip, field)
                setattr(trip, field, data[field])
                new_values[field] = data[field]
        
        # Validation checks
        if trip.start_date and trip.end_date and trip.start_date > trip.end_date:
            return jsonify({
                'success': False,
                'error': 'End date must be after start date',
                'code': 'INVALID_DATE_RANGE'
            }), 400
        
        if trip.min_participants and trip.max_participants and trip.min_participants > trip.max_participants:
            return jsonify({
                'success': False,
                'error': 'Minimum participants cannot exceed maximum participants',
                'code': 'INVALID_PARTICIPANT_RANGE'
            }), 400
        
        if trip.min_age and trip.max_age and trip.min_age > trip.max_age:
            return jsonify({
                'success': False,
                'error': 'Minimum age cannot exceed maximum age',
                'code': 'INVALID_AGE_RANGE'
            }), 400
        
        # Commit changes
        db.session.commit()
        
        # Log the action
        log_admin_action(
            action='trip_updated',
            trip=trip,
            old_values=old_values,
            new_values=new_values,
            description=f"Admin updated trip '{trip.title}' (ID: {trip.id})"
        )
        
        return jsonify({
            'success': True,
            'message': 'Trip updated successfully',
            'data': {
                'trip': trip.serialize(include_details=True),
                'updated_fields': list(new_values.keys())
            }
        }), 200
        
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"Integrity error in update_trip: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database integrity error. Check for duplicate values.',
            'code': 'INTEGRITY_ERROR'
        }), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in update_trip: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in update_trip: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


# ============================================================================
# DELETE TRIP
# ============================================================================

@admin_trips_bp.route('/admin/trips/<int:trip_id>', methods=['DELETE'])
@roles_required('admin')
def delete_trip_admin(trip_id):
    """
    Delete a trip (soft delete by cancelling or hard delete if no registrations)
    """
    try:
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found',
                'code': 'TRIP_NOT_FOUND'
            }), 404
        
        # Check if trip has registrations
        registration_count = trip.registrations.count()
        force_delete = request.args.get('force', 'false').lower() == 'true'
        
        if registration_count > 0 and not force_delete:
            # Soft delete - cancel the trip
            old_status = trip.status
            trip.cancel_trip(reason="Deleted by administrator")
            
            log_admin_action(
                action='trip_cancelled',
                trip=trip,
                old_values={'status': old_status},
                new_values={'status': 'cancelled'},
                description=f"Admin cancelled trip '{trip.title}' (ID: {trip.id}) - had {registration_count} registrations"
            )
            
            return jsonify({
                'success': True,
                'message': 'Trip cancelled successfully (has registrations)',
                'data': {
                    'trip_id': trip.id,
                    'status': 'cancelled',
                    'registrations_count': registration_count,
                    'action': 'soft_delete'
                }
            }), 200
        else:
            # Hard delete - remove from database
            trip_data = {
                'id': trip.id,
                'title': trip.title,
                'status': trip.status,
                'organizer_id': trip.organizer_id
            }
            
            db.session.delete(trip)
            db.session.commit()
            
            log_admin_action(
                action='trip_deleted',
                old_values=trip_data,
                description=f"Admin permanently deleted trip '{trip_data['title']}' (ID: {trip_data['id']})"
            )
            
            return jsonify({
                'success': True,
                'message': 'Trip deleted successfully',
                'data': {
                    'trip_id': trip_id,
                    'action': 'hard_delete'
                }
            }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in delete_trip: {str(e)}")
        
        log_admin_action(
            action='trip_delete_failed',
            description=f"Failed to delete trip ID {trip_id}",
            status='failed',
            error_message=str(e)
        )
        
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in delete_trip: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


# ============================================================================
# STATUS MANAGEMENT
# ============================================================================

@admin_trips_bp.route('/admin/trips/<int:trip_id>/status', methods=['PATCH'])
@roles_required('admin')
def update_trip_status_admin(trip_id):
    """
    Update trip status (approve, cancel, publish, etc.)
    
    Body: {"status": "published", "reason": "optional reason for status change"}
    """
    try:
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found',
                'code': 'TRIP_NOT_FOUND'
            }), 404
        
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'error': 'Status is required',
                'code': 'MISSING_STATUS'
            }), 400
        
        new_status = data['status']
        reason = data.get('reason', '')
        
        valid_statuses = ['draft', 'published', 'registration_open', 'registration_closed',
                         'full', 'in_progress', 'completed', 'cancelled']
        
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
                'code': 'INVALID_STATUS'
            }), 400
        
        old_status = trip.status
        
        # Status transition validation
        if new_status == old_status:
            return jsonify({
                'success': False,
                'error': f'Trip is already in {new_status} status',
                'code': 'NO_STATUS_CHANGE'
            }), 400
        
        # Use appropriate method based on status
        if new_status == 'published':
            trip.publish()
        elif new_status == 'registration_open':
            trip.open_registration()
        elif new_status == 'registration_closed':
            trip.close_registration()
        elif new_status == 'in_progress':
            if not trip.can_start():
                return jsonify({
                    'success': False,
                    'error': 'Trip cannot be started. Check participant count and date requirements.',
                    'code': 'CANNOT_START_TRIP'
                }), 400
            trip.start_trip()
        elif new_status == 'completed':
            trip.complete_trip()
        elif new_status == 'cancelled':
            trip.cancel_trip(reason=reason)
        else:
            # Direct status update
            trip.status = new_status
            db.session.commit()
        
        log_admin_action(
            action='trip_status_changed',
            trip=trip,
            old_values={'status': old_status},
            new_values={'status': new_status, 'reason': reason},
            description=f"Admin changed trip '{trip.title}' status from {old_status} to {new_status}"
        )
        
        return jsonify({
            'success': True,
            'message': f'Trip status updated to {new_status}',
            'data': {
                'trip': trip.serialize(include_details=False),
                'old_status': old_status,
                'new_status': new_status
            }
        }), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'VALIDATION_ERROR'
        }), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in update_trip_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in update_trip_status: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


# ============================================================================
# FEATURE/UNFEATURE TRIP
# ============================================================================

@admin_trips_bp.route('/admin/trips/<int:trip_id>/feature', methods=['PATCH'])
@roles_required('admin')
def toggle_feature_trip_admin(trip_id):
    """
    Feature or unfeature a trip
    
    Body: {"featured": true/false}
    """
    try:
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found',
                'code': 'TRIP_NOT_FOUND'
            }), 404
        
        data = request.get_json()
        
        if data is None or 'featured' not in data:
            return jsonify({
                'success': False,
                'error': 'Featured status is required',
                'code': 'MISSING_FEATURED_STATUS'
            }), 400
        
        featured = bool(data['featured'])
        old_featured = trip.featured
        
        trip.featured = featured
        db.session.commit()
        
        action = 'featured' if featured else 'unfeatured'
        log_admin_action(
            action=f'trip_{action}',
            trip=trip,
            old_values={'featured': old_featured},
            new_values={'featured': featured},
            description=f"Admin {action} trip '{trip.title}' (ID: {trip.id})"
        )
        
        return jsonify({
            'success': True,
            'message': f'Trip {action} successfully',
            'data': {
                'trip_id': trip.id,
                'featured': featured
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in toggle_feature_trip: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in toggle_feature_trip: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


# ============================================================================
# TRIP STATISTICS
# ============================================================================

@admin_trips_bp.route('/admin/trips/statistics', methods=['GET'])
@roles_required('admin')
def get_trip_statistics():
    """
    Get comprehensive trip statistics and analytics
    
    Query Parameters:
        - period: 'week', 'month', 'quarter', 'year', 'all' (default: 'month')
        - start_date: Custom start date (YYYY-MM-DD)
        - end_date: Custom end date (YYYY-MM-DD)
    """
    try:
        period = request.args.get('period', 'month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Determine date range
        today = date.today()
        
        if start_date and end_date:
            try:
                date_from = datetime.strptime(start_date, '%Y-%m-%d').date()
                date_to = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD',
                    'code': 'INVALID_DATE_FORMAT'
                }), 400
        else:
            if period == 'week':
                date_from = today - timedelta(days=7)
                date_to = today
            elif period == 'quarter':
                date_from = today - timedelta(days=90)
                date_to = today
            elif period == 'year':
                date_from = today - timedelta(days=365)
                date_to = today
            elif period == 'all':
                date_from = None
                date_to = None
            else:  # month
                date_from = today - timedelta(days=30)
                date_to = today
        
        # Build base query
        base_query = Trip.query
        if date_from and date_to:
            base_query = base_query.filter(Trip.created_at.between(date_from, date_to))
        
        # Overall statistics
        total_trips = base_query.count()
        published_trips = base_query.filter_by(is_published=True).count()
        draft_trips = base_query.filter_by(status='draft').count()
        active_trips = base_query.filter(
            Trip.status.in_(['published', 'registration_open', 'in_progress'])
        ).count()
        completed_trips = base_query.filter_by(status='completed').count()
        cancelled_trips = base_query.filter_by(status='cancelled').count()
        
        # Status breakdown
        status_counts = db.session.query(
            Trip.status,
            func.count(Trip.id).label('count')
        ).filter(
            Trip.created_at.between(date_from, date_to) if date_from and date_to else True
        ).group_by(Trip.status).all()
        
        status_breakdown = {status: count for status, count in status_counts}
        
        # Category breakdown
        category_counts = db.session.query(
            Trip.category,
            func.count(Trip.id).label('count')
        ).filter(
            Trip.created_at.between(date_from, date_to) if date_from and date_to else True,
            Trip.category.isnot(None)
        ).group_by(Trip.category).all()
        
        category_breakdown = {cat: count for cat, count in category_counts}
        
        # Financial statistics
        total_revenue = db.session.query(
            func.sum(Trip.price_per_student * 
                func.coalesce(
                    db.session.query(func.count(TripRegistration.id))
                    .filter(
                        TripRegistration.trip_id == Trip.id,
                        TripRegistration.status == 'confirmed'
                    ).correlate(Trip).scalar_subquery(), 0
                )
            )
        ).filter(
            Trip.created_at.between(date_from, date_to) if date_from and date_to else True
        ).scalar() or 0
        
        # Participant statistics
        total_participants = db.session.query(
            func.count(TripRegistration.id)
        ).join(Trip).filter(
            TripRegistration.status == 'confirmed',
            Trip.created_at.between(date_from, date_to) if date_from and date_to else True
        ).scalar() or 0
        
        pending_registrations = db.session.query(
            func.count(TripRegistration.id)
        ).join(Trip).filter(
            TripRegistration.status == 'pending',
            Trip.created_at.between(date_from, date_to) if date_from and date_to else True
        ).scalar() or 0
        
        # Average statistics
        avg_price = db.session.query(
            func.avg(Trip.price_per_student)
        ).filter(
            Trip.created_at.between(date_from, date_to) if date_from and date_to else True
        ).scalar() or 0
        
        avg_participants = db.session.query(
            func.avg(
                db.session.query(func.count(TripRegistration.id))
                .filter(
                    TripRegistration.trip_id == Trip.id,
                    TripRegistration.status == 'confirmed'
                ).correlate(Trip).scalar_subquery()
            )
        ).filter(
            Trip.created_at.between(date_from, date_to) if date_from and date_to else True
        ).scalar() or 0
        
        # Capacity utilization
        capacity_stats = db.session.query(
            func.sum(Trip.max_participants).label('total_capacity'),
            func.sum(
                db.session.query(func.count(TripRegistration.id))
                .filter(
                    TripRegistration.trip_id == Trip.id,
                    TripRegistration.status == 'confirmed'
                ).correlate(Trip).scalar_subquery()
            ).label('total_filled')
        ).filter(
            Trip.created_at.between(date_from, date_to) if date_from and date_to else True,
            Trip.status != 'cancelled'
        ).first()
        
        capacity_utilization = 0
        if capacity_stats.total_capacity and capacity_stats.total_capacity > 0:
            capacity_utilization = (float(capacity_stats.total_filled or 0) / 
                                   float(capacity_stats.total_capacity)) * 100
        
        # Top destinations
        top_destinations = db.session.query(
            Trip.destination,
            func.count(Trip.id).label('count')
        ).filter(
            Trip.created_at.between(date_from, date_to) if date_from and date_to else True
        ).group_by(Trip.destination).order_by(func.count(Trip.id).desc()).limit(10).all()
        
        # Monthly trend (for charts)
        monthly_trend = db.session.query(
            extract('year', Trip.created_at).label('year'),
            extract('month', Trip.created_at).label('month'),
            func.count(Trip.id).label('count')
        ).filter(
            Trip.created_at.between(date_from, date_to) if date_from and date_to else True
        ).group_by('year', 'month').order_by('year', 'month').all()
        
        monthly_data = [
            {
                'year': int(row.year),
                'month': int(row.month),
                'count': row.count,
                'label': f"{int(row.year)}-{int(row.month):02d}"
            }
            for row in monthly_trend
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'type': period,
                    'start_date': date_from.isoformat() if date_from else None,
                    'end_date': date_to.isoformat() if date_to else None
                },
                'overview': {
                    'total_trips': total_trips,
                    'published_trips': published_trips,
                    'draft_trips': draft_trips,
                    'active_trips': active_trips,
                    'completed_trips': completed_trips,
                    'cancelled_trips': cancelled_trips,
                    'total_participants': total_participants,
                    'pending_registrations': pending_registrations,
                    'total_revenue': float(total_revenue),
                    'average_price': float(avg_price),
                    'average_participants': float(avg_participants),
                    'capacity_utilization': round(capacity_utilization, 2)
                },
                'breakdowns': {
                    'by_status': status_breakdown,
                    'by_category': category_breakdown,
                    'top_destinations': [
                        {'destination': dest, 'count': count}
                        for dest, count in top_destinations
                    ]
                },
                'trends': {
                    'monthly': monthly_data
                }
            }
        }), 200
        
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in get_trip_statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in get_trip_statistics: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


# ============================================================================
# GENERATE TRIP REPORT
# ============================================================================

@admin_trips_bp.route('/admin/trips/<int:trip_id>/report', methods=['GET'])
@roles_required('admin')
def generate_trip_report(trip_id):
    """
    Generate comprehensive report for a specific trip
    
    Query Parameters:
        - format: 'json' (default), 'summary' - future: 'pdf', 'excel'
        - include_participants: Include participant details (true/false)
        - include_financials: Include financial breakdown (true/false)
        - include_activity: Include activity log (true/false)
    """
    try:
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found',
                'code': 'TRIP_NOT_FOUND'
            }), 404
        
        report_format = request.args.get('format', 'json')
        include_participants = request.args.get('include_participants', 'true').lower() == 'true'
        include_financials = request.args.get('include_financials', 'true').lower() == 'true'
        include_activity = request.args.get('include_activity', 'true').lower() == 'true'
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'generated_by': current_user.serialize(),
            'trip': trip.serialize(include_details=True)
        }
        
        # Registration summary
        registrations = trip.registrations.all()
        report['registration_summary'] = {
            'total': len(registrations),
            'confirmed': sum(1 for r in registrations if r.status == 'confirmed'),
            'pending': sum(1 for r in registrations if r.status == 'pending'),
            'waitlisted': sum(1 for r in registrations if r.status == 'waitlisted'),
            'cancelled': sum(1 for r in registrations if r.status == 'cancelled'),
            'completed': sum(1 for r in registrations if r.status == 'completed')
        }
        
        # Participant details
        if include_participants:
            participants_data = []
            for reg in registrations:
                participant = reg.participant
                participants_data.append({
                    'registration_id': reg.id,
                    'registration_number': reg.registration_number,
                    'participant': {
                        'id': participant.id,
                        'full_name': participant.full_name,
                        'age': participant.age,
                        'grade_level': participant.grade_level,
                        'has_medical_info': participant.has_complete_medical_info
                    },
                    'parent': {
                        'id': reg.parent.id,
                        'full_name': reg.parent.full_name,
                        'email': reg.parent.email,
                        'phone': reg.parent.phone
                    },
                    'status': reg.status,
                    'payment_status': reg.payment_status,
                    'amount_paid': float(reg.amount_paid or 0),
                    'outstanding_balance': reg.outstanding_balance,
                    'registration_date': reg.registration_date.isoformat() if reg.registration_date else None
                })
            
            report['participants'] = participants_data
        
        # Financial breakdown
        if include_financials:
            # Revenue breakdown
            revenue_by_status = {
                'confirmed': sum(float(r.amount_paid or 0) for r in registrations if r.status == 'confirmed'),
                'pending': sum(float(r.amount_paid or 0) for r in registrations if r.status == 'pending'),
                'total_collected': sum(float(r.amount_paid or 0) for r in registrations)
            }
            
            expected_revenue = sum(float(r.total_amount) for r in registrations if r.status in ['confirmed', 'pending'])
            outstanding = expected_revenue - revenue_by_status['total_collected']
            
            # Expenses breakdown
            service_bookings = trip.service_bookings.all()
            expenses_by_type = {}
            total_expenses = 0
            
            for booking in service_bookings:
                if booking.status in ['confirmed', 'completed']:
                    amount = float(booking.total_amount or 0)
                    booking_type = booking.booking_type
                    expenses_by_type[booking_type] = expenses_by_type.get(booking_type, 0) + amount
                    total_expenses += amount
            
            report['financials'] = {
                'revenue': {
                    'expected': expected_revenue,
                    'collected': revenue_by_status['total_collected'],
                    'outstanding': outstanding,
                    'by_status': revenue_by_status
                },
                'expenses': {
                    'total': total_expenses,
                    'by_type': expenses_by_type,
                    'bookings_count': len(service_bookings)
                },
                'profit': {
                    'estimated': revenue_by_status['total_collected'] - total_expenses,
                    'margin_percentage': (
                        ((revenue_by_status['total_collected'] - total_expenses) / 
                         revenue_by_status['total_collected'] * 100)
                        if revenue_by_status['total_collected'] > 0 else 0
                    )
                },
                'currency': trip.currency if hasattr(trip, 'currency') else 'KES'
            }
        
        # Payment status breakdown
        payment_breakdown = {
            'fully_paid': sum(1 for r in registrations if r.payment_status == 'paid'),
            'partially_paid': sum(1 for r in registrations if r.payment_status == 'partial'),
            'unpaid': sum(1 for r in registrations if r.payment_status == 'unpaid'),
            'refunded': sum(1 for r in registrations if r.payment_status == 'refunded')
        }
        report['payment_breakdown'] = payment_breakdown
        
        # Documentation status
        documentation_status = {
            'consent_signed': sum(1 for r in registrations if r.consent_signed),
            'medical_submitted': sum(1 for r in registrations if r.medical_form_submitted),
            'fully_documented': sum(1 for r in registrations if r.is_documentation_complete)
        }
        report['documentation_status'] = documentation_status
        
        # Activity log
        if include_activity:
            activity_logs = ActivityLog.get_trip_activity(trip_id, limit=50)
            report['activity_log'] = [log.serialize() for log in activity_logs]
        
        # Service bookings summary
        bookings_summary = {
            'total': len(service_bookings),
            'confirmed': sum(1 for b in service_bookings if b.status == 'confirmed'),
            'pending': sum(1 for b in service_bookings if b.status == 'pending'),
            'completed': sum(1 for b in service_bookings if b.status == 'completed'),
            'cancelled': sum(1 for b in service_bookings if b.status == 'cancelled')
        }
        report['service_bookings_summary'] = bookings_summary
        
        # Trip timeline
        timeline = {
            'created': trip.created_at.isoformat() if trip.created_at else None,
            'registration_opens': trip.registration_start_date.isoformat() if trip.registration_start_date else None,
            'registration_deadline': trip.registration_deadline.isoformat() if trip.registration_deadline else None,
            'trip_starts': trip.start_date.isoformat() if trip.start_date else None,
            'trip_ends': trip.end_date.isoformat() if trip.end_date else None,
            'days_until_trip': trip.days_until_trip,
            'duration_days': trip.duration_days
        }
        report['timeline'] = timeline
        
        # Key metrics
        report['key_metrics'] = {
            'capacity_utilization': (
                (trip.current_participants_count / trip.max_participants * 100)
                if trip.max_participants > 0 else 0
            ),
            'registration_conversion': (
                (report['registration_summary']['confirmed'] / 
                 report['registration_summary']['total'] * 100)
                if report['registration_summary']['total'] > 0 else 0
            ),
            'documentation_completion': (
                (documentation_status['fully_documented'] / 
                 report['registration_summary']['total'] * 100)
                if report['registration_summary']['total'] > 0 else 0
            ),
            'payment_completion': (
                (payment_breakdown['fully_paid'] / 
                 report['registration_summary']['total'] * 100)
                if report['registration_summary']['total'] > 0 else 0
            )
        }
        
        # Log report generation
        log_admin_action(
            action='trip_report_generated',
            trip=trip,
            description=f"Admin generated report for trip '{trip.title}' (ID: {trip.id})",
            new_values={
                'format': report_format,
                'include_participants': include_participants,
                'include_financials': include_financials
            }
        )
        
        if report_format == 'summary':
            # Return condensed summary
            return jsonify({
                'success': True,
                'data': {
                    'trip': {
                        'id': trip.id,
                        'title': trip.title,
                        'status': trip.status
                    },
                    'registration_summary': report['registration_summary'],
                    'payment_breakdown': report['payment_breakdown'],
                    'key_metrics': report['key_metrics'],
                    'timeline': timeline
                }
            }), 200
        
        # Return full report
        return jsonify({
            'success': True,
            'data': report
        }), 200
        
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in generate_trip_report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in generate_trip_report: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


# ============================================================================
# BULK OPERATIONS
# ============================================================================

@admin_trips_bp.route('/admin/trips/bulk/status', methods=['PATCH'])
@roles_required('admin')
def bulk_update_status():
    """
    Update status for multiple trips
    
    Body: {
        "trip_ids": [1, 2, 3],
        "status": "published",
        "reason": "optional"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'trip_ids' not in data or 'status' not in data:
            return jsonify({
                'success': False,
                'error': 'trip_ids and status are required',
                'code': 'MISSING_REQUIRED_FIELDS'
            }), 400
        
        trip_ids = data['trip_ids']
        new_status = data['status']
        reason = data.get('reason', '')
        
        if not isinstance(trip_ids, list) or len(trip_ids) == 0:
            return jsonify({
                'success': False,
                'error': 'trip_ids must be a non-empty list',
                'code': 'INVALID_TRIP_IDS'
            }), 400
        
        valid_statuses = ['draft', 'published', 'registration_open', 'registration_closed',
                         'full', 'in_progress', 'completed', 'cancelled']
        
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
                'code': 'INVALID_STATUS'
            }), 400
        
        trips = Trip.query.filter(Trip.id.in_(trip_ids)).all()
        
        if len(trips) != len(trip_ids):
            return jsonify({
                'success': False,
                'error': 'Some trip IDs were not found',
                'code': 'TRIPS_NOT_FOUND'
            }), 404
        
        updated_trips = []
        failed_trips = []
        
        for trip in trips:
            try:
                old_status = trip.status
                trip.status = new_status
                db.session.flush()
                
                updated_trips.append({
                    'id': trip.id,
                    'title': trip.title,
                    'old_status': old_status,
                    'new_status': new_status
                })
            except Exception as e:
                failed_trips.append({
                    'id': trip.id,
                    'title': trip.title,
                    'error': str(e)
                })
        
        db.session.commit()
        
        log_admin_action(
            action='bulk_status_update',
            description=f"Admin updated status to {new_status} for {len(updated_trips)} trips",
            new_values={
                'status': new_status,
                'trip_ids': [t['id'] for t in updated_trips],
                'reason': reason
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated {len(updated_trips)} trips',
            'data': {
                'updated': updated_trips,
                'failed': failed_trips,
                'updated_count': len(updated_trips),
                'failed_count': len(failed_trips)
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in bulk_update_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in bulk_update_status: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500