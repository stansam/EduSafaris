import click
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models.trip import Trip
from flask import current_app
from app.config_dir.cli.trips_utils import get_or_create_organizer, get_trip_data
from app.extensions import db



def seed_trips_command(clear):
    """Seed the database with sample Kenyan educational trips"""
    try:
        current_app.logger.info("=" * 60)
        current_app.logger.info("Starting trip seeding process...")
        current_app.logger.info("=" * 60)
        
        # Clear existing trips if flag is set
        if clear:
            current_app.logger.warning("Clearing existing trips...")
            try:
                deleted_count = Trip.query.delete()
                db.session.commit()
                current_app.logger.info(f"Deleted {deleted_count} existing trips")
            except SQLAlchemyError as e:
                db.session.rollback()
                current_app.logger.error(f"Error clearing trips: {str(e)}")
                raise
        
        # Get or create organizer
        organizer = get_or_create_organizer()
        
        # Get trip data
        trips_data = get_trip_data(organizer.id)
        
        # Track statistics
        created_count = 0
        failed_count = 0
        failed_trips = []
        
        # Create trips
        for idx, trip_data in enumerate(trips_data, 1):
            try:
                current_app.logger.info(f"\n[{idx}/12] Creating trip: {trip_data['title']}")
                
                # Check if trip already exists
                existing_trip = Trip.query.filter_by(
                    title=trip_data['title'],
                    organizer_id=organizer.id
                ).first()
                
                if existing_trip:
                    current_app.logger.warning(f"  ⚠ Trip already exists (ID: {existing_trip.id})")
                    continue
                
                # Create new trip
                trip = Trip(**trip_data)
                db.session.add(trip)
                db.session.flush()  # Get the ID without committing
                
                current_app.logger.info(f"  ✓ Created: {trip.title}")
                current_app.logger.info(f"    - Destination: {trip.destination}")
                current_app.logger.info(f"    - Duration: {trip.duration_days} days")
                current_app.logger.info(f"    - Price: KSh {trip.price_per_student:,.2f}")
                current_app.logger.info(f"    - Capacity: {trip.max_participants} students")
                current_app.logger.info(f"    - Start Date: {trip.start_date}")
                
                created_count += 1
                
            except IntegrityError as e:
                db.session.rollback()
                current_app.logger.error(f"  ✗ Integrity error for '{trip_data['title']}': {str(e)}")
                failed_count += 1
                failed_trips.append(trip_data['title'])
                
            except SQLAlchemyError as e:
                db.session.rollback()
                current_app.logger.error(f"  ✗ Database error for '{trip_data['title']}': {str(e)}")
                failed_count += 1
                failed_trips.append(trip_data['title'])
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"  ✗ Unexpected error for '{trip_data['title']}': {str(e)}")
                failed_count += 1
                failed_trips.append(trip_data['title'])
        
        # Commit all successful trips
        try:
            db.session.commit()
            current_app.logger.info("\n" + "=" * 60)
            current_app.logger.info("SEEDING SUMMARY")
            current_app.logger.info("=" * 60)
            current_app.logger.info(f"✓ Successfully created: {created_count} trips")
            
            if failed_count > 0:
                current_app.logger.warning(f"✗ Failed: {failed_count} trips")
                current_app.logger.warning(f"Failed trips: {', '.join(failed_trips)}")
            
            current_app.logger.info(f"Total in database: {Trip.query.count()} trips")
            current_app.logger.info("=" * 60)
            
            click.echo(click.style(
                f"\n✓ Successfully seeded {created_count} trips!",
                fg='green',
                bold=True
            ))
            
            if failed_count > 0:
                click.echo(click.style(
                    f"✗ {failed_count} trips failed to create",
                    fg='yellow'
                ))
                
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error committing transactions: {str(e)}")
            click.echo(click.style(
                "✗ Failed to commit trips to database",
                fg='red',
                bold=True
            ))
            raise
            
    except Exception as e:
        current_app.logger.error(f"Fatal error during seeding: {str(e)}")
        click.echo(click.style(
            f"✗ Seeding failed: {str(e)}",
            fg='red',
            bold=True
        ))
        raise
