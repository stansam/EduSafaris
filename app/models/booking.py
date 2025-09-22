from datetime import datetime
from sqlalchemy import Numeric
from app.extensions import db
from app.models.base import BaseModel

class Booking(BaseModel):
    __tablename__ = 'bookings'
    
    # Status and Type
    status = db.Column(db.Enum('pending', 'confirmed', 'in_progress', 'completed', 'cancelled', 
                              name='booking_status'), default='pending', nullable=False)
    booking_type = db.Column(db.String(50), nullable=False)  # 'transportation', 'accommodation', 'activity'
    
    # Booking Details
    service_description = db.Column(db.Text)
    special_requirements = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # Pricing
    quoted_amount = db.Column(Numeric(10, 2))
    final_amount = db.Column(Numeric(10, 2))
    
    # Dates
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    
    # Rating and Review
    rating = db.Column(db.Integer)  # 1-5 stars
    review = db.Column(db.Text)
    review_date = db.Column(db.DateTime)
    
    # Foreign Keys
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    
    # Relationships
    payments = db.relationship('Payment', backref='booking', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_booking_status', 'status'),
        db.Index('idx_booking_type', 'booking_type'),
        db.Index('idx_booking_trip', 'trip_id'),
        db.Index('idx_booking_vendor', 'vendor_id'),
    )
    
    @property
    def total_amount(self):
        """Get the final amount or quoted amount if final not set"""
        return self.final_amount or self.quoted_amount
    
    def can_be_cancelled(self):
        """Check if booking can be cancelled"""
        return self.status in ['pending', 'confirmed']
    
    def confirm_booking(self, final_amount=None):
        """Confirm the booking"""
        self.status = 'confirmed'
        self.confirmed_date = datetime.utcnow()
        if final_amount:
            self.final_amount = final_amount
        db.session.commit()
    
    def complete_booking(self):
        """Mark booking as completed"""
        self.status = 'completed'
        self.completed_date = datetime.utcnow()
        db.session.commit()
    
    def add_review(self, rating, review_text):
        """Add rating and review"""
        self.rating = rating
        self.review = review_text
        self.review_date = datetime.utcnow()
        db.session.commit()
        
        # Update vendor's average rating
        self.vendor.update_rating()
    
    def serialize(self):
        return {
            'id': self.id,
            'status': self.status,
            'booking_type': self.booking_type,
            'service_description': self.service_description,
            'quoted_amount': float(self.quoted_amount) if self.quoted_amount else None,
            'final_amount': float(self.final_amount) if self.final_amount else None,
            'total_amount': float(self.total_amount) if self.total_amount else None,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'confirmed_date': self.confirmed_date.isoformat() if self.confirmed_date else None,
            'rating': self.rating,
            'review': self.review,
            'trip': self.trip.serialize() if self.trip else None,
            'vendor': self.vendor.serialize() if self.vendor else None
        }
    
    def __repr__(self):
        return f'<Booking {self.id} - {self.booking_type}>'
