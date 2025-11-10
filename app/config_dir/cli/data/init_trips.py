from flask import current_app
import click
from datetime import timedelta, date
from app.extensions import db
from decimal import Decimal
from app.models import School, Trip, User


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