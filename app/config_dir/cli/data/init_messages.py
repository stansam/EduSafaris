from flask import current_app
import click
import random
from datetime import datetime, timedelta
from app.extensions import db
from app.models import User, Message, Trip, TripRegistration

def init_messages_data():
    """Initialize messages"""
    try:
        current_app.logger.info("Initializing messages...")
        
        if Message.query.first():
            current_app.logger.info("Messages already exist, skipping...")
            click.echo("Messages already initialized")
            return
        
        teachers = User.query.filter_by(role='teacher').all()
        parents = User.query.filter_by(role='parent').limit(5).all()
        trips = Trip.query.limit(3).all()
        
        messages_created = 0
        
        # Create messages between teachers and parents
        for trip in trips:
            teacher = trip.organizer
            registrations = TripRegistration.query.filter_by(trip_id=trip.id).limit(3).all()
            
            for registration in registrations:
                parent = registration.parent
                
                # Teacher sends message to parent
                message = Message(
                    sender_id=teacher.id,
                    recipient_id=parent.id,
                    subject=f'Update: {trip.title}',
                    content=f'Hello {parent.first_name}, just wanted to update you on the upcoming trip. All preparations are on track!',
                    message_type='direct',
                    priority='normal',
                    trip_id=trip.id,
                    is_read=random.choice([True, False])
                )
                if message.is_read:
                    message.read_date = datetime.now() - timedelta(days=random.randint(1, 5))
                
                db.session.add(message)
                messages_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {messages_created} messages")
        click.echo(f"✓ Created {messages_created} messages")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize messages: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize messages: {str(e)}", fg='red'))
        raise
