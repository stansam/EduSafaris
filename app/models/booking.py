from datetime import datetime
from sqlalchemy import Numeric
from app.extensions import db
from app.models.base import BaseModel

class VendorBooking(BaseModel):
    __tablename__ = 'vendor_bookings'
    
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
    booking_date = db.Column(db.DateTime, default=datetime.now)
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
    payments = db.relationship('Payment', back_populates='booking', lazy='dynamic', cascade='all, delete-orphan')
    
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
        self.confirmed_date = datetime.now()
        if final_amount:
            self.final_amount = final_amount
        db.session.commit()
    
    def complete_booking(self):
        """Mark booking as completed"""
        self.status = 'completed'
        self.completed_date = datetime.now()
        db.session.commit()
    
    def add_review(self, rating, review_text):
        """Add rating and review"""
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
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'confirmed_date': self.confirmed_date.isoformat() if self.confirmed_date else None,
            'rating': self.rating,
            'review': self.review,
            'trip': self.trip.serialize() if self.trip else None,
            'vendor': self.vendor.serialize() if self.vendor else None
        }
    
    def __repr__(self):
        return f'<Booking {self.id} - {self.booking_type}>'
    
class ChildBooking(BaseModel):
    __tablename__ = 'child_bookings'
    
    # Foreign Keys
    child_id = db.Column(db.Integer, db.ForeignKey('participants.id', name='fk_booking_child_id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id', name='fk_booking_trip_id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_booking_parent_id'), nullable=False)
    
    # Booking Details
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('pending', 'confirmed', 'cancelled', 'completed', 
                               name='booking_status'), default='pending', nullable=False)
    payment_status = db.Column(db.Enum('pending', 'partial', 'paid', 'refunded', 
                                       name='booking_payment_status'), default='pending', nullable=False)
    amount_due = db.Column(Numeric(10, 2), default=0)
    amount_paid = db.Column(Numeric(10, 2), default=0)
    payment_reference = db.Column(db.String(100))
    
    # Notes and Flags
    remarks = db.Column(db.Text)
    consent_signed = db.Column(db.Boolean, default=False)
    
    # Relationships
    trip = db.relationship('Trip', backref=db.backref('child_bookings', lazy='dynamic', cascade='all, delete-orphan'))
    child = db.relationship('Participant', backref=db.backref('bookings', lazy='dynamic', cascade='all, delete-orphan'))
    parent = db.relationship('User', backref=db.backref('child_bookings', lazy='dynamic'))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_childbooking_trip', 'trip_id'),
        db.Index('idx_childbooking_parent', 'parent_id'),
        db.Index('idx_childbooking_child', 'child_id'),
    )

    def confirm_booking(self):
        """Confirm booking and link participant to the trip"""
        self.status = 'confirmed'
        self.payment_status = 'partial' if self.amount_paid > 0 else 'pending'
        self.child.status = 'confirmed'
        self.child.trip_id = self.trip_id
        db.session.commit()
    
    def add_payment(self, amount):
        """Add payment and update status"""
        self.amount_paid = (self.amount_paid or 0) + amount
        if self.amount_paid >= self.amount_due:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        db.session.commit()

    def serialize(self):
        return {
            'id': self.id,
            'child': self.child.serialize() if self.child else None,
            'trip': self.trip.serialize() if self.trip else None,
            'parent': self.parent.serialize() if self.parent else None,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'status': self.status,
            'payment_status': self.payment_status,
            'amount_due': float(self.amount_due) if self.amount_due else 0,
            'amount_paid': float(self.amount_paid) if self.amount_paid else 0,
            'remarks': self.remarks,
            'consent_signed': self.consent_signed
        }

    def __repr__(self):
        return f"<ChildBooking child={self.child_id} trip={self.trip_id} status={self.status}>"
