from datetime import datetime, date
from sqlalchemy import Numeric
from app.extensions import db
from app.models.base import BaseModel

class Trip(BaseModel):
    __tablename__ = 'trips'
    
    # Basic Information
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    itinerary = db.Column(db.JSON)  # Store detailed itinerary as JSON
    
    # Dates and Duration
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    registration_start_date = db.Column(db.Date)  # When registration opens
    registration_deadline = db.Column(db.Date)
    
    # Capacity and Pricing
    max_participants = db.Column(db.Integer, nullable=False, default=30)
    min_participants = db.Column(db.Integer, default=5)
    price_per_student = db.Column(Numeric(10, 2), nullable=False)
    
    # Deposit and Payment Terms
    deposit_amount = db.Column(Numeric(10, 2))  # Optional deposit
    deposit_deadline = db.Column(db.Date)
    allows_installments = db.Column(db.Boolean, default=False)
    refund_policy = db.Column(db.Text)
    
    # Status and Requirements
    status = db.Column(db.Enum('draft', 'published', 'registration_open', 'registration_closed', 
                              'full', 'in_progress', 'completed', 'cancelled', 
                              name='trip_status'), default='draft', nullable=False)
    medical_info_required = db.Column(db.Boolean, default=True)
    consent_required = db.Column(db.Boolean, default=True)
    
    # Location and Category
    destination = db.Column(db.String(200), nullable=False)
    destination_country = db.Column(db.String(100))
    meeting_point = db.Column(db.String(300))  # Where to meet for departure
    category = db.Column(db.String(50))  # 'science', 'history', 'cultural', 'sports', 'adventure'
    tags = db.Column(db.JSON)  # Array of tags for better searchability
    
    # Target Audience
    grade_level = db.Column(db.String(20))  # e.g., 'K-2', '3-5', '6-8', '9-12'
    min_age = db.Column(db.Integer)
    max_age = db.Column(db.Integer)
    
    # Visibility and Marketing
    featured = db.Column(db.Boolean, default=False, nullable=False)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    cover_image_url = db.Column(db.String(300))
    gallery_images = db.Column(db.JSON)  # Array of image URLs
    
    # Educational Value
    learning_objectives = db.Column(db.JSON)  # Array of learning objectives
    subjects_covered = db.Column(db.JSON)  # Array of subjects
    
    # Logistics
    transportation_included = db.Column(db.Boolean, default=True)
    meals_included = db.Column(db.Boolean, default=True)
    accommodation_included = db.Column(db.Boolean, default=False)
    meals_provided = db.Column(db.JSON)  # e.g., ['breakfast', 'lunch', 'dinner']
    
    # Safety and Requirements
    insurance_required = db.Column(db.Boolean, default=False)
    vaccination_requirements = db.Column(db.Text)
    special_equipment_needed = db.Column(db.Text)
    physical_requirements = db.Column(db.Text)
    
    # Cancellation
    cancellation_date = db.Column(db.DateTime)
    cancellation_reason = db.Column(db.Text)
    
    # Foreign Keys
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))  # If applicable
    
    # Relationships
    # participants = db.relationship('Participant', backref='trip', lazy='select', 
    #                               cascade='all, delete-orphan')
    participants = db.relationship('Participant', secondary='trip_registrations', back_populates='trips', viewonly=True)
    registrations = db.relationship('TripRegistration', back_populates='trip', lazy='dynamic', 
                                   cascade='all, delete-orphan')
    service_bookings = db.relationship('ServiceBooking', back_populates='trip', lazy='dynamic', 
                                      cascade='all, delete-orphan')
    locations = db.relationship('Location', backref='trip', lazy='select', 
                               cascade='all, delete-orphan')
    advertisements = db.relationship('Advertisement', backref='trip', lazy='dynamic')
    documents = db.relationship('Document', backref='trip', lazy='dynamic')
    emergencies = db.relationship('Emergency', backref='trip', lazy='dynamic')
    reviews = db.relationship('Review', backref='trip', lazy='dynamic')
    messages = db.relationship('Message', backref='trip', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', backref='trip', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_trip_dates', 'start_date', 'end_date'),
        db.Index('idx_trip_status', 'status'),
        db.Index('idx_trip_organizer', 'organizer_id'),
        db.Index('idx_trip_destination', 'destination'),
        db.Index('idx_trip_category', 'category'),
        db.Index('idx_trip_price', 'price_per_student'),
        db.Index('idx_trip_featured', 'featured'),
        db.Index('idx_trip_published', 'is_published'),
        db.Index('idx_trip_registration_deadline', 'registration_deadline'),
    )
    
    @property
    def duration_days(self):
        """Calculate trip duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    @property
    def current_participants_count(self):
        """Get current number of confirmed participants"""
        return self.registrations.filter_by(status='confirmed').count()
    
    @property
    def pending_registrations_count(self):
        """Get number of pending registrations"""
        return self.registrations.filter_by(status='pending').count()
    
    @property
    def available_spots(self):
        """Get number of available spots"""
        return max(0, self.max_participants - self.current_participants_count)
    
    @property
    def is_full(self):
        """Check if trip is at capacity"""
        return self.current_participants_count >= self.max_participants
    
    @property
    def is_upcoming(self):
        """Check if trip is upcoming"""
        return self.start_date and self.start_date > date.today()
    
    @property
    def is_in_progress(self):
        """Check if trip is currently in progress"""
        today = date.today()
        return (self.start_date and self.end_date and 
                self.start_date <= today <= self.end_date and
                self.status == 'in_progress')
    
    @property
    def registration_is_open(self):
        """Check if registration is currently open"""
        today = date.today()
        
        # Check basic status
        if self.status not in ['published', 'registration_open']:
            return False
        
        # Check if full
        if self.is_full:
            return False
        
        # Check registration dates
        if self.registration_start_date and today < self.registration_start_date:
            return False
        
        if self.registration_deadline and today > self.registration_deadline:
            return False
        
        return True
    
    @property
    def days_until_trip(self):
        """Get number of days until trip starts"""
        if not self.start_date:
            return None
        today = date.today()
        if self.start_date < today:
            return 0
        return (self.start_date - today).days
    
    @property
    def days_until_registration_deadline(self):
        """Get days until registration deadline"""
        if not self.registration_deadline:
            return None
        today = date.today()
        if self.registration_deadline < today:
            return 0
        return (self.registration_deadline - today).days
    
    def can_start(self):
        """Check if trip can be started"""
        return (self.status in ['registration_closed', 'full'] and 
                self.current_participants_count >= self.min_participants and
                self.start_date <= date.today())
    
    def get_total_revenue(self):
        """Calculate total revenue from confirmed registrations"""
        confirmed_count = self.current_participants_count
        return float(confirmed_count * self.price_per_student)
    
    def get_expected_revenue(self):
        """Calculate expected revenue including pending registrations"""
        confirmed_count = self.current_participants_count
        pending_count = self.pending_registrations_count
        return float((confirmed_count + pending_count) * self.price_per_student)
    
    def get_total_expenses(self):
        """Calculate total expenses from service bookings"""
        confirmed_bookings = self.service_bookings.filter_by(status='confirmed').all()
        return sum(float(booking.total_amount or 0) for booking in confirmed_bookings)
    
    def get_profit_estimate(self):
        """Estimate profit (revenue - expenses)"""
        return self.get_total_revenue() - self.get_total_expenses()
    
    def publish(self):
        """Publish the trip"""
        if self.status == 'draft':
            self.status = 'published'
            self.is_published = True
            db.session.commit()
    
    def open_registration(self):
        """Open registration for the trip"""
        if self.status == 'published':
            self.status = 'registration_open'
            db.session.commit()
    
    def close_registration(self):
        """Close registration"""
        if self.status in ['published', 'registration_open']:
            self.status = 'registration_closed'
            db.session.commit()
    
    def start_trip(self):
        """Mark trip as in progress"""
        if self.can_start():
            self.status = 'in_progress'
            db.session.commit()
    
    def complete_trip(self):
        """Mark trip as completed"""
        if self.status == 'in_progress':
            self.status = 'completed'
            
            # Complete all registrations
            for registration in self.registrations.filter_by(status='confirmed').all():
                registration.complete_registration()
            
            db.session.commit()
    
    def cancel_trip(self, reason=None):
        """Cancel the trip"""
        if self.status not in ['completed', 'cancelled']:
            self.status = 'cancelled'
            self.cancellation_date = datetime.now()
            if reason:
                self.cancellation_reason = reason
            db.session.commit()
    
    @classmethod
    def get_featured_trips(cls, limit=10):
        """Get featured trips"""
        return cls.query.filter_by(featured=True, is_published=True)\
                       .filter(cls.start_date > date.today())\
                       .order_by(cls.start_date)\
                       .limit(limit).all()
    
    @classmethod
    def get_upcoming_trips(cls, limit=20):
        """Get upcoming trips with open registration"""
        today = date.today()
        return cls.query.filter_by(is_published=True)\
                       .filter(cls.start_date > today)\
                       .filter(cls.status.in_(['published', 'registration_open']))\
                       .order_by(cls.start_date)\
                       .limit(limit).all()
    
    def serialize(self, include_details=False):
        base_data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'destination': self.destination,
            'destination_country': self.destination_country,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'registration_deadline': self.registration_deadline.isoformat() if self.registration_deadline else None,
            'duration_days': self.duration_days,
            'max_participants': self.max_participants,
            'min_participants': self.min_participants,
            'current_participants': self.current_participants_count,
            'available_spots': self.available_spots,
            'price_per_student': float(self.price_per_student),
            'deposit_amount': float(self.deposit_amount) if self.deposit_amount else None,
            'status': self.status,
            'category': self.category,
            'grade_level': self.grade_level,
            'registration_is_open': self.registration_is_open,
            'is_full': self.is_full,
            'featured': self.featured,
            'cover_image_url': self.cover_image_url,
            'days_until_trip': self.days_until_trip,
            'organizer': self.organizer.serialize() if self.organizer else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_details:
            base_data.update({
                'itinerary': self.itinerary,
                'meeting_point': self.meeting_point,
                'learning_objectives': self.learning_objectives,
                'subjects_covered': self.subjects_covered,
                'transportation_included': self.transportation_included,
                'meals_included': self.meals_included,
                'accommodation_included': self.accommodation_included,
                'meals_provided': self.meals_provided,
                'refund_policy': self.refund_policy,
                'insurance_required': self.insurance_required,
                'vaccination_requirements': self.vaccination_requirements,
                'special_equipment_needed': self.special_equipment_needed,
                'gallery_images': self.gallery_images,
                'tags': self.tags,
                'total_revenue': self.get_total_revenue(),
                'total_expenses': self.get_total_expenses(),
                'profit_estimate': self.get_profit_estimate()
            })
        
        return base_data
    
    def __repr__(self):
        return f'<Trip {self.title}>'