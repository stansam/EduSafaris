from sqlalchemy import Numeric
from app.extensions import db
from app.models.base import BaseModel

class Vendor(BaseModel):
    __tablename__ = 'vendors'
    
    # Basic Information
    business_name = db.Column(db.String(200), nullable=False)
    business_type = db.Column(db.String(100))  # e.g., 'transportation', 'accommodation', 'activities'
    description = db.Column(db.Text)
    
    # Contact Information
    contact_email = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    website = db.Column(db.String(200))
    
    # Address
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))
    
    # Business Details
    license_number = db.Column(db.String(100))
    insurance_details = db.Column(db.Text)
    capacity = db.Column(db.Integer)  # Maximum capacity they can handle
    specializations = db.Column(db.JSON)  # Array of specialization areas
    
    # Pricing and Availability
    base_price = db.Column(Numeric(10, 2))
    price_per_person = db.Column(Numeric(10, 2))
    pricing_notes = db.Column(db.Text)
    
    # Status and Verification
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    verification_documents = db.Column(db.JSON)  # Store document file paths
    
    # Ratings and Reviews
    average_rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    bookings = db.relationship('Booking', backref='vendor', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_vendor_type', 'business_type'),
        db.Index('idx_vendor_active', 'is_active'),
        db.Index('idx_vendor_verified', 'is_verified'),
        db.Index('idx_vendor_city', 'city'),
    )
    
    @property
    def full_address(self):
        """Get formatted full address"""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in parts if part])
    
    def update_rating(self):
        """Recalculate average rating based on bookings"""
        from app.models import Booking
        completed_bookings = self.bookings.filter(
            db.and_(Booking.status == 'completed', Booking.rating.isnot(None))
        ).all()
        
        if completed_bookings:
            total_rating = sum(booking.rating for booking in completed_bookings)
            self.average_rating = total_rating / len(completed_bookings)
            self.total_reviews = len(completed_bookings)
        else:
            self.average_rating = 0.0
            self.total_reviews = 0
        
        db.session.commit()
    
    def is_available(self, start_date, end_date):
        from app.models import Booking, Trip
        """Check if vendor is available for given date range"""
        # Check for conflicting bookings
        conflicting_bookings = self.bookings.join(Trip).filter(
            db.and_(
                Booking.status.in_(['confirmed', 'in_progress']),
                db.not_(
                    db.or_(
                        Trip.end_date < start_date,
                        Trip.start_date > end_date
                    )
                )
            )
        ).count()
        
        return conflicting_bookings == 0
    
    def get_revenue_for_period(self, start_date, end_date):
        """Calculate revenue for a given period"""
        from app.models import Booking, Trip
        bookings = self.bookings.join(Trip).filter(
            db.and_(
                Booking.status == 'completed',
                Trip.start_date >= start_date,
                Trip.end_date <= end_date
            )
        ).all()
        
        return sum(booking.total_amount for booking in bookings if booking.total_amount)
    
    def serialize(self):
        return {
            'id': self.id,
            'business_name': self.business_name,
            'business_type': self.business_type,
            'description': self.description,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'website': self.website,
            'address': self.full_address,
            'city': self.city,
            'state': self.state,
            'capacity': self.capacity,
            'specializations': self.specializations,
            'base_price': float(self.base_price) if self.base_price else None,
            'price_per_person': float(self.price_per_person) if self.price_per_person else None,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'average_rating': self.average_rating,
            'total_reviews': self.total_reviews,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Vendor {self.business_name}>'