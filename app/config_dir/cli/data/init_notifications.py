from flask import current_app
import click
import random
from datetime import datetime, timedelta, date 
from app.extensions import db
from app.models import Notification, User, Trip

def init_notifications_data():
    """Initialize notifications"""
    try:
        current_app.logger.info("Initializing notifications...")
        
        if Notification.query.first():
            current_app.logger.info("Notifications already exist, skipping...")
            click.echo("Notifications already initialized")
            return
        
        parents = User.query.filter_by(role='parent').limit(10).all()
        trips = Trip.query.filter_by(status='registration_open').limit(3).all()
        
        notifications_created = 0
        
        notification_templates = [
            {
                'title': 'Trip Registration Confirmed',
                'message': 'Your child has been successfully registered for {trip_title}',
                'notification_type': 'trip_update',
                'priority': 'normal'
            },
            {
                'title': 'Payment Reminder',
                'message': 'Reminder: Payment deadline for {trip_title} is approaching',
                'notification_type': 'payment',
                'priority': 'high'
            },
            {
                'title': 'Document Submission Required',
                'message': 'Please submit required documents for {trip_title}',
                'notification_type': 'trip_update',
                'priority': 'high'
            },
            {
                'title': 'New Trip Available',
                'message': 'Check out our new educational trip: {trip_title}',
                'notification_type': 'trip_update',
                'priority': 'normal'
            }
        ]
        
        for parent in parents:
            # Send 2-3 notifications to each parent
            num_notifications = random.randint(2, 3)
            
            for _ in range(num_notifications):
                trip = random.choice(trips)
                template = random.choice(notification_templates)
                
                notification = Notification(
                    title=template['title'],
                    message=template['message'].format(trip_title=trip.title),
                    notification_type=template['notification_type'],
                    priority=template['priority'],
                    recipient_id=parent.id,
                    is_read=random.choice([True, False, False]),
                    send_email=True,
                    send_push=True,
                    email_sent=True,
                    push_sent=True,
                    sent_date=datetime.now() - timedelta(days=random.randint(1, 10)),
                    related_data={'trip_id': trip.id}
                )
                
                if notification.is_read:
                    notification.read_date = datetime.now() - timedelta(days=random.randint(0, 5))
                
                db.session.add(notification)
                notifications_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {notifications_created} notifications")
        click.echo(f"✓ Created {notifications_created} notifications")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize notifications: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize notifications: {str(e)}", fg='red'))
        raise
