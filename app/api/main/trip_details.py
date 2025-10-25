from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload
from app.models.trip import Trip
from app.models.user import User
from app.extensions import db
from datetime import date
from app.api import api_bp as trip_api
from app.api.main.utils import get_trip_image_url, calculate_trip_rating
# Create blueprint
# trip_api = Blueprint('trip_api', __name__, url_prefix='/api/trips')

@trip_api.route('/trip/<int:trip_id>', methods=['GET'])
def get_trip_details(trip_id):
    """
    Fetch detailed information about a specific trip
    Returns comprehensive trip data including organizer info, participants, and statistics
    """
    try:
        # Fetch trip with eager loading for related data
        trip = Trip.query.options(
            joinedload(Trip.organizer),
            joinedload(Trip.participants),
            joinedload(Trip.locations)
        ).get(trip_id)
        
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found'
            }), 404
        
        # Build comprehensive response
        trip_data = {
            'success': True,
            'trip': {
                # Basic Information
                'id': trip.id,
                'title': trip.title,
                'description': trip.description,
                'destination': trip.destination,
                'category': trip.category,
                'grade_level': trip.grade_level,
                'itinerary': trip.itinerary,
                'image_url': get_trip_image_url(trip),
                'rating': calculate_trip_rating(trip),
                
                # Dates
                'start_date': trip.start_date.isoformat() if trip.start_date else None,
                'end_date': trip.end_date.isoformat() if trip.end_date else None,
                'registration_deadline': trip.registration_deadline.isoformat() if trip.registration_deadline else None,
                'duration_days': trip.duration_days,
                
                # Capacity & Pricing
                'max_participants': trip.max_participants,
                'min_participants': trip.min_participants,
                'current_participants': trip.current_participants,
                'available_spots': trip.available_spots,
                'price_per_student': float(trip.price_per_student),
                
                # Status
                'status': trip.status,
                'is_full': trip.is_full,
                'is_upcoming': trip.is_upcoming,
                'is_active': trip.is_active,
                'registration_open': trip.registration_open,
                'can_start': trip.can_start(),
                
                # Requirements
                'medical_info_required': trip.medical_info_required,
                'consent_required': trip.consent_required,
                
                # Financial
                'total_revenue': trip.get_total_revenue(),
                
                # Organizer Information
                'organizer': {
                    'id': trip.organizer.id,
                    'name': trip.organizer.full_name,
                    'email': trip.organizer.email,
                    'phone': trip.organizer.phone,
                    'school': trip.organizer.school,
                    'profile_picture': trip.organizer.profile_picture
                } if trip.organizer else None,
                
                # Locations
                'locations': [
                    {
                        'id': loc.id,
                        'name': loc.name if hasattr(loc, 'name') else None,
                        'address': loc.address if hasattr(loc, 'address') else None,
                        'type': loc.type if hasattr(loc, 'type') else None
                    } for loc in trip.locations
                ] if trip.locations else [],
                
                # Timestamps
                'created_at': trip.created_at.isoformat() if trip.created_at else None,
                'updated_at': trip.updated_at.isoformat() if trip.updated_at else None
            }
        }
        
        # Add participant statistics
        # confirmed_participants = trip.participants.filter_by(status='confirmed').all()
        # trip_data['trip']['participant_breakdown'] = {
        #     'confirmed': len(confirmed_participants),
        #     'pending': trip.participants.filter_by(status='pending').count(),
        #     'cancelled': trip.participants.filter_by(status='cancelled').count()
        # }
        confirmed_participants = [p for p in trip.participants if p.status == 'confirmed']
        pending_participants = [p for p in trip.participants if p.status == 'pending']
        cancelled_participants = [p for p in trip.participants if p.status == 'cancelled']

        trip_data['trip']['participant_breakdown'] = {
            'confirmed': len(confirmed_participants),
            'pending': len(pending_participants),
            'cancelled': len(cancelled_participants)
        }
        
        # Add booking statistics if available
        confirmed_bookings = trip.get_confirmed_vendor_bookings()
        trip_data['trip']['vendor_bookings'] = len(confirmed_bookings)
        
        return jsonify(trip_data), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500


@trip_api.route('/trip/<int:trip_id>/summary', methods=['GET'])
def get_trip_summary(trip_id):
    """
    Fetch a lightweight summary of trip information
    Useful for cards, lists, and quick previews
    """
    try:
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found'
            }), 404
        
        summary = {
            'success': True,
            'trip': {
                'id': trip.id,
                'title': trip.title,
                'destination': trip.destination,
                'category': trip.category,
                'start_date': trip.start_date.isoformat() if trip.start_date else None,
                'end_date': trip.end_date.isoformat() if trip.end_date else None,
                'duration_days': trip.duration_days,
                'price_per_student': float(trip.price_per_student),
                'available_spots': trip.available_spots,
                'status': trip.status,
                'registration_open': trip.registration_open
            }
        }
        
        return jsonify(summary), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500