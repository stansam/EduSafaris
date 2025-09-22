from flask_login import current_user

def register_jinja_extensions(app):
    """Register Jinja2 filters and global functions"""
    
    @app.template_filter('currency')
    def currency_filter(amount, currency='USD'):
        """Format currency for display"""
        from app.utils import format_currency
        return format_currency(amount, currency)
    
    @app.template_filter('phone')
    def phone_filter(phone):
        """Format phone number for display"""
        from app.utils import format_phone
        return format_phone(phone)
    
    @app.template_filter('datetime')
    def datetime_filter(datetime_obj, format='%Y-%m-%d %H:%M'):
        """Format datetime for display"""
        if datetime_obj:
            return datetime_obj.strftime(format)
        return ''
    
    @app.template_filter('date')
    def date_filter(date_obj, format='%Y-%m-%d'):
        """Format date for display"""
        if date_obj:
            return date_obj.strftime(format)
        return ''
    
    @app.template_global()
    def get_active_ads(placement=None):
        """Get active advertisements for current user"""
        from app.models import Advertisement
        return Advertisement.get_active_ads_for_user(current_user, placement)
    
    @app.template_global()
    def get_unread_notifications():
        """Get unread notifications for current user"""
        if current_user.is_authenticated:
            from app.models import Notification
            return Notification.query.filter_by(
                recipient_id=current_user.id,
                is_read=False
            ).order_by(Notification.created_at.desc()).limit(5).all()
        return []