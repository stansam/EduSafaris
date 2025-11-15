from flask import request, current_app
from flask_login import current_user
from app.models import ActivityLog, Trip, TripRegistration
from datetime import datetime
from decimal import Decimal, InvalidOperation
from app.extensions import db
from sqlalchemy import or_, func

def get_request_metadata():
    """Extract request metadata for activity logging"""
    return {
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', '')[:300],
        'request_method': request.method,
        'request_url': request.url[:500]
    }


def log_admin_action(action, trip=None, old_values=None, new_values=None, 
                     description=None, status='success', error_message=None):
    """Log admin actions with comprehensive details"""
    try:
        metadata = get_request_metadata()
        ActivityLog.log_action(
            action=action,
            user_id=current_user.id,
            entity_type='trip' if trip else None,
            entity_id=trip.id if trip else None,
            description=description,
            category='admin_trip_management',
            trip_id=trip.id if trip else None,
            old_values=old_values,
            new_values=new_values,
            status=status,
            error_message=error_message,
            **metadata
        )
    except Exception as e:
        current_app.logger.error(f"Failed to log admin action: {str(e)}")


def build_trip_filters(query, filters):
    """Build SQLAlchemy filters from request parameters"""
    
    # Status filter
    if filters.get('status'):
        statuses = filters['status'].split(',')
        query = query.filter(Trip.status.in_(statuses))
    
    # Date range filters
    if filters.get('start_date_from'):
        try:
            start_from = datetime.strptime(filters['start_date_from'], '%Y-%m-%d').date()
            query = query.filter(Trip.start_date >= start_from)
        except ValueError:
            pass
    
    if filters.get('start_date_to'):
        try:
            start_to = datetime.strptime(filters['start_date_to'], '%Y-%m-%d').date()
            query = query.filter(Trip.start_date <= start_to)
        except ValueError:
            pass
    
    # Category filter
    if filters.get('category'):
        categories = filters['category'].split(',')
        query = query.filter(Trip.category.in_(categories))
    
    # Destination filter
    if filters.get('destination'):
        query = query.filter(Trip.destination.ilike(f"%{filters['destination']}%"))
    
    # Organizer filter
    if filters.get('organizer_id'):
        try:
            organizer_id = int(filters['organizer_id'])
            query = query.filter(Trip.organizer_id == organizer_id)
        except (ValueError, TypeError):
            pass
    
    # Price range
    if filters.get('min_price'):
        try:
            min_price = Decimal(filters['min_price'])
            query = query.filter(Trip.price_per_student >= min_price)
        except (ValueError, InvalidOperation):
            pass
    
    if filters.get('max_price'):
        try:
            max_price = Decimal(filters['max_price'])
            query = query.filter(Trip.price_per_student <= max_price)
        except (ValueError, InvalidOperation):
            pass
    
    # Featured filter
    if filters.get('featured') is not None:
        featured = filters['featured'].lower() in ('true', '1', 'yes')
        query = query.filter(Trip.featured == featured)
    
    # Published filter
    if filters.get('is_published') is not None:
        is_published = filters['is_published'].lower() in ('true', '1', 'yes')
        query = query.filter(Trip.is_published == is_published)
    
    # Search query (title, description, destination)
    if filters.get('search'):
        search_term = f"%{filters['search']}%"
        query = query.filter(
            or_(
                Trip.title.ilike(search_term),
                Trip.description.ilike(search_term),
                Trip.destination.ilike(search_term)
            )
        )
    
    # Capacity filters
    if filters.get('has_available_spots'):
        has_spots = filters['has_available_spots'].lower() in ('true', '1', 'yes')
        if has_spots:
            # Subquery to count confirmed registrations
            confirmed_count = db.session.query(
                func.count(TripRegistration.id)
            ).filter(
                TripRegistration.trip_id == Trip.id,
                TripRegistration.status == 'confirmed'
            ).correlate(Trip).scalar_subquery()
            
            query = query.filter(Trip.max_participants > confirmed_count)
    
    return query


def apply_trip_sorting(query, sort_by, sort_order):
    """Apply sorting to trip query"""
    valid_sort_fields = {
        'title': Trip.title,
        'start_date': Trip.start_date,
        'end_date': Trip.end_date,
        'created_at': Trip.created_at,
        'price': Trip.price_per_student,
        'status': Trip.status,
        'destination': Trip.destination,
        'max_participants': Trip.max_participants,
        'registration_deadline': Trip.registration_deadline
    }
    
    sort_field = valid_sort_fields.get(sort_by, Trip.created_at)
    
    if sort_order.lower() == 'asc':
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    
    return query