from flask import current_app
import os
import sys
from datetime import datetime, date, timedelta
from app import create_app
from app.extensions import db
from app.models import (
    User, Trip, Vendor, Booking, Participant, 
    Consent, Location, Payment, Notification, Advertisement
)

def create_user_if_not_exists(email, user_data):
    """Helper function to create a user if it doesn't exist"""
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(**user_data)
        db.session.add(user)
        db.session.flush()  
        current_app.logger(f"Created user: {email}")
    else:
        current_app.logger(f"User already exists: {email}")
    return user

def create_vendor_if_not_exists(business_name, vendor_data):
    """Helper function to create a vendor if it doesn't exist"""
    vendor = Vendor.query.filter_by(business_name=business_name).first()
    if not vendor:
        vendor = Vendor(**vendor_data)
        db.session.add(vendor)
        db.session.flush()  # Get ID without committing
        current_app.logger(f"Created vendor: {business_name}")
    else:
        current_app.logger(f"Vendor already exists: {business_name}")
    return vendor

def create_trip_if_not_exists(title, trip_data):
    """Helper function to create a trip if it doesn't exist"""
    trip = Trip.query.filter_by(title=title).first()
    if not trip:
        trip = Trip(**trip_data)
        db.session.add(trip)
        db.session.flush()  # Get ID without committing
        current_app.logger(f"Created trip: {title}")
    else:
        current_app.logger(f"Trip already exists: {title}")
    return trip

def seed_database():
    """Seed the database with initial data"""
    try:
        app = create_app()
        
        with app.app_context():
            app.logger("Starting database seeding...")
            
            # Create admin user
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@edusafaris.com')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            
            admin_data = {
                'email': admin_email,
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_active': True,
                'is_verified': True,
                'phone': '+1-555-0100'
            }
            admin = create_user_if_not_exists(admin_email, admin_data)
            if admin.password != admin_password:  
                admin.password = admin_password
            
            # Create sample teacher
            teacher_data = {
                'email': 'teacher@school.edu',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'role': 'teacher',
                'is_active': True,
                'is_verified': True,
                'phone': '+1-555-0101',
                'school': 'Lincoln High School',
                'emergency_contact': 'John Johnson',
                'emergency_phone': '+1-555-0102'
            }
            teacher = create_user_if_not_exists('teacher@school.edu', teacher_data)
            if not hasattr(teacher, '_password') or not teacher._password:
                teacher.password = 'teacher123'
            
            # Create sample parent
            parent_data = {
                'email': 'parent@example.com',
                'first_name': 'Michael',
                'last_name': 'Davis',
                'role': 'parent',
                'is_active': True,
                'is_verified': True,
                'phone': '+1-555-0103',
                'emergency_contact': 'Lisa Davis',
                'emergency_phone': '+1-555-0104'
            }
            parent = create_user_if_not_exists('parent@example.com', parent_data)
            if not hasattr(parent, '_password') or not parent._password:
                parent.password = 'parent123'
            
            # Create sample vendor user
            vendor_user_data = {
                'email': 'vendor@buscompany.com',
                'first_name': 'Robert',
                'last_name': 'Wilson',
                'role': 'vendor',
                'is_active': True,
                'is_verified': True,
                'phone': '+1-555-0105'
            }
            vendor_user = create_user_if_not_exists('vendor@buscompany.com', vendor_user_data)
            if not hasattr(vendor_user, '_password') or not vendor_user._password:
                vendor_user.password = 'vendor123'
            
            # Create hotel vendor user
            hotel_user_data = {
                'email': 'hotel@educationinn.com',
                'first_name': 'Jennifer',
                'last_name': 'Martinez',
                'role': 'vendor',
                'is_active': True,
                'is_verified': True,
                'phone': '+1-555-0107'
            }
            hotel_user = create_user_if_not_exists('hotel@educationinn.com', hotel_user_data)
            if not hasattr(hotel_user, '_password') or not hotel_user._password:
                hotel_user.password = 'hotel123'
            
            # Commit users to ensure IDs are available
            db.session.commit()
            
            # Create sample vendor company (Transportation)
            transport_vendor_data = {
                'business_name': 'Safe Travel Bus Company',
                'business_type': 'transportation',
                'description': 'Professional transportation services for educational trips',
                'contact_email': 'contact@buscompany.com',
                'contact_phone': '+1-555-0106',
                'website': 'https://www.safetravelbus.com',
                'address_line1': '123 Transport Ave',
                'city': 'Springfield',
                'state': 'IL',
                'postal_code': '62701',
                'country': 'USA',
                'license_number': 'ST-12345',
                'capacity': 45,
                'base_price': 500.00,
                'price_per_person': 15.00,
                'is_verified': True,
                'is_active': True,
                'user_id': vendor_user.id,
                'specializations': ['school_trips', 'long_distance', 'luxury_coaches']
            }
            vendor = create_vendor_if_not_exists('Safe Travel Bus Company', transport_vendor_data)
            
            # Create accommodation vendor
            hotel_vendor_data = {
                'business_name': 'Education Inn & Suites',
                'business_type': 'accommodation',
                'description': 'Student-friendly accommodation with group rates',
                'contact_email': 'reservations@educationinn.com',
                'contact_phone': '+1-555-0108',
                'website': 'https://www.educationinn.com',
                'address_line1': '456 Hotel Boulevard',
                'city': 'Chicago',
                'state': 'IL',
                'postal_code': '60601',
                'country': 'USA',
                'license_number': 'EI-67890',
                'capacity': 120,
                'base_price': 80.00,
                'price_per_person': 60.00,
                'is_verified': True,
                'is_active': True,
                'user_id': hotel_user.id,
                'specializations': ['student_groups', 'educational_rates', 'meal_plans']
            }
            hotel_vendor = create_vendor_if_not_exists('Education Inn & Suites', hotel_vendor_data)
            
            # Commit vendors
            db.session.commit()
            
            # Create sample trips
            trip1_data = {
                'title': 'Science Museum Discovery',
                'description': 'Explore the wonders of science at the Chicago Science Museum. Interactive exhibits, planetarium shows, and hands-on experiments await!',
                'destination': 'Chicago, IL',
                'start_date': date.today() + timedelta(days=30),
                'end_date': date.today() + timedelta(days=32),
                'registration_deadline': date.today() + timedelta(days=15),
                'max_participants': 40,
                'min_participants': 15,
                'price_per_student': 125.00,
                'status': 'active',
                'medical_info_required': True,
                'consent_required': True,
                'category': 'science',
                'grade_level': '6-8',
                'organizer_id': teacher.id,
                'itinerary': {
                    "day1": "Arrival and museum orientation",
                    "day2": "Interactive science exhibits and planetarium",
                    "day3": "Hands-on workshops and departure"
                }
            }
            trip1 = create_trip_if_not_exists('Science Museum Discovery', trip1_data)
            
            trip2_data = {
                'title': 'Historical Washington DC',
                'description': 'Visit the nation\'s capital and explore American history through monuments, museums, and government buildings.',
                'destination': 'Washington, DC',
                'start_date': date.today() + timedelta(days=60),
                'end_date': date.today() + timedelta(days=63),
                'registration_deadline': date.today() + timedelta(days=45),
                'max_participants': 35,
                'min_participants': 20,
                'price_per_student': 275.00,
                'status': 'active',
                'medical_info_required': True,
                'consent_required': True,
                'category': 'history',
                'grade_level': '9-12',
                'organizer_id': teacher.id,
                'itinerary': {
                    "day1": "Arrival and Lincoln Memorial",
                    "day2": "Smithsonian Museums",
                    "day3": "Capitol Building and White House tour",
                    "day4": "Arlington Cemetery and departure"
                }
            }
            trip2 = create_trip_if_not_exists('Historical Washington DC', trip2_data)
            
            # Commit trips
            db.session.commit()
            
            # Create sample participant
            participant1 = Participant.query.filter_by(
                first_name='Emma', 
                last_name='Thompson',
                trip_id=trip1.id
            ).first()
            
            if not participant1:
                participant1 = Participant(
                    first_name='Emma',
                    last_name='Thompson',
                    date_of_birth=date(2010, 5, 15),
                    grade_level='8th',
                    student_id='ST2024001',
                    email='emma.t@student.school.edu',
                    medical_conditions='None',
                    allergies='Peanuts',
                    dietary_restrictions='Vegetarian',
                    emergency_contact_1_name='Michael Davis',
                    emergency_contact_1_phone='+1-555-0103',
                    emergency_contact_1_relationship='Father',
                    status='confirmed',
                    payment_status='paid',
                    amount_paid=125.00,
                    trip_id=trip1.id,
                    user_id=parent.id
                )
                db.session.add(participant1)
                db.session.flush()
                app.logger("Created sample participant Emma Thompson")
            
            # Create sample booking
            booking1 = Booking.query.filter_by(
                trip_id=trip1.id, 
                vendor_id=vendor.id,
                booking_type='transportation'
            ).first()
            
            if not booking1:
                booking1 = Booking(
                    status='confirmed',
                    booking_type='transportation',
                    service_description='Round-trip bus transportation for 40 students',
                    quoted_amount=600.00,
                    final_amount=600.00,
                    confirmed_date=datetime.utcnow(),
                    trip_id=trip1.id,
                    vendor_id=vendor.id
                )
                db.session.add(booking1)
                app.logger("Created sample transportation booking")
            
            # Create sample consent form
            if participant1:
                consent1 = Consent.query.filter_by(participant_id=participant1.id).first()
                if not consent1:
                    consent1 = Consent(
                        consent_type='trip_participation',
                        title='Trip Participation Consent',
                        content='I hereby give permission for my child to participate in the Science Museum Discovery trip...',
                        is_signed=True,
                        signed_date=datetime.utcnow(),
                        signer_name='Michael Davis',
                        signer_relationship='parent',
                        signer_email='parent@example.com',
                        participant_id=participant1.id,
                        parent_id=parent.id
                    )
                    db.session.add(consent1)
                    app.logger("Created sample consent form")
            
            # Create sample payment
            if participant1:
                payment1 = Payment.query.filter_by(participant_id=participant1.id).first()
                if not payment1:
                    payment1 = Payment(
                        amount=125.00,
                        currency='USD',
                        payment_method='stripe',
                        status='completed',
                        processed_date=datetime.utcnow(),
                        transaction_id='pi_1234567890',
                        description='Payment for Science Museum Discovery trip',
                        payer_name='Michael Davis',
                        payer_email='parent@example.com',
                        trip_id=trip1.id,
                        participant_id=participant1.id
                    )
                    db.session.add(payment1)
                    app.logger("Created sample payment")
            
            # Create sample advertisement
            ad1 = Advertisement.query.filter_by(title='Spring Break Science Adventure').first()
            if not ad1:
                ad1 = Advertisement(
                    title='Spring Break Science Adventure',
                    content='Join us for an amazing science-focused trip this spring break! Early bird discount available.',
                    target_audience='teachers',
                    grade_levels=['6', '7', '8'],
                    campaign_name='Spring 2024 Promotion',
                    start_date=date.today(),
                    end_date=date.today() + timedelta(days=30),
                    budget=500.00,
                    cost_per_click=2.50,
                    click_url=f'/trips/{trip1.id}',
                    call_to_action='Book Now',
                    ad_type='banner',
                    placement='trip_list',
                    trip_id=trip1.id
                )
                db.session.add(ad1)
                app.logger("Created sample advertisement")
            
            # Create sample notification
            notification1 = Notification.query.filter_by(
                title='Welcome to Edu Safaris!',
                recipient_id=teacher.id
            ).first()
            
            if not notification1:
                notification1 = Notification(
                    title='Welcome to Edu Safaris!',
                    message='Thank you for joining our platform. Explore our educational trips and start planning your next adventure.',
                    notification_type='welcome',
                    priority='normal',
                    recipient_id=teacher.id,
                    category='general',
                    related_data={'welcome': True}
                )
                db.session.add(notification1)
                app.logger("Created welcome notification")
            
            # Final commit
            db.session.commit()
            
            app.logger("\n" + "="*50)
            app.logger("Database seeding completed successfully!")
            app.logger("="*50)
            app.logger("\nSample users created:")
            app.logger(f"- Admin: {admin_email} / {admin_password}")
            app.logger("- Teacher: teacher@school.edu / teacher123")
            app.logger("- Parent: parent@example.com / parent123")
            app.logger("- Vendor: vendor@buscompany.com / vendor123")
            app.logger("- Hotel: hotel@educationinn.com / hotel123")
            app.logger("\nSample trips and data have been created.")
            app.logger("You can now start the application and test with these accounts.")
            
    except Exception as e:
        app.logger(f"Error during database seeding: {str(e)}")
        db.session.rollback()
        sys.exit(1)

if __name__ == '__main__':
    seed_database()