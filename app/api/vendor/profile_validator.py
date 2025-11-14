import re 
from decimal import Decimal, InvalidOperation

class VendorProfileValidator:
    """Validation utilities for vendor profile data"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email:
            return False, "Email is required"
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        if len(email) > 120:
            return False, "Email must be less than 120 characters"
        
        return True, None
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number"""
        if not phone:
            return False, "Phone number is required"
        
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        
        if not cleaned.isdigit():
            return False, "Phone number must contain only digits"
        
        if len(cleaned) < 10 or len(cleaned) > 15:
            return False, "Phone number must be between 10 and 15 digits"
        
        return True, None
    
    @staticmethod
    def validate_price(price, field_name="Price"):
        """Validate price field"""
        if price is None:
            return True, None  # Price is optional
        
        try:
            price_decimal = Decimal(str(price))
            if price_decimal < 0:
                return False, f"{field_name} cannot be negative"
            if price_decimal > Decimal('9999999.99'):
                return False, f"{field_name} exceeds maximum value"
            return True, None
        except (ValueError, InvalidOperation):
            return False, f"Invalid {field_name.lower()} format"
    
    @staticmethod
    def validate_capacity(capacity):
        """Validate capacity field"""
        if capacity is None:
            return True, None  # Capacity is optional
        
        try:
            capacity_int = int(capacity)
            if capacity_int < 1:
                return False, "Capacity must be at least 1"
            if capacity_int > 10000:
                return False, "Capacity exceeds maximum value"
            return True, None
        except (ValueError, TypeError):
            return False, "Invalid capacity format"
    
    @staticmethod
    def validate_url(url):
        """Validate URL format"""
        if not url:
            return True, None  # URL is optional
        
        pattern = r'^https?://[\w\-]+(\.[\w\-]+)+[/#?]?.*$'
        if not re.match(pattern, url):
            return False, "Invalid URL format"
        
        if len(url) > 200:
            return False, "URL must be less than 200 characters"
        
        return True, None
    
    @staticmethod
    def validate_business_name(name):
        """Validate business name"""
        if not name or not name.strip():
            return False, "Business name is required"
        
        if len(name) < 3:
            return False, "Business name must be at least 3 characters"
        
        if len(name) > 200:
            return False, "Business name must be less than 200 characters"
        
        return True, None
    
    @staticmethod
    def validate_business_type(business_type):
        """Validate business type"""
        valid_types = [
            'transportation', 'accommodation', 'activities', 
            'food_service', 'tour_guide', 'equipment_rental', 'other'
        ]
        
        if business_type and business_type not in valid_types:
            return False, f"Business type must be one of: {', '.join(valid_types)}"
        
        return True, None