from flask import jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.models.participant import Participant
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
        
        # Calculate statistics
        total_children = len(children)
        active_trips = sum(1 for c in children if c.status in ['registered', 'confirmed'])
        pending_payments = sum(1 for c in children if c.payment_status in ['pending', 'partial'])
        unsigned_consents = sum(1 for c in children if not c.has_all_consents())
        
        # Get upcoming trips
        upcoming_trips = []
        for child in children:
            if child.trip and child.trip.start_date and child.trip.start_date >= datetime.now().date():
                trip_info = {
                    'trip_id': child.trip.id,
                    'trip_title': child.trip.title,
                    'child_name': child.full_name,
                    'start_date': child.trip.start_date.isoformat(),
                    'status': child.status,
                    'payment_status': child.payment_status
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