from flask import current_app
import click
import random
from app.extensions import db
from app.models import Review, ServiceBooking, TripRegistration, Vendor

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