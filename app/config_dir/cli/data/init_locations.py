from flask import current_app
import click
import random
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Location, Trip, TripRegistration


def init_locations_data():
    """Initialize location tracking data"""
    try:
        current_app.logger.info("Initializing locations...")
        
        if Location.query.first():
            current_app.logger.info("Locations already exist, skipping...")
            click.echo("Locations already initialized")
            return
        
        # Only create locations for completed or in-progress trips
        completed_trips = Trip.query.filter(Trip.status.in_(['completed', 'in_progress'])).all()
        
        if not completed_trips:
            current_app.logger.info("No completed trips found, skipping locations...")
            click.echo("No completed trips to create locations for")
            return
        
        locations_created = 0
        
        # Kenya coordinates for various destinations
        destinations = {
            'Maasai Mara': (-1.5, 35.1),
            'Mount Kenya': (-0.15, 37.3),
            'Mombasa': (-4.05, 39.66),
            'Lake Nakuru': (-0.3, 36.08),
            'Nairobi': (-1.286389, 36.817223)
        }
        
        for trip in completed_trips:
            registrations = TripRegistration.query.filter_by(
                trip_id=trip.id,
                status='completed'
            ).limit(10).all()
            
            # Get base coordinates for destination
            base_lat, base_lon = destinations.get('Nairobi')  # Default
            for dest_name, coords in destinations.items():
                if dest_name.lower() in trip.destination.lower():
                    base_lat, base_lon = coords
                    break
            
            # Create locations for each participant
            for registration in registrations:
                # Create 3-5 location points throughout the trip
                num_locations = random.randint(3, 5)
                trip_duration = (trip.end_date - trip.start_date).days + 1
                
                for i in range(num_locations):
                    # Spread locations across trip days
                    day_offset = (trip_duration / num_locations) * i
                    timestamp = datetime.combine(trip.start_date, datetime.min.time()) + timedelta(days=day_offset, hours=random.randint(8, 18))
                    
                    # Add some random variation to coordinates
                    lat_variation = random.uniform(-0.05, 0.05)
                    lon_variation = random.uniform(-0.05, 0.05)
                    
                    location = Location(
                        name=f'Check-in Point {i+1}',
                        latitude=base_lat + lat_variation,
                        longitude=base_lon + lon_variation,
                        accuracy=random.uniform(5.0, 20.0),
                        city=trip.destination,
                        country=trip.destination_country,
                        timestamp=timestamp,
                        server_timestamp=timestamp,
                        location_type='checkin',
                        is_valid=True,
                        is_safe_zone=True,
                        device_id=f'device_{registration.participant_id}',
                        device_type='mobile',
                        trip_id=trip.id,
                        participant_id=registration.participant_id
                    )
                    db.session.add(location)
                    locations_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {locations_created} location records")
        click.echo(f"✓ Created {locations_created} location records")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize locations: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize locations: {str(e)}", fg='red'))
        raise