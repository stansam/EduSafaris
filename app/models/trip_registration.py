from datetime import datetime
from sqlalchemy import Numeric
from app.extensions import db
from app.models.base import BaseModel

class TripRegistration(BaseModel):
    """Parent registering their child for a trip"""
    __tablename__ = 'trip_registrations'
    
    # Foreign Keys
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Registration Details
    registration_date = db.Column(db.DateTime, default=datetime.now)
    registration_number = db.Column(db.String(50), unique=True)  # Unique registration reference
    
    # Status
    status = db.Column(db.Enum('pending', 'confirmed', 'waitlisted', 'cancelled', 'completed', 
                               name='registration_status'), default='pending', nullable=False)
    
    # Payment Information
    payment_status = db.Column(db.Enum('unpaid', 'partial', 'paid', 'refunded', 
                                       name='registration_payment_status'), default='unpaid', nullable=False)
    total_amount = db.Column(Numeric(10, 2), nullable=False)  # Copy from trip price at registration
    amount_paid = db.Column(Numeric(10, 2), default=0)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # Payment Plan
    payment_plan = db.Column(db.String(50))  # 'full', 'installment', 'deposit'
    payment_deadline = db.Column(db.Date)
    
    # Documentation Status
    consent_signed = db.Column(db.Boolean, default=False)
    medical_form_submitted = db.Column(db.Boolean, default=False)
    
    # Important Dates
    confirmed_date = db.Column(db.DateTime)
    cancelled_date = db.Column(db.DateTime)
    cancellation_reason = db.Column(db.Text)
    completed_date = db.Column(db.DateTime)
    
    # Notes
    parent_notes = db.Column(db.Text)  # Notes from parent
    admin_notes = db.Column(db.Text)   # Internal notes
    
    # Relationships
    trip = db.relationship('Trip', back_populates='registrations')
    participant = db.relationship('Participant', back_populates='registrations')
    parent = db.relationship('User', back_populates='registrations')
    payments = db.relationship('RegistrationPayment', back_populates='registration', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_registration_trip', 'trip_id'),
        db.Index('idx_registration_parent', 'parent_id'),
        db.Index('idx_registration_participant', 'participant_id'),
        db.Index('idx_registration_status', 'status'),
        db.Index('idx_registration_payment_status', 'payment_status'),
        db.Index('idx_registration_number', 'registration_number'),
    )
    
    @property
    def outstanding_balance(self):
        """Calculate remaining balance"""
        return float(self.total_amount - (self.amount_paid or 0))
    
    @property
    def is_fully_paid(self):
        """Check if registration is fully paid"""
        return self.amount_paid >= self.total_amount
    
    @property
    def is_documentation_complete(self):
        """Check if all required documentation is complete"""
        docs_complete = True
        
        if self.trip.consent_required and not self.consent_signed:
            docs_complete = False
        
        if self.trip.medical_info_required and not self.medical_form_submitted:
            docs_complete = False
        
        return docs_complete
    
    @property
    def can_be_confirmed(self):
        """Check if registration can be confirmed"""
        return (
            self.status == 'pending' and 
            self.is_documentation_complete and
            (self.payment_status in ['paid', 'partial'])  # At least some payment made
        )
    
    @classmethod
    def latest_for_participant_and_teacher(cls, participant_id, teacher_id):
        from app.models import Trip
        return (
            cls.query
            .join(Trip)
            .filter(
                cls.participant_id == participant_id,
                Trip.organizer_id == teacher_id
            )
            .order_by(cls.registration_date.desc())
            .first()
        )

    def generate_registration_number(self):
        """Generate unique registration number"""
        import random
        import string
        timestamp = datetime.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.registration_number = f"REG-{timestamp}-{random_str}"
    
    def confirm_registration(self):
        """Confirm the registration"""
        if not self.can_be_confirmed:
            raise ValueError("Registration cannot be confirmed. Check documentation and payment status.")
        
        self.status = 'confirmed'
        self.confirmed_date = datetime.now()
        
        # Update participant status
        self.participant.status = 'confirmed'
        # self.participant.trip_id = self.trip_id
        
        db.session.commit()
    
    def add_payment(self, amount):
        """Add payment and update statuses"""
        self.amount_paid = (self.amount_paid or 0) + amount
        
        # Update payment status
        if self.amount_paid >= self.total_amount:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        
        db.session.commit()
    
    def cancel_registration(self, reason=None):
        """Cancel the registration"""
        if self.status == 'completed':
            raise ValueError("Cannot cancel completed registration")
        
        self.status = 'cancelled'
        self.cancelled_date = datetime.now()
        if reason:
            self.cancellation_reason = reason
        
        # Update participant status
        self.participant.status = 'cancelled'
        
        db.session.commit()
    
    def complete_registration(self):
        """Mark registration as completed (after trip ends)"""
        self.status = 'completed'
        self.completed_date = datetime.now()
        
        # Update participant status
        self.participant.status = 'completed'
        
        db.session.commit()
    
    def serialize(self):
        return {
            'id': self.id,
            'registration_number': self.registration_number,
            'participant': self.participant.serialize() if self.participant else None,
            'trip': {
                'id': self.trip.id,
                'title': self.trip.title,
                'start_date': self.trip.start_date.isoformat() if self.trip.start_date else None,
                'end_date': self.trip.end_date.isoformat() if self.trip.end_date else None,
            } if self.trip else None,
            'parent': {
                'id': self.parent.id,
                'full_name': self.parent.full_name,
                'email': self.parent.email
            } if self.parent else None,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'status': self.status,
            'payment_status': self.payment_status,
            'total_amount': float(self.total_amount),
            'amount_paid': float(self.amount_paid) if self.amount_paid else 0,
            'outstanding_balance': self.outstanding_balance,
            'currency': self.currency,
            'consent_signed': self.consent_signed,
            'medical_form_submitted': self.medical_form_submitted,
            'is_documentation_complete': self.is_documentation_complete,
            'confirmed_date': self.confirmed_date.isoformat() if self.confirmed_date else None,
            'parent_notes': self.parent_notes
        }
    
    def __repr__(self):
        return f"<TripRegistration {self.registration_number} - {self.status}>"