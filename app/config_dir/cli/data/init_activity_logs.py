from flask import current_app
import click
import random
from datetime import datetime, timedelta
from app.extensions import db
from app.models import User, ActivityLog, RegistrationPayment, Trip, TripRegistration

def init_activity_logs_data():
    """Initialize activity logs"""
    try:
        current_app.logger.info("Initializing activity logs...")
        
        if ActivityLog.query.first():
            current_app.logger.info("Activity logs already exist, skipping...")
            click.echo("Activity logs already initialized")
            return
        
        users = User.query.all()
        trips = Trip.query.all()
        registrations = TripRegistration.query.all()
        payments = RegistrationPayment.query.all()
        
        logs_created = 0
        
        # User login activities
        for user in users[:15]:
            for _ in range(random.randint(3, 8)):
                log = ActivityLog(
                    action='login',
                    user_id=user.id,
                    description=f'{user.full_name} logged in',
                    action_category='user',
                    entity_type='user',
                    entity_id=user.id,
                    status='success',
                    ip_address=f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}',
                    request_method='POST',
                    request_url='/auth/login'
                )
                # Backdate the creation
                log.created_at = datetime.now() - timedelta(days=random.randint(1, 30))
                db.session.add(log)
                logs_created += 1
        
        # Trip creation activities
        for trip in trips:
            log = ActivityLog.log_trip(
                trip=trip,
                user_id=trip.organizer_id,
                action_type='created'
            )
            log.created_at = trip.created_at
            logs_created += 1
        
        # Registration activities
        for registration in registrations[:20]:
            log = ActivityLog(
                action='booking_created',
                user_id=registration.parent_id,
                entity_type='registration',
                entity_id=registration.id,
                description=f'Registration created for {registration.trip.title}',
                action_category='booking',
                trip_id=registration.trip_id,
                status='success',
                new_values={
                    'registration_number': registration.registration_number,
                    'status': registration.status
                }
            )
            log.created_at = registration.registration_date
            db.session.add(log)
            logs_created += 1
        
        # Payment activities
        for payment in payments[:20]:
            log = ActivityLog.log_payment(
                payment=payment,
                user_id=payment.parent_id
            )
            log.created_at = payment.payment_date
            logs_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {logs_created} activity logs")
        click.echo(f"✓ Created {logs_created} activity logs")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize activity logs: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize activity logs: {str(e)}", fg='red'))
        raise