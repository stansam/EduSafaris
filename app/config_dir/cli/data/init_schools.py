from flask import current_app
import click
from app.extensions import db
from app.models import School

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