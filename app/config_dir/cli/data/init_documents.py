from flask import current_app
import click
from datetime import timedelta, date 
from app.extensions import db
from app.models import Document, Trip, Participant, Vendor

def init_documents_data():
    """Initialize documents"""
    try:
        current_app.logger.info("Initializing documents...")
        
        if Document.query.first():
            current_app.logger.info("Documents already exist, skipping...")
            click.echo("Documents already initialized")
            return
        
        trips = Trip.query.all()
        participants = Participant.query.limit(10).all()
        vendors = Vendor.query.all()
        
        docs_created = 0
        
        # Trip documents
        for trip in trips[:3]:
            doc = Document(
                title=f'{trip.title} - Itinerary',
                description='Detailed trip itinerary and schedule',
                file_name=f'itinerary_{trip.id}.pdf',
                file_path=f'/documents/trips/{trip.id}/itinerary.pdf',
                file_size=245680,
                file_type='application/pdf',
                document_type='itinerary',
                is_verified=True,
                is_active=True,
                uploaded_by=trip.organizer_id,
                trip_id=trip.id
            )
            db.session.add(doc)
            docs_created += 1
        
        # Participant documents
        for participant in participants[:5]:
            doc = Document(
                title=f'Medical Form - {participant.full_name}',
                description='Completed medical information form',
                file_name=f'medical_{participant.id}.pdf',
                file_path=f'/documents/participants/{participant.id}/medical.pdf',
                file_size=128450,
                file_type='application/pdf',
                document_type='medical_form',
                is_verified=True,
                is_active=True,
                uploaded_by=participant.parent_id,
                participant_id=participant.id
            )
            db.session.add(doc)
            docs_created += 1
        
        # Vendor documents
        for vendor in vendors:
            doc = Document(
                title=f'{vendor.business_name} - Business License',
                description='Valid business operating license',
                file_name=f'license_{vendor.id}.pdf',
                file_path=f'/documents/vendors/{vendor.id}/license.pdf',
                file_size=356890,
                file_type='application/pdf',
                document_type='vendor_license',
                is_verified=True,
                is_active=True,
                uploaded_by=vendor.user_id,
                vendor_id=vendor.id,
                expiry_date=date.today() + timedelta(days=365)
            )
            db.session.add(doc)
            docs_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {docs_created} documents")
        click.echo(f"✓ Created {docs_created} documents")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize documents: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize documents: {str(e)}", fg='red'))
        raise

















