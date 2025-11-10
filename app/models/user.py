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
                    nullable=False, default='parent')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Profile Information
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))  # For teachers
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(300))
    date_of_birth = db.Column(db.Date)
    
    # Address Information
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))
    
    # Emergency Contact (for teachers)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    
    # Professional Information (for teachers)
    teacher_id = db.Column(db.String(50))  # Staff/Teacher ID
    department = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    years_of_experience = db.Column(db.Integer)
    
    # Authentication
    last_login = db.Column(db.DateTime)
    password_reset_token = db.Column(db.String(100))
    password_reset_expires = db.Column(db.DateTime)
    email_verification_token = db.Column(db.String(100))
    email_verification_sent_at = db.Column(db.DateTime)
    
    # Preferences
    notification_preferences = db.Column(db.JSON)  # Email, SMS, Push preferences
    language_preference = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='UTC')
    
    # Relationships
    # School relationship
    school = db.relationship('School', backref='teachers')
    
    # Teacher relationships
    organized_trips = db.relationship('Trip', backref='organizer', lazy='dynamic', 
                                     foreign_keys='Trip.organizer_id')
    
    # Vendor relationship
    vendor_profile = db.relationship('Vendor', backref='user', uselist=False)
    
    # Parent relationships
    children = db.relationship('Participant', backref='parent', 
                              foreign_keys='Participant.parent_id', lazy='dynamic')
    registrations = db.relationship('TripRegistration', back_populates='parent', lazy='dynamic')
    registration_payments = db.relationship('RegistrationPayment', back_populates='parent', 
                                           foreign_keys='RegistrationPayment.parent_id', lazy='dynamic')
    
    # Communication
    sent_messages = db.relationship('Message', backref='sender', 
                                   foreign_keys='Message.sender_id', lazy='dynamic')
    received_messages = db.relationship('Message', backref='recipient', 
                                       foreign_keys='Message.recipient_id', lazy='dynamic')
    sent_notifications = db.relationship('Notification', backref='sender', 
                                        foreign_keys='Notification.sender_id', lazy='dynamic')
    received_notifications = db.relationship('Notification', backref='recipient', 
                                            foreign_keys='Notification.recipient_id', lazy='dynamic')
    
    # Other relationships
    documents = db.relationship('Document', backref='uploader', 
                               foreign_keys='Document.uploaded_by', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', backref='user', 
                                   foreign_keys='ActivityLog.user_id', lazy='dynamic')
    reviews = db.relationship('Review', backref='reviewer', 
                             foreign_keys='Review.reviewer_id', lazy='dynamic')
    emergency_contacts = db.relationship('Emergency', backref='contact_person', lazy='dynamic')
    consents = db.relationship('Consent', backref='parent', 
                              foreign_keys='Consent.parent_id', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_user_email', 'email'),
        db.Index('idx_user_role', 'role'),
        db.Index('idx_user_active', 'is_active'),
        db.Index('idx_user_school', 'school_id'),
        db.Index('idx_user_verified', 'is_verified'),
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
    
    @property
    def full_address(self):
        """Get formatted full address"""
        parts = [self.address_line1, self.address_line2, self.city, 
                self.state, self.postal_code, self.country]
        return ', '.join([part for part in parts if part])
    
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

        if self.is_admin():
            return url_for('admin.dashboard')
        elif self.is_teacher():
            return url_for('teacher.dashboard')
        elif self.is_vendor():
            return url_for('vendor.dashboard')
        elif self.is_parent():
            return url_for('parent_comm.dashboard')
        else:
            return url_for('main.index')
    
    # Teacher-specific methods
    def get_total_students(self):
        """Get total number of students across all trips"""
        if not self.is_teacher():
            return 0
        return sum(trip.current_participants_count for trip in self.organized_trips.all())
    
    def get_active_trips_count(self):
        """Get number of active trips"""
        if not self.is_teacher():
            return 0
        from datetime import date
        from app.models import Trip

        return self.organized_trips.filter(
            db.or_(
                Trip.status == 'in_progress',
                db.and_(
                    Trip.status.in_(['published', 'registration_open']),
                    Trip.start_date > date.today()
                )
            )
        ).count()
    
    def get_upcoming_trips(self):
        """Get upcoming trips for teacher"""
        if not self.is_teacher():
            return []
        from datetime import date
        from app.models import Trip

        return self.organized_trips.filter(
            Trip.start_date > date.today()
        ).order_by(Trip.start_date).all()
    
    # Vendor-specific methods
    def get_average_rating(self):
        """Get average rating for vendor"""
        if not self.vendor_profile:
            return 0.0
        return self.vendor_profile.average_rating
    
    # Parent-specific methods
    def get_children_count(self):
        """Get total number of children"""
        if not self.is_parent():
            return 0
        return self.children.filter_by(status='active').count()
    
    def get_active_registrations(self):
        """Get active trip registrations for parent"""
        from app.models import TripRegistration

        if not self.is_parent():
            return []
        return self.registrations.filter(
            TripRegistration.status.in_(['pending', 'confirmed', 'waitlisted'])
        ).all()
    
    def get_upcoming_trips_count(self):
        """Get count of upcoming trips for parent's children"""
        if not self.is_parent():
            return 0
        from datetime import date
        from app.models import TripRegistration, Trip
        return self.registrations.filter(
            TripRegistration.status == 'confirmed',
            TripRegistration.trip.has(Trip.start_date > date.today())
        ).count()
    
    def get_total_spent(self):
        """Get total amount spent by parent"""
        if not self.is_parent():
            return 0.0
        completed_payments = self.registration_payments.filter_by(status='completed').all()
        return sum(float(payment.amount) for payment in completed_payments)
    
    def get_outstanding_balance(self):
        """Get total outstanding balance for parent"""
        if not self.is_parent():
            return 0.0
        active_registrations = self.get_active_registrations()
        return sum(reg.outstanding_balance for reg in active_registrations)
    
    # Notification methods
    def get_unread_notifications_count(self):
        """Get count of unread notifications"""
        return self.received_notifications.filter_by(is_read=False).count()
    
    def get_unread_messages_count(self):
        """Get count of unread messages"""
        return self.received_messages.filter_by(is_read=False).count()
    
    def serialize(self, include_sensitive=False):
        base_data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'profile_picture': self.profile_picture,
            'city': self.city,
            'country': self.country,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        # Role-specific data
        if self.is_teacher():
            base_data.update({
                'school': self.school.serialize() if self.school else None,
                'teacher_id': self.teacher_id,
                'department': self.department,
                'specialization': self.specialization,
                'active_trips_count': self.get_active_trips_count(),
                'total_students': self.get_total_students()
            })
        elif self.is_parent():
            base_data.update({
                'children_count': self.get_children_count(),
                'upcoming_trips_count': self.get_upcoming_trips_count(),
                'unread_notifications': self.get_unread_notifications_count()
            })
        elif self.is_vendor():
            base_data.update({
                'vendor_profile': self.vendor_profile.serialize() if self.vendor_profile else None
            })
        
        if include_sensitive:
            base_data.update({
                'address': self.full_address,
                'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
                'bio': self.bio
            })
        
        return base_data
    
    def __repr__(self):
        return f'<User {self.email} - {self.role}>'