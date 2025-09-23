import os
import base64
import secrets
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.exceptions import Forbidden

from app.extensions import db, socketio
from app.models.user import User
from app.models.trip import Trip
from app.models.participant import Participant
from app.models.consent import Consent
from app.models.notification import Notification
from app.utils import send_email, send_sms  # External helpers
from .forms import ConsentForm, NotificationForm
from . import parent_comm_bp


@parent_comm_bp.route('/trips')
@login_required
def parent_trips():
    """Parent dashboard listing trips their children are registered for"""
    if current_user.role != 'parent':
        flash('Access denied. Parent access required.', 'error')
        return redirect(url_for('main.index'))
    
    # Get all participants registered by this parent
    participants = Participant.query.filter_by(user_id=current_user.id).all()
    
    # Organize data by trip
    trips_data = []
    for participant in participants:
        trip = participant.trip
        if trip:
            # Check consent status
            consent = Consent.query.filter_by(
                participant_id=participant.id,
                consent_type='trip_participation'
            ).first()
            
            # Count unread notifications for this trip
            unread_notifications = Notification.query.filter_by(
                recipient_id=current_user.id,
                is_read=False
            ).filter(
                Notification.related_data.contains({'trip_id': trip.id})
            ).count()
            
            trips_data.append({
                'trip': trip,
                'participant': participant,
                'consent': consent,
                'consent_status': 'signed' if consent and consent.is_signed else 'pending',
                'payment_status': participant.payment_status,
                'outstanding_balance': participant.outstanding_balance,
                'unread_notifications': unread_notifications
            })
    
    return render_template(
        'parent_comm/parent_trips.html',
        trips_data=trips_data,
        active_tab='trips'
    )


@parent_comm_bp.route('/consent/<int:trip_id>', methods=['GET', 'POST'])
@login_required
def consent_form(trip_id):
    """Handle consent form display and submission"""
    if current_user.role != 'parent':
        flash('Access denied. Parent access required.', 'error')
        return redirect(url_for('main.index'))
    
    # Find the participant for this trip registered by this parent
    participant = Participant.query.filter_by(
        trip_id=trip_id,
        user_id=current_user.id
    ).first()
    
    if not participant:
        flash('Participant not found or access denied.', 'error')
        return redirect(url_for('parent_comm.parent_trips'))
    
    trip = participant.trip
    
    # Check if consent already exists
    existing_consent = Consent.query.filter_by(
        participant_id=participant.id,
        consent_type='trip_participation'
    ).first()
    
    if existing_consent and existing_consent.is_signed:
        flash('Consent form has already been signed for this trip.', 'info')
        return redirect(url_for('parent_comm.parent_trips'))
    
    form = ConsentForm()
    
    # Pre-populate form data
    form.student_name.data = participant.full_name
    if request.method == 'GET':
        form.medical_info.data = participant.medical_conditions or ''
        form.emergency_contact.data = f"{participant.emergency_contact_1_name} - {participant.emergency_contact_1_phone}" if participant.emergency_contact_1_name else ''
    
    if form.validate_on_submit():
        try:
            # Handle signature data
            signature_path = None
            signature_data = None
            
            if form.signature_image.data:
                # Process canvas signature
                signature_data_url = form.signature_image.data
                if signature_data_url.startswith('data:image/png;base64,'):
                    # Extract base64 data
                    signature_base64 = signature_data_url.split(',')[1]
                    
                    # Generate secure filename
                    filename = f"consent_{participant.id}_{secrets.token_hex(8)}.png"
                    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'consents')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    signature_path = os.path.join(upload_dir, filename)
                    
                    # Save signature image
                    with open(signature_path, 'wb') as f:
                        f.write(base64.b64decode(signature_base64))
                    
                    signature_data = f"uploads/consents/{filename}"
            
            # Use typed signature if no canvas signature
            if not signature_data and form.signature_text.data:
                signature_data = f"typed:{form.signature_text.data}"
            
            # Create or update consent
            if existing_consent:
                consent = existing_consent
            else:
                consent = Consent(
                    participant_id=participant.id,
                    parent_id=current_user.id,
                    consent_type='trip_participation',
                    title=f'Trip Participation Consent - {trip.title}',
                    content=f'Consent for {participant.full_name} to participate in {trip.title}'
                )
                db.session.add(consent)
            
            # Sign the consent
            consent.sign_consent(
                signer_name=current_user.full_name,
                signer_relationship='parent',
                signer_email=current_user.email,
                signature_data=signature_data,
                ip_address=request.remote_addr
            )
            
            # Update participant medical info if provided
            if form.medical_info.data:
                participant.medical_conditions = form.medical_info.data
            
            db.session.commit()
            
            flash('Consent form submitted successfully!', 'success')
            return redirect(url_for('parent_comm.parent_trips'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Consent submission error: {str(e)}')
            flash('An error occurred while submitting the consent form.', 'error')
    
    return render_template(
        'parent_comm/consent_form.html',
        form=form,
        trip=trip,
        participant=participant,
        existing_consent=existing_consent
    )


@parent_comm_bp.route('/notifications')
@login_required
def notifications():
    """List parent's notifications"""
    if current_user.role != 'parent':
        flash('Access denied. Parent access required.', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('NOTIFICATIONS_PER_PAGE', 20)
    
    notifications = Notification.query.filter_by(
        recipient_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Count unread notifications
    unread_count = Notification.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).count()
    
    return render_template(
        'parent_comm/notifications.html',
        notifications=notifications,
        unread_count=unread_count,
        active_tab='notifications'
    )


@parent_comm_bp.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    if current_user.role != 'parent':
        return jsonify({'error': 'Access denied'}), 403
    
    notification = Notification.query.filter_by(
        id=notification_id,
        recipient_id=current_user.id
    ).first()
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    notification.mark_as_read()
    return jsonify({'success': True})


@parent_comm_bp.route('/send_notification', methods=['GET', 'POST'])
@login_required
def send_notification():
    """Send notification to parents (teachers and admins only)"""
    if current_user.role not in ['teacher', 'admin']:
        flash('Access denied. Teacher or admin access required.', 'error')
        return redirect(url_for('main.index'))
    
    form = NotificationForm()
    
    # Populate trip choices
    if current_user.role == 'teacher':
        trips = current_user.organized_trips.filter(Trip.status.in_(['active', 'in_progress'])).all()
    else:  # admin
        trips = Trip.query.filter(Trip.status.in_(['active', 'in_progress'])).all()
    
    form.trip_id.choices = [(0, 'Select a trip')] + [(trip.id, trip.title) for trip in trips]
    
    if form.validate_on_submit():
        try:
            trip = Trip.query.get(form.trip_id.data)
            if not trip:
                flash('Invalid trip selected.', 'error')
                return render_template('parent_comm/send_notification.html', form=form)
            
            # Verify teacher can send notifications for this trip
            if current_user.role == 'teacher' and trip.organizer_id != current_user.id:
                flash('You can only send notifications for your own trips.', 'error')
                return render_template('parent_comm/send_notification.html', form=form)
            
            # Get all parents with children on this trip
            participants = Participant.query.filter_by(trip_id=trip.id).all()
            parent_ids = set()
            
            for participant in participants:
                if participant.user_id and participant.user.role == 'parent':
                    parent_ids.add(participant.user_id)
            
            if not parent_ids:
                flash('No parents found for this trip.', 'warning')
                return render_template('parent_comm/send_notification.html', form=form)
            
            # Create notifications for each parent
            notifications_created = []
            for parent_id in parent_ids:
                notification = Notification(
                    title=f'Trip Update: {trip.title}',
                    message=form.message.data,
                    notification_type='trip_update',
                    priority='normal',
                    sender_id=current_user.id,
                    recipient_id=parent_id,
                    related_data={'trip_id': trip.id}
                )
                db.session.add(notification)
                notifications_created.append(notification)
            
            db.session.commit()
            
            # Broadcast via SocketIO to online parents
            for notification in notifications_created:
                socketio.emit(
                    'new_notification',
                    notification.serialize(),
                    room=f'user_{notification.recipient_id}'
                )
                
                # Send email/SMS fallback for offline parents
                try:
                    parent = User.query.get(notification.recipient_id)
                    if parent:
                        # Send email notification
                        send_email(
                            to=parent.email,
                            subject=notification.title,
                            template='notification_email.html',
                            notification=notification,
                            trip=trip
                        )
                        
                        # Send SMS if parent has phone number
                        if parent.phone:
                            send_sms(
                                phone=parent.phone,
                                message=f"{notification.title}: {notification.message[:100]}..."
                            )
                except Exception as e:
                    current_app.logger.error(f'Failed to send notification fallback: {str(e)}')
            
            flash(f'Notification sent to {len(parent_ids)} parents successfully!', 'success')
            return redirect(url_for('parent_comm.send_notification'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Notification send error: {str(e)}')
            flash('An error occurred while sending the notification.', 'error')
    
    return render_template('parent_comm/send_notification.html', form=form)


@parent_comm_bp.route('/consent-pdf/<int:participant_id>')
@login_required
def consent_pdf(participant_id):
    """Generate printable consent form"""
    if current_user.role != 'parent':
        flash('Access denied. Parent access required.', 'error')
        return redirect(url_for('main.index'))
    
    participant = Participant.query.filter_by(
        id=participant_id,
        user_id=current_user.id
    ).first()
    
    if not participant:
        flash('Participant not found or access denied.', 'error')
        return redirect(url_for('parent_comm.parent_trips'))
    
    consent = Consent.query.filter_by(
        participant_id=participant_id,
        consent_type='trip_participation'
    ).first()
    
    if not consent or not consent.is_signed:
        flash('No signed consent found for this participant.', 'error')
        return redirect(url_for('parent_comm.parent_trips'))
    
    return render_template(
        'parent_comm/snippets/consent_pdf.html',
        participant=participant,
        consent=consent,
        trip=participant.trip
    )


# SocketIO event handlers
@socketio.on('join_parent_room')
def join_parent_room():
    """Join parent-specific room for real-time notifications"""
    if current_user.is_authenticated and current_user.role == 'parent':
        room = f'user_{current_user.id}'
        socketio.join_room(room)
        socketio.emit('room_joined', {'room': room})


@socketio.on('leave_parent_room')
def leave_parent_room():
    """Leave parent room"""
    if current_user.is_authenticated and current_user.role == 'parent':
        room = f'user_{current_user.id}'
        socketio.leave_room(room)