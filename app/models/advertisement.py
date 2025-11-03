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
    cost_per_impression = db.Column(Numeric(5, 4))  # Usually very small amount
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # Billing Model
    billing_model = db.Column(db.Enum('cpc', 'cpm', 'flat_rate', name='ad_billing_model'), 
                             default='cpc', nullable=False)  # CPC = Cost Per Click, CPM = Cost Per Mille (1000 impressions)
    
    # Scheduling
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Performance Metrics
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)  # Successful bookings/registrations
    total_spent = db.Column(Numeric(10, 2), default=0)
    
    # Links and Actions
    click_url = db.Column(db.String(300))
    call_to_action = db.Column(db.String(50))  # 'Book Now', 'Learn More', 'Contact Us'
    
    # Ad Type and Placement
    ad_type = db.Column(db.String(50), default='banner')  # 'banner', 'popup', 'inline', 'sponsored'
    placement = db.Column(db.String(50))  # 'header', 'sidebar', 'footer', 'trip_list', 'search_results'
    
    # Status
    status = db.Column(db.Enum('draft', 'pending_approval', 'approved', 'active', 'paused', 
                               'completed', 'rejected', name='ad_status'), 
                      default='draft', nullable=False)
    rejection_reason = db.Column(db.Text)
    
    # Foreign Keys
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'))  # If advertising a specific trip
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'))  # If vendor advertisement
    advertiser_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Who created the ad
    
    # Relationships
    payments = db.relationship('AdvertisementPayment', back_populates='advertisement', 
                              lazy='dynamic', cascade='all, delete-orphan')
    advertiser = db.relationship('User', foreign_keys=[advertiser_id])
    
    # Indexes
    __table_args__ = (
        db.Index('idx_ad_dates', 'start_date', 'end_date'),
        db.Index('idx_ad_active', 'is_active'),
        db.Index('idx_ad_status', 'status'),
        db.Index('idx_ad_audience', 'target_audience'),
        db.Index('idx_ad_placement', 'placement'),
        db.Index('idx_ad_trip', 'trip_id'),
        db.Index('idx_ad_vendor', 'vendor_id'),
        db.Index('idx_ad_advertiser', 'advertiser_id'),
    )
    
    @property
    def is_currently_active(self):
        """Check if ad is currently active based on dates, status and budget"""
        today = date.today()
        
        # Check basic requirements
        if not (self.is_active and self.status == 'active'):
            return False
        
        # Check dates
        if not (self.start_date <= today <= self.end_date):
            return False
        
        # Check budget if applicable
        if self.budget and self.total_spent >= self.budget:
            return False
        
        return True
    
    @property
    def click_through_rate(self):
        """Calculate click-through rate (CTR)"""
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
    
    @property
    def average_cpc(self):
        """Calculate average cost per click"""
        if self.clicks == 0:
            return 0
        return float(self.total_spent / self.clicks)
    
    @property
    def budget_remaining(self):
        """Calculate remaining budget"""
        if not self.budget:
            return None
        return float(self.budget - (self.total_spent or 0))
    
    @property
    def budget_utilization_percentage(self):
        """Calculate budget utilization as percentage"""
        if not self.budget or self.budget == 0:
            return 0
        return (float(self.total_spent) / float(self.budget)) * 100
    
    def record_impression(self):
        """Record an ad impression"""
        self.impressions += 1
        
        # Charge for impression if CPM billing
        if self.billing_model == 'cpm' and self.cost_per_impression:
            cost = self.cost_per_impression
            self.total_spent = (self.total_spent or 0) + cost
        
        # Pause if budget exceeded
        if self.budget and self.total_spent >= self.budget:
            self.pause_campaign()
        
        db.session.commit()
    
    def record_click(self):
        """Record an ad click"""
        self.clicks += 1
        
        # Charge for click if CPC billing
        if self.billing_model == 'cpc' and self.cost_per_click:
            cost = self.cost_per_click
            self.total_spent = (self.total_spent or 0) + cost
        
        # Pause if budget exceeded
        if self.budget and self.total_spent >= self.budget:
            self.pause_campaign()
        
        db.session.commit()
    
    def record_conversion(self):
        """Record a conversion (e.g., registration/booking made)"""
        self.conversions += 1
        db.session.commit()
    
    def pause_campaign(self):
        """Pause the advertisement"""
        self.status = 'paused'
        self.is_active = False
        db.session.commit()
    
    def resume_campaign(self):
        """Resume the advertisement"""
        if self.status == 'paused':
            # Check if we can resume (budget, dates, etc.)
            today = date.today()
            
            if today > self.end_date:
                raise ValueError("Cannot resume: Campaign end date has passed")
            
            if self.budget and self.total_spent >= self.budget:
                raise ValueError("Cannot resume: Budget exhausted")
            
            self.status = 'active'
            self.is_active = True
            db.session.commit()
    
    def approve_campaign(self):
        """Approve the campaign (admin action)"""
        if self.status == 'pending_approval':
            self.status = 'approved'
            db.session.commit()
    
    def reject_campaign(self, reason):
        """Reject the campaign (admin action)"""
        if self.status == 'pending_approval':
            self.status = 'rejected'
            self.rejection_reason = reason
            db.session.commit()
    
    def activate_campaign(self):
        """Activate an approved campaign"""
        if self.status == 'approved':
            self.status = 'active'
            self.is_active = True
            db.session.commit()
    
    def complete_campaign(self):
        """Mark campaign as completed"""
        self.status = 'completed'
        self.is_active = False
        db.session.commit()
    
    @classmethod
    def get_active_ads_for_user(cls, user, placement=None):
        """Get active ads relevant to a specific user"""
        today = date.today()
        query = cls.query.filter(
            cls.is_active == True,
            cls.status == 'active',
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
    
    @classmethod
    def get_performance_report(cls, advertiser_id, start_date=None, end_date=None):
        """Get performance report for an advertiser"""
        query = cls.query.filter_by(advertiser_id=advertiser_id)
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)
        
        ads = query.all()
        
        return {
            'total_ads': len(ads),
            'total_impressions': sum(ad.impressions for ad in ads),
            'total_clicks': sum(ad.clicks for ad in ads),
            'total_conversions': sum(ad.conversions for ad in ads),
            'total_spent': sum(float(ad.total_spent) for ad in ads),
            'average_ctr': sum(ad.click_through_rate for ad in ads) / len(ads) if ads else 0,
            'average_conversion_rate': sum(ad.conversion_rate for ad in ads) / len(ads) if ads else 0
        }
    
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url,
            'target_audience': self.target_audience,
            'grade_levels': self.grade_levels,
            'campaign_name': self.campaign_name,
            'budget': float(self.budget) if self.budget else None,
            'budget_remaining': self.budget_remaining,
            'budget_utilization_percentage': round(self.budget_utilization_percentage, 2),
            'currency': self.currency,
            'billing_model': self.billing_model,
            'cost_per_click': float(self.cost_per_click) if self.cost_per_click else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'is_active': self.is_active,
            'is_currently_active': self.is_currently_active,
            'impressions': self.impressions,
            'clicks': self.clicks,
            'conversions': self.conversions,
            'total_spent': float(self.total_spent) if self.total_spent else 0,
            'click_through_rate': round(self.click_through_rate, 2),
            'conversion_rate': round(self.conversion_rate, 2),
            'cost_per_conversion': round(self.cost_per_conversion, 2) if self.cost_per_conversion else 0,
            'average_cpc': round(self.average_cpc, 2),
            'click_url': self.click_url,
            'call_to_action': self.call_to_action,
            'ad_type': self.ad_type,
            'placement': self.placement,
            'trip_id': self.trip_id,
            'vendor_id': self.vendor_id,
            'advertiser': self.advertiser.serialize() if self.advertiser else None
        }
    
    def __repr__(self):
        return f'<Advertisement {self.title} - {self.status}>'