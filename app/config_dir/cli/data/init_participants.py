from flask import current_app
import click
import random
from datetime import datetime, timedelta, date 
from app.extensions import db
from decimal import Decimal
from app.models import Participant, User

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
