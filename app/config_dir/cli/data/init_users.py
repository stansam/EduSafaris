from flask import current_app
import click
from app.extensions import db
from app.models import User, School

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