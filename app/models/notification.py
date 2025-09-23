from datetime import datetime
from app.extensions import db
from app.models.base import BaseModel

class Notification(BaseModel):
    __tablename__ = 'notifications'
    
    # Notification Content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 'trip_update', 'payment', 'booking', 'emergency'
    
    # Delivery Information
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_date = db.Column(db.DateTime)
    
    # Delivery Methods
    send_email = db.Column(db.Boolean, default=True)
    send_sms = db.Column(db.Boolean, default=False)
    send_push = db.Column(db.Boolean, default=True)
    
    # Delivery Status
    email_sent = db.Column(db.Boolean, default=False)
    sms_sent = db.Column(db.Boolean, default=False)
    push_sent = db.Column(db.Boolean, default=False)
    
    # Scheduling
    scheduled_for = db.Column(db.DateTime)  # For scheduled notifications
    sent_date = db.Column(db.DateTime)
    
    # Priority and Category
    priority = db.Column(db.Enum('low', 'normal', 'high', 'urgent', name='notification_priority'), 
                        default='normal', nullable=False)
    category = db.Column(db.String(50))
    
    # Related Data
    related_data = db.Column(db.JSON)  # Store related object IDs and data
    action_url = db.Column(db.String(200))  # URL for action button
    action_text = db.Column(db.String(50))  # Text for action button
    
    # Foreign Keys
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_notification_recipient', 'recipient_id'),
        db.Index('idx_notification_type', 'notification_type'),
        db.Index('idx_notification_read', 'is_read'),
        db.Index('idx_notification_priority', 'priority'),
        db.Index('idx_notification_scheduled', 'scheduled_for'),
    )
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_date = datetime.now()
        db.session.commit()
    
    def mark_as_sent(self, email=False, sms=False, push=False):
        """Mark delivery methods as sent"""
        if email:
            self.email_sent = True
        if sms:
            self.sms_sent = True
        if push:
            self.push_sent = True
        
        if not self.sent_date:
            self.sent_date = datetime.now()
        
        db.session.commit()
    
    @classmethod
    def create_trip_notification(cls, trip, message, notification_type='trip_update', priority='normal'):
        """Create notification for all trip participants"""
        notifications = []
        
        # Notify trip organizer
        notification = cls(
            title=f'Trip Update: {trip.title}',
            message=message,
            notification_type=notification_type,
            priority=priority,
            sender_id=None,  # System notification
            recipient_id=trip.organizer_id,
            related_data={'trip_id': trip.id}
        )
        db.session.add(notification)
        notifications.append(notification)
        
        # Notify participants' parents/guardians
        for participant in trip.participants:
            if participant.user and participant.user.id != trip.organizer_id:
                notification = cls(
                    title=f'Trip Update: {trip.title}',
                    message=message,
                    notification_type=notification_type,
                    priority=priority,
                    sender_id=None,
                    recipient_id=participant.user.id,
                    related_data={'trip_id': trip.id, 'participant_id': participant.id}
                )
                db.session.add(notification)
                notifications.append(notification)
        
        db.session.commit()
        return notifications
    
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'read_date': self.read_date.isoformat() if self.read_date else None,
            'priority': self.priority,
            'category': self.category,
            'action_url': self.action_url,
            'action_text': self.action_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sender': self.sender.serialize() if self.sender else None,
            'related_data': self.related_data
        }
    
    def __repr__(self):
        return f'<Notification {self.title}>'
