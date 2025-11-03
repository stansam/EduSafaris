from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy import func, and_, or_
from app.extensions import db
from app.models import (
    User, Trip, Participant, Consent, Notification, 
    Location, Emergency, ServicePayment as Payment, ServiceBooking as Booking
)
from app.teacher import teacher_bp

@teacher_bp.route('/api/trips', methods=['POST'])
@login_required
def create_trip():
    """Create a new trip"""
    try:
        if not current_user.is_teacher():
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'destination', 'start_date', 'end_date', 
                          'max_participants', 'price_per_student']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        registration_deadline = datetime.strptime(data.get('registration_deadline'), '%Y-%m-%d').date() \
            if data.get('registration_deadline') else None
        
        # Validate dates
        if end_date < start_date:
            return jsonify({'error': 'End date must be after start date'}), 400
        
        # Create trip
        trip = Trip(
            title=data['title'],
            description=data.get('description', ''),
            destination=data['destination'],
            start_date=start_date,
            end_date=end_date,
            registration_deadline=registration_deadline,
            max_participants=data['max_participants'],
            min_participants=data.get('min_participants', 5),
            price_per_student=data['price_per_student'],
            category=data.get('category'),
            grade_level=data.get('grade_level'),
            itinerary=data.get('itinerary'),
            medical_info_required=data.get('medical_info_required', True),
            consent_required=data.get('consent_required', True),
            status=data.get('status', 'draft'),
            organizer_id=current_user.id
        )
        
        db.session.add(trip)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trip created successfully',
            'trip': trip.serialize()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@teacher_bp.route('/api/trips/<int:trip_id>', methods=['PUT'])
@login_required
def update_trip(trip_id):
    """Update an existing trip"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        
        # Check authorization
        if trip.organizer_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            trip.title = data['title']
        if 'description' in data:
            trip.description = data['description']
        if 'destination' in data:
            trip.destination = data['destination']
        if 'start_date' in data:
            trip.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data:
            trip.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if 'registration_deadline' in data:
            trip.registration_deadline = datetime.strptime(data['registration_deadline'], '%Y-%m-%d').date()
        if 'max_participants' in data:
            trip.max_participants = data['max_participants']
        if 'min_participants' in data:
            trip.min_participants = data['min_participants']
        if 'price_per_student' in data:
            trip.price_per_student = data['price_per_student']
        if 'category' in data:
            trip.category = data['category']
        if 'grade_level' in data:
            trip.grade_level = data['grade_level']
        if 'itinerary' in data:
            trip.itinerary = data['itinerary']
        if 'status' in data:
            trip.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trip updated successfully',
            'trip': trip.serialize()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@teacher_bp.route('/api/trips/<int:trip_id>', methods=['DELETE'])
@login_required
def delete_trip(trip_id):
    """Delete a trip (only if no confirmed participants)"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        
        # Check authorization
        if trip.organizer_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if trip has confirmed participants
        if trip.current_participants > 0:
            return jsonify({'error': 'Cannot delete trip with confirmed participants'}), 400
        
        db.session.delete(trip)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trip deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500