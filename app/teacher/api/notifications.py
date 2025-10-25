from flask import jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (
    Trip, Notification, 
)
from app.teacher import teacher_bp

@teacher_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        # Check authorization
        if notification.recipient_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        notification.mark_as_read()
        
        return jsonify({
            'success': True,
            'message': 'Notification marked as read'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@teacher_bp.route('/api/notifications/send', methods=['POST'])
@login_required
def send_notification():
    """Send notification to trip participants"""
    try:
        if not current_user.is_teacher():
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        trip = Trip.query.get_or_404(data['trip_id'])
        if trip.organizer_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Create notifications for all participants
        notifications = Notification.create_trip_notification(
            trip=trip,
            message=data['message'],
            notification_type=data.get('notification_type', 'trip_update'),
            priority=data.get('priority', 'normal')
        )
        
        return jsonify({
            'success': True,
            'message': f'Notification sent to {len(notifications)} recipients'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500