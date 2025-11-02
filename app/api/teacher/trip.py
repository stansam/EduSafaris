from app.api.teacher.utils import validate_trip_data
from app.api import api_bp as trips_bp
from flask import request, jsonify
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.utils.utils import roles_required
from app.extensions import db
from app.models.trip import Trip
from app.models.user import User


@trips_bp.route('/trip/create', methods=['POST'])
@roles_required('teacher', 'admin')
def create_trip():
    """
    Create a new trip
    
    Expected JSON payload:
    {
        "title": "Summer Science Camp",
        "description": "An exciting science adventure",
        "destination": "Science Center, City",
        "start_date": "2025-07-01",
        "end_date": "2025-07-05",
        "registration_deadline": "2025-06-15",
        "price_per_student": 299.99,
        "max_participants": 30,
        "min_participants": 10,
        "category": "science",
        "grade_level": "6-8",
        "itinerary": {...},
        "medical_info_required": true,
        "consent_required": true,
        "status": "draft"
    }
    """
    try:
        # Get JSON data
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body cannot be empty'}), 400
        
        # Get organizer ID from auth header (customize based on your auth system)
        organizer_id = request.headers.get('X-User-ID')
        
        # Verify organizer exists
        organizer = User.query.get(organizer_id)
        if not organizer:
            return jsonify({'error': 'Organizer not found'}), 404
        
        # Validate data
        cleaned_data, validation_errors = validate_trip_data(data, is_update=False)
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Create trip
        trip = Trip(
            organizer_id=organizer_id,
            **cleaned_data
        )
        
        # Save to database
        db.session.add(trip)
        db.session.commit()
        
        return jsonify({
            'message': 'Trip created successfully',
            'trip': trip.serialize()
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Database integrity error',
            'details': 'A trip with similar details may already exist'
        }), 409
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500


@trips_bp.route('/trip/edit/<int:trip_id>', methods=['PUT', 'PATCH'])
@roles_required('teacher', 'admin')
def update_trip(trip_id):
    """
    Update an existing trip
    
    PUT: Full update (all fields)
    PATCH: Partial update (only specified fields)
    
    Expected JSON payload (all fields optional for PATCH):
    {
        "title": "Updated Title",
        "description": "Updated description",
        "start_date": "2025-08-01",
        "price_per_student": 349.99,
        ...
    }
    """
    try:
        # Get JSON data
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body cannot be empty'}), 400
        
        # Get trip
        trip = Trip.query.get(trip_id)
        if not trip:
            return jsonify({'error': 'Trip not found'}), 404
        
        # Get user ID from auth header
        user_id = request.headers.get('X-User-ID')
        
        # Authorization check (customize based on your role system)
        if trip.organizer_id != int(user_id):
            # Add additional checks for admin roles if needed
            return jsonify({'error': 'Not authorized to update this trip'}), 403
        
        # Check if trip can be updated
        if trip.status == 'completed':
            return jsonify({'error': 'Cannot update a completed trip'}), 400
        
        if trip.status == 'in_progress' and data.get('status') != 'in_progress':
            # Allow limited updates for in-progress trips
            allowed_fields = ['description', 'itinerary', 'status']
            disallowed = [k for k in data.keys() if k not in allowed_fields]
            if disallowed:
                return jsonify({
                    'error': 'Limited updates allowed for in-progress trips',
                    'allowed_fields': allowed_fields,
                    'disallowed_fields': disallowed
                }), 400
        
        # Validate data
        cleaned_data, validation_errors = validate_trip_data(data, is_update=True)
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Additional validation for updates
        if 'max_participants' in cleaned_data:
            if cleaned_data['max_participants'] < trip.current_participants:
                return jsonify({
                    'error': 'Cannot reduce max participants below current participant count',
                    'current_participants': trip.current_participants,
                    'requested_max': cleaned_data['max_participants']
                }), 400
        
        # Update trip fields
        for key, value in cleaned_data.items():
            setattr(trip, key, value)
        
        # Auto-update status based on capacity
        if trip.is_full and trip.status == 'active':
            trip.status = 'full'
        
        # Commit changes
        trip.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Trip updated successfully',
            'trip': trip.serialize()
        }), 200
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Database integrity error',
            'details': 'Update would violate database constraints'
        }), 409
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Database error occurred',
            'details': str(e)
        }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500


