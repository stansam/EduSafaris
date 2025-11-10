from flask import current_app
import click
import random
from datetime import datetime, timedelta
from app.extensions import db
from decimal import Decimal
from app.models import ServiceBooking, Trip, Vendor

def init_service_bookings_data():
    """Initialize service bookings with vendors"""
    try:
        current_app.logger.info("Initializing service bookings...")
        
        if ServiceBooking.query.first():
            current_app.logger.info("Service bookings already exist, skipping...")
            click.echo("Service bookings already initialized")
            return
        
        trips = Trip.query.all()
        vendors = Vendor.query.all()
        
        if not trips or not vendors:
            raise ValueError("Trips and vendors must be initialized first")
        
        bookings_created = 0
        
        for trip in trips:
            # Create 2-3 bookings per trip (transport, accommodation, activity)
            transport_vendor = next((v for v in vendors if v.business_type == 'transportation'), None)
            accommodation_vendor = next((v for v in vendors if v.business_type == 'accommodation'), None)
            activity_vendor = next((v for v in vendors if v.business_type == 'activity'), None)
            
            if transport_vendor:
                booking = ServiceBooking(
                    trip_id=trip.id,
                    vendor_id=transport_vendor.id,
                    booked_by=trip.organizer_id,
                    booking_type='transportation',
                    service_description='Round-trip bus transportation',
                    quoted_amount=Decimal('5000.00'),
                    final_amount=Decimal('4800.00'),
                    status='confirmed' if trip.status != 'draft' else 'pending',
                    service_start_date=datetime.combine(trip.start_date, datetime.min.time()),
                    service_end_date=datetime.combine(trip.end_date, datetime.max.time())
                )
                db.session.add(booking)
                bookings_created += 1
            
            if accommodation_vendor and trip.accommodation_included:
                booking = ServiceBooking(
                    trip_id=trip.id,
                    vendor_id=accommodation_vendor.id,
                    booked_by=trip.organizer_id,
                    booking_type='accommodation',
                    service_description='Camping accommodation with meals',
                    quoted_amount=Decimal('8000.00'),
                    final_amount=Decimal('7500.00'),
                    status='confirmed' if trip.status != 'draft' else 'pending',
                    service_start_date=datetime.combine(trip.start_date, datetime.min.time()),
                    service_end_date=datetime.combine(trip.end_date, datetime.max.time())
                )
                db.session.add(booking)
                bookings_created += 1
            
            if activity_vendor and random.random() > 0.5:
                booking = ServiceBooking(
                    trip_id=trip.id,
                    vendor_id=activity_vendor.id,
                    booked_by=trip.organizer_id,
                    booking_type='activity',
                    service_description='Guided nature walks and educational activities',
                    quoted_amount=Decimal('6000.00'),
                    final_amount=Decimal('5800.00'),
                    status='confirmed' if trip.status != 'draft' else 'pending',
                    service_start_date=datetime.combine(trip.start_date, datetime.min.time()),
                    service_end_date=datetime.combine(trip.end_date, datetime.max.time())
                )
                db.session.add(booking)
                bookings_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {bookings_created} service bookings")
        click.echo(f"✓ Created {bookings_created} service bookings")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize service bookings: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize service bookings: {str(e)}", fg='red'))
        raise