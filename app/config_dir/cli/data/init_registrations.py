from flask import current_app
import click
import random
from datetime import datetime, timedelta
from app.extensions import db
from decimal import Decimal
from app.models import Participant, Trip, TripRegistration

def init_registrations_data():
    """Initialize trip registrations"""
    try:
        current_app.logger.info("Initializing trip registrations...")
        
        if TripRegistration.query.first():
            current_app.logger.info("Registrations already exist, skipping...")
            click.echo("Registrations already initialized")
            return
        
        participants = Participant.query.all()
        trips = Trip.query.filter(Trip.status.in_(['registration_open', 'completed'])).all()
        
        if not participants or not trips:
            raise ValueError("Participants and trips must be initialized first")
        
        registrations_created = 0
        
        # Register participants for various trips
        for trip in trips:
            # Determine number of registrations based on trip status
            if trip.status == 'completed':
                num_registrations = random.randint(15, min(25, len(participants)))
            else:
                num_registrations = random.randint(5, min(20, len(participants)))
            
            selected_participants = random.sample(participants, num_registrations)
            
            for participant in selected_participants:
                # Determine registration status
                if trip.status == 'completed':
                    status = 'completed'
                    payment_status = 'paid'
                    amount_paid = trip.price_per_student
                else:
                    status = random.choice(['pending', 'confirmed', 'confirmed', 'confirmed'])
                    payment_status = random.choice(['unpaid', 'partial', 'paid', 'paid'])
                    
                    if payment_status == 'paid':
                        amount_paid = trip.price_per_student
                    elif payment_status == 'partial':
                        amount_paid = trip.deposit_amount or (trip.price_per_student * Decimal('0.5'))
                    else:
                        amount_paid = Decimal('0.00')
                
                registration = TripRegistration(
                    participant_id=participant.id,
                    trip_id=trip.id,
                    parent_id=participant.parent_id,
                    status=status,
                    payment_status=payment_status,
                    total_amount=trip.price_per_student,
                    amount_paid=amount_paid,
                    consent_signed=status == 'confirmed' or status == 'completed',
                    medical_form_submitted=status == 'confirmed' or status == 'completed'
                )
                registration.generate_registration_number()
                
                if status == 'confirmed' or status == 'completed':
                    registration.confirmed_date = datetime.now() - timedelta(days=random.randint(1, 20))
                
                if status == 'completed':
                    registration.completed_date = trip.end_date
                
                db.session.add(registration)
                registrations_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {registrations_created} registrations")
        click.echo(f"✓ Created {registrations_created} registrations")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize registrations: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize registrations: {str(e)}", fg='red'))
        raise
