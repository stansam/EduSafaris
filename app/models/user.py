from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.base import BaseModel

class User(UserMixin, BaseModel):
    __tablename__ = 'users'
    
    # Basic Information
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    _password_hash = db.Column("password_hash", db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    
    # Role and Status
    role = db.Column(db.Enum('student', 'parent', 'teacher', 'vendor', 'admin', name='user_roles'), 
                    nullable=False, default='student')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Profile Information
    school = db.Column(db.String(100))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    
    # Emergency Contact (for teachers/parents)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    
    # Authentication
    last_login = db.Column(db.DateTime)
    password_reset_token = db.Column(db.String(100))
    password_reset_expires = db.Column(db.DateTime)
    email_verification_token = db.Column(db.String(100))
    
    # Relationships
    organized_trips = db.relationship('Trip', backref='organizer', lazy='dynamic', 
                                    foreign_keys='Trip.organizer_id')
    vendor_profile = db.relationship('Vendor', backref='user', uselist=False)
    trip_participants = db.relationship('Participant', backref='user', lazy='dynamic')
    sent_notifications = db.relationship('Notification', backref='sender', lazy='dynamic',
                                       foreign_keys='Notification.sender_id')
    received_notifications = db.relationship('Notification', backref='recipient', lazy='dynamic',
                                           foreign_keys='Notification.recipient_id')
    emergency_contacts = db.relationship('Emergency', backref='contact_person', lazy='dynamic')
    consents = db.relationship('Consent', backref='parent', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_user_email', 'email'),
        db.Index('idx_user_role', 'role'),
        db.Index('idx_user_active', 'is_active'),
    )
    
    @property
    def password(self):
        raise AttributeError('Password is write-only.')
    
    @password.setter
    def password(self, password):
        self._password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self._password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_vendor(self):
        return self.role == 'vendor'
    
    def is_parent(self):
        return self.role == 'parent'
    
    def get_dashboard_url(self):
        from flask import url_for

        if self.is_admin:
            return url_for('admin.dashboard')
        if self.is_teacher:
            return url_for('trips.list_trips')
        if self.is_vendor:
            return url_for('vendor.vendor_directory')
        if self.is_parent:
            return url_for('parent')
        else:
            return url_for('student')
    
    def get_total_students(self):
        """Get total number of students for teacher"""
        if not self.is_teacher():
            return 0
        return sum(trip.participants.count() for trip in self.organized_trips)
    
    def get_average_rating(self):
        """Get average rating for vendor"""
        if not self.vendor_profile:
            return 0.0
        
        ratings = [booking.rating for booking in self.vendor_profile.bookings 
                  if booking.rating is not None]
        return sum(ratings) / len(ratings) if ratings else 0.0
    
    def get_upcoming_trips_count(self):
        """Get count of upcoming trips for parent"""
        if not self.is_parent():
            return 0
        
        upcoming_count = 0
        for consent in self.consents:
            if consent.participant and consent.participant.trip:
                trip = consent.participant.trip
                if trip.start_date and trip.start_date > datetime.now().date():
                    upcoming_count += 1
        return upcoming_count
    
    def serialize(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'school': self.school,
            'profile_picture': self.profile_picture,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.email}>'