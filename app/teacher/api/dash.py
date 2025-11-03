from flask import jsonify, request
from flask_login import login_required, current_user
from datetime import date
from sqlalchemy import func, or_
from app.extensions import db
from app.models import (
     Trip, Participant, Consent, Notification, 
    ServicePayment as Payment
)
from app.teacher import teacher_bp


@teacher_bp.route('/api/dashboard/stats')
@login_required
def get_dashboard_stats():
    """Get dashboard statistics for teacher"""
    try:
        if not current_user.is_teacher():
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get all trips for current teacher
        teacher_trips = current_user.organized_trips
        
        # Upcoming trips count
        upcoming_trips = teacher_trips.filter(
            Trip.start_date > date.today(),
            Trip.status.in_(['active', 'draft'])
        ).count()
        
        # Total confirmed students across all trips
        confirmed_students = db.session.query(func.count(Participant.id)).join(Trip).filter(
            Trip.organizer_id == current_user.id,
            Participant.status == 'confirmed'
        ).scalar() or 0
        
        # Consent completion rate
        total_participants = db.session.query(func.count(Participant.id)).join(Trip).filter(
            Trip.organizer_id == current_user.id,
            Participant.status.in_(['registered', 'confirmed'])
        ).scalar() or 0
        
        participants_with_consent = db.session.query(func.count(Participant.id.distinct())).join(
            Consent, Participant.id == Consent.participant_id
        ).join(Trip, Participant.trip_id == Trip.id).filter(
            Trip.organizer_id == current_user.id,
            Consent.is_signed == True,
            Participant.status.in_(['registered', 'confirmed'])
        ).scalar() or 0
        
        consent_completion = (participants_with_consent / total_participants * 100) if total_participants > 0 else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'upcoming_trips': upcoming_trips,
                'confirmed_students': confirmed_students,
                'consent_completion': round(consent_completion, 1),
                'total_trips': teacher_trips.count()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@teacher_bp.route('/api/trips')
@login_required
def get_trips():
    """Get all trips for current teacher with filters"""
    try:
        if not current_user.is_teacher():
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get query parameters
        status = request.args.get('status')
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Base query
        query = current_user.organized_trips
        
        # Apply filters
        if status and status != 'all':
            query = query.filter(Trip.status == status)
        
        if search:
            query = query.filter(
                or_(
                    Trip.title.ilike(f'%{search}%'),
                    Trip.destination.ilike(f'%{search}%')
                )
            )
        
        # Order by start date
        query = query.order_by(Trip.start_date.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        trips_data = []
        for trip in pagination.items:
            pending_consents = (db.session.query(Consent).join(Participant, Consent.participant_id == Participant.id)
                                .filter(Participant.trip_id == trip.id,Consent.is_signed == False).count()
                                if trip.consent_required else 0
                            )
            trips_data.append({
                **trip.serialize(),
                'current_participants_count': trip.current_participants,
                'pending_consents': pending_consents
            })
        
        return jsonify({
            'success': True,
            'trips': trips_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@teacher_bp.route('/api/trips/<int:trip_id>')
@login_required
def get_trip_details(trip_id):
    """Get detailed information about a specific trip"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        
        # Check authorization
        if trip.organizer_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get participants with details
        participants = []
        for participant in trip.participants:
            participants.append({
                **participant.serialize(),
                'consent_status': 'signed' if participant.has_all_consents() else 'pending'
            })
        
        # Get bookings
        bookings = [booking.serialize() for booking in trip.bookings.all()]
        
        # Get payments summary
        total_revenue = trip.get_total_revenue()
        total_paid = db.session.query(func.sum(Payment.amount)).filter(
            Payment.trip_id == trip_id,
            Payment.status == 'completed'
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'trip': {
                **trip.serialize(),
                'participants': participants,
                'bookings': bookings,
                'financial': {
                    'total_revenue': float(total_revenue),
                    'total_paid': float(total_paid),
                    'outstanding': float(float(total_revenue) - float(total_paid))
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@teacher_bp.route('/api/participants')
@login_required
def get_participants():
    """Get all participants across teacher's trips"""
    try:
        if not current_user.is_teacher():
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Query parameters
        trip_id = request.args.get('trip_id', type=int)
        status = request.args.get('status')
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Base query
        query = db.session.query(Participant).join(Trip).filter(
            Trip.organizer_id == current_user.id
        )
        
        # Apply filters
        if trip_id:
            query = query.filter(Participant.trip_id == trip_id)
        
        if status:
            query = query.filter(Participant.status == status)
        
        if search:
            query = query.filter(
                or_(
                    Participant.first_name.ilike(f'%{search}%'),
                    Participant.last_name.ilike(f'%{search}%'),
                    Participant.email.ilike(f'%{search}%')
                )
            )
        
        # Order by registration date
        query = query.order_by(Participant.registration_date.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        participants_data = []
        for participant in pagination.items:
            participants_data.append({
                **participant.serialize(),
                'trip_title': participant.trip.title if participant.trip else None,
                'consent_status': 'signed' if participant.has_all_consents() else 'pending',
                'payment_percentage': (float(participant.amount_paid) / float(participant.trip.price_per_student) * 100) 
                    if participant.trip and participant.trip.price_per_student else 0
            })
        
        return jsonify({
            'success': True,
            'participants': participants_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@teacher_bp.route('/api/consents')
@login_required
def get_consents():
    """Get consent forms status"""
    try:
        if not current_user.is_teacher():
            return jsonify({'error': 'Unauthorized'}), 403
        
        trip_id = request.args.get('trip_id', type=int)
        signed = request.args.get('signed', type=lambda v: v.lower() == 'true')
        
        # Base query
        query = db.session.query(Consent).join(Participant).join(Trip).filter(
            Trip.organizer_id == current_user.id
        )
        
        if trip_id:
            query = query.filter(Participant.trip_id == trip_id)
        
        if signed is not None:
            query = query.filter(Consent.is_signed == signed)
        
        query = query.order_by(Consent.created_at.desc())
        
        consents = []
        for consent in query.all():
            consents.append({
                **consent.serialize(),
                'participant_name': consent.participant.full_name,
                'trip_title': consent.participant.trip.title
            })
        
        return jsonify({
            'success': True,
            'consents': consents
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@teacher_bp.route('/api/notifications')
@login_required
def get_notifications():
    """Get notifications for teacher"""
    try:
        if not current_user.is_teacher():
            return jsonify({'error': 'Unauthorized'}), 403
        
        unread_only = request.args.get('unread_only', type=lambda v: v.lower() == 'true')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = current_user.received_notifications
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        query = query.order_by(Notification.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        notifications = [notif.serialize() for notif in pagination.items]
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500