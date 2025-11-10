from flask import jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.models import Participant, TripRegistration, Consent
from app.api.parent.children import get_current_user

from app.api import api_bp as parent_bp 


@parent_bp.route('/dashboard/summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    """
    Get summary information for parent dashboard
    
    Returns:
        200: Dashboard summary data
        401: Unauthorized
        500: Server error
    """
    try:
        user, error, status_code = get_current_user()
        if error:
            return jsonify(error), status_code
        
        # Get all children
        children = Participant.query.filter_by(parent_id=user.id).all()
        
        # Get all active registrations
        active_registrations = TripRegistration.query.filter_by(
            parent_id=user.id
        ).filter(TripRegistration.status.in_(['pending', 'confirmed'])).all()

        # Calculate statistics
        total_children = len(children)
        active_trips = len(active_registrations)
        pending_payments = TripRegistration.query.filter_by(
            parent_id=user.id
        ).filter(
            TripRegistration.status.in_(['pending', 'confirmed']),
            TripRegistration.payment_status.in_(['unpaid', 'partial'])
        ).count()
        
        unsigned_consents = Consent.query.join(Participant).filter(
            Participant.parent_id == user.id,
            Consent.is_signed == False,
            Consent.is_required == True
        ).count()
        
        # Get upcoming trips
        upcoming_trips = []
        for registration in active_registrations:
            if registration.trip and registration.trip.start_date >= datetime.now().date():
                trip_info = {
                    'registration_id': registration.id,
                    'registration_number': registration.registration_number,
                    'trip_id': registration.trip.id,
                    'trip_title': registration.trip.title,
                    'child_name': registration.participant.full_name,
                    'start_date': registration.trip.start_date.isoformat(),
                    'status': registration.status,
                    'payment_status': registration.payment_status,
                    'outstanding_balance': registration.outstanding_balance
                }
                upcoming_trips.append(trip_info)
        
        # Sort upcoming trips by date
        upcoming_trips.sort(key=lambda x: x['start_date'])
        
        return jsonify({
            'success': True,
            'summary': {
                'total_children': total_children,
                'active_trips': active_trips,
                'pending_payments': pending_payments,
                'unsigned_consents': unsigned_consents,
                'upcoming_trips': upcoming_trips[:5]  # Limit to 5 most recent
            }
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