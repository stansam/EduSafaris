from app.extensions import db
from app.models.base import BaseModel


class ActivityLog(BaseModel):
    __tablename__ = 'activity_logs'
    
    # Action Information
    action = db.Column(db.String(100), nullable=False)
    # Actions: 'create', 'update', 'delete', 'login', 'logout', 'payment_made', 
    #          'booking_confirmed', 'consent_signed', 'emergency_reported', etc.
    
    description = db.Column(db.Text)
    action_category = db.Column(db.String(50))
    # Categories: 'user', 'trip', 'payment', 'booking', 'security', 'emergency'
    
    # Entity Information (Polymorphic)
    entity_type = db.Column(db.String(50))  # 'trip', 'payment', 'booking', 'user', etc.
    entity_id = db.Column(db.Integer)
    
    # Details
    old_values = db.Column(db.JSON)  # Store previous values for updates
    new_values = db.Column(db.JSON)  # Store new values
    meta_data = db.Column(db.JSON)  # Additional contextual information
    
    # Request Information
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(300))
    request_method = db.Column(db.String(10))  # GET, POST, PUT, DELETE
    request_url = db.Column(db.String(500))
    
    # Status
    status = db.Column(db.String(20), default='success')  # 'success', 'failed', 'warning'
    error_message = db.Column(db.Text)  # If status is 'failed'
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # User who performed the action
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'))  # If action related to a trip
    
    # Indexes
    __table_args__ = (
        db.Index('idx_activity_user', 'user_id'),
        db.Index('idx_activity_action', 'action'),
        db.Index('idx_activity_category', 'action_category'),
        db.Index('idx_activity_entity', 'entity_type', 'entity_id'),
        db.Index('idx_activity_trip', 'trip_id'),
        db.Index('idx_activity_created', 'created_at'),
        db.Index('idx_activity_status', 'status'),
    )
    
    @classmethod
    def log_action(cls, action, user_id=None, entity_type=None, entity_id=None, 
                   description=None, category=None, trip_id=None, old_values=None, 
                   new_values=None, metadata=None, ip_address=None, user_agent=None,
                   request_method=None, request_url=None, status='success', error_message=None):
        """Create a new activity log entry"""
        log = cls(
            action=action,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            action_category=category,
            trip_id=trip_id,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_url=request_url,
            status=status,
            error_message=error_message
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @classmethod
    def log_payment(cls, payment, user_id):
        """Log payment action"""
        return cls.log_action(
            action='payment_processed',
            user_id=user_id,
            entity_type='payment',
            entity_id=payment.id,
            description=f"Payment of {payment.amount} {payment.currency} processed",
            category='payment',
            trip_id=payment.trip_id,
            new_values={
                'amount': float(payment.amount),
                'status': payment.status,
                'payment_method': payment.payment_method
            }
        )
    
    @classmethod
    def log_consent(cls, consent, user_id):
        """Log consent signing"""
        return cls.log_action(
            action='consent_signed',
            user_id=user_id,
            entity_type='consent',
            entity_id=consent.id,
            description=f"Consent '{consent.title}' signed",
            category='consent',
            new_values={
                'signer_name': consent.signer_name,
                'signer_relationship': consent.signer_relationship
            }
        )
    
    @classmethod
    def log_emergency(cls, emergency, user_id):
        """Log emergency report"""
        return cls.log_action(
            action='emergency_reported',
            user_id=user_id,
            entity_type='emergency',
            entity_id=emergency.id,
            description=f"Emergency reported: {emergency.title}",
            category='emergency',
            trip_id=emergency.trip_id,
            new_values={
                'severity': emergency.severity,
                'emergency_type': emergency.emergency_type
            },
            status='warning'
        )
    
    @classmethod
    def log_booking(cls, booking, user_id, action_type='created'):
        """Log booking action"""
        return cls.log_action(
            action=f'booking_{action_type}',
            user_id=user_id,
            entity_type='booking',
            entity_id=booking.id,
            description=f"Booking {action_type}: {booking.booking_type}",
            category='booking',
            trip_id=booking.trip_id,
            new_values={
                'status': booking.status,
                'booking_type': booking.booking_type,
                'vendor_id': booking.vendor_id
            }
        )
    
    @classmethod
    def log_trip(cls, trip, user_id, action_type='created', old_status=None):
        """Log trip action"""
        old_vals = {'status': old_status} if old_status else None
        new_vals = {'status': trip.status, 'title': trip.title}
        
        return cls.log_action(
            action=f'trip_{action_type}',
            user_id=user_id,
            entity_type='trip',
            entity_id=trip.id,
            description=f"Trip {action_type}: {trip.title}",
            category='trip',
            trip_id=trip.id,
            old_values=old_vals,
            new_values=new_vals
        )
    
    @classmethod
    def get_user_activity(cls, user_id, limit=50):
        """Get activity log for a specific user"""
        return cls.query.filter_by(user_id=user_id)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit).all()
    
    @classmethod
    def get_trip_activity(cls, trip_id, limit=100):
        """Get activity log for a specific trip"""
        return cls.query.filter_by(trip_id=trip_id)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit).all()
    
    @classmethod
    def get_entity_activity(cls, entity_type, entity_id, limit=50):
        """Get activity log for a specific entity"""
        return cls.query.filter_by(entity_type=entity_type, entity_id=entity_id)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit).all()
    
    def serialize(self):
        return {
            'id': self.id,
            'action': self.action,
            'description': self.description,
            'action_category': self.action_category,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'metadata': self.meta_data,
            'status': self.status,
            'error_message': self.error_message,
            'user': self.user.serialize() if self.user else None,
            'trip_id': self.trip_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ActivityLog {self.action} - {self.entity_type}:{self.entity_id}>'
