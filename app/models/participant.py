from datetime import datetime
from sqlalchemy import Numeric
from app.extensions import db
from app.models.base import BaseModel

class Participant(BaseModel):
    __tablename__ = 'participants'
    
    # Participant Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date)
    grade_level = db.Column(db.String(20))
    student_id = db.Column(db.String(50))
    
    # Contact Information
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    
    # Medical Information
    medical_conditions = db.Column(db.Text)
    medications = db.Column(db.Text)
    allergies = db.Column(db.Text)
    dietary_restrictions = db.Column(db.Text)
    emergency_medical_info = db.Column(db.Text)
    
    # Emergency Contacts
    emergency_contact_1_name = db.Column(db.String(100))
    emergency_contact_1_phone = db.Column(db.String(20))
    emergency_contact_1_relationship = db.Column(db.String(50))
    
    emergency_contact_2_name = db.Column(db.String(100))
    emergency_contact_2_phone = db.Column(db.String(20))
    emergency_contact_2_relationship = db.Column(db.String(50))
    
    # Status and Registration
    status = db.Column(db.Enum('registered', 'confirmed', 'cancelled', 'completed', 
                              name='participant_status'), default='registered', nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.now)
    confirmation_date = db.Column(db.DateTime)
    
    # Payment Information
    payment_status = db.Column(db.Enum('pending', 'partial', 'paid', 'refunded', 
                                      name='payment_status'), default='pending', nullable=False)
    amount_paid = db.Column(Numeric(10, 2), default=0)
    
    # Special Notes
    special_requirements = db.Column(db.Text)
    internal_notes = db.Column(db.Text)  # For staff use only
    
    # Foreign Keys
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # User who registered them (parent/teacher)
    
    # Relationships
    consents = db.relationship('Consent', backref='participant', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_participant_trip', 'trip_id'),
        db.Index('idx_participant_status', 'status'),
        db.Index('idx_participant_payment_status', 'payment_status'),
    )
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate age based on date of birth"""
        if not self.date_of_birth:
            return None
        today = datetime.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def outstanding_balance(self):
        """Calculate outstanding balance"""
        if not self.trip:
            return 0
        return float(self.trip.price_per_student - (self.amount_paid or 0))
    
    def confirm_participation(self):
        """Confirm participant's spot on the trip"""
        self.status = 'confirmed'
        self.confirmation_date = datetime.now()
        db.session.commit()
    
    def cancel_participation(self):
        """Cancel participant's spot"""
        self.status = 'cancelled'
        db.session.commit()
    
    def add_payment(self, amount):
        """Add payment amount"""
        self.amount_paid = (self.amount_paid or 0) + amount
        
        # Update payment status
        if self.outstanding_balance <= 0:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        
        db.session.commit()
    
    def has_all_consents(self):
        """Check if all required consents are signed"""
        if not self.trip or not self.trip.consent_required:
            return True
        
        # Check for signed consent forms
        signed_consents = self.consents.filter_by(is_signed=True).count()
        return signed_consents > 0
    
    def serialize(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'age': self.age,
            'grade_level': self.grade_level,
            'email': self.email,
            'phone': self.phone,
            'status': self.status,
            'payment_status': self.payment_status,
            'amount_paid': float(self.amount_paid) if self.amount_paid else 0,
            'outstanding_balance': self.outstanding_balance,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'has_medical_info': bool(self.medical_conditions or self.medications or self.allergies),
            'has_all_consents': self.has_all_consents(),
            'trip_id': self.trip_id
        }
    
    def __repr__(self):
        return f'<Participant {self.full_name}>'
