from flask import jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from app.extensions import db
from app.models import (
    Trip, Participant, Consent, Notification, 
)
from app.teacher import teacher_bp

@teacher_bp.route('/api/participants', methods=['POST'])
@login_required
def add_participant():
    """Add a new participant to a trip"""
    try:
        if not current_user.is_teacher():
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Validate trip
        trip = Trip.query.get_or_404(data['trip_id'])
        if trip.organizer_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if trip is full
        if trip.is_full:
            return jsonify({'error': 'Trip is full'}), 400
        
        # Create participant
        participant = Participant(
            trip_id=data['trip_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data.get('email'),
            phone=data.get('phone'),
            date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date() if data.get('date_of_birth') else None,
            grade_level=data.get('grade_level'),
            student_id=data.get('student_id'),
            medical_conditions=data.get('medical_conditions'),
            medications=data.get('medications'),
            allergies=data.get('allergies'),
            dietary_restrictions=data.get('dietary_restrictions'),
            emergency_contact_1_name=data.get('emergency_contact_1_name'),
            emergency_contact_1_phone=data.get('emergency_contact_1_phone'),
            emergency_contact_1_relationship=data.get('emergency_contact_1_relationship'),
            special_requirements=data.get('special_requirements'),
            user_id=current_user.id
        )
        
        db.session.add(participant)
        db.session.commit()
        
        # Create default consent form if required
        if trip.consent_required:
            consent = Consent(
                participant_id=participant.id,
                consent_type='trip_participation',
                title=f'Trip Participation Consent - {trip.title}',
                content='Standard trip participation consent form.',
                is_required=True
            )
            db.session.add(consent)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Participant added successfully',
            'participant': participant.serialize()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@teacher_bp.route('/api/participants/<int:participant_id>', methods=['PUT'])
@login_required
def update_participant(participant_id):
    """Update participant information"""
    try:
        participant = Participant.query.get_or_404(participant_id)
        
        # Check authorization
        if participant.trip.organizer_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Update fields
        updateable_fields = [
            'first_name', 'last_name', 'email', 'phone', 'grade_level',
            'student_id', 'medical_conditions', 'medications', 'allergies',
            'dietary_restrictions', 'emergency_contact_1_name', 
            'emergency_contact_1_phone', 'emergency_contact_1_relationship',
            'emergency_contact_2_name', 'emergency_contact_2_phone',
            'emergency_contact_2_relationship', 'special_requirements',
            'internal_notes', 'status'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(participant, field, data[field])
        
        if 'date_of_birth' in data and data['date_of_birth']:
            participant.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Participant updated successfully',
            'participant': participant.serialize()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@teacher_bp.route('/api/participants/<int:participant_id>/confirm', methods=['POST'])
@login_required
def confirm_participant(participant_id):
    """Confirm a participant's spot"""
    try:
        participant = Participant.query.get_or_404(participant_id)
        
        # Check authorization
        if participant.trip.organizer_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        participant.confirm_participation()
        
        # Send notification to parent/guardian
        if participant.user:
            notification = Notification(
                title=f'Participant Confirmed - {participant.trip.title}',
                message=f'{participant.full_name} has been confirmed for the trip.',
                notification_type='trip_update',
                priority='normal',
                recipient_id=participant.user.id,
                related_data={'trip_id': participant.trip_id, 'participant_id': participant.id}
            )
            db.session.add(notification)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Participant confirmed successfully',
            'participant': participant.serialize()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500