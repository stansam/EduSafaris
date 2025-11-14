from flask import request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.service_booking import ServiceBooking
from app.models.user import User
from app.models.vendor import Vendor
from app.models.activity_log import ActivityLog
from app.api.vendor.booking_utils import serialize_booking_detailed, log_booking_action
from app.utils.utils import roles_required
from app.api import api_bp as vendor_booking_bp 



def validate_booking_access(f):
    """Decorator to validate vendor owns the booking"""
    @wraps(f)
    def decorated_function(booking_id, *args, **kwargs):
        try:
            booking = ServiceBooking.query.get(booking_id)
            
            if not booking:
                return jsonify({
                    'success': False,
                    'error': 'Booking not found',
                    'code': 'BOOKING_NOT_FOUND'
                }), 404
            
            if booking.vendor_id != current_user.vendor_profile.id:
                return jsonify({
                    'success': False,
                    'error': 'Access denied to this booking',
                    'code': 'ACCESS_DENIED'
                }), 403
            
            # Pass booking to the route function
            return f(booking_id, booking, *args, **kwargs)
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Database error occurred',
                'code': 'DATABASE_ERROR'
            }), 500
    
    return decorated_function


@vendor_booking_bp.route('/vendor/bookings', methods=['GET'])
@login_required
@roles_required('vendor')
def get_bookings():
    """
    Get all booking requests for vendor with filtering and pagination
    
    Query Parameters:
    - status: Filter by status (pending, confirmed, in_progress, completed, cancelled)
    - booking_type: Filter by type (transportation, accommodation, activity)
    - start_date: Filter bookings starting from this date (YYYY-MM-DD)
    - end_date: Filter bookings ending before this date (YYYY-MM-DD)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    - sort: Sort by (booking_date, service_start_date, status) default: booking_date
    - order: Sort order (asc, desc) default: desc
    """
    try:
        vendor = current_user.vendor_profile
        
        # Build base query
        query = ServiceBooking.query.filter_by(vendor_id=vendor.id)
        
        # Apply filters
        status = request.args.get('status')
        if status:
            valid_statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
            if status not in valid_statuses:
                return jsonify({
                    'success': False,
                    'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
                    'code': 'INVALID_STATUS'
                }), 400
            query = query.filter_by(status=status)
        
        booking_type = request.args.get('booking_type')
        if booking_type:
            valid_types = ['transportation', 'accommodation', 'activity']
            if booking_type not in valid_types:
                return jsonify({
                    'success': False,
                    'error': f'Invalid booking type. Must be one of: {", ".join(valid_types)}',
                    'code': 'INVALID_BOOKING_TYPE'
                }), 400
            query = query.filter_by(booking_type=booking_type)
        
        # Date filters
        start_date = request.args.get('start_date')
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(ServiceBooking.service_start_date >= start_date_obj)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid start_date format. Use YYYY-MM-DD',
                    'code': 'INVALID_DATE_FORMAT'
                }), 400
        
        end_date = request.args.get('end_date')
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(ServiceBooking.service_end_date <= end_date_obj)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid end_date format. Use YYYY-MM-DD',
                    'code': 'INVALID_DATE_FORMAT'
                }), 400
        
        # Sorting
        sort_by = request.args.get('sort', 'booking_date')
        order = request.args.get('order', 'desc')
        
        valid_sort_fields = ['booking_date', 'service_start_date', 'status']
        if sort_by not in valid_sort_fields:
            sort_by = 'booking_date'
        
        if order == 'asc':
            query = query.order_by(getattr(ServiceBooking, sort_by).asc())
        else:
            query = query.order_by(getattr(ServiceBooking, sort_by).desc())
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 20
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Statistics
        stats = {
            'pending': ServiceBooking.query.filter_by(
                vendor_id=vendor.id, status='pending'
            ).count(),
            'confirmed': ServiceBooking.query.filter_by(
                vendor_id=vendor.id, status='confirmed'
            ).count(),
            'in_progress': ServiceBooking.query.filter_by(
                vendor_id=vendor.id, status='in_progress'
            ).count(),
            'completed': ServiceBooking.query.filter_by(
                vendor_id=vendor.id, status='completed'
            ).count(),
            'total': ServiceBooking.query.filter_by(vendor_id=vendor.id).count()
        }
        
        return jsonify({
            'success': True,
            'data': {
                'bookings': [serialize_booking_detailed(b) for b in pagination.items],
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                },
                'statistics': stats
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


@vendor_booking_bp.route('/vendor/bookings/<int:booking_id>', methods=['GET'])
@login_required
@roles_required('vendor')
@validate_booking_access
def get_vendor_booking_details(booking_id, booking):
    """Get detailed information about a specific booking"""
    try:
        return jsonify({
            'success': True,
            'data': serialize_booking_detailed(booking)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


@vendor_booking_bp.route('/vendor/bookings/<int:booking_id>/accept', methods=['POST'])
@login_required
@roles_required('vendor')
@validate_booking_access
def accept_booking(booking_id, booking):
    """
    Accept a booking request
    
    Request Body:
    - final_amount (optional): Final confirmed amount
    - notes (optional): Additional notes for acceptance
    """
    try:
        # Validate current status
        if booking.status != 'pending':
            return jsonify({
                'success': False,
                'error': f'Cannot accept booking in {booking.status} status',
                'code': 'INVALID_STATUS_TRANSITION'
            }), 400
        
        data = request.get_json() or {}
        
        # Validate final amount if provided
        final_amount = data.get('final_amount')
        if final_amount is not None:
            try:
                final_amount = float(final_amount)
                if final_amount <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'Final amount must be greater than 0',
                        'code': 'INVALID_AMOUNT'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Invalid final amount format',
                    'code': 'INVALID_AMOUNT'
                }), 400
        
        # Accept the booking
        booking.confirm_booking(final_amount=final_amount)
        
        # Update notes if provided
        if data.get('notes'):
            booking.notes = f"{booking.notes}\n\nVendor Acceptance Notes: {data['notes']}" if booking.notes else f"Vendor Acceptance Notes: {data['notes']}"
            db.session.commit()
        
        # Log the action
        log_booking_action(
            booking=booking,
            action='accepted',
            description=f"Booking accepted by vendor {current_user.vendor_profile.business_name}",
            user_id=current_user.id,
            metadata={'final_amount': final_amount}
        )
        
        # TODO: Send notification to trip organizer
        
        return jsonify({
            'success': True,
            'message': 'Booking accepted successfully',
            'data': serialize_booking_detailed(booking)
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'VALIDATION_ERROR'
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


@vendor_booking_bp.route('/vendor/bookings/<int:booking_id>/reject', methods=['POST'])
@login_required
@roles_required('vendor')
@validate_booking_access
def reject_booking(booking_id, booking):
    """
    Reject a booking request
    
    Request Body:
    - reason (required): Reason for rejection
    """
    try:
        # Validate current status
        if booking.status != 'pending':
            return jsonify({
                'success': False,
                'error': f'Cannot reject booking in {booking.status} status',
                'code': 'INVALID_STATUS_TRANSITION'
            }), 400
        
        data = request.get_json() or {}
        reason = data.get('reason', '').strip()
        
        if not reason:
            return jsonify({
                'success': False,
                'error': 'Rejection reason is required',
                'code': 'REASON_REQUIRED'
            }), 400
        
        if len(reason) < 10:
            return jsonify({
                'success': False,
                'error': 'Rejection reason must be at least 10 characters',
                'code': 'REASON_TOO_SHORT'
            }), 400
        
        # Cancel the booking
        booking.cancel_booking(reason=f"Rejected by vendor: {reason}")
        
        # Log the action
        log_booking_action(
            booking=booking,
            action='rejected',
            description=f"Booking rejected by vendor {current_user.vendor_profile.business_name}",
            user_id=current_user.id,
            metadata={'reason': reason}
        )
        
        # TODO: Send notification to trip organizer
        
        return jsonify({
            'success': True,
            'message': 'Booking rejected successfully',
            'data': serialize_booking_detailed(booking)
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'VALIDATION_ERROR'
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


@vendor_booking_bp.route('/vendor/bookings/<int:booking_id>/status', methods=['PUT'])
@login_required
@roles_required('vendor')
@validate_booking_access
def update_booking_status(booking_id, booking):
    """
    Update booking status
    
    Request Body:
    - status (required): New status (in_progress, completed)
    - notes (optional): Additional notes
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required',
                'code': 'MISSING_DATA'
            }), 400
        
        new_status = data.get('status')
        if not new_status:
            return jsonify({
                'success': False,
                'error': 'Status is required',
                'code': 'STATUS_REQUIRED'
            }), 400
        
        # Validate status transitions
        valid_transitions = {
            'pending': [],  # Can only accept or reject
            'confirmed': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': []
        }
        
        if new_status not in valid_transitions.get(booking.status, []):
            return jsonify({
                'success': False,
                'error': f'Cannot change status from {booking.status} to {new_status}',
                'code': 'INVALID_STATUS_TRANSITION'
            }), 400
        
        old_status = booking.status
        
        # Handle status change
        if new_status == 'in_progress':
            booking.status = 'in_progress'
            db.session.commit()
        elif new_status == 'completed':
            booking.complete_booking()
        elif new_status == 'cancelled':
            reason = data.get('cancellation_reason', '').strip()
            if not reason:
                return jsonify({
                    'success': False,
                    'error': 'Cancellation reason is required',
                    'code': 'REASON_REQUIRED'
                }), 400
            booking.cancel_booking(reason=reason)
        
        # Add notes if provided
        notes = data.get('notes', '').strip()
        if notes:
            booking.notes = f"{booking.notes}\n\nStatus Update Notes: {notes}" if booking.notes else f"Status Update Notes: {notes}"
            db.session.commit()
        
        # Log the action
        log_booking_action(
            booking=booking,
            action='status_updated',
            description=f"Status changed from {old_status} to {new_status}",
            user_id=current_user.id,
            metadata={'old_status': old_status, 'new_status': new_status}
        )
        
        return jsonify({
            'success': True,
            'message': f'Booking status updated to {new_status}',
            'data': serialize_booking_detailed(booking)
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


@vendor_booking_bp.route('/vendor/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@roles_required('vendor')
@validate_booking_access
def cancel_service_booking(booking_id, booking):
    """
    Cancel a booking
    
    Request Body:
    - reason (required): Reason for cancellation
    """
    try:
        if not booking.can_be_cancelled():
            return jsonify({
                'success': False,
                'error': f'Cannot cancel booking in {booking.status} status',
                'code': 'CANNOT_CANCEL'
            }), 400
        
        data = request.get_json() or {}
        reason = data.get('reason', '').strip()
        
        if not reason:
            return jsonify({
                'success': False,
                'error': 'Cancellation reason is required',
                'code': 'REASON_REQUIRED'
            }), 400
        
        if len(reason) < 10:
            return jsonify({
                'success': False,
                'error': 'Cancellation reason must be at least 10 characters',
                'code': 'REASON_TOO_SHORT'
            }), 400
        
        # Cancel the booking
        booking.cancel_booking(reason=f"Cancelled by vendor: {reason}")
        
        # Log the action
        log_booking_action(
            booking=booking,
            action='cancelled',
            description=f"Booking cancelled by vendor {current_user.vendor_profile.business_name}",
            user_id=current_user.id,
            metadata={'reason': reason}
        )
        
        # TODO: Send notification to trip organizer
        # TODO: Handle refund if payment was made
        
        return jsonify({
            'success': True,
            'message': 'Booking cancelled successfully',
            'data': serialize_booking_detailed(booking)
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


@vendor_booking_bp.route('/vendor/bookings/<int:booking_id>/modification-request', methods=['POST'])
@login_required
@roles_required('vendor')
@validate_booking_access
def request_modification(booking_id, booking):
    """
    Request modification to a booking
    
    Request Body:
    - modification_type (required): Type of modification (dates, pricing, requirements, other)
    - details (required): Details of requested modification
    - suggested_dates (optional): New suggested dates {start_date, end_date}
    - suggested_amount (optional): New suggested amount
    """
    try:
        if booking.status not in ['pending', 'confirmed']:
            return jsonify({
                'success': False,
                'error': f'Cannot request modification for booking in {booking.status} status',
                'code': 'INVALID_STATUS'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required',
                'code': 'MISSING_DATA'
            }), 400
        
        modification_type = data.get('modification_type', '').strip()
        details = data.get('details', '').strip()
        
        valid_types = ['dates', 'pricing', 'requirements', 'other']
        if modification_type not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid modification type. Must be one of: {", ".join(valid_types)}',
                'code': 'INVALID_MODIFICATION_TYPE'
            }), 400
        
        if not details:
            return jsonify({
                'success': False,
                'error': 'Modification details are required',
                'code': 'DETAILS_REQUIRED'
            }), 400
        
        if len(details) < 20:
            return jsonify({
                'success': False,
                'error': 'Modification details must be at least 20 characters',
                'code': 'DETAILS_TOO_SHORT'
            }), 400
        
        # Prepare modification request data
        modification_data = {
            'type': modification_type,
            'details': details,
            'requested_by': 'vendor',
            'vendor_name': current_user.vendor_profile.business_name,
            'request_date': datetime.now().isoformat()
        }
        
        # Handle date modification
        if modification_type == 'dates':
            suggested_dates = data.get('suggested_dates', {})
            start_date = suggested_dates.get('start_date')
            end_date = suggested_dates.get('end_date')
            
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                    modification_data['suggested_start_date'] = start_date
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid start_date format. Use YYYY-MM-DD',
                        'code': 'INVALID_DATE_FORMAT'
                    }), 400
            
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                    modification_data['suggested_end_date'] = end_date
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid end_date format. Use YYYY-MM-DD',
                        'code': 'INVALID_DATE_FORMAT'
                    }), 400
        
        # Handle pricing modification
        if modification_type == 'pricing':
            suggested_amount = data.get('suggested_amount')
            if suggested_amount is not None:
                try:
                    suggested_amount = float(suggested_amount)
                    if suggested_amount <= 0:
                        return jsonify({
                            'success': False,
                            'error': 'Suggested amount must be greater than 0',
                            'code': 'INVALID_AMOUNT'
                        }), 400
                    modification_data['suggested_amount'] = suggested_amount
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'error': 'Invalid suggested amount format',
                        'code': 'INVALID_AMOUNT'
                    }), 400
        
        # Add modification request to booking notes
        modification_text = f"\n\n--- MODIFICATION REQUEST ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ---\n"
        modification_text += f"Type: {modification_type}\n"
        modification_text += f"Details: {details}\n"
        if modification_data.get('suggested_start_date'):
            modification_text += f"Suggested Start Date: {modification_data['suggested_start_date']}\n"
        if modification_data.get('suggested_end_date'):
            modification_text += f"Suggested End Date: {modification_data['suggested_end_date']}\n"
        if modification_data.get('suggested_amount'):
            modification_text += f"Suggested Amount: {modification_data['suggested_amount']} {booking.currency}\n"
        
        booking.notes = f"{booking.notes}{modification_text}" if booking.notes else modification_text
        db.session.commit()
        
        # Log the action
        ActivityLog.log_action(
            action='modification_requested',
            user_id=current_user.id,
            entity_type='service_booking',
            entity_id=booking.id,
            description=f"Modification requested by vendor for booking #{booking.id}",
            category='vendor_booking',
            trip_id=booking.trip_id,
            new_values=modification_data
        )
        
        # TODO: Send notification to trip organizer
        
        return jsonify({
            'success': True,
            'message': 'Modification request submitted successfully',
            'data': {
                'booking': serialize_booking_detailed(booking),
                'modification_request': modification_data
            }
        }), 200
        
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


@vendor_booking_bp.route('/vendor/bookings/calendar', methods=['GET'])
@login_required
@roles_required('vendor')
def get_booking_calendar():
    """
    Get calendar view of bookings
    
    Query Parameters:
    - start_date (required): Start date for calendar (YYYY-MM-DD)
    - end_date (required): End date for calendar (YYYY-MM-DD)
    - view: Calendar view type (month, week, day) default: month
    """
    try:
        vendor = current_user.vendor_profile
        
        # Get date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            # Default to current month
            from datetime import date
            today = date.today()
            start_date = date(today.year, today.month, 1).isoformat()
            # Last day of month
            if today.month == 12:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
            end_date = end_date.isoformat()
        
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD',
                'code': 'INVALID_DATE_FORMAT'
            }), 400
        
        if start_date_obj > end_date_obj:
            return jsonify({
                'success': False,
                'error': 'Start date must be before end date',
                'code': 'INVALID_DATE_RANGE'
            }), 400
        
        # Limit range to 1 year
        if (end_date_obj - start_date_obj).days > 365:
            return jsonify({
                'success': False,
                'error': 'Date range cannot exceed 365 days',
                'code': 'DATE_RANGE_TOO_LARGE'
            }), 400
        
        # Get bookings in date range
        bookings = ServiceBooking.query.filter(
            ServiceBooking.vendor_id == vendor.id,
            ServiceBooking.status.in_(['confirmed', 'in_progress']),
            or_(
                and_(
                    ServiceBooking.service_start_date >= start_date_obj,
                    ServiceBooking.service_start_date <= end_date_obj
                ),
                and_(
                    ServiceBooking.service_end_date >= start_date_obj,
                    ServiceBooking.service_end_date <= end_date_obj
                ),
                and_(
                    ServiceBooking.service_start_date <= start_date_obj,
                    ServiceBooking.service_end_date >= end_date_obj
                )
            )
        ).all()
        
        # Format calendar events
        events = []
        for booking in bookings:
            event = {
                'id': booking.id,
                'title': f"{booking.booking_type.title()} - {booking.trip.title if booking.trip else 'N/A'}",
                'start': booking.service_start_date.isoformat() if booking.service_start_date else None,
                'end': booking.service_end_date.isoformat() if booking.service_end_date else None,
                'status': booking.status,
                'booking_type': booking.booking_type,
                'amount': float(booking.total_amount) if booking.total_amount else None,
                'payment_status': booking.payment_status,
                'trip': {
                    'id': booking.trip.id,
                    'title': booking.trip.title
                } if booking.trip else None,
                'color': _get_event_color(booking.status)
            }
            events.append(event)
        
        # Get availability summary
        availability = _calculate_availability(vendor, start_date_obj, end_date_obj, bookings)
        
        return jsonify({
            'success': True,
            'data': {
                'events': events,
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'availability': availability,
                'summary': {
                    'total_bookings': len(events),
                    'confirmed': len([e for e in events if e['status'] == 'confirmed']),
                    'in_progress': len([e for e in events if e['status'] == 'in_progress'])
                }
            }
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


def _get_event_color(status):
    """Get color code for calendar event based on status"""
    colors = {
        'pending': '#FFA500',      # Orange
        'confirmed': '#4CAF50',    # Green
        'in_progress': '#2196F3',  # Blue
        'completed': '#9E9E9E',    # Grey
        'cancelled': '#F44336'     # Red
    }
    return colors.get(status, '#9E9E9E')


def _calculate_availability(vendor, start_date, end_date, bookings):
    """Calculate availability percentage for the date range"""
    total_days = (end_date - start_date).days + 1
    booked_days = set()
    
    for booking in bookings:
        if booking.service_start_date and booking.service_end_date:
            current_date = max(booking.service_start_date, start_date)
            end = min(booking.service_end_date, end_date)
            
            while current_date <= end:
                booked_days.add(current_date.date())
                current_date += timedelta(days=1)
    
    booked_count = len(booked_days)
    available_count = total_days - booked_count
    
    return {
        'total_days': total_days,
        'booked_days': booked_count,
        'available_days': available_count,
        'availability_percentage': round((available_count / total_days) * 100, 2) if total_days > 0 else 100
    }


@vendor_booking_bp.route('/statistics', methods=['GET'])
@login_required
@roles_required('vendor')
def get_statistics():
    """
    Get booking statistics for vendor
    
    Query Parameters:
    - period: Time period (week, month, quarter, year, all) default: month
    - start_date: Custom start date (YYYY-MM-DD)
    - end_date: Custom end date (YYYY-MM-DD)
    """
    try:
        vendor = current_user.vendor_profile
        
        # Determine date range
        period = request.args.get('period', 'month')
        custom_start = request.args.get('start_date')
        custom_end = request.args.get('end_date')
        
        from datetime import date
        today = date.today()
        
        if custom_start and custom_end:
            try:
                start_date = datetime.strptime(custom_start, '%Y-%m-%d')
                end_date = datetime.strptime(custom_end, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD',
                    'code': 'INVALID_DATE_FORMAT'
                }), 400
        else:
            if period == 'week':
                start_date = datetime.now() - timedelta(days=7)
            elif period == 'month':
                start_date = datetime.now() - timedelta(days=30)
            elif period == 'quarter':
                start_date = datetime.now() - timedelta(days=90)
            elif period == 'year':
                start_date = datetime.now() - timedelta(days=365)
            else:  # all
                start_date = datetime(2000, 1, 1)
            
            end_date = datetime.now()
        
        # Get bookings in period
        bookings = ServiceBooking.query.filter(
            ServiceBooking.vendor_id == vendor.id,
            ServiceBooking.created_at >= start_date,
            ServiceBooking.created_at <= end_date
        ).all()
        
        # Calculate statistics
        stats = {
            'period': {
                'start': start_date.date().isoformat(),
                'end': end_date.date().isoformat(),
                'label': period
            },
            'bookings': {
                'total': len(bookings),
                'pending': len([b for b in bookings if b.status == 'pending']),
                'confirmed': len([b for b in bookings if b.status == 'confirmed']),
                'in_progress': len([b for b in bookings if b.status == 'in_progress']),
                'completed': len([b for b in bookings if b.status == 'completed']),
                'cancelled': len([b for b in bookings if b.status == 'cancelled'])
            },
            'revenue': {
                'total': sum(float(b.total_amount) for b in bookings if b.total_amount and b.status == 'completed'),
                'pending': sum(float(b.total_amount) for b in bookings if b.total_amount and b.status in ['confirmed', 'in_progress']),
                'currency': bookings[0].currency if bookings else 'USD'
            },
            'booking_types': {},
            'payment_status': {
                'paid': len([b for b in bookings if b.payment_status == 'paid']),
                'partial': len([b for b in bookings if b.payment_status == 'partial']),
                'unpaid': len([b for b in bookings if b.payment_status == 'unpaid'])
            },
            'average_booking_value': 0,
            'acceptance_rate': 0
        }
        
        # Calculate booking types distribution
        for booking in bookings:
            booking_type = booking.booking_type
            if booking_type not in stats['booking_types']:
                stats['booking_types'][booking_type] = 0
            stats['booking_types'][booking_type] += 1
        
        # Calculate average booking value
        completed_bookings = [b for b in bookings if b.status == 'completed' and b.total_amount]
        if completed_bookings:
            stats['average_booking_value'] = round(
                sum(float(b.total_amount) for b in completed_bookings) / len(completed_bookings),
                2
            )
        
        # Calculate acceptance rate
        responded_bookings = [b for b in bookings if b.status != 'pending']
        if responded_bookings:
            accepted = len([b for b in responded_bookings if b.status in ['confirmed', 'in_progress', 'completed']])
            stats['acceptance_rate'] = round((accepted / len(responded_bookings)) * 100, 2)
        
        # Monthly trend (last 6 months)
        monthly_data = []
        for i in range(6):
            month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_bookings = [b for b in bookings if b.created_at.month == month_start.month and b.created_at.year == month_start.year]
            monthly_data.append({
                'month': month_start.strftime('%B %Y'),
                'bookings': len(month_bookings),
                'revenue': sum(float(b.total_amount) for b in month_bookings if b.total_amount and b.status == 'completed')
            })
        
        stats['monthly_trend'] = list(reversed(monthly_data))
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


@vendor_booking_bp.route('/pending-actions', methods=['GET'])
@login_required
@roles_required('vendor')
def get_pending_actions():
    """Get list of bookings requiring vendor action"""
    try:
        vendor = current_user.vendor_profile
        
        # Get pending bookings
        pending_bookings = ServiceBooking.query.filter_by(
            vendor_id=vendor.id,
            status='pending'
        ).order_by(ServiceBooking.booking_date.desc()).all()
        
        # Get bookings needing updates (confirmed but no progress)
        from datetime import date
        stale_bookings = ServiceBooking.query.filter(
            ServiceBooking.vendor_id == vendor.id,
            ServiceBooking.status == 'confirmed',
            ServiceBooking.service_start_date < datetime.now()
        ).order_by(ServiceBooking.service_start_date).all()
        
        # Get upcoming bookings (next 7 days)
        upcoming_bookings = ServiceBooking.query.filter(
            ServiceBooking.vendor_id == vendor.id,
            ServiceBooking.status.in_(['confirmed', 'in_progress']),
            ServiceBooking.service_start_date >= datetime.now(),
            ServiceBooking.service_start_date <= datetime.now() + timedelta(days=7)
        ).order_by(ServiceBooking.service_start_date).all()
        
        return jsonify({
            'success': True,
            'data': {
                'pending_approval': {
                    'count': len(pending_bookings),
                    'bookings': [serialize_booking_detailed(b) for b in pending_bookings]
                },
                'need_status_update': {
                    'count': len(stale_bookings),
                    'bookings': [serialize_booking_detailed(b) for b in stale_bookings]
                },
                'upcoming': {
                    'count': len(upcoming_bookings),
                    'bookings': [serialize_booking_detailed(b) for b in upcoming_bookings]
                },
                'total_actions_needed': len(pending_bookings) + len(stale_bookings)
            }
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


@vendor_booking_bp.route('/<int:booking_id>/notes', methods=['POST'])
@login_required
@roles_required('vendor')
@validate_booking_access
def add_booking_note(booking_id, booking):
    """
    Add internal note to booking
    
    Request Body:
    - note (required): Note text
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required',
                'code': 'MISSING_DATA'
            }), 400
        
        note = data.get('note', '').strip()
        
        if not note:
            return jsonify({
                'success': False,
                'error': 'Note text is required',
                'code': 'NOTE_REQUIRED'
            }), 400
        
        # Add timestamp and user info to note
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        formatted_note = f"\n\n[{timestamp}] {current_user.full_name}: {note}"
        
        booking.notes = f"{booking.notes}{formatted_note}" if booking.notes else formatted_note
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Note added successfully',
            'data': serialize_booking_detailed(booking)
        }), 200
        
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