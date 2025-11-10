import click
from flask import current_app
from flask.cli import with_appcontext
from datetime import datetime, date, timedelta
from decimal import Decimal
import random
from app.extensions import db
from app.models import (
    User, School, Participant, Trip, TripRegistration, Vendor,
    ServiceBooking, RegistrationPayment, ServicePayment,
    Advertisement, AdvertisementPayment, Document, Consent,
    Emergency, Location, Message, Notification, Review,
    ActivityLog
)
from app.config_dir.cli.data import (
    init_schools_data, init_activity_logs_data, init_advertisements_data, init_consents_data,
    init_users_data, init_participants_data, init_registrations_data, init_vendors_data, 
    init_documents_data, init_payments_data, init_service_bookings_data, init_trips_data,
    init_messages_data, init_notifications_data, init_emergencies_data, init_locations_data,
    init_reviews_data
    )


@click.group()
def init_db():
    """Database initialization commands"""
    pass


@init_db.command()
@with_appcontext
def init_all():
    """Initialize all tables with sample data"""
    current_app.logger.info("Starting full database initialization...")
    
    try:
        # Order matters due to foreign key dependencies
        init_schools_data()
        init_users_data()
        init_vendors_data()
        init_participants_data()
        init_trips_data()
        init_registrations_data()
        init_payments_data()
        init_service_bookings_data()
        init_advertisements_data()
        init_documents_data()
        init_consents_data()
        init_locations_data()
        init_emergencies_data()
        init_messages_data()
        init_notifications_data()
        init_reviews_data()
        init_activity_logs_data()
        
        current_app.logger.info("✓ Full database initialization completed successfully!")
        click.echo(click.style("✓ Database initialized with sample data!", fg='green', bold=True))
        
    except Exception as e:
        current_app.logger.error(f"Database initialization failed: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Initialization failed: {str(e)}", fg='red', bold=True))
        db.session.rollback()


@init_db.command()
@with_appcontext
def clear_all():
    """Clear all data from database (WARNING: Destructive!)"""
    if click.confirm('Are you sure you want to delete ALL data?', abort=True):
        try:
            current_app.logger.warning("Clearing all database tables...")
            
            # Drop all tables and recreate
            db.drop_all()
            db.create_all()
            
            current_app.logger.info("✓ All tables cleared and recreated")
            click.echo(click.style("✓ Database cleared successfully!", fg='green', bold=True))
            
        except Exception as e:
            current_app.logger.error(f"Failed to clear database: {str(e)}", exc_info=True)
            click.echo(click.style(f"✗ Clear failed: {str(e)}", fg='red', bold=True))



@init_db.command()
@with_appcontext
def init_schools():
    """Initialize schools table"""
    init_schools_data()


@init_db.command()
@with_appcontext
def init_users():
    """Initialize users table"""
    init_users_data()


@init_db.command()
@with_appcontext
def init_vendors():
    """Initialize vendors table"""
    init_vendors_data()


@init_db.command()
@with_appcontext
def init_participants():
    """Initialize participants table"""
    init_participants_data()


@init_db.command()
@with_appcontext
def init_trips():
    """Initialize trips table"""
    init_trips_data()


@init_db.command()
@with_appcontext
def init_registrations():
    """Initialize trip registrations table"""
    init_registrations_data()


@init_db.command()
@with_appcontext
def init_payments():
    """Initialize payments tables"""
    init_payments_data()


@init_db.command()
@with_appcontext
def init_bookings():
    """Initialize service bookings table"""
    init_service_bookings_data()


@init_db.command()
@with_appcontext
def init_ads():
    """Initialize advertisements table"""
    init_advertisements_data()


@init_db.command()
@with_appcontext
def init_documents():
    """Initialize documents table"""
    init_documents_data()


@init_db.command()
@with_appcontext
def init_consents():
    """Initialize consents table"""
    init_consents_data()


@init_db.command()
@with_appcontext
def init_locations():
    """Initialize locations table"""
    init_locations_data()


@init_db.command()
@with_appcontext
def init_emergencies():
    """Initialize emergencies table"""
    init_emergencies_data()


@init_db.command()
@with_appcontext
def init_messages():
    """Initialize messages table"""
    init_messages_data()


@init_db.command()
@with_appcontext
def init_notifications():
    """Initialize notifications table"""
    init_notifications_data()


@init_db.command()
@with_appcontext
def init_reviews():
    """Initialize reviews table"""
    init_reviews_data()


@init_db.command()
@with_appcontext
def init_activity_logs():
    """Initialize activity logs table"""
    init_activity_logs_data()


@init_db.command()
@with_appcontext
def stats():
    """Display database statistics"""
    try:
        click.echo(click.style("\n=== EduSafaris Database Statistics ===\n", fg='cyan', bold=True))
        
        stats_data = [
            ('Schools', School.query.count()),
            ('Users', User.query.count()),
            ('  - Admins', User.query.filter_by(role='admin').count()),
            ('  - Teachers', User.query.filter_by(role='teacher').count()),
            ('  - Parents', User.query.filter_by(role='parent').count()),
            ('  - Vendors', User.query.filter_by(role='vendor').count()),
            ('Vendors', Vendor.query.count()),
            ('Participants', Participant.query.count()),
            ('Trips', Trip.query.count()),
            ('  - Published', Trip.query.filter_by(is_published=True).count()),
            ('  - Registration Open', Trip.query.filter_by(status='registration_open').count()),
            ('  - Completed', Trip.query.filter_by(status='completed').count()),
            ('Registrations', TripRegistration.query.count()),
            ('  - Confirmed', TripRegistration.query.filter_by(status='confirmed').count()),
            ('  - Pending', TripRegistration.query.filter_by(status='pending').count()),
            ('  - Completed', TripRegistration.query.filter_by(status='completed').count()),
            ('Payments', RegistrationPayment.query.count()),
            ('  - Completed', RegistrationPayment.query.filter_by(status='completed').count()),
            ('Service Bookings', ServiceBooking.query.count()),
            ('Advertisements', Advertisement.query.count()),
            ('Documents', Document.query.count()),
            ('Consents', Consent.query.count()),
            ('Locations', Location.query.count()),
            ('Emergencies', Emergency.query.count()),
            ('Messages', Message.query.count()),
            ('Notifications', Notification.query.count()),
            ('Reviews', Review.query.count()),
            ('Activity Logs', ActivityLog.query.count()),
        ]
        
        for label, count in stats_data:
            indent = '  ' if label.startswith('  ') else ''
            label = label.strip()
            click.echo(f"{indent}{label}: {click.style(str(count), fg='green', bold=True)}")
        
        click.echo()
        
        # Financial summary
        total_revenue = db.session.query(db.func.sum(RegistrationPayment.amount)).filter_by(status='completed').scalar() or 0
        click.echo(click.style("Financial Summary:", fg='yellow', bold=True))
        click.echo(f"Total Revenue: {click.style(f'KES {float(total_revenue):,.2f}', fg='green', bold=True)}")
        
        click.echo()
        
    except Exception as e:
        current_app.logger.error(f"Failed to get stats: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to get statistics: {str(e)}", fg='red'))


@init_db.command()
@with_appcontext
@click.option('--table', help='Specific table to check')
def check(table):
    """Check if tables have data"""
    try:
        tables = {
            'schools': School,
            'users': User,
            'vendors': Vendor,
            'participants': Participant,
            'trips': Trip,
            'registrations': TripRegistration,
            'payments': RegistrationPayment,
            'bookings': ServiceBooking,
            'advertisements': Advertisement,
            'documents': Document,
            'consents': Consent,
            'locations': Location,
            'emergencies': Emergency,
            'messages': Message,
            'notifications': Notification,
            'reviews': Review,
            'activity_logs': ActivityLog
        }
        
        if table:
            if table not in tables:
                click.echo(click.style(f"Unknown table: {table}", fg='red'))
                click.echo(f"Available tables: {', '.join(tables.keys())}")
                return
            
            model = tables[table]
            count = model.query.count()
            status = 'populated' if count > 0 else 'empty'
            color = 'green' if count > 0 else 'yellow'
            click.echo(f"{table}: {click.style(status, fg=color)} ({count} records)")
        else:
            click.echo(click.style("\nDatabase Table Status:\n", fg='cyan', bold=True))
            for table_name, model in tables.items():
                count = model.query.count()
                status = '✓' if count > 0 else '✗'
                color = 'green' if count > 0 else 'yellow'
                click.echo(f"{status} {table_name}: {click.style(str(count), fg=color)} records")
            click.echo()
        
    except Exception as e:
        current_app.logger.error(f"Failed to check tables: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Check failed: {str(e)}", fg='red'))


@init_db.command()
@with_appcontext
@click.option('--email', prompt='User email', help='Email of user to show')
def show_user(email):
    """Show detailed user information"""
    try:
        user = User.query.filter_by(email=email).first()
        
        if not user:
            click.echo(click.style(f"User not found: {email}", fg='red'))
            return
        
        click.echo(click.style(f"\n=== User Details ===\n", fg='cyan', bold=True))
        click.echo(f"Name: {user.full_name}")
        click.echo(f"Email: {user.email}")
        click.echo(f"Phone: {user.phone}")
        click.echo(f"Role: {click.style(user.role, fg='yellow', bold=True)}")
        click.echo(f"Active: {user.is_active}")
        click.echo(f"Verified: {user.is_verified}")
        click.echo(f"Created: {user.created_at}")
        
        if user.role == 'teacher':
            click.echo(f"\nSchool: {user.school.name if user.school else 'N/A'}")
            click.echo(f"Department: {user.department}")
            click.echo(f"Active Trips: {user.get_active_trips_count()}")
            click.echo(f"Total Students: {user.get_total_students()}")
        
        elif user.role == 'parent':
            click.echo(f"\nChildren: {user.get_children_count()}")
            click.echo(f"Active Registrations: {len(user.get_active_registrations())}")
            click.echo(f"Total Spent: KES {user.get_total_spent():,.2f}")
            click.echo(f"Outstanding Balance: KES {user.get_outstanding_balance():,.2f}")
        
        elif user.role == 'vendor':
            vendor = user.vendor_profile
            if vendor:
                click.echo(f"\nBusiness: {vendor.business_name}")
                click.echo(f"Type: {vendor.business_type}")
                click.echo(f"Rating: {vendor.average_rating:.1f}/5.0")
                click.echo(f"Reviews: {vendor.total_reviews}")
        
        click.echo()
        
    except Exception as e:
        current_app.logger.error(f"Failed to show user: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed: {str(e)}", fg='red'))


@init_db.command()
@with_appcontext
def show_trips():
    """Show all trips summary"""
    try:
        trips = Trip.query.order_by(Trip.start_date).all()
        
        if not trips:
            click.echo(click.style("No trips found", fg='yellow'))
            return
        
        click.echo(click.style(f"\n=== All Trips ({len(trips)}) ===\n", fg='cyan', bold=True))
        
        for trip in trips:
            status_color = {
                'registration_open': 'green',
                'completed': 'blue',
                'in_progress': 'yellow',
                'cancelled': 'red'
            }.get(trip.status, 'white')
            
            click.echo(f"{trip.id}. {click.style(trip.title, bold=True)}")
            click.echo(f"   Status: {click.style(trip.status, fg=status_color)}")
            click.echo(f"   Dates: {trip.start_date} to {trip.end_date}")
            click.echo(f"   Participants: {trip.current_participants_count}/{trip.max_participants}")
            click.echo(f"   Price: KES {float(trip.price_per_student):,.2f}")
            click.echo(f"   Organizer: {trip.organizer.full_name}")
            click.echo()
        
    except Exception as e:
        current_app.logger.error(f"Failed to show trips: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed: {str(e)}", fg='red'))

