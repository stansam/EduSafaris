from flask import current_app
import click
import random
from datetime import datetime, timedelta, date 
from app.extensions import db
from decimal import Decimal
from app.models import Emergency, Trip

def init_emergencies_data():
    """Initialize emergency records"""
    try:
        current_app.logger.info("Initializing emergencies...")
        
        if Emergency.query.first():
            current_app.logger.info("Emergencies already exist, skipping...")
            click.echo("Emergencies already initialized")
            return
        
        completed_trips = Trip.query.filter_by(status='completed').all()
        
        if not completed_trips:
            current_app.logger.info("No completed trips found, skipping emergencies...")
            click.echo("No completed trips to create emergencies for")
            return
        
        emergencies_created = 0
        
        # Create a couple of resolved emergencies for completed trips
        for trip in completed_trips[:2]:
            emergency = Emergency(
                title='Minor Medical Incident',
                description='Student reported feeling unwell during activity',
                emergency_type='medical',
                severity='low',
                status='resolved',
                resolved=True,
                resolution_details='Student rested and recovered. No serious issues.',
                resolved_date=datetime.combine(trip.start_date, datetime.min.time()) + timedelta(days=1, hours=3),
                reported_by=trip.organizer.full_name,
                reporter_phone=trip.organizer.phone,
                injuries_reported=False,
                emergency_services_contacted=False,
                trip_id=trip.id,
                contact_person_id=trip.organizer_id
            )
            emergency.add_response_action('First aid administered')
            emergency.add_response_action('Parent notified')
            emergency.add_response_action('Student monitored and recovered')
            
            db.session.add(emergency)
            emergencies_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {emergencies_created} emergency records")
        click.echo(f"✓ Created {emergencies_created} emergency records")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize emergencies: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize emergencies: {str(e)}", fg='red'))
        raise
