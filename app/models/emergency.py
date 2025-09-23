from datetime import datetime
from app.extensions import db
from app.models.base import BaseModel

class Emergency(BaseModel):
    __tablename__ = 'emergencies'
    
    # Emergency Information
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    emergency_type = db.Column(db.String(50), nullable=False)  # 'medical', 'safety', 'weather', 'transport', 'other'
    
    # Severity and Status
    severity = db.Column(db.Enum('low', 'medium', 'high', 'critical', name='emergency_severity'), 
                        nullable=False)
    status = db.Column(db.Enum('active', 'responding', 'resolved', 'closed', name='emergency_status'), 
                      default='active', nullable=False)
    
    # Location Information
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_description = db.Column(db.String(300))
    
    # People Involved
    people_affected = db.Column(db.JSON)  # Array of participant IDs or names
    injuries_reported = db.Column(db.Boolean, default=False)
    injury_details = db.Column(db.Text)
    
    # Response Information
    response_actions = db.Column(db.JSON)  # Array of actions taken
    emergency_services_contacted = db.Column(db.Boolean, default=False)
    emergency_services_details = db.Column(db.Text)
    
    # Resolution
    resolution_details = db.Column(db.Text)
    resolved_date = db.Column(db.DateTime)
    
    # Reporting
    reported_by = db.Column(db.String(100))  # Name of person reporting
    reporter_phone = db.Column(db.String(20))
    
    # Follow-up
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_notes = db.Column(db.Text)
    
    # Foreign Keys
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'))
    contact_person_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Primary contact handling emergency
    
    # Indexes
    __table_args__ = (
        db.Index('idx_emergency_trip', 'trip_id'),
        db.Index('idx_emergency_severity', 'severity'),
        db.Index('idx_emergency_status', 'status'),
        db.Index('idx_emergency_type', 'emergency_type'),
        db.Index('idx_emergency_created', 'created_at'),
    )
    
    def add_response_action(self, action, timestamp=None):
        """Add a response action to the emergency"""
        if not self.response_actions:
            self.response_actions = []
        
        action_entry = {
            'action': action,
            'timestamp': (timestamp or datetime.now()).isoformat(),
            'recorded_at': datetime.now().isoformat()
        }
        
        # SQLAlchemy requires reassignment for JSON columns to detect changes
        actions = self.response_actions.copy()
        actions.append(action_entry)
        self.response_actions = actions
        
        db.session.commit()
    
    def escalate_severity(self, new_severity, reason=None):
        """Escalate emergency severity"""
        old_severity = self.severity
        self.severity = new_severity
        
        escalation_action = f'Severity escalated from {old_severity} to {new_severity}'
        if reason:
            escalation_action += f'. Reason: {reason}'
        
        self.add_response_action(escalation_action)
    
    def resolve_emergency(self, resolution_details):
        """Mark emergency as resolved"""
        self.status = 'resolved'
        self.resolved_date = datetime.now()
        self.resolution_details = resolution_details
        
        self.add_response_action(f'Emergency resolved: {resolution_details}')
        
        db.session.commit()
    
    def close_emergency(self):
        """Close the emergency"""
        self.status = 'closed'
        db.session.commit()
    
    @property
    def duration_minutes(self):
        """Calculate duration of emergency in minutes"""
        end_time = self.resolved_date or datetime.now()
        return int((end_time - self.created_at).total_seconds() / 60)
    
    @classmethod
    def create_medical_emergency(cls, trip_id, description, people_affected, location_desc=None, 
                                latitude=None, longitude=None, reporter_name=None, reporter_phone=None):
        """Create a medical emergency"""
        emergency = cls(
            title='Medical Emergency',
            description=description,
            emergency_type='medical',
            severity='high',
            trip_id=trip_id,
            people_affected=people_affected,
            injuries_reported=True,
            location_description=location_desc,
            latitude=latitude,
            longitude=longitude,
            reported_by=reporter_name,
            reporter_phone=reporter_phone
        )
        
        db.session.add(emergency)
        db.session.commit()
        
        emergency.add_response_action('Medical emergency reported')
        return emergency
    
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'emergency_type': self.emergency_type,
            'severity': self.severity,
            'status': self.status,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'location_description': self.location_description,
            'people_affected': self.people_affected,
            'injuries_reported': self.injuries_reported,
            'emergency_services_contacted': self.emergency_services_contacted,
            'response_actions': self.response_actions,
            'resolution_details': self.resolution_details,
            'resolved_date': self.resolved_date.isoformat() if self.resolved_date else None,
            'duration_minutes': self.duration_minutes,
            'reported_by': self.reported_by,
            'reporter_phone': self.reporter_phone,
            'follow_up_required': self.follow_up_required,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'trip_id': self.trip_id
        }
    
    def __repr__(self):
        return f'<Emergency {self.title} - {self.severity}>'
