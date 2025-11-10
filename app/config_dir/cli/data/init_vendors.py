from flask import current_app
import click
from app.extensions import db
from decimal import Decimal
from app.models import Vendor, User


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