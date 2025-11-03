from datetime import datetime
from app.extensions import db
from app.models.base import BaseModel

class Document(BaseModel):
    __tablename__ = 'documents'
    
    # Document Information
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_name = db.Column(db.String(300), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    file_type = db.Column(db.String(50))  # MIME type
    
    # Document Classification
    document_type = db.Column(db.String(50), nullable=False)
    # Types: 'consent_form', 'medical_form', 'itinerary', 'insurance', 
    #        'vendor_license', 'verification', 'receipt', 'emergency_contact', 'other'
    
    category = db.Column(db.String(50))  # Additional categorization
    
    # Status and Validation
    is_verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_date = db.Column(db.DateTime)
    
    expiry_date = db.Column(db.Date)  # For documents that expire
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    version = db.Column(db.String(10), default='1.0')
    notes = db.Column(db.Text)
    meta_data = db.Column(db.JSON)  # Store additional metadata
    
    # Foreign Keys (Polymorphic - can belong to different entities)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'))
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'))
    booking_id = db.Column(db.Integer, db.ForeignKey('service_bookings.id'))
    # registration_id = db.Column(db.Integer, db.ForeignKey('trip_registrations.id'))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_document_type', 'document_type'),
        db.Index('idx_document_trip', 'trip_id'),
        db.Index('idx_document_participant', 'participant_id'),
        db.Index('idx_document_vendor', 'vendor_id'),
        db.Index('idx_document_uploader', 'uploaded_by'),
        db.Index('idx_document_active', 'is_active'),
        db.Index('idx_document_verified', 'is_verified'),
    )
    
    @property
    def is_expired(self):
        """Check if document has expired"""
        if not self.expiry_date:
            return False
        from datetime import date
        return self.expiry_date < date.today()
    
    @property
    def file_size_mb(self):
        """Get file size in megabytes"""
        if not self.file_size:
            return 0
        return round(self.file_size / (1024 * 1024), 2)
    
    def verify_document(self, verifier_id):
        """Mark document as verified"""
        self.is_verified = True
        self.verified_by = verifier_id
        self.verified_date = datetime.now()
        db.session.commit()
    
    def deactivate(self):
        """Deactivate the document"""
        self.is_active = False
        db.session.commit()
    
    @classmethod
    def get_participant_documents(cls, participant_id, document_type=None):
        """Get all documents for a participant"""
        query = cls.query.filter_by(participant_id=participant_id, is_active=True)
        if document_type:
            query = query.filter_by(document_type=document_type)
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_trip_documents(cls, trip_id, document_type=None):
        """Get all documents for a trip"""
        query = cls.query.filter_by(trip_id=trip_id, is_active=True)
        if document_type:
            query = query.filter_by(document_type=document_type)
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_vendor_documents(cls, vendor_id, document_type=None):
        """Get all documents for a vendor"""
        query = cls.query.filter_by(vendor_id=vendor_id, is_active=True)
        if document_type:
            query = query.filter_by(document_type=document_type)
        return query.order_by(cls.created_at.desc()).all()
    
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_mb': self.file_size_mb,
            'file_type': self.file_type,
            'document_type': self.document_type,
            'category': self.category,
            'is_verified': self.is_verified,
            'verified_date': self.verified_date.isoformat() if self.verified_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_expired': self.is_expired,
            'is_active': self.is_active,
            'version': self.version,
            'uploaded_by': self.uploader.serialize() if self.uploader else None,
            'trip_id': self.trip_id,
            'participant_id': self.participant_id,
            'vendor_id': self.vendor_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Document {self.title} - {self.document_type}>'