from flask import current_app
import click
import random
from datetime import datetime, timedelta
from app.extensions import db
from app.models import TripRegistration, RegistrationPayment


def init_payments_data():
    """Initialize payment records"""
    try:
        current_app.logger.info("Initializing payments...")
        
        if RegistrationPayment.query.first():
            current_app.logger.info("Payments already exist, skipping...")
            click.echo("Payments already initialized")
            return
        
        registrations = TripRegistration.query.filter(
            TripRegistration.payment_status.in_(['partial', 'paid'])
        ).all()
        
        if not registrations:
            current_app.logger.info("No paid registrations found, skipping payments...")
            click.echo("No paid registrations to create payments for")
            return
        
        payments_created = 0
        
        for registration in registrations:
            # Create payment record
            payment = RegistrationPayment(
                registration_id=registration.id,
                parent_id=registration.parent_id,
                amount=registration.amount_paid,
                currency='KES',
                payment_method=random.choice(['mpesa', 'stripe', 'bank_transfer']),
                status='completed',
                payment_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                processed_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                description=f'Payment for {registration.trip.title}',
                payer_name=registration.parent.full_name,
                payer_email=registration.parent.email,
                payer_phone=registration.parent.phone
            )
            payment.generate_reference_number()
            payment.transaction_id = f'TXN{random.randint(100000, 999999)}'
            payment.receipt_number = f'RCT{random.randint(100000, 999999)}'
            
            db.session.add(payment)
            payments_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {payments_created} payments")
        click.echo(f"✓ Created {payments_created} payments")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize payments: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize payments: {str(e)}", fg='red'))
        raise