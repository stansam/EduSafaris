from datetime import datetime
from app.extensions import db
from app.models.base import BaseModel

class Location(BaseModel):
    __tablename__ = 'locations'
    
    # Location Information
    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # Coordinates
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    altitude = db.Column(db.Float)
    accuracy = db.Column(db.Float)  # GPS accuracy in meters
    
    # Address Information
    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    speed = db.Column(db.Float)
    heading = db.Column(db.Float)

    device_id = db.Column(db.String(50), nullable=False)  
    device_type = db.Column(db.String(30), default='mobile')

    # Tracking Information
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)
    server_timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)
    location_type = db.Column(db.String(50))  # 'checkin', 'waypoint', 'accommodation', 'activity', 'emergency'
    
    # Status
    is_valid = db.Column(db.Boolean, default=True)
    battery_level = db.Column(db.Integer)  # if applicable
    signal_strength = db.Column(db.Integer)

    is_safe_zone = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    
    # Foreign Keys
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_location_trip', 'trip_id'),
        db.Index('idx_trip_location_device', 'device_id'),
        db.Index('idx_location_coordinates', 'latitude', 'longitude'),
        db.Index('idx_location_timestamp', 'timestamp'),
        db.Index('idx_trip_location_trip_device', 'trip_id', 'device_id'),
        db.Index('idx_location_type', 'location_type'),
    )
    
    @classmethod
    def add_checkin(cls, trip_id, latitude, longitude, name=None, notes=None):
        """Add a check-in location for a trip"""
        location = cls(
            trip_id=trip_id,
            latitude=latitude,
            longitude=longitude,
            name=name or 'Check-in Point',
            location_type='checkin',
            notes=notes
        )
        db.session.add(location)
        db.session.commit()
        return location
    
    def calculate_distance_to(self, other_location):
        """Calculate distance to another location using Haversine formula"""
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other_location.latitude), math.radians(other_location.longitude)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def is_within_radius(self, center_lat, center_lon, radius_km):
        """Check if location is within specified radius of a center point"""
        import math
        
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(center_lat), math.radians(center_lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance = c * 6371  # Earth's radius in km
        
        return distance <= radius_km
    
    @classmethod
    def get_latest_for_trip(cls, trip_id, limit=10):
        """Get latest locations for a trip"""
        return cls.query.filter_by(trip_id=trip_id, is_valid=True)\
                       .order_by(cls.timestamp.desc())\
                       .limit(limit).all()
    
    @classmethod
    def get_latest_for_device(cls, trip_id, device_id):
        """Get latest location for specific device"""
        return cls.query.filter_by(trip_id=trip_id, device_id=device_id, is_valid=True)\
                       .order_by(cls.timestamp.desc()).first()
    
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'accuracy': self.accuracy,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'location_type': self.location_type,
            'is_safe_zone': self.is_safe_zone,
            'notes': self.notes,
            'trip_id': self.trip_id
        }
    
    def __repr__(self):
        return f'<Location {self.name} ({self.latitude}, {self.longitude})>'
