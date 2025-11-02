from datetime import datetime
from app.extensions import db
from app.models import BaseModel

class Review(BaseModel):
    __tablename__ = 'reviews'
    
    # Review Content
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200))
    review_text = db.Column(db.Text)
    
    # Review Type
    review_type = db.Column(db.String(50), nullable=False)
    # Types: 'trip', 'vendor', 'service'
    
    # Additional Ratings (optional breakdown)
    value_rating = db.Column(db.Integer)  # Value for money
    safety_rating = db.Column(db.Integer)  # Safety measures
    organization_rating = db.Column(db.Integer)  # How well organized
    communication_rating = db.Column(db.Integer)  # Communication quality
    
    # Status and Moderation
    is_approved = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    moderation_notes = db.Column(db.Text)
    moderated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    moderated_date = db.Column(db.DateTime)
    
    # Response from Service Provider
    response_text = db.Column(db.Text)
    response_date = db.Column(db.DateTime)
    responded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Helpful Votes
    helpful_count = db.Column(db.Integer, default=0)
    not_helpful_count = db.Column(db.Integer, default=0)
    
    # Verification
    is_verified_purchase = db.Column(db.Boolean, default=False)  # Did they actually book?
    
    # Foreign Keys
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'))
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'))
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_review_type', 'review_type'),
        db.Index('idx_review_trip', 'trip_id'),
        db.Index('idx_review_vendor', 'vendor_id'),
        db.Index('idx_review_reviewer', 'reviewer_id'),
        db.Index('idx_review_rating', 'rating'),
        db.Index('idx_review_approved', 'is_approved'),
        db.Index('idx_review_published', 'is_published'),
        db.Index('idx_review_featured', 'is_featured'),
        db.Index('idx_review_created', 'created_at'),
    )
    
    @property
    def average_detailed_rating(self):
        """Calculate average of detailed ratings"""
        ratings = [r for r in [self.value_rating, self.safety_rating, 
                              self.organization_rating, self.communication_rating] if r]
        return sum(ratings) / len(ratings) if ratings else self.rating
    
    @property
    def helpfulness_score(self):
        """Calculate helpfulness score"""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0
        return (self.helpful_count / total) * 100
    
    def approve(self, moderator_id, notes=None):
        """Approve the review"""
        self.is_approved = True
        self.is_published = True
        self.moderated_by = moderator_id
        self.moderated_date = datetime.now()
        if notes:
            self.moderation_notes = notes
        db.session.commit()
        
        # Update related entity ratings
        self._update_entity_rating()
    
    def reject(self, moderator_id, notes):
        """Reject the review"""
        self.is_approved = False
        self.is_published = False
        self.moderated_by = moderator_id
        self.moderated_date = datetime.now()
        self.moderation_notes = notes
        db.session.commit()
    
    def add_response(self, responder_id, response_text):
        """Add response from service provider"""
        self.response_text = response_text
        self.response_date = datetime.now()
        self.responded_by = responder_id
        db.session.commit()
    
    def mark_helpful(self):
        """Mark review as helpful"""
        self.helpful_count += 1
        db.session.commit()
    
    def mark_not_helpful(self):
        """Mark review as not helpful"""
        self.not_helpful_count += 1
        db.session.commit()
    
    def _update_entity_rating(self):
        """Update rating for the reviewed entity"""
        if self.vendor_id and self.vendor:
            self.vendor.update_rating()
        elif self.trip_id and self.trip:
            # Calculate trip average rating
            reviews = Review.query.filter_by(
                trip_id=self.trip_id,
                is_published=True
            ).all()
            if reviews:
                avg_rating = sum(r.rating for r in reviews) / len(reviews)
                # Store in trip metadata or add rating field to Trip model
    
    @classmethod
    def create_trip_review(cls, trip_id, reviewer_id, rating, title=None, 
                          review_text=None, booking_id=None, **kwargs):
        """Create a review for a trip"""
        review = cls(
            trip_id=trip_id,
            reviewer_id=reviewer_id,
            rating=rating,
            title=title,
            review_text=review_text,
            review_type='trip',
            booking_id=booking_id,
            is_verified_purchase=bool(booking_id),
            **kwargs
        )
        db.session.add(review)
        db.session.commit()
        return review
    
    @classmethod
    def create_vendor_review(cls, vendor_id, reviewer_id, rating, title=None,
                            review_text=None, booking_id=None, **kwargs):
        """Create a review for a vendor"""
        review = cls(
            vendor_id=vendor_id,
            reviewer_id=reviewer_id,
            rating=rating,
            title=title,
            review_text=review_text,
            review_type='vendor',
            booking_id=booking_id,
            is_verified_purchase=bool(booking_id),
            **kwargs
        )
        db.session.add(review)
        db.session.commit()
        return review
    
    @classmethod
    def get_published_reviews(cls, entity_type, entity_id, limit=20):
        """Get published reviews for an entity"""
        filter_dict = {'is_published': True}
        if entity_type == 'trip':
            filter_dict['trip_id'] = entity_id
        elif entity_type == 'vendor':
            filter_dict['vendor_id'] = entity_id
        
        return cls.query.filter_by(**filter_dict)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit).all()
    
    @classmethod
    def get_pending_reviews(cls):
        """Get reviews pending moderation"""
        return cls.query.filter_by(is_approved=False, is_published=False)\
                       .order_by(cls.created_at.asc()).all()
    
    def serialize(self):
        return {
            'id': self.id,
            'rating': self.rating,
            'title': self.title,
            'review_text': self.review_text,
            'review_type': self.review_type,
            'value_rating': self.value_rating,
            'safety_rating': self.safety_rating,
            'organization_rating': self.organization_rating,
            'communication_rating': self.communication_rating,
            'average_detailed_rating': self.average_detailed_rating,
            'is_approved': self.is_approved,
            'is_published': self.is_published,
            'is_featured': self.is_featured,
            'is_verified_purchase': self.is_verified_purchase,
            'helpful_count': self.helpful_count,
            'not_helpful_count': self.not_helpful_count,
            'helpfulness_score': round(self.helpfulness_score, 2),
            'response_text': self.response_text,
            'response_date': self.response_date.isoformat() if self.response_date else None,
            'reviewer': self.reviewer.serialize() if self.reviewer else None,
            'trip_id': self.trip_id,
            'vendor_id': self.vendor_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Review {self.rating}★ - {self.review_type}>'
