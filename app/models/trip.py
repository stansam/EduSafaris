from datetime import datetime, date
from sqlalchemy import Numeric
from app.extensions import db
from app.models.base import BaseModel

class Trip(BaseModel):
    __tablename__ = 'trips'
    
    # Basic Information
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    itinerary = db.Column(db.JSON)  # Store itinerary as JSON
    
    # Dates and Duration
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    registration_deadline = db.Column(db.Date)
    
    # Capacity and Pricing
    max_participants = db.Column(db.Integer, nullable=False, default=30)
    min_participants = db.Column(db.Integer, default=5)
    price_per_student = db.Column(Numeric(10, 2), nullable=False)
    
    # Status and Requirements
    status = db.Column(db.Enum('draft', 'active', 'full', 'in_progress', 'completed', 'cancelled', 
                              name='trip_status'), default='draft', nullable=False)
    medical_info_required = db.Column(db.Boolean, default=True)
    consent_required = db.Column(db.Boolean, default=True)
    
    # Location and Category
    destination = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))  # e.g., 'science', 'history', 'cultural'
    grade_level = db.Column(db.String(20))  # e.g., 'K-2', '3-5', '6-8', '9-12'
    
    # Foreign Keys
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    participants = db.relationship('Participant', backref='trip', lazy='dynamic', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='trip', lazy='dynamic', cascade='all, delete-orphan')
    locations = db.relationship('Location', backref='trip', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='trip', lazy='dynamic')
    advertisements = db.relationship('Advertisement', backref='trip', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_trip_dates', 'start_date', 'end_date'),
        db.Index('idx_trip_status', 'status'),
        db.Index('idx_trip_organizer', 'organizer_id'),
        db.Index('idx_trip_destination', 'destination'),
    )
    
    @property
    def duration_days(self):
        """Calculate trip duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    @property
    def current_participants(self):
        """Get current number of participants"""
        return self.participants.filter_by(status='confirmed').count()
    
    @property
    def available_spots(self):
        """Get number of available spots"""
        return max(0, self.max_participants - self.current_participants)
    
    @property
    def is_full(self):
        """Check if trip is at capacity"""
        return self.current_participants >= self.max_participants
    
    @property
    def is_upcoming(self):
        """Check if trip is upcoming"""
        return self.start_date and self.start_date > date.today()
    
    @property
    def is_active(self):
        """Check if trip is currently in progress"""
        today = date.today()
        return (self.start_date and self.end_date and 
                self.start_date <= today <= self.end_date and
                self.status == 'in_progress')
    
    @property
    def registration_open(self):
        """Check if registration is still open"""
        today = date.today()
        return (self.status == 'active' and 
                not self.is_full and
                (not self.registration_deadline or self.registration_deadline >= today))
    
    def can_start(self):
        """Check if trip can be started"""
        return (self.status == 'active' and 
                self.current_participants >= self.min_participants and
                self.start_date <= date.today())
    
    def get_total_revenue(self):
        """Calculate total revenue from confirmed bookings"""
        confirmed_participants = self.participants.filter_by(status='confirmed').count()
        return float(confirmed_participants * self.price_per_student)
    
    def get_confirmed_vendor_bookings(self):
        """Get all confirmed vendor bookings for this trip"""
        return self.bookings.filter_by(status='confirmed').all()
    
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'destination': self.destination,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'duration_days': self.duration_days,
            'max_participants': self.max_participants,
            'current_participants': self.current_participants,
            'available_spots': self.available_spots,
            'price_per_student': float(self.price_per_student),
            'status': self.status,
            'category': self.category,
            'grade_level': self.grade_level,
            'registration_open': self.registration_open,
            'organizer': self.organizer.serialize() if self.organizer else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Trip {self.title}>'