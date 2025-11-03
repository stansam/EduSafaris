from datetime import datetime
from sqlalchemy import Numeric
from app.extensions import db
from app.models.base import BaseModel

class Participant(BaseModel):
    """Child/Student who participates in trips"""
    __tablename__ = 'participants'
    
    # Participant Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.Enum('male', 'female', 'other', 'prefer_not_to_say', 
                               name='gender_type'), nullable=False)
    
    # School Information
    grade_level = db.Column(db.String(20))
    student_id = db.Column(db.String(50))
    school_name = db.Column(db.String(200))
    
    # Contact Information (Optional - child's own contact)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    
    # Medical Information
    blood_type = db.Column(db.String(5))
    medical_conditions = db.Column(db.Text)
    medications = db.Column(db.Text)
    allergies = db.Column(db.Text)
    dietary_restrictions = db.Column(db.Text)
    emergency_medical_info = db.Column(db.Text)
    doctor_name = db.Column(db.String(100))
    doctor_phone = db.Column(db.String(20))
    
    # Emergency Contacts
    emergency_contact_1_name = db.Column(db.String(100), nullable=False)
    emergency_contact_1_phone = db.Column(db.String(20), nullable=False)
    emergency_contact_1_relationship = db.Column(db.String(50), nullable=False)
    emergency_contact_1_email = db.Column(db.String(120))
    
    emergency_contact_2_name = db.Column(db.String(100))
    emergency_contact_2_phone = db.Column(db.String(20))
    emergency_contact_2_relationship = db.Column(db.String(50))
    emergency_contact_2_email = db.Column(db.String(120))
    
    # Status (Overall status for the participant profile)
    status = db.Column(db.Enum('active', 'inactive', name='participant_profile_status'), 
                      default='active', nullable=False)
    
    # Profile Photo
    photo_url = db.Column(db.String(300))
    
    # Special Notes
    special_requirements = db.Column(db.Text)
    behavioral_notes = db.Column(db.Text)  # For teachers/staff
    
    # Foreign Keys - Participant belongs to parent/guardian
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    # parent = db.relationship('User', foreign_keys=[parent_id], backref='children')
    creator = db.relationship('User', foreign_keys=[created_by])
    registrations = db.relationship('TripRegistration', back_populates='participant', 
                                   lazy='dynamic', cascade='all, delete-orphan')
    consents = db.relationship('Consent', backref='participant', lazy='dynamic')
    documents = db.relationship('Document', backref='participant', lazy='dynamic')
    locations = db.relationship('Location', backref='participant', lazy='dynamic')
    trips = db.relationship('Trip', secondary='trip_registrations', back_populates='participants', viewonly=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_participant_parent', 'parent_id'),
        db.Index('idx_participant_status', 'status'),
        db.Index('idx_participant_dob', 'date_of_birth'),
        db.Index('idx_participant_name', 'first_name', 'last_name'),
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
    def active_registrations_count(self):
        """Get number of active registrations"""
        from app.models import TripRegistration

        return self.registrations.filter(
            TripRegistration.status.in_(['pending', 'confirmed', 'waitlisted'])
        ).count()
    
    @property
    def completed_trips_count(self):
        """Get number of completed trips"""
        return self.registrations.filter_by(status='completed').count()
    
    @property
    def has_complete_medical_info(self):
        """Check if medical information is complete"""
        required_fields = [
            self.blood_type,
            self.emergency_contact_1_name,
            self.emergency_contact_1_phone
        ]
        return all(required_fields)
    
    @property
    def emergency_contacts_list(self):
        """Get list of emergency contacts"""
        contacts = []
        
        if self.emergency_contact_1_name:
            contacts.append({
                'name': self.emergency_contact_1_name,
                'phone': self.emergency_contact_1_phone,
                'relationship': self.emergency_contact_1_relationship,
                'email': self.emergency_contact_1_email,
                'priority': 1
            })
        
        if self.emergency_contact_2_name:
            contacts.append({
                'name': self.emergency_contact_2_name,
                'phone': self.emergency_contact_2_phone,
                'relationship': self.emergency_contact_2_relationship,
                'email': self.emergency_contact_2_email,
                'priority': 2
            })
        
        return contacts
    
    def get_registration_for_trip(self, trip_id):
        """Get registration for a specific trip"""
        return self.registrations.filter_by(trip_id=trip_id).first()
    
    def is_registered_for_trip(self, trip_id):
        """Check if participant is registered for a trip"""
        registration = self.get_registration_for_trip(trip_id)
        return registration is not None and registration.status != 'cancelled'
    
    def get_latest_location(self):
        """Get participant's most recent location"""
        from app.models import Location
        return self.locations.filter_by(is_valid=True)\
                            .order_by(Location.timestamp.desc()).first()
    
    def get_upcoming_trips(self):
        """Get upcoming trips for this participant"""
        from datetime import date
        from app.models import Trip, TripRegistration
        return [reg.trip for reg in self.registrations.filter(
            TripRegistration.status == 'confirmed',
            TripRegistration.trip.has(Trip.start_date > date.today())
        ).all()]
    
    def serialize(self, include_sensitive=False):
        base_data = {
            'id': self.id,
            'full_name': self.full_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'age': self.age,
            'gender': self.gender,
            'grade_level': self.grade_level,
            'school_name': self.school_name,
            'photo_url': self.photo_url,
            'status': self.status,
            'active_registrations_count': self.active_registrations_count,
            'completed_trips_count': self.completed_trips_count,
            'has_complete_medical_info': self.has_complete_medical_info,
            'parent': {
                'id': self.parent.id,
                'full_name': self.parent.full_name,
                'email': self.parent.email,
                'phone': self.parent.phone
            } if self.parent else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_sensitive:
            base_data.update({
                'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
                'email': self.email,
                'phone': self.phone,
                'blood_type': self.blood_type,
                'medical_conditions': self.medical_conditions,
                'medications': self.medications,
                'allergies': self.allergies,
                'dietary_restrictions': self.dietary_restrictions,
                'emergency_medical_info': self.emergency_medical_info,
                'emergency_contacts': self.emergency_contacts_list,
                'special_requirements': self.special_requirements
            })
        
        return base_data
    
    def __repr__(self):
        return f'<Participant {self.full_name}>'