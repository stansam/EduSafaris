from app.extensions import db
from app.models.base import BaseModel

class School(BaseModel):
    """School/Institution model for organizing trips"""
    __tablename__ = 'schools'
    
    # Basic Information
    name = db.Column(db.String(200), nullable=False)
    short_name = db.Column(db.String(50))  # Abbreviation
    school_type = db.Column(db.String(50))  # 'primary', 'secondary', 'high', 'university'
    description = db.Column(db.Text)
    
    # Contact Information
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    website = db.Column(db.String(200))
    
    # Address
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))
    
    # Registration Details
    registration_number = db.Column(db.String(100))  # Government registration
    tax_id = db.Column(db.String(100))
    
    # Settings
    logo_url = db.Column(db.String(300))
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Statistics
    total_students = db.Column(db.Integer, default=0)
    total_teachers = db.Column(db.Integer, default=0)
    
    # Relationships
    trips = db.relationship('Trip', backref='school', lazy='dynamic')
    # teachers = db.relationship('User', backref='school', lazy='dynamic',
    #                          foreign_keys='User.school_id')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_school_name', 'name'),
        db.Index('idx_school_city', 'city'),
        db.Index('idx_school_type', 'school_type'),
        db.Index('idx_school_active', 'is_active'),
        db.Index('idx_school_verified', 'is_verified'),
    )
    
    @property
    def full_address(self):
        """Get formatted full address"""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in parts if part])
    
    @property
    def total_trips(self):
        """Get total number of trips organized by this school"""
        return self.trips.count()
    
    @property
    def active_trips(self):
        """Get number of active trips"""
        from datetime import date
        from app.models import Trip

        return self.trips.filter(
            db.or_(
                Trip.status == 'in_progress',
                db.and_(
                    Trip.status.in_(['published', 'registration_open']),
                    Trip.start_date > date.today()
                )
            )
        ).count()
    
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'school_type': self.school_type,
            'description': self.description,
            'email': self.email,
            'phone': self.phone,
            'website': self.website,
            'address': self.full_address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'logo_url': self.logo_url,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'total_students': self.total_students,
            'total_teachers': self.total_teachers,
            'total_trips': self.total_trips,
            'active_trips': self.active_trips,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<School {self.name}>'