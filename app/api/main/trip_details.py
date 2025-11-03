from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload
from app.models import Trip, TripRegistration
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
            # joinedload(Trip.registrations),
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
                'destination_country': trip.destination_country,
                'category': trip.category,
                'grade_level': trip.grade_level,
                'itinerary': trip.itinerary,
                'image_url': get_trip_image_url(trip),
                'rating': calculate_trip_rating(trip),
                
                # Dates
                'start_date': trip.start_date.isoformat() if trip.start_date else None,
                'end_date': trip.end_date.isoformat() if trip.end_date else None,
                'registration_deadline': trip.registration_deadline.isoformat() if trip.registration_deadline else None,
                'registration_start_date': trip.registration_start_date.isoformat() if trip.registration_start_date else None,
                'duration_days': trip.duration_days,
                
                # Capacity & Pricing
                'max_participants': trip.max_participants,
                'min_participants': trip.min_participants,
                'current_participants': trip.current_participants_count,
                'available_spots': trip.available_spots,
                'price_per_student': float(trip.price_per_student),
                'deposit_amount': float(trip.deposit_amount) if trip.deposit_amount else None,
                'deposit_deadline': trip.deposit_deadline.isoformat() if trip.deposit_deadline else None,
                'allows_installments': trip.allows_installments,
                
                # Status
                'status': trip.status,
                'is_full': trip.is_full,
                'is_upcoming': trip.is_upcoming,
                'is_published': trip.is_published,
                'registration_is_open': trip.registration_is_open,
                'can_start': trip.can_start(),
                'is_in_progress': trip.is_in_progress,
                
                # Requirements
                'medical_info_required': trip.medical_info_required,
                'consent_required': trip.consent_required,
                'insurance_required': trip.insurance_required,
                'vaccination_requirements': trip.vaccination_requirements,
                'special_equipment_needed': trip.special_equipment_needed,
                'physical_requirements': trip.physical_requirements,
                
                # Logistics
                'transportation_included': trip.transportation_included,
                'meals_included': trip.meals_included,
                'accommodation_included': trip.accommodation_included,
                'meals_provided': trip.meals_provided,
                'meeting_point': trip.meeting_point,
                
                # Educational
                'learning_objectives': trip.learning_objectives,
                'subjects_covered': trip.subjects_covered,
                
                # Financial
                'total_revenue': trip.get_total_revenue(),
                'total_expenses': trip.get_total_expenses(),
                'expected_revenue': trip.get_expected_revenue(),
                'profit_estimate': trip.get_profit_estimate(),
                
                # Additional Info
                'refund_policy': trip.refund_policy,
                'tags': trip.tags,
                'cover_image_url': trip.cover_image_url,
                'gallery_images': trip.gallery_images,
                
                # Time-based Properties
                'days_until_trip': trip.days_until_trip,
                'days_until_registration_deadline': trip.days_until_registration_deadline,
                                
                # Organizer Information
                'organizer': {
                    'id': trip.organizer.id,
                    'name': trip.organizer.full_name,
                    'email': trip.organizer.email,
                    'phone': trip.organizer.phone,
                    'school': trip.organizer.school.name if trip.organizer.school else None,
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

        all_registrations = TripRegistration.query.options(
            joinedload(TripRegistration.participant)
        ).filter_by(trip_id=trip_id).all()
        
        # Group by status in Python (more efficient than multiple queries)
        confirmed_registrations = [r for r in all_registrations if r.status == 'confirmed']
        pending_registrations = [r for r in all_registrations if r.status == 'pending']
        cancelled_registrations = [r for r in all_registrations if r.status == 'cancelled']
        
        trip_data['trip']['registration_breakdown'] = {
            'confirmed': len(confirmed_registrations),
            'pending': len(pending_registrations),
            'cancelled': len(cancelled_registrations),
            'total': trip.registrations.count()
        }
        
        trip_data['trip']['participants'] = [
            {
                'id': reg.participant.id,
                'name': reg.participant.full_name,
                'status': reg.status,
                'registered_at': reg.created_at.isoformat() if reg.created_at else None
            } for reg in confirmed_registrations
        ]
        
        # Add booking statistics if available
        confirmed_bookings = trip.service_bookings.filter_by(status='confirmed').all()
        trip_data['trip']['service_bookings'] = {
            'count': len(confirmed_bookings),
            'total_amount': sum(float(booking.total_amount or 0) for booking in confirmed_bookings)
        }
        
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
                'destination_country': trip.destination_country,
                'category': trip.category,
                'grade_level': trip.grade_level,
                'start_date': trip.start_date.isoformat() if trip.start_date else None,
                'end_date': trip.end_date.isoformat() if trip.end_date else None,
                'duration_days': trip.duration_days,
                'price_per_student': float(trip.price_per_student),
                'available_spots': trip.available_spots,
                'current_participants': trip.current_participants_count,
                'status': trip.status,
                'is_published': trip.is_published,
                'featured': trip.featured,
                'registration_is_open': trip.registration_is_open,
                'cover_image_url': trip.cover_image_url,
                'image_url': get_trip_image_url(trip),
                'days_until_trip': trip.days_until_trip
            }
        }
        
        return jsonify(summary), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500