from datetime import datetime, date
from sqlalchemy import Numeric
from app.extensions import db
from app.models.base import BaseModel

class Advertisement(BaseModel):
    __tablename__ = 'advertisements'
    
    # Advertisement Content
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300))
    
    # Targeting
    target_audience = db.Column(db.String(50))  # 'all', 'teachers', 'parents', 'students'
    grade_levels = db.Column(db.JSON)  # Array of target grade levels
    locations = db.Column(db.JSON)  # Array of target locations/cities
    
    # Campaign Information
    campaign_name = db.Column(db.String(100))
    budget = db.Column(Numeric(10, 2))
    cost_per_click = db.Column(Numeric(5, 2))
    
    # Scheduling
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Performance Metrics
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)
    total_spent = db.Column(Numeric(10, 2), default=0)
    
    # Links and Actions
    click_url = db.Column(db.String(300))
    call_to_action = db.Column(db.String(50))  # 'Book Now', 'Learn More', 'Contact Us'
    
    # Ad Type and Placement
    ad_type = db.Column(db.String(50), default='banner')  # 'banner', 'popup', 'inline', 'email'
    placement = db.Column(db.String(50))  # 'header', 'sidebar', 'footer', 'trip_list'
    
    # Foreign Keys
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'))  # If advertising a specific trip
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'))  # If vendor advertisement
    
    # Indexes
    __table_args__ = (
        db.Index('idx_ad_dates', 'start_date', 'end_date'),
        db.Index('idx_ad_active', 'is_active'),
        db.Index('idx_ad_audience', 'target_audience'),
        db.Index('idx_ad_placement', 'placement'),
    )
    
    @property
    def is_currently_active(self):
        """Check if ad is currently active based on dates and status"""
        today = date.today()
        return (self.is_active and 
                self.start_date <= today <= self.end_date)
    
    @property
    def click_through_rate(self):
        """Calculate click-through rate"""
        if self.impressions == 0:
            return 0
        return (self.clicks / self.impressions) * 100
    
    @property
    def conversion_rate(self):
        """Calculate conversion rate"""
        if self.clicks == 0:
            return 0
        return (self.conversions / self.clicks) * 100
    
    @property
    def cost_per_conversion(self):
        """Calculate cost per conversion"""
        if self.conversions == 0:
            return 0
        return float(self.total_spent / self.conversions)
    
    def record_impression(self):
        """Record an ad impression"""
        self.impressions += 1
        db.session.commit()
    
    def record_click(self, cost=None):
        """Record an ad click"""
        self.clicks += 1
        if cost:
            self.total_spent = (self.total_spent or 0) + cost
        elif self.cost_per_click:
            self.total_spent = (self.total_spent or 0) + self.cost_per_click
        db.session.commit()
    
    def record_conversion(self):
        """Record a conversion (e.g., booking made)"""
        self.conversions += 1
        db.session.commit()
    
    def pause_campaign(self):
        """Pause the advertisement"""
        self.is_active = False
        db.session.commit()
    
    def resume_campaign(self):
        """Resume the advertisement"""
        self.is_active = True
        db.session.commit()
    
    @classmethod
    def get_active_ads_for_user(cls, user, placement=None):
        """Get active ads relevant to a specific user"""
        today = date.today()
        query = cls.query.filter(
            cls.is_active == True,
            cls.start_date <= today,
            cls.end_date >= today
        )
        
        # Filter by placement if specified
        if placement:
            query = query.filter(cls.placement == placement)
        
        # Filter by target audience
        if user:
            query = query.filter(
                db.or_(
                    cls.target_audience == 'all',
                    cls.target_audience == user.role
                )
            )
        
        return query.all()
    
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url,
            'target_audience': self.target_audience,
            'grade_levels': self.grade_levels,
            'campaign_name': self.campaign_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'is_currently_active': self.is_currently_active,
            'impressions': self.impressions,
            'clicks': self.clicks,
            'conversions': self.conversions,
            'click_through_rate': round(self.click_through_rate, 2),
            'conversion_rate': round(self.conversion_rate, 2),
            'click_url': self.click_url,
            'call_to_action': self.call_to_action,
            'ad_type': self.ad_type,
            'placement': self.placement,
            'trip_id': self.trip_id,
            'vendor_id': self.vendor_id
        }
    
    def __repr__(self):
        return f'<Advertisement {self.title}>'
