from datetime import datetime
from app.extensions import db
from app.models.base import BaseModel

class Consent(BaseModel):
    __tablename__ = 'consents'
    
    # Consent Information
    consent_type = db.Column(db.String(50), nullable=False)  # 'trip_participation', 'medical', 'photo_release'
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Signature Information
    is_signed = db.Column(db.Boolean, default=False, nullable=False)
    signed_date = db.Column(db.DateTime)
    signature_data = db.Column(db.Text)  # Digital signature data
    ip_address = db.Column(db.String(45))  # IP address when signed
    
    # Signer Information
    signer_name = db.Column(db.String(100))
    signer_relationship = db.Column(db.String(50))  # 'parent', 'guardian', 'self'
    signer_email = db.Column(db.String(120))
    
    # Consent Details
    is_required = db.Column(db.Boolean, default=True, nullable=False)
    expires_date = db.Column(db.Date)
    version = db.Column(db.String(10), default='1.0')
    
    # Foreign Keys
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Parent/guardian who signed
    
    # Indexes
    __table_args__ = (
        db.Index('idx_consent_participant', 'participant_id'),
        db.Index('idx_consent_type', 'consent_type'),
        db.Index('idx_consent_signed', 'is_signed'),
    )
    
    @property
    def is_expired(self):
        """Check if consent has expired"""
        if not self.expires_date:
            return False
        return self.expires_date < datetime.now().date()
    
    @property
    def is_valid(self):
        """Check if consent is valid (signed and not expired)"""
        return self.is_signed and not self.is_expired
    
    def sign_consent(self, signer_name, signer_relationship, signer_email, signature_data=None, ip_address=None):
        """Sign the consent form"""
        self.is_signed = True
        self.signed_date = datetime.utcnow()
        self.signer_name = signer_name
        self.signer_relationship = signer_relationship
        self.signer_email = signer_email
        self.signature_data = signature_data
        self.ip_address = ip_address
        db.session.commit()
    
    def revoke_consent(self):
        """Revoke the consent"""
        self.is_signed = False
        self.signed_date = None
        self.signature_data = None
        db.session.commit()
    
    def serialize(self):
        return {
            'id': self.id,
            'consent_type': self.consent_type,
            'title': self.title,
            'content': self.content,
            'is_signed': self.is_signed,
            'signed_date': self.signed_date.isoformat() if self.signed_date else None,
            'signer_name': self.signer_name,
            'signer_relationship': self.signer_relationship,
            'is_required': self.is_required,
            'is_expired': self.is_expired,
            'is_valid': self.is_valid,
            'expires_date': self.expires_date.isoformat() if self.expires_date else None,
            'version': self.version,
            'participant_id': self.participant_id
        }
    
    def __repr__(self):
        return f'<Consent {self.title} - {"Signed" if self.is_signed else "Unsigned"}>'
