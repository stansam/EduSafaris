import re
from datetime import datetime


def validate_email(email):
    """
    Validate email format
    
    Args:
        email: Email string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # RFC 5322 compliant email regex (simplified)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False
    
    # Additional checks
    if len(email) > 320:  # Max email length
        return False
    
    local_part, domain = email.rsplit('@', 1)
    
    if len(local_part) > 64:  # Max local part length
        return False
    
    if len(domain) > 255:  # Max domain length
        return False
    
    # Check for consecutive dots
    if '..' in email:
        return False
    
    return True


def validate_phone(phone):
    """
    Validate phone number format
    Accepts international formats with optional country code
    
    Args:
        phone: Phone string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    
    # Check if it starts with + (international format)
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    
    # Should contain only digits now
    if not cleaned.isdigit():
        return False
    
    # Length check (international phone numbers are typically 7-15 digits)
    if len(cleaned) < 7 or len(cleaned) > 15:
        return False
    
    return True


def validate_password_strength(password):
    """
    Validate password strength
    
    Args:
        password: Password string to validate
        
    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    errors = []
    
    if not password:
        return False, ['Password is required']
    
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    
    if len(password) > 128:
        errors.append('Password must not exceed 128 characters')
    
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')
    
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')
    
    if not re.search(r'\d', password):
        errors.append('Password must contain at least one digit')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character')
    
    # Check for common weak passwords
    common_passwords = [
        'password', '12345678', 'qwerty123', 'admin123', 
        'password123', 'letmein', 'welcome123'
    ]
    if password.lower() in common_passwords:
        errors.append('Password is too common')
    
    return len(errors) == 0, errors


def validate_date(date_string, date_format='%Y-%m-%d'):
    """
    Validate date string format
    
    Args:
        date_string: Date string to validate
        date_format: Expected date format (default: YYYY-MM-DD)
        
    Returns:
        tuple: (is_valid: bool, date_object: datetime or None)
    """
    if not date_string:
        return False, None
    
    try:
        date_obj = datetime.strptime(date_string, date_format)
        return True, date_obj
    except ValueError:
        return False, None


def validate_url(url):
    """
    Validate URL format
    
    Args:
        url: URL string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None


def sanitize_string(input_string, max_length=None):
    """
    Sanitize string input by removing potentially harmful characters
    
    Args:
        input_string: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized string
    """
    if not input_string:
        return ''
    
    # Convert to string if not already
    sanitized = str(input_string)
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    # Strip leading/trailing whitespace
    sanitized = sanitized.strip()
    
    # Truncate if max_length specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_role(role):
    """
    Validate user role
    
    Args:
        role: Role string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    valid_roles = ['parent', 'teacher', 'vendor', 'admin']
    return role in valid_roles


def validate_json_structure(data, required_fields):
    """
    Validate JSON data structure
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Returns:
        tuple: (is_valid: bool, missing_fields: list)
    """
    if not isinstance(data, dict):
        return False, ['Invalid data format']
    
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    return len(missing_fields) == 0, missing_fields


def validate_pagination_params(page, per_page, max_per_page=100):
    """
    Validate and sanitize pagination parameters
    
    Args:
        page: Page number
        per_page: Items per page
        max_per_page: Maximum allowed items per page
        
    Returns:
        tuple: (page: int, per_page: int)
    """
    try:
        page = int(page) if page else 1
        page = max(1, page)  # Ensure page is at least 1
    except (ValueError, TypeError):
        page = 1
    
    try:
        per_page = int(per_page) if per_page else 20
        per_page = max(1, min(per_page, max_per_page))  # Clamp between 1 and max
    except (ValueError, TypeError):
        per_page = 20
    
    return page, per_page