from datetime import datetime
from sqlalchemy import Numeric
from app.extensions import db
from app.models.base import BaseModel

class BasePayment(BaseModel):
    """Base payment model with common fields"""
    __abstract__ = True
    
    # Payment Information
    amount = db.Column(Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # 'mpesa', 'stripe', 'bank_transfer', 'cash'
    
    # Status and Processing
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed', 'refunded', 
                              name='payment_status'), default='pending', nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.now)
    processed_date = db.Column(db.DateTime)
    
    # External References
    transaction_id = db.Column(db.String(100), unique=True)  # From payment processor
    reference_number = db.Column(db.String(100), unique=True)  # Internal reference
    
    # Payment Details
    description = db.Column(db.String(200))
    payer_name = db.Column(db.String(100))
    payer_email = db.Column(db.String(120))
    payer_phone = db.Column(db.String(20))
    
    # Processing Information
    processor_response = db.Column(db.JSON)
    failure_reason = db.Column(db.String(200))
    
    # Refund Information
    refund_reason = db.Column(db.String(200))
    refund_date = db.Column(db.DateTime)
    refunded_amount = db.Column(Numeric(10, 2))
    refund_transaction_id = db.Column(db.String(100))
    
    # Receipt
    receipt_url = db.Column(db.String(300))
    receipt_number = db.Column(db.String(50))
    
    def generate_reference_number(self):
        """Generate unique reference number"""
        import random
        import string
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.digits, k=6))
        prefix = self.__class__.__name__[:3].upper()
        self.reference_number = f"{prefix}-{timestamp}-{random_str}"
    
    def mark_completed(self, transaction_id=None, processor_response=None):
        """Mark payment as completed"""
        self.status = 'completed'
        self.processed_date = datetime.now()
        if transaction_id:
            self.transaction_id = transaction_id
        if processor_response:
            self.processor_response = processor_response
        db.session.commit()

        from app.models.activity_log import ActivityLog
        ActivityLog.log_payment(self, getattr(self, 'parent_id', getattr(self, 'paid_by', None)))
    
    def mark_failed(self, failure_reason=None, processor_response=None):
        """Mark payment as failed"""
        self.status = 'failed'
        self.processed_date = datetime.now()
        if failure_reason:
            self.failure_reason = failure_reason
        if processor_response:
            self.processor_response = processor_response
        db.session.commit()
    
    def process_refund(self, refund_reason=None, refund_amount=None):
        """Process refund for this payment"""
        if self.status != 'completed':
            raise ValueError("Can only refund completed payments")
        
        self.status = 'refunded'
        self.refund_date = datetime.now()
        self.refunded_amount = refund_amount or self.amount
        if refund_reason:
            self.refund_reason = refund_reason
        db.session.commit()


class RegistrationPayment(BasePayment):
    """Payments made by parents for trip registrations"""
    __tablename__ = 'registration_payments'
    
    # Foreign Keys
    registration_id = db.Column(db.Integer, db.ForeignKey('trip_registrations.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    registration = db.relationship('TripRegistration', back_populates='payments')
    parent = db.relationship('User', foreign_keys=[parent_id])
    
    # Indexes
    __table_args__ = (
        db.Index('idx_reg_payment_registration', 'registration_id'),
        db.Index('idx_reg_payment_parent', 'parent_id'),
        db.Index('idx_reg_payment_status', 'status'),
        db.Index('idx_reg_payment_date', 'payment_date'),
        db.Index('idx_reg_payment_transaction', 'transaction_id'),
    )
    
    def serialize(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'currency': self.currency,
            'payment_method': self.payment_method,
            'status': self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'transaction_id': self.transaction_id,
            'reference_number': self.reference_number,
            'description': self.description,
            'payer_name': self.payer_name,
            'receipt_number': self.receipt_number,
            'registration': {
                'id': self.registration.id,
                'registration_number': self.registration.registration_number
            } if self.registration else None
        }
    
    def __repr__(self):
        return f'<RegistrationPayment {self.reference_number} - {self.amount}>'


class ServicePayment(BasePayment):
    """Payments made by teachers/schools to vendors for services"""
    __tablename__ = 'service_payments'
    
    # Foreign Keys
    service_booking_id = db.Column(db.Integer, db.ForeignKey('service_bookings.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    paid_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Teacher/admin
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    
    # Relationships
    service_booking = db.relationship('ServiceBooking', back_populates='payments')
    trip = db.relationship('Trip')
    payer = db.relationship('User', foreign_keys=[paid_by])
    vendor = db.relationship('Vendor')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_service_payment_booking', 'service_booking_id'),
        db.Index('idx_service_payment_trip', 'trip_id'),
        db.Index('idx_service_payment_vendor', 'vendor_id'),
        db.Index('idx_service_payment_status', 'status'),
        db.Index('idx_service_payment_date', 'payment_date'),
    )
    
    def serialize(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'currency': self.currency,
            'payment_method': self.payment_method,
            'status': self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'transaction_id': self.transaction_id,
            'reference_number': self.reference_number,
            'description': self.description,
            'service_booking': {
                'id': self.service_booking.id,
                'booking_type': self.service_booking.booking_type
            } if self.service_booking else None,
            'vendor': {
                'id': self.vendor.id,
                'business_name': self.vendor.business_name
            } if self.vendor else None
        }
    
    def __repr__(self):
        return f'<ServicePayment {self.reference_number} - {self.amount}>'


class AdvertisementPayment(BasePayment):
    """Payments for advertisement campaigns"""
    __tablename__ = 'advertisement_payments'
    
    # Foreign Keys
    advertisement_id = db.Column(db.Integer, db.ForeignKey('advertisements.id'), nullable=False)
    paid_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Campaign billing
    billing_period_start = db.Column(db.Date)
    billing_period_end = db.Column(db.Date)
    impressions_charged = db.Column(db.Integer, default=0)
    clicks_charged = db.Column(db.Integer, default=0)
    
    # Relationships
    advertisement = db.relationship('Advertisement', back_populates='payments')
    payer = db.relationship('User', foreign_keys=[paid_by])
    
    # Indexes
    __table_args__ = (
        db.Index('idx_ad_payment_advertisement', 'advertisement_id'),
        db.Index('idx_ad_payment_payer', 'paid_by'),
        db.Index('idx_ad_payment_status', 'status'),
        db.Index('idx_ad_payment_period', 'billing_period_start', 'billing_period_end'),
    )
    
    def serialize(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status,
            'billing_period_start': self.billing_period_start.isoformat() if self.billing_period_start else None,
            'billing_period_end': self.billing_period_end.isoformat() if self.billing_period_end else None,
            'impressions_charged': self.impressions_charged,
            'clicks_charged': self.clicks_charged
        }
    
    def __repr__(self):
        return f'<AdvertisementPayment {self.reference_number}>'