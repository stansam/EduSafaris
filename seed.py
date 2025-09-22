#!/usr/bin/env python3
"""
Database seeding script for Edu Safaris
"""
import os
from datetime import datetime, date, timedelta
from app import create_app
from app.extensions import db
from app.models import (
    User, Trip, Vendor, Booking, Participant, 
    Consent, Location, Payment, Notification, Advertisement
)

def seed_database():
    """Seed the database with initial data"""
    app = create_app()
    
    with app.app_context():
        print("Starting database seeding...")
        
        # Create admin user
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@edusafaris.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                first_name='Admin',
                last_name='User',
                role='admin',
                is_active=True,
                is_verified=True,
                phone='+1-555-0100'
            )
            admin.password = admin_password
            db.session.add(admin)
            print(f"Created admin user: {admin_email}")
        
        # Create sample teacher
        teacher = User.query.filter_by(email='teacher@school.edu').first()
        if not teacher:
            teacher = User(
                email='teacher@school.edu',
                first_name='Sarah',
                last_name='Johnson',
                role='teacher',
                is_active=True,
                is_verified=True,
                phone='+1-555-0101',
                school='Lincoln High School',
                emergency_contact='John Johnson',
                emergency_phone='+1-555-0102'
            )
            teacher.password = 'teacher123'
            db.session.add(teacher)
            print("Created sample teacher")
        
        # Create sample parent
        parent = User.query.filter_by(email='parent@example.com').first()
        if not parent:
            parent = User(
                email='parent@example.com',
                first_name='Michael',
                last_name='Davis',
                role='parent',
                is_active=True,
                is_verified=True,
                phone='+1-555-0103',
                emergency_contact='Lisa Davis',
                emergency_phone='+1-555-0104'
            )
            parent.password = 'parent123'
            db.session.add(parent)
            print("Created sample parent")
        
        # Create sample vendor user
        vendor_user = User.query.filter_by(email='vendor@buscompany.com').first()
        if not vendor_user:
            vendor_user = User(
                email='vendor@buscompany.com',
                first_name='Robert',
                last_name='Wilson',
                role='vendor',
                is_active=True,
                is_verified=True,
                phone='+1-555-0105'
            )
            vendor_user.password = 'vendor123'
            db.session.add(vendor_user)
            print("Created sample vendor user")
        
        # Commit users first to get IDs
        db.session.commit()
        
        # Create sample vendor company
        vendor = Vendor.query.filter_by(business_name='Safe Travel Bus Company').first()
        if not vendor:
            vendor = Vendor(
                business_name='Safe Travel Bus Company',
                business_type='transportation',
                description='Professional transportation services for educational trips',
                contact_email='contact@buscompany.com',
                contact_phone='+1-555-0106',
                website='https://www.safetravelbus.com',
                address_line1='123 Transport Ave',
                city='Springfield',
                state='IL',
                postal_code='62701',
                country='USA',
                license_number='ST-12345',
                capacity=45,
                base_price=500.00,
                price_per_person=15.00,
                is_verified=True,
                is_active=True,
                user_id=vendor_user.id,
                specializations=['school_trips', 'long_distance', 'luxury_coaches']
            )
            db.session.add(vendor)
            print("Created sample vendor company")
        
        # Create accommodation vendor
        hotel_user = User.query.filter_by(email='hotel@educationinn.com').first()
        if not hotel_user:
            hotel_user = User(
                email='hotel@educationinn.com',
                first_name='Jennifer',
                last_name='Martinez',
                role='vendor',
                is_active=True,
                is_verified=True,
                phone='+1-555-0107'
            )
            hotel_user.password = 'hotel123'
            db.session.add(hotel_user)
            db.session.commit()
            
            hotel_vendor = Vendor(
                business_name='Education Inn & Suites',
                business_type='accommodation',
                description='Student-friendly accommodation with group rates',
                contact_email='reservations@educationinn.com',
                contact_phone='+1-555-0108',
                website='https://www.educationinn.com',
                address_line1='456 Hotel Boulevard',
                city='Chicago',
                state='IL',
                postal_code='60601',
                country='USA',
                license_number='EI-67890',
                capacity=120,
                base_price=80.00,
                price_per_person=60.00,
                is_verified=True,
                is_active=True,
                user_id=hotel_user.id,
                specializations=['student_groups', 'educational_rates', 'meal_plans']
            )
            db.session.add(hotel_vendor)
            print("Created sample accommodation vendor")
        
        # Commit vendors
        db.session.commit()
        
        # Create sample trips
        trip1 = Trip.query.filter_by(title='Science Museum Discovery').first()
        if not trip1:
            trip1 = Trip(
                title='Science Museum Discovery',
                description='Explore the wonders of science at the Chicago Science Museum. Interactive exhibits, planetarium shows, and hands-on experiments await!',
                destination='Chicago, IL',
                start_date=date.today() + timedelta(days=30),
                end_date=date.today() + timedelta(days=32),
                registration_deadline=date.today() + timedelta(days=15),
                max_participants=40,
                min_participants=15,
                price_per_student=125.00,
                status='active',
                medical_info_required=True,
                consent_required=True,
                category='science',
                grade_level='6-8',
                organizer_id=teacher.id,
                itinerary={
                    "day1": "Arrival and museum orientation",
                    "day2": "Interactive science exhibits and planetarium",
                    "day3": "Hands-on workshops and departure"
                }\n            )\n            db.session.add(trip1)\n            print("Created Science Museum Discovery trip")\n        \n        trip2 = Trip.query.filter_by(title='Historical Washington DC').first()\n        if not trip2:\n            trip2 = Trip(\n                title='Historical Washington DC',\n                description='Visit the nation\\'s capital and explore American history through monuments, museums, and government buildings.',\n                destination='Washington, DC',\n                start_date=date.today() + timedelta(days=60),\n                end_date=date.today() + timedelta(days=63),\n                registration_deadline=date.today() + timedelta(days=45),\n                max_participants=35,\n                min_participants=20,\n                price_per_student=275.00,\n                status='active',\n                medical_info_required=True,\n                consent_required=True,\n                category='history',\n                grade_level='9-12',\n                organizer_id=teacher.id,\n                itinerary={\n                    \"day1\": \"Arrival and Lincoln Memorial\",\n                    \"day2\": \"Smithsonian Museums\",\n                    \"day3\": \"Capitol Building and White House tour\",\n                    \"day4\": \"Arlington Cemetery and departure\"\n                }\n            )\n            db.session.add(trip2)\n            print("Created Historical Washington DC trip")\n        \n        # Commit trips\n        db.session.commit()\n        \n        # Create sample participants\n        participant1 = Participant.query.filter_by(first_name='Emma', last_name='Thompson').first()\n        if not participant1:\n            participant1 = Participant(\n                first_name='Emma',\n                last_name='Thompson',\n                date_of_birth=date(2010, 5, 15),\n                grade_level='8th',\n                student_id='ST2024001',\n                email='emma.t@student.school.edu',\n                medical_conditions='None',\n                allergies='Peanuts',\n                dietary_restrictions='Vegetarian',\n                emergency_contact_1_name='Michael Davis',\n                emergency_contact_1_phone='+1-555-0103',\n                emergency_contact_1_relationship='Father',\n                status='confirmed',\n                payment_status='paid',\n                amount_paid=125.00,\n                trip_id=trip1.id,\n                user_id=parent.id\n            )\n            db.session.add(participant1)\n            print("Created sample participant Emma Thompson")\n        \n        # Create sample bookings\n        booking1 = Booking.query.filter_by(trip_id=trip1.id, vendor_id=vendor.id).first()\n        if not booking1:\n            booking1 = Booking(\n                status='confirmed',\n                booking_type='transportation',\n                service_description='Round-trip bus transportation for 40 students',\n                quoted_amount=600.00,\n                final_amount=600.00,\n                confirmed_date=datetime.utcnow(),\n                trip_id=trip1.id,\n                vendor_id=vendor.id\n            )\n            db.session.add(booking1)\n            print("Created sample transportation booking")\n        \n        # Create sample consent form\n        if participant1:\n            consent1 = Consent.query.filter_by(participant_id=participant1.id).first()\n            if not consent1:\n                consent1 = Consent(\n                    consent_type='trip_participation',\n                    title='Trip Participation Consent',\n                    content='I hereby give permission for my child to participate in the Science Museum Discovery trip...',\n                    is_signed=True,\n                    signed_date=datetime.utcnow(),\n                    signer_name='Michael Davis',\n                    signer_relationship='parent',\n                    signer_email='parent@example.com',\n                    participant_id=participant1.id,\n                    parent_id=parent.id\n                )\n                db.session.add(consent1)\n                print("Created sample consent form")\n        \n        # Create sample payment\n        payment1 = Payment.query.filter_by(participant_id=participant1.id).first()\n        if not payment1 and participant1:\n            payment1 = Payment(\n                amount=125.00,\n                currency='USD',\n                payment_method='stripe',\n                status='completed',\n                processed_date=datetime.utcnow(),\n                transaction_id='pi_1234567890',\n                description='Payment for Science Museum Discovery trip',\n                payer_name='Michael Davis',\n                payer_email='parent@example.com',\n                trip_id=trip1.id,\n                participant_id=participant1.id\n            )\n            db.session.add(payment1)\n            print("Created sample payment")\n        \n        # Create sample advertisement\n        ad1 = Advertisement.query.filter_by(title='Spring Break Science Adventure').first()\n        if not ad1:\n            ad1 = Advertisement(\n                title='Spring Break Science Adventure',\n                content='Join us for an amazing science-focused trip this spring break! Early bird discount available.',\n                target_audience='teachers',\n                grade_levels=['6', '7', '8'],\n                campaign_name='Spring 2024 Promotion',\n                start_date=date.today(),\n                end_date=date.today() + timedelta(days=30),\n                budget=500.00,\n                cost_per_click=2.50,\n                click_url='/trips/1',\n                call_to_action='Book Now',\n                ad_type='banner',\n                placement='trip_list',\n                trip_id=trip1.id\n            )\n            db.session.add(ad1)\n            print("Created sample advertisement")\n        \n        # Create sample notification\n        notification1 = Notification.query.filter_by(title='Welcome to Edu Safaris!').first()\n        if not notification1:\n            notification1 = Notification(\n                title='Welcome to Edu Safaris!',\n                message='Thank you for joining our platform. Explore our educational trips and start planning your next adventure.',\n                notification_type='welcome',\n                priority='normal',\n                recipient_id=teacher.id,\n                category='general',\n                related_data={'welcome': True}\n            )\n            db.session.add(notification1)\n            print("Created welcome notification")\n        \n        # Final commit\n        db.session.commit()\n        print("\\nDatabase seeding completed successfully!")\n        print("\\nSample users created:")\n        print(f"- Admin: {admin_email} / {admin_password}")\n        print("- Teacher: teacher@school.edu / teacher123")\n        print("- Parent: parent@example.com / parent123")\n        print("- Vendor: vendor@buscompany.com / vendor123")\n        print("- Hotel: hotel@educationinn.com / hotel123")\n        print("\\nSample trips and data have been created.")\n\nif __name__ == '__main__':\n    seed_database()