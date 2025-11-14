from datetime import datetime
from sqlalchemy import Numeric
from app.extensions import db
from app.models.base import BaseModel

class ServiceBooking(BaseModel):
    """Bookings for services from vendors (transportation, accommodation, activities)"""
    __tablename__ = 'service_bookings'
    
    # Status and Type
    status = db.Column(db.Enum('pending', 'confirmed', 'in_progress', 'completed', 'cancelled', 
                              name='service_booking_status'), default='pending', nullable=False)
    booking_type = db.Column(db.String(50), nullable=False)  # 'transportation', 'accommodation', 'activity'
    
    # Booking Details
    service_description = db.Column(db.Text)
    special_requirements = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # Pricing
    quoted_amount = db.Column(Numeric(10, 2))
    final_amount = db.Column(Numeric(10, 2))
    currency = db.Column(db.String(3), default='KES', nullable=False)
    
    # Dates
    service_start_date = db.Column(db.DateTime)  # When service starts
    service_end_date = db.Column(db.DateTime)    # When service ends
    booking_date = db.Column(db.DateTime, default=datetime.now)
    confirmed_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    cancelled_date = db.Column(db.DateTime)
    cancellation_reason = db.Column(db.Text)
    
    # Rating and Review
    rating = db.Column(db.Integer)  # 1-5 stars
    review = db.Column(db.Text)
    review_date = db.Column(db.DateTime)
    
    # Foreign Keys
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    booked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Teacher who booked
    
    # Relationships
    payments = db.relationship('ServicePayment', back_populates='service_booking', lazy='dynamic', cascade='all, delete-orphan')
    trip = db.relationship('Trip', back_populates='service_bookings')
    vendor = db.relationship('Vendor', back_populates='service_bookings')
    booker = db.relationship('User', foreign_keys=[booked_by])
    
    # Indexes
    __table_args__ = (
        db.Index('idx_service_booking_status', 'status'),
        db.Index('idx_service_booking_type', 'booking_type'),
        db.Index('idx_service_booking_trip', 'trip_id'),
        db.Index('idx_service_booking_vendor', 'vendor_id'),
        db.Index('idx_service_booking_dates', 'service_start_date', 'service_end_date'),
    )
    
    @property
    def total_amount(self):
        """Get the final amount or quoted amount if final not set"""
        return self.final_amount or self.quoted_amount
    
    @property
    def payment_status(self):
        """Calculate payment status based on payments"""
        if not self.total_amount:
            return 'not_required'
        
        total_paid = sum(float(p.amount) for p in self.payments.filter_by(status='completed').all())
        
        if total_paid >= float(self.total_amount):
            return 'paid'
        elif total_paid > 0:
            return 'partial'
        else:
            return 'unpaid'
    
    def can_be_cancelled(self):
        """Check if booking can be cancelled"""
        return self.status in ['pending', 'confirmed']
    
    def confirm_booking(self, final_amount=None):
        """Confirm the booking"""
        self.status = 'confirmed'
        self.confirmed_date = datetime.now()
        if final_amount:
            self.final_amount = final_amount
        db.session.commit()
    
    def cancel_booking(self, reason=None):
        """Cancel the booking"""
        if not self.can_be_cancelled():
            raise ValueError("Booking cannot be cancelled in current status")
        
        self.status = 'cancelled'
        self.cancelled_date = datetime.now()
        if reason:
            self.cancellation_reason = reason
        db.session.commit()
    
    def complete_booking(self):
        """Mark booking as completed"""
        self.status = 'completed'
        self.completed_date = datetime.now()
        db.session.commit()
    
    def add_review(self, rating, review_text):
        """Add rating and review"""
        if self.status != 'completed':
            raise ValueError("Can only review completed bookings")
        
        self.rating = rating
        self.review = review_text
        self.review_date = datetime.now()
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
            'currency': self.currency,
            'payment_status': self.payment_status,
            'service_start_date': self.service_start_date.isoformat() if self.service_start_date else None,
            'service_end_date': self.service_end_date.isoformat() if self.service_end_date else None,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'confirmed_date': self.confirmed_date.isoformat() if self.confirmed_date else None,
            'rating': self.rating,
            'review': self.review,
            'trip': {'id': self.trip.id, 'title': self.trip.title} if self.trip else None,
            'vendor': self.vendor.serialize() if self.vendor else None,
            'booked_by': self.booker.serialize() if self.booker else None
        }
    
    def __repr__(self):
        return f'<ServiceBooking {self.id} - {self.booking_type}>'