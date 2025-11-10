from flask import current_app
import click
import random
from datetime import timedelta, date 
from app.extensions import db
from decimal import Decimal
from app.models import Advertisement, Vendor, Trip



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
