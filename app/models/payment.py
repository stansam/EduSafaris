from datetime import datetime
from sqlalchemy import Numeric
from app.extensions import db
from app.models.base import BaseModel

class Payment(BaseModel):
    __tablename__ = 'payments'
    
    # Payment Information
    amount = db.Column(Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # 'stripe', 'mpesa', 'bank_transfer', 'cash'
    
    # Status and Processing
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed', 'refunded', 
                              name='payment_status'), default='pending', nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed_date = db.Column(db.DateTime)
    
    # External References
    transaction_id = db.Column(db.String(100))  # External payment processor transaction ID
    reference_number = db.Column(db.String(100))  # Internal reference
    
    # Payment Details
    description = db.Column(db.String(200))
    payer_name = db.Column(db.String(100))
    payer_email = db.Column(db.String(120))
    payer_phone = db.Column(db.String(20))
    
    # Processing Information
    processor_response = db.Column(db.JSON)  # Store full response from payment processor
    failure_reason = db.Column(db.String(200))
    refund_reason = db.Column(db.String(200))
    refund_date = db.Column(db.DateTime)
    
    # Foreign Keys
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'))
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_payment_status', 'status'),
        db.Index('idx_payment_method', 'payment_method'),
        db.Index('idx_payment_transaction', 'transaction_id'),
        db.Index('idx_payment_date', 'payment_date'),
    )
    
    def mark_completed(self, transaction_id=None, processor_response=None):
        """Mark payment as completed"""
        self.status = 'completed'
        self.processed_date = datetime.utcnow()
        if transaction_id:
            self.transaction_id = transaction_id
        if processor_response:
            self.processor_response = processor_response
        db.session.commit()
    
    def mark_failed(self, failure_reason=None, processor_response=None):
        """Mark payment as failed"""
        self.status = 'failed'
        self.processed_date = datetime.utcnow()
        if failure_reason:
            self.failure_reason = failure_reason
        if processor_response:
            self.processor_response = processor_response
        db.session.commit()
    
    def process_refund(self, refund_reason=None):
        """Process refund for this payment"""
        self.status = 'refunded'
        self.refund_date = datetime.utcnow()
        if refund_reason:
            self.refund_reason = refund_reason
        db.session.commit()
    
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
            'payer_email': self.payer_email,
            'failure_reason': self.failure_reason,
            'refund_reason': self.refund_reason
        }
    
    def __repr__(self):
        return f'<Payment {self.id} - {self.amount} {self.currency}>'
