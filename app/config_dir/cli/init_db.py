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


# ============================================================================
# MAIN INITIALIZATION COMMANDS
# ============================================================================

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


# ============================================================================
# INDIVIDUAL TABLE INITIALIZATION COMMANDS
# ============================================================================

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


# ============================================================================
# DATA INITIALIZATION FUNCTIONS
# ============================================================================

def init_schools_data():
    """Initialize schools with sample data"""
    try:
        current_app.logger.info("Initializing schools...")
        
        if School.query.first():
            current_app.logger.info("Schools already exist, skipping...")
            click.echo("Schools already initialized")
            return
        
        schools_data = [
            {
                'name': 'Nairobi International School',
                'short_name': 'NIS',
                'school_type': 'primary',
                'email': 'info@nairobiintl.ac.ke',
                'phone': '+254-700-123456',
                'website': 'https://nairobiintl.ac.ke',
                'address_line1': 'Valley Road',
                'city': 'Nairobi',
                'state': 'Nairobi County',
                'country': 'Kenya',
                'postal_code': '00100',
                'is_verified': True,
                'is_active': True,
                'total_students': 450,
                'total_teachers': 35
            },
            {
                'name': 'Brookhouse School',
                'short_name': 'BHS',
                'school_type': 'secondary',
                'email': 'admissions@brookhouse.ac.ke',
                'phone': '+254-700-234567',
                'website': 'https://brookhouse.ac.ke',
                'address_line1': 'Langata Road',
                'city': 'Nairobi',
                'state': 'Nairobi County',
                'country': 'Kenya',
                'postal_code': '00100',
                'is_verified': True,
                'is_active': True,
                'total_students': 850,
                'total_teachers': 65
            },
            {
                'name': 'Braeburn School Arusha',
                'short_name': 'BSA',
                'school_type': 'primary',
                'email': 'info@braeburn.ac.tz',
                'phone': '+255-27-2500000',
                'website': 'https://braeburn-arusha.com',
                'address_line1': 'Njiro Road',
                'city': 'Arusha',
                'state': 'Arusha',
                'country': 'Tanzania',
                'postal_code': '23456',
                'is_verified': True,
                'is_active': True,
                'total_students': 320,
                'total_teachers': 28
            },
            {
                'name': 'St. Andrews School Turi',
                'short_name': 'SAST',
                'school_type': 'high',
                'email': 'info@satschool.com',
                'phone': '+254-700-345678',
                'website': 'https://satschool.com',
                'address_line1': 'Molo Road',
                'city': 'Turi',
                'state': 'Nakuru County',
                'country': 'Kenya',
                'postal_code': '20106',
                'is_verified': True,
                'is_active': True,
                'total_students': 550,
                'total_teachers': 45
            },
            {
                'name': 'Peponi School',
                'short_name': 'PS',
                'school_type': 'secondary',
                'email': 'office@peponischool.org',
                'phone': '+254-700-456789',
                'website': 'https://peponischool.org',
                'address_line1': 'Peponi Road',
                'city': 'Nairobi',
                'state': 'Nairobi County',
                'country': 'Kenya',
                'postal_code': '00100',
                'is_verified': True,
                'is_active': True,
                'total_students': 600,
                'total_teachers': 50
            }
        ]
        
        for school_data in schools_data:
            school = School(**school_data)
            db.session.add(school)
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {len(schools_data)} schools")
        click.echo(f"✓ Created {len(schools_data)} schools")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize schools: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize schools: {str(e)}", fg='red'))
        raise


def init_users_data():
    """Initialize users with sample data"""
    try:
        current_app.logger.info("Initializing users...")
        
        if User.query.first():
            current_app.logger.info("Users already exist, skipping...")
            click.echo("Users already initialized")
            return
        
        schools = School.query.all()
        if not schools:
            raise ValueError("Schools must be initialized first")
        
        # Admin users
        admin = User(
            email='admin@edusafaris.com',
            first_name='Admin',
            last_name='User',
            phone='+254-700-000001',
            role='admin',
            is_active=True,
            is_verified=True
        )
        admin.password = 'Admin@123'
        db.session.add(admin)
        
        # Teacher users
        teachers_data = [
            {
                'email': 'john.kamau@nairobiintl.ac.ke',
                'first_name': 'John',
                'last_name': 'Kamau',
                'phone': '+254-722-111111',
                'school_id': schools[0].id,
                'teacher_id': 'TCH001',
                'department': 'Science',
                'specialization': 'Biology',
                'years_of_experience': 12
            },
            {
                'email': 'mary.wanjiru@brookhouse.ac.ke',
                'first_name': 'Mary',
                'last_name': 'Wanjiru',
                'phone': '+254-722-222222',
                'school_id': schools[1].id,
                'teacher_id': 'TCH002',
                'department': 'History',
                'specialization': 'East African History',
                'years_of_experience': 8
            },
            {
                'email': 'david.omondi@braeburn.ac.tz',
                'first_name': 'David',
                'last_name': 'Omondi',
                'phone': '+255-755-333333',
                'school_id': schools[2].id,
                'teacher_id': 'TCH003',
                'department': 'Geography',
                'specialization': 'Physical Geography',
                'years_of_experience': 15
            },
            {
                'email': 'sarah.mwangi@satschool.com',
                'first_name': 'Sarah',
                'last_name': 'Mwangi',
                'phone': '+254-722-444444',
                'school_id': schools[3].id,
                'teacher_id': 'TCH004',
                'department': 'Environmental Studies',
                'specialization': 'Conservation',
                'years_of_experience': 10
            }
        ]
        
        for teacher_data in teachers_data:
            teacher = User(
                role='teacher',
                is_active=True,
                is_verified=True,
                **teacher_data
            )
            teacher.password = 'Teacher@123'
            db.session.add(teacher)
        
        # Parent users
        parents_data = [
            {'email': 'james.njoroge@email.com', 'first_name': 'James', 'last_name': 'Njoroge', 'phone': '+254-722-555551'},
            {'email': 'grace.akinyi@email.com', 'first_name': 'Grace', 'last_name': 'Akinyi', 'phone': '+254-722-555552'},
            {'email': 'peter.kimani@email.com', 'first_name': 'Peter', 'last_name': 'Kimani', 'phone': '+254-722-555553'},
            {'email': 'lucy.wambui@email.com', 'first_name': 'Lucy', 'last_name': 'Wambui', 'phone': '+254-722-555554'},
            {'email': 'joseph.otieno@email.com', 'first_name': 'Joseph', 'last_name': 'Otieno', 'phone': '+254-722-555555'},
            {'email': 'esther.nyambura@email.com', 'first_name': 'Esther', 'last_name': 'Nyambura', 'phone': '+254-722-555556'},
            {'email': 'daniel.maina@email.com', 'first_name': 'Daniel', 'last_name': 'Maina', 'phone': '+254-722-555557'},
            {'email': 'rose.adhiambo@email.com', 'first_name': 'Rose', 'last_name': 'Adhiambo', 'phone': '+254-722-555558'},
            {'email': 'samuel.kariuki@email.com', 'first_name': 'Samuel', 'last_name': 'Kariuki', 'phone': '+254-722-555559'},
            {'email': 'jane.wairimu@email.com', 'first_name': 'Jane', 'last_name': 'Wairimu', 'phone': '+254-722-555560'},
        ]
        
        for parent_data in parents_data:
            parent = User(
                role='parent',
                is_active=True,
                is_verified=True,
                city='Nairobi',
                country='Kenya',
                **parent_data
            )
            parent.password = 'Parent@123'
            db.session.add(parent)
        
        # Vendor users
        vendors_data = [
            {'email': 'contact@safaritrans.com', 'first_name': 'Safari', 'last_name': 'Transport', 'phone': '+254-722-666661'},
            {'email': 'info@wildcamping.com', 'first_name': 'Wilderness', 'last_name': 'Camping', 'phone': '+254-722-666662'},
            {'email': 'booking@marineparks.com', 'first_name': 'Marine', 'last_name': 'Parks', 'phone': '+254-722-666663'},
            {'email': 'tours@mountainguides.com', 'first_name': 'Mountain', 'last_name': 'Guides', 'phone': '+254-722-666664'},
        ]
        
        for vendor_data in vendors_data:
            vendor = User(
                role='vendor',
                is_active=True,
                is_verified=True,
                **vendor_data
            )
            vendor.password = 'Vendor@123'
            db.session.add(vendor)
        
        db.session.commit()
        
        total_users = 1 + len(teachers_data) + len(parents_data) + len(vendors_data)
        current_app.logger.info(f"✓ Created {total_users} users")
        click.echo(f"✓ Created {total_users} users (1 admin, {len(teachers_data)} teachers, {len(parents_data)} parents, {len(vendors_data)} vendors)")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize users: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize users: {str(e)}", fg='red'))
        raise


def init_vendors_data():
    """Initialize vendor profiles"""
    try:
        current_app.logger.info("Initializing vendor profiles...")
        
        if Vendor.query.first():
            current_app.logger.info("Vendors already exist, skipping...")
            click.echo("Vendors already initialized")
            return
        
        vendor_users = User.query.filter_by(role='vendor').all()
        if not vendor_users:
            raise ValueError("Vendor users must be initialized first")
        
        vendors_data = [
            {
                'business_name': 'Safari Transport Services',
                'business_type': 'transportation',
                'description': 'Professional school transportation with experienced drivers and well-maintained vehicles',
                'contact_email': 'contact@safaritrans.com',
                'contact_phone': '+254-722-666661',
                'city': 'Nairobi',
                'country': 'Kenya',
                'capacity': 50,
                'base_price': Decimal('150.00'),
                'price_per_person': Decimal('25.00'),
                'is_verified': True,
                'is_active': True,
                'average_rating': 4.5,
                'total_reviews': 23,
                'specializations': ['Bus Transport', 'Safari Vehicles', 'Long Distance']
            },
            {
                'business_name': 'Wilderness Camping Co.',
                'business_type': 'accommodation',
                'description': 'Eco-friendly camping experiences with full safety equipment and trained guides',
                'contact_email': 'info@wildcamping.com',
                'contact_phone': '+254-722-666662',
                'city': 'Naivasha',
                'country': 'Kenya',
                'capacity': 100,
                'base_price': Decimal('200.00'),
                'price_per_person': Decimal('30.00'),
                'is_verified': True,
                'is_active': True,
                'average_rating': 4.7,
                'total_reviews': 18,
                'specializations': ['Camping', 'Hiking', 'Team Building']
            },
            {
                'business_name': 'Marine Parks Adventures',
                'business_type': 'activity',
                'description': 'Educational marine activities including snorkeling, boat tours, and marine biology workshops',
                'contact_email': 'booking@marineparks.com',
                'contact_phone': '+254-722-666663',
                'city': 'Mombasa',
                'country': 'Kenya',
                'capacity': 40,
                'base_price': Decimal('300.00'),
                'price_per_person': Decimal('50.00'),
                'is_verified': True,
                'is_active': True,
                'average_rating': 4.8,
                'total_reviews': 31,
                'specializations': ['Snorkeling', 'Glass Bottom Boat', 'Marine Education']
            },
            {
                'business_name': 'Mountain Guides Kenya',
                'business_type': 'activity',
                'description': 'Professional mountain climbing and hiking expeditions with certified guides',
                'contact_email': 'tours@mountainguides.com',
                'contact_phone': '+254-722-666664',
                'city': 'Nanyuki',
                'country': 'Kenya',
                'capacity': 30,
                'base_price': Decimal('400.00'),
                'price_per_person': Decimal('75.00'),
                'is_verified': True,
                'is_active': True,
                'average_rating': 4.9,
                'total_reviews': 27,
                'specializations': ['Mountain Climbing', 'Hiking', 'Rock Climbing']
            }
        ]
        
        for i, vendor_data in enumerate(vendors_data):
            vendor = Vendor(
                user_id=vendor_users[i].id,
                **vendor_data
            )
            db.session.add(vendor)
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {len(vendors_data)} vendor profiles")
        click.echo(f"✓ Created {len(vendors_data)} vendor profiles")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize vendors: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize vendors: {str(e)}", fg='red'))
        raise


def init_participants_data():
    """Initialize participants (children/students)"""
    try:
        current_app.logger.info("Initializing participants...")
        
        if Participant.query.first():
            current_app.logger.info("Participants already exist, skipping...")
            click.echo("Participants already initialized")
            return
        
        parents = User.query.filter_by(role='parent').all()
        if not parents:
            raise ValueError("Parents must be initialized first")
        
        first_names_boys = ['Michael', 'David', 'Kevin', 'Brian', 'Joshua', 'Emmanuel', 'Samuel', 'Daniel']
        first_names_girls = ['Sarah', 'Emily', 'Grace', 'Faith', 'Joy', 'Mercy', 'Rachel', 'Rebecca']
        last_names = ['Kamau', 'Njoroge', 'Ochieng', 'Mwangi', 'Kimani', 'Akinyi', 'Wanjiru', 'Otieno']
        
        participants_created = 0
        
        # Create 2-3 children per parent
        for parent in parents[:8]:  # First 8 parents
            num_children = random.randint(2, 3)
            
            for i in range(num_children):
                gender = random.choice(['male', 'female'])
                first_name = random.choice(first_names_boys if gender == 'male' else first_names_girls)
                last_name = parent.last_name
                
                age = random.randint(6, 17)
                dob = date.today() - timedelta(days=age*365 + random.randint(0, 364))
                
                participant = Participant(
                    first_name=first_name,
                    last_name=last_name,
                    date_of_birth=dob,
                    gender=gender,
                    grade_level=f'Grade {age - 5}' if age >= 6 else 'Pre-school',
                    blood_type=random.choice(['A+', 'B+', 'O+', 'AB+', 'A-', 'B-', 'O-', 'AB-']),
                    allergies='None' if random.random() > 0.3 else 'Peanuts',
                    dietary_restrictions='None' if random.random() > 0.2 else 'Vegetarian',
                    emergency_contact_1_name=parent.full_name,
                    emergency_contact_1_phone=parent.phone,
                    emergency_contact_1_relationship='Parent',
                    emergency_contact_1_email=parent.email,
                    status='active',
                    parent_id=parent.id,
                    created_by=parent.id
                )
                db.session.add(participant)
                participants_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {participants_created} participants")
        click.echo(f"✓ Created {participants_created} participants")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize participants: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize participants: {str(e)}", fg='red'))
        raise


def init_trips_data():
    """Initialize trips with sample data"""
    try:
        current_app.logger.info("Initializing trips...")
        
        if Trip.query.first():
            current_app.logger.info("Trips already exist, skipping...")
            click.echo("Trips already initialized")
            return
        
        teachers = User.query.filter_by(role='teacher').all()
        schools = School.query.all()
        
        if not teachers or not schools:
            raise ValueError("Teachers and schools must be initialized first")
        
        today = date.today()
        
        trips_data = [
            {
                'title': 'Maasai Mara Wildlife Safari',
                'description': 'Three-day educational safari to Maasai Mara National Reserve focusing on wildlife conservation and ecosystem studies.',
                'destination': 'Maasai Mara National Reserve',
                'destination_country': 'Kenya',
                'start_date': today + timedelta(days=45),
                'end_date': today + timedelta(days=47),
                'registration_deadline': today + timedelta(days=30),
                'max_participants': 40,
                'min_participants': 15,
                'price_per_student': Decimal('350.00'),
                'deposit_amount': Decimal('100.00'),
                'category': 'science',
                'grade_level': '6-8',
                'status': 'registration_open',
                'is_published': True,
                'featured': True,
                'transportation_included': True,
                'meals_included': True,
                'accommodation_included': True,
                'learning_objectives': ['Wildlife identification', 'Ecosystem understanding', 'Conservation awareness'],
                'tags': ['wildlife', 'safari', 'conservation', 'camping']
            },
            {
                'title': 'Mount Kenya Climbing Expedition',
                'description': 'Five-day mountain climbing adventure with professional guides, focusing on physical geography and adventure education.',
                'destination': 'Mount Kenya National Park',
                'destination_country': 'Kenya',
                'start_date': today + timedelta(days=60),
                'end_date': today + timedelta(days=64),
                'registration_deadline': today + timedelta(days=40),
                'max_participants': 25,
                'min_participants': 10,
                'price_per_student': Decimal('450.00'),
                'deposit_amount': Decimal('150.00'),
                'category': 'adventure',
                'grade_level': '9-12',
                'status': 'registration_open',
                'is_published': True,
                'featured': True,
                'transportation_included': True,
                'meals_included': True,
                'accommodation_included': True,
                'learning_objectives': ['Mountain ecosystems', 'Physical endurance', 'Team building'],
                'tags': ['mountain', 'climbing', 'adventure', 'camping']
            },
            {
                'title': 'Mombasa Marine Biology Workshop',
                'description': 'Four-day marine biology workshop including snorkeling, coral reef studies, and marine conservation.',
                'destination': 'Mombasa Marine National Park',
                'destination_country': 'Kenya',
                'start_date': today + timedelta(days=30),
                'end_date': today + timedelta(days=33),
                'registration_deadline': today + timedelta(days=15),
                'max_participants': 35,
                'min_participants': 12,
                'price_per_student': Decimal('400.00'),
                'deposit_amount': Decimal('120.00'),
                'category': 'science',
                'grade_level': '9-12',
                'status': 'registration_open',
                'is_published': True,
                'featured': True,
                'transportation_included': True,
                'meals_included': True,
                'accommodation_included': True,
                'learning_objectives': ['Marine biodiversity', 'Coral reef ecology', 'Conservation methods'],
                'tags': ['marine', 'snorkeling', 'biology', 'conservation']
            },
            {
                'title': 'Lake Nakuru Flamingo Study',
                'description': 'Two-day bird watching and ecological study at Lake Nakuru National Park.',
                'destination': 'Lake Nakuru National Park',
                'destination_country': 'Kenya',
                'start_date': today + timedelta(days=20),
                'end_date': today + timedelta(days=21),
                'registration_deadline': today + timedelta(days=10),
                'max_participants': 30,
                'min_participants': 15,
                'price_per_student': Decimal('200.00'),
                'deposit_amount': Decimal('50.00'),
                'category': 'science',
                'grade_level': '6-8',
                'status': 'registration_open',
                'is_published': True,
                'featured': False,
                'transportation_included': True,
                'meals_included': True,
                'accommodation_included': False,
                'learning_objectives': ['Bird species identification', 'Lake ecosystems', 'Photography skills'],
                'tags': ['birdwatching', 'photography', 'ecology']
            },
            {
                'title': 'Great Rift Valley Geography Tour',
                'description': 'Three-day educational tour exploring the geological features of the Great Rift Valley.',
                'destination': 'Great Rift Valley',
                'destination_country': 'Kenya',
                'start_date': today + timedelta(days=75),
                'end_date': today + timedelta(days=77),
                'registration_deadline': today + timedelta(days=55),
                'max_participants': 45,
                'min_participants': 20,
                'price_per_student': Decimal('280.00'),
                'deposit_amount': Decimal('80.00'),
                'category': 'geography',
                'grade_level': '6-8',
                'status': 'published',
                'is_published': True,
                'featured': False,
                'transportation_included': True,
                'meals_included': True,
                'accommodation_included': True,
                'learning_objectives': ['Tectonic activity', 'Volcanic formations', 'Valley ecosystems'],
                'tags': ['geology', 'geography', 'rift valley']
            },
            {
                'title': 'Fort Jesus Historical Tour',
                'description': 'One-day historical and cultural tour of Fort Jesus and Old Town Mombasa.',
                'destination': 'Fort Jesus, Mombasa',
                'destination_country': 'Kenya',
                'start_date': today + timedelta(days=90),
                'end_date': today + timedelta(days=90),
                'registration_deadline': today + timedelta(days=75),
                'max_participants': 50,
                'min_participants': 20,
                'price_per_student': Decimal('120.00'),
                'deposit_amount': Decimal('30.00'),
                'category': 'history',
                'grade_level': '6-12',
                'status': 'published',
                'is_published': True,
                'featured': False,
                'transportation_included': True,
                'meals_included': True,
                'accommodation_included': False,
                'learning_objectives': ['Coastal history', 'Swahili culture', 'Colonial architecture'],
                'tags': ['history', 'culture', 'architecture']
            },
            {
                'title': 'Hell\'s Gate Cycling Adventure',
                'description': 'Two-day cycling and camping trip at Hell\'s Gate National Park.',
                'destination': 'Hell\'s Gate National Park',
                'destination_country': 'Kenya',
                'start_date': today - timedelta(days=10),
                'end_date': today - timedelta(days=8),
                'registration_deadline': today - timedelta(days=25),
                'max_participants': 30,
                'min_participants': 15,
                'price_per_student': Decimal('250.00'),
                'deposit_amount': Decimal('75.00'),
                'category': 'adventure',
                'grade_level': '9-12',
                'status': 'completed',
                'is_published': True,
                'featured': False,
                'transportation_included': True,
                'meals_included': True,
                'accommodation_included': True,
                'learning_objectives': ['Physical fitness', 'Wildlife observation', 'Camping skills'],
                'tags': ['cycling', 'camping', 'wildlife']
            }
        ]
        
        for i, trip_data in enumerate(trips_data):
            teacher = teachers[i % len(teachers)]
            school = schools[i % len(schools)]
            
            trip = Trip(
                organizer_id=teacher.id,
                school_id=school.id,
                **trip_data
            )
            db.session.add(trip)
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {len(trips_data)} trips")
        click.echo(f"✓ Created {len(trips_data)} trips")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize trips: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize trips: {str(e)}", fg='red'))
        raise


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


def init_advertisements_data():
    """Initialize advertisements"""
    try:
        current_app.logger.info("Initializing advertisements...")
        
        if Advertisement.query.first():
            current_app.logger.info("Advertisements already exist, skipping...")
            click.echo("Advertisements already initialized")
            return
        
        vendors = Vendor.query.all()
        trips = Trip.query.filter_by(featured=True).all()
        
        if not vendors:
            current_app.logger.info("No vendors found, skipping advertisements...")
            click.echo("No vendors to create advertisements for")
            return
        
        ads_created = 0
        today = date.today()
        
        # Vendor advertisements
        for vendor in vendors[:2]:
            ad = Advertisement(
                title=f'Book Your Trip with {vendor.business_name}',
                content=f'{vendor.description} Special rates for school groups!',
                target_audience='teachers',
                campaign_name=f'{vendor.business_name} Campaign Q1',
                budget=Decimal('500.00'),
                cost_per_click=Decimal('2.50'),
                currency='USD',
                billing_model='cpc',
                start_date=today - timedelta(days=15),
                end_date=today + timedelta(days=45),
                is_active=True,
                status='active',
                impressions=random.randint(500, 2000),
                clicks=random.randint(50, 200),
                conversions=random.randint(5, 20),
                total_spent=Decimal(random.uniform(100, 300)),
                click_url=f'https://edusafaris.com/vendors/{vendor.id}',
                call_to_action='Book Now',
                ad_type='banner',
                placement='trip_list',
                vendor_id=vendor.id,
                advertiser_id=vendor.user_id
            )
            db.session.add(ad)
            ads_created += 1
        
        # Trip advertisements
        for trip in trips[:2]:
            ad = Advertisement(
                title=f'Join Our {trip.title}!',
                content=f'{trip.description[:150]}... Limited spots available!',
                target_audience='parents',
                grade_levels=[trip.grade_level],
                campaign_name=f'{trip.title} Promotion',
                budget=Decimal('300.00'),
                cost_per_click=Decimal('1.50'),
                currency='USD',
                billing_model='cpc',
                start_date=today - timedelta(days=10),
                end_date=trip.registration_deadline,
                is_active=True,
                status='active',
                impressions=random.randint(1000, 3000),
                clicks=random.randint(100, 400),
                conversions=random.randint(10, 40),
                total_spent=Decimal(random.uniform(150, 250)),
                click_url=f'https://edusafaris.com/trips/{trip.id}',
                call_to_action='Register Now',
                ad_type='sponsored',
                placement='search_results',
                trip_id=trip.id,
                advertiser_id=trip.organizer_id
            )
            db.session.add(ad)
            ads_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {ads_created} advertisements")
        click.echo(f"✓ Created {ads_created} advertisements")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize advertisements: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize advertisements: {str(e)}", fg='red'))
        raise


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


def init_messages_data():
    """Initialize messages"""
    try:
        current_app.logger.info("Initializing messages...")
        
        if Message.query.first():
            current_app.logger.info("Messages already exist, skipping...")
            click.echo("Messages already initialized")
            return
        
        teachers = User.query.filter_by(role='teacher').all()
        parents = User.query.filter_by(role='parent').limit(5).all()
        trips = Trip.query.limit(3).all()
        
        messages_created = 0
        
        # Create messages between teachers and parents
        for trip in trips:
            teacher = trip.organizer
            registrations = TripRegistration.query.filter_by(trip_id=trip.id).limit(3).all()
            
            for registration in registrations:
                parent = registration.parent
                
                # Teacher sends message to parent
                message = Message(
                    sender_id=teacher.id,
                    recipient_id=parent.id,
                    subject=f'Update: {trip.title}',
                    content=f'Hello {parent.first_name}, just wanted to update you on the upcoming trip. All preparations are on track!',
                    message_type='direct',
                    priority='normal',
                    trip_id=trip.id,
                    is_read=random.choice([True, False])
                )
                if message.is_read:
                    message.read_date = datetime.now() - timedelta(days=random.randint(1, 5))
                
                db.session.add(message)
                messages_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {messages_created} messages")
        click.echo(f"✓ Created {messages_created} messages")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize messages: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize messages: {str(e)}", fg='red'))
        raise


def init_notifications_data():
    """Initialize notifications"""
    try:
        current_app.logger.info("Initializing notifications...")
        
        if Notification.query.first():
            current_app.logger.info("Notifications already exist, skipping...")
            click.echo("Notifications already initialized")
            return
        
        parents = User.query.filter_by(role='parent').limit(10).all()
        trips = Trip.query.filter_by(status='registration_open').limit(3).all()
        
        notifications_created = 0
        
        notification_templates = [
            {
                'title': 'Trip Registration Confirmed',
                'message': 'Your child has been successfully registered for {trip_title}',
                'notification_type': 'trip_update',
                'priority': 'normal'
            },
            {
                'title': 'Payment Reminder',
                'message': 'Reminder: Payment deadline for {trip_title} is approaching',
                'notification_type': 'payment',
                'priority': 'high'
            },
            {
                'title': 'Document Submission Required',
                'message': 'Please submit required documents for {trip_title}',
                'notification_type': 'trip_update',
                'priority': 'high'
            },
            {
                'title': 'New Trip Available',
                'message': 'Check out our new educational trip: {trip_title}',
                'notification_type': 'trip_update',
                'priority': 'normal'
            }
        ]
        
        for parent in parents:
            # Send 2-3 notifications to each parent
            num_notifications = random.randint(2, 3)
            
            for _ in range(num_notifications):
                trip = random.choice(trips)
                template = random.choice(notification_templates)
                
                notification = Notification(
                    title=template['title'],
                    message=template['message'].format(trip_title=trip.title),
                    notification_type=template['notification_type'],
                    priority=template['priority'],
                    recipient_id=parent.id,
                    is_read=random.choice([True, False, False]),
                    send_email=True,
                    send_push=True,
                    email_sent=True,
                    push_sent=True,
                    sent_date=datetime.now() - timedelta(days=random.randint(1, 10)),
                    related_data={'trip_id': trip.id}
                )
                
                if notification.is_read:
                    notification.read_date = datetime.now() - timedelta(days=random.randint(0, 5))
                
                db.session.add(notification)
                notifications_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {notifications_created} notifications")
        click.echo(f"✓ Created {notifications_created} notifications")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize notifications: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize notifications: {str(e)}", fg='red'))
        raise


def init_reviews_data():
    """Initialize reviews"""
    try:
        current_app.logger.info("Initializing reviews...")
        
        if Review.query.first():
            current_app.logger.info("Reviews already exist, skipping...")
            click.echo("Reviews already initialized")
            return
        
        completed_registrations = TripRegistration.query.filter_by(status='completed').all()
        vendors = Vendor.query.all()
        
        reviews_created = 0
        
        # Trip reviews from completed registrations
        for registration in completed_registrations[:10]:
            review = Review(
                reviewer_id=registration.parent_id,
                trip_id=registration.trip_id,
                review_type='trip',
                rating=random.randint(4, 5),
                title=random.choice([
                    'Excellent Educational Experience',
                    'My Child Loved It!',
                    'Great Organization',
                    'Highly Recommend',
                    'Wonderful Trip'
                ]),
                review_text=random.choice([
                    'The trip was well-organized and my child learned so much. The teachers were attentive and safety was clearly a priority.',
                    'Amazing experience! My child came back excited and full of stories. Worth every penny.',
                    'Great value for money. The educational content was excellent and the kids had a blast.',
                    'Professional organization from start to finish. Communication was excellent throughout.',
                    'My child had an unforgettable experience. The activities were engaging and age-appropriate.'
                ]),
                value_rating=random.randint(4, 5),
                safety_rating=random.randint(4, 5),
                organization_rating=random.randint(4, 5),
                communication_rating=random.randint(4, 5),
                is_approved=True,
                is_published=True,
                is_verified_purchase=True,
                helpful_count=random.randint(2, 15),
                not_helpful_count=random.randint(0, 2)
            )
            db.session.add(review)
            reviews_created += 1
        
        # Vendor reviews from service bookings
        completed_bookings = ServiceBooking.query.filter_by(status='completed').limit(8).all()
        
        for booking in completed_bookings:
            review = Review(
                reviewer_id=booking.booked_by,
                vendor_id=booking.vendor_id,
                booking_id=booking.id,
                review_type='vendor',
                rating=random.randint(4, 5),
                title=random.choice([
                    'Reliable Service Provider',
                    'Professional and Punctual',
                    'Exceeded Expectations',
                    'Great Experience'
                ]),
                review_text=random.choice([
                    'Very professional service. Equipment was in excellent condition and staff were helpful.',
                    'Punctual and reliable. Would definitely book again for our next school trip.',
                    'The team went above and beyond to ensure everything ran smoothly.',
                    'Great communication and flexible to our needs. Highly recommended.'
                ]),
                is_approved=True,
                is_published=True,
                is_verified_purchase=True,
                helpful_count=random.randint(1, 10)
            )
            db.session.add(review)
            reviews_created += 1
        
        db.session.commit()
        current_app.logger.info(f"✓ Created {reviews_created} reviews")
        click.echo(f"✓ Created {reviews_created} reviews")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize reviews: {str(e)}", exc_info=True)
        click.echo(click.style(f"✗ Failed to initialize reviews: {str(e)}", fg='red'))
        raise


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


# ============================================================================
# UTILITY COMMANDS
# ============================================================================

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

