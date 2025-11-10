from flask import current_app
import click
import random
from datetime import datetime, timedelta, date 
from app.extensions import db
from decimal import Decimal
from app.models import Consent, TripRegistration

def init_consents_data():
    """Initialize consent forms"""
    try:
        current_app.logger.info("Initializing consents...")
        
        if Consent.query.first():
            current_app.logger.info("Consents already exist, skipping...")
            click.echo("Consents already initialized")
            return
        
        registrations = TripRegistration.query.filter_by(consent_signed=True).all()
        
        if not registrations:
            current_app.logger.info("No confirmed registrations found, skipping consents...")
            click.echo("No confirmed registrations to create consents for")
            return
        
        consents_created = 0
        
        for registration in registrations[:15]:
            # Trip participation consent
            consent = Consent(
                consent_type='trip_participation',
                title='Trip Participation Consent',
                content='I hereby give consent for my child to participate in this educational trip...',
                is_signed=True,
                signed_date=datetime.now() - timedelta(days=random.randint(5, 25)),
                signer_name=registration.parent.full_name,
                signer_relationship='parent',
                signer_email=registration.parent.email,
                is_required=True,
                participant_id=registration.participant_id,
                parent_id=registration.parent_id
            )
            db.session.add(consent)
            consents_created += 1
            
            # Photo release consent
            if random.random() > 0.3:
                consent = Consent(
                    consent_type='photo_release',
                    title='Photo Release Consent',
                    content='I consent to photographs and videos being taken during the trip...',
                    is_signed=True,
                    signed_date=datetime.now() - timedelta(days=random.randint(5, 25)),
                    signer_name=registration.parent.full_name,
                    signer_relationship='parent',
                    signer_email=registration.parent.email,
                    is_required=False,
                    participant_id=registration.participant_id,
                    parent_id=registration.parent_id
                )
                db.session.add(consent)
                consents_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {consents_created} consents")
        click.echo(f"✓ Created {consents_created} consents")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize consents: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize consents: {str(e)}", fg='red'))
        raise
