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
            meta_data=metadata,
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
        """Log payment action dynamically based on payment type"""
        from app.models import RegistrationPayment, ServicePayment, AdvertisementPayment
        entity_type = payment.__class__.__name__  # Detects: 'RegistrationPayment', 'ServicePayment', etc.
        trip_id = None
        description = None
        category = 'payment'
        new_values = {
            'amount': float(payment.amount),
            'currency': payment.currency,
            'status': payment.status,
            'payment_method': payment.payment_method,
            'reference_number': payment.reference_number,
            'transaction_id': payment.transaction_id
        }

        # --- Case 1: Parent paying for child registration ---
        if isinstance(payment, RegistrationPayment):
            trip_id = getattr(payment.registration, 'trip_id', None)
            description = (
                f"Parent payment for trip registration "
                f"(Reg ID: {payment.registration_id}, Parent ID: {payment.parent_id})"
            )
            new_values.update({
                'registration_id': payment.registration_id,
                'parent_id': payment.parent_id
            })

        # --- Case 2: Teacher paying vendor for a service ---
        elif isinstance(payment, ServicePayment):
            trip_id = payment.trip_id
            description = (
                f"Service payment to vendor '{payment.vendor.business_name}' "
                f"for trip '{payment.trip.title if payment.trip else 'N/A'}'"
            )
            category = 'vendor_payment'
            new_values.update({
                'vendor_id': payment.vendor_id,
                'trip_id': payment.trip_id,
                'service_booking_id': payment.service_booking_id
            })

        # --- Case 3: Advertisement campaign payment ---
        elif isinstance(payment, AdvertisementPayment):
            description = (
                f"Advertisement payment for campaign ID {payment.advertisement_id} "
                f"({payment.billing_period_start} to {payment.billing_period_end})"
            )
            category = 'advertisement_payment'
            new_values.update({
                'advertisement_id': payment.advertisement_id,
                'billing_period_start': str(payment.billing_period_start),
                'billing_period_end': str(payment.billing_period_end),
            })

        else:
            description = f"Generic payment of {payment.amount} {payment.currency}"

        # --- Create the activity log ---
        return cls.log_action(
            action='payment_processed',
            user_id=user_id,
            entity_type=entity_type,
            entity_id=payment.id,
            description=description,
            category=category,
            trip_id=trip_id,
            new_values=new_values
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
    def log_trip_registration(cls, registration, user_id, action_type='created'):
        """Log parent booking their child into a trip"""
        return cls.log_action(
            action=f'trip_registration_{action_type}',
            user_id=user_id,
            entity_type='trip_registration',
            entity_id=registration.id,
            description=f"Trip registration {action_type} for participant '{registration.participant.full_name}'",
            category='booking',
            trip_id=registration.trip_id,
            new_values={
                'status': registration.status,
                'payment_status': registration.payment_status,
                'amount_paid': float(registration.amount_paid or 0),
                'participant_id': registration.participant_id,
                'parent_id': registration.parent_id
            }
        )


    @classmethod
    def log_service_booking(cls, booking, user_id, action_type='created'):
        """Log teacher booking a vendor/service for a trip"""
        return cls.log_action(
            action=f'service_booking_{action_type}',
            user_id=user_id,
            entity_type='service_booking',
            entity_id=booking.id,
            description=f"Service booking {action_type} with vendor ID {booking.vendor_id}",
            category='vendor_booking',
            trip_id=booking.trip_id,
            new_values={
                'status': booking.status,
                'service_type': booking.service_type,
                'vendor_id': booking.vendor_id,
                'total_amount': float(booking.total_amount or 0)
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
            description=f"Trip '{trip.title}' {action_type} by user {user_id}",
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
