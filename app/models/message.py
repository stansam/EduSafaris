from datetime import datetime
from app.extensions import db
from app.models.base import BaseModel

class Message(BaseModel):
    __tablename__ = 'messages'
    
    # Message Content
    subject = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    
    # Message Type and Priority
    message_type = db.Column(db.String(50), default='direct')
    # Types: 'direct', 'trip_broadcast', 'system', 'support'
    
    priority = db.Column(db.Enum('low', 'normal', 'high', 'urgent', 
                                 name='message_priority'), default='normal')
    
    # Status
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_date = db.Column(db.DateTime)
    is_archived = db.Column(db.Boolean, default=False)
    is_deleted_by_sender = db.Column(db.Boolean, default=False)
    is_deleted_by_recipient = db.Column(db.Boolean, default=False)
    
    # Thread Information
    parent_message_id = db.Column(db.Integer, db.ForeignKey('messages.id'))
    thread_id = db.Column(db.String(50))  # Group related messages
    
    # Attachments
    has_attachments = db.Column(db.Boolean, default=False)
    attachment_count = db.Column(db.Integer, default=0)
    
    # Foreign Keys
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'))  # If related to a trip
    
    # Relationships
    replies = db.relationship('Message', backref=db.backref('parent_message', remote_side='Message.id'),
                             lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_message_sender', 'sender_id'),
        db.Index('idx_message_recipient', 'recipient_id'),
        db.Index('idx_message_trip', 'trip_id'),
        db.Index('idx_message_read', 'is_read'),
        db.Index('idx_message_thread', 'thread_id'),
        db.Index('idx_message_type', 'message_type'),
        db.Index('idx_message_created', 'created_at'),
    )
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_date = datetime.now()
            db.session.commit()
    
    def archive(self):
        """Archive the message"""
        self.is_archived = True
        db.session.commit()
    
    def delete_for_sender(self):
        """Delete message from sender's view"""
        self.is_deleted_by_sender = True
        db.session.commit()
    
    def delete_for_recipient(self):
        """Delete message from recipient's view"""
        self.is_deleted_by_recipient = True
        db.session.commit()
    
    def reply(self, sender_id, content, subject=None):
        """Create a reply to this message"""
        reply_message = Message(
            sender_id=sender_id,
            recipient_id=self.sender_id,
            subject=subject or f"Re: {self.subject}",
            content=content,
            parent_message_id=self.id,
            thread_id=self.thread_id or str(self.id),
            trip_id=self.trip_id,
            message_type=self.message_type
        )
        db.session.add(reply_message)
        db.session.commit()
        return reply_message
    
    @classmethod
    def create_trip_broadcast(cls, trip, sender_id, subject, content):
        """Create broadcast message to all trip participants' parents"""
        messages = []
        
        # Get unique parents from trip participants
        parent_ids = set()
        for participant in trip.participants:
            if participant.parent_id:
                parent_ids.add(participant.parent_id)
        
        # Create message for each parent
        for parent_id in parent_ids:
            message = cls(
                sender_id=sender_id,
                recipient_id=parent_id,
                subject=subject,
                content=content,
                trip_id=trip.id,
                message_type='trip_broadcast',
                thread_id=f"trip_{trip.id}_broadcast_{datetime.now().timestamp()}"
            )
            db.session.add(message)
            messages.append(message)
        
        db.session.commit()
        return messages
    
    @classmethod
    def get_conversation(cls, user1_id, user2_id, trip_id=None):
        """Get conversation between two users"""
        query = cls.query.filter(
            db.or_(
                db.and_(cls.sender_id == user1_id, cls.recipient_id == user2_id),
                db.and_(cls.sender_id == user2_id, cls.recipient_id == user1_id)
            )
        )
        
        if trip_id:
            query = query.filter_by(trip_id=trip_id)
        
        return query.order_by(cls.created_at.desc()).all()
    
    def serialize(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'content': self.content,
            'message_type': self.message_type,
            'priority': self.priority,
            'is_read': self.is_read,
            'read_date': self.read_date.isoformat() if self.read_date else None,
            'is_archived': self.is_archived,
            'has_attachments': self.has_attachments,
            'attachment_count': self.attachment_count,
            'sender': self.sender.serialize() if self.sender else None,
            'recipient': self.recipient.serialize() if self.recipient else None,
            'trip_id': self.trip_id,
            'parent_message_id': self.parent_message_id,
            'thread_id': self.thread_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reply_count': self.replies.count() if self.replies else 0
        }
    
    def __repr__(self):
        return f'<Message {self.id} - {self.subject}>'
