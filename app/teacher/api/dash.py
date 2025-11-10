from flask import jsonify, request
from flask_login import login_required, current_user
from datetime import date
from sqlalchemy import func, or_
from app.extensions import db
from app.models import (
    Trip, Participant, Consent, Notification, TripRegistration,
    RegistrationPayment
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
        teacher_trips = Trip.query.filter_by(organizer_id=current_user.id)
        
        # Upcoming trips count
        upcoming_trips = teacher_trips.filter(
            Trip.start_date > date.today(),
            Trip.status.in_(['published', 'registration_open', 'registration_closed', 'full'])
        ).count()
        
        # Total confirmed students across all trips (via TripRegistration)
        confirmed_students = db.session.query(func.count(TripRegistration.id)).join(Trip).filter(
            Trip.organizer_id == current_user.id,
            TripRegistration.status == 'confirmed'
        ).scalar() or 0
        
        # Consent completion rate - participants with registrations
        total_registrations = db.session.query(func.count(TripRegistration.id)).join(Trip).filter(
            Trip.organizer_id == current_user.id,
            TripRegistration.status.in_(['pending', 'confirmed'])
        ).scalar() or 0
        
        # Count registrations where consent is signed
        registrations_with_consent = db.session.query(
            func.count(TripRegistration.id.distinct())
        ).join(Trip).filter(
            Trip.organizer_id == current_user.id,
            TripRegistration.status.in_(['pending', 'confirmed']),
            TripRegistration.consent_signed == True
        ).scalar() or 0
        
        consent_completion = (registrations_with_consent / total_registrations * 100) if total_registrations > 0 else 0
        
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
        query = Trip.query.filter_by(organizer_id=current_user.id)
        
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
            # Count pending consents via TripRegistration
            pending_consents = (
                db.session.query(func.count(TripRegistration.id))
                .filter(
                    TripRegistration.trip_id == trip.id,
                    TripRegistration.consent_signed == False,
                    TripRegistration.status.in_(['pending', 'confirmed'])
                ).scalar() or 0
            ) if trip.consent_required else 0
            
            trips_data.append({
                **trip.serialize(),
                'current_participants_count': trip.current_participants_count,
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
        
        # Get registrations with participant details
        registrations = []
        for registration in trip.registrations.all():
            # Check if participant has signed consent
            consent_status = 'signed' if registration.consent_signed else 'pending'
            
            registrations.append({
                **registration.serialize(),
                'consent_status': consent_status
            })
        
        # Get service bookings
        bookings = [booking.serialize() for booking in trip.service_bookings.all()]
        
        # Get payments summary - use RegistrationPayment
        total_revenue = trip.get_total_revenue()
        
        # Sum of all completed registration payments for this trip
        total_paid = db.session.query(
            func.sum(RegistrationPayment.amount)
        ).join(TripRegistration).filter(
            TripRegistration.trip_id == trip_id,
            RegistrationPayment.status == 'completed'
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'trip': {
                **trip.serialize(include_details=True),
                'registrations': registrations,
                'bookings': bookings,
                'financial': {
                    'total_revenue': float(total_revenue),
                    'total_paid': float(total_paid),
                    'outstanding': float(total_revenue - float(total_paid))
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@teacher_bp.route('/api/registrations')
@login_required
def get_registrations():
    """Get all registrations across teacher's trips"""
    try:
        if not current_user.is_teacher():
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Query parameters
        trip_id = request.args.get('trip_id', type=int)
        status = request.args.get('status')
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Base query - get registrations for teacher's trips
        query = db.session.query(TripRegistration).join(Trip).filter(
            Trip.organizer_id == current_user.id
        )
        
        # Apply filters
        if trip_id:
            query = query.filter(TripRegistration.trip_id == trip_id)
        
        if status:
            query = query.filter(TripRegistration.status == status)
        
        if search:
            # Search in participant name via join
            query = query.join(Participant).filter(
                or_(
                    Participant.first_name.ilike(f'%{search}%'),
                    Participant.last_name.ilike(f'%{search}%'),
                    TripRegistration.registration_number.ilike(f'%{search}%')
                )
            )
        
        # Order by registration date
        query = query.order_by(TripRegistration.registration_date.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        registrations_data = []
        for registration in pagination.items:
            reg_data = registration.serialize()
            reg_data.update({
                'consent_status': 'signed' if registration.consent_signed else 'pending',
                'medical_status': 'submitted' if registration.medical_form_submitted else 'pending',
                'payment_percentage': (float(registration.amount_paid) / float(registration.total_amount) * 100) 
                    if registration.total_amount else 0
            })
            registrations_data.append(reg_data)
        
        return jsonify({
            'success': True,
            'registrations': registrations_data,
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
        
        # Base query - get consents for participants in teacher's trips
        query = db.session.query(Consent).join(
            Participant, Consent.participant_id == Participant.id
        ).join(
            TripRegistration, Participant.id == TripRegistration.participant_id
        ).join(
            Trip, TripRegistration.trip_id == Trip.id
        ).filter(
            Trip.organizer_id == current_user.id
        )
        
        if trip_id:
            query = query.filter(TripRegistration.trip_id == trip_id)
        
        if signed is not None:
            query = query.filter(Consent.is_signed == signed)
        
        query = query.order_by(Consent.created_at.desc())
        
        consents = []
        for consent in query.all():
            # Get the registration for this participant
            registration = TripRegistration.query.filter_by(
                participant_id=consent.participant_id
            ).first()
            
            consent_data = consent.serialize()
            consent_data.update({
                'participant_name': consent.participant.full_name,
                'trip_title': registration.trip.title if registration and registration.trip else None
            })
            consents.append(consent_data)
        
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
        
        # Query notifications for current user
        query = Notification.query.filter_by(user_id=current_user.id)
        
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