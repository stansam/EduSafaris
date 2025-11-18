import re
from datetime import datetime, date


def validate_email(email):
    """
    Validate email format
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # RFC 5322 simplified regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone):
    """
    Validate phone number format
    Supports: +254123456789, 0712345678, +1-234-567-8900, etc.
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone.strip())
    
    # Check if it's a valid phone number (7-15 digits, optional + prefix)
    pattern = r'^\+?[0-9]{7,15}$'
    return bool(re.match(pattern, cleaned))


def validate_url(url):
    """
    Validate URL format
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    pattern = r'^https?://[a-zA-Z0-9][-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*$'
    return bool(re.match(pattern, url.strip()))


def validate_date_string(date_string, format='%Y-%m-%d'):
    """
    Validate date string format
    
    Args:
        date_string (str): Date string to validate
        format (str): Expected date format
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not date_string or not isinstance(date_string, str):
        return False
    
    try:
        datetime.strptime(date_string.strip(), format)
        return True
    except ValueError:
        return False


def validate_date_range(start_date, end_date):
    """
    Validate that end_date is after start_date
    
    Args:
        start_date: Date or datetime object
        end_date: Date or datetime object
        
    Returns:
        bool: True if valid range, False otherwise
    """
    if not start_date or not end_date:
        return False
    
    # Convert datetime to date if needed
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    
    return end_date >= start_date


def validate_positive_number(value, allow_zero=False):
    """
    Validate that value is a positive number
    
    Args:
        value: Value to validate
        allow_zero (bool): Whether to allow zero
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        num = float(value)
        return num >= 0 if allow_zero else num > 0
    except (TypeError, ValueError):
        return False


def validate_integer_range(value, min_val=None, max_val=None):
    """
    Validate that value is an integer within specified range
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        num = int(value)
        
        if min_val is not None and num < min_val:
            return False
        if max_val is not None and num > max_val:
            return False
        
        return True
    except (TypeError, ValueError):
        return False


def validate_string_length(value, min_len=None, max_len=None):
    """
    Validate string length
    
    Args:
        value: String to validate
        min_len: Minimum length
        max_len: Maximum length
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(value, str):
        return False
    
    length = len(value.strip())
    
    if min_len is not None and length < min_len:
        return False
    if max_len is not None and length > max_len:
        return False
    
    return True


def validate_enum(value, allowed_values):
    """
    Validate that value is in allowed values
    
    Args:
        value: Value to validate
        allowed_values: List/tuple of allowed values
        
    Returns:
        bool: True if valid, False otherwise
    """
    return value in allowed_values


def sanitize_string(value, max_length=None):
    """
    Sanitize string input
    
    Args:
        value: String to sanitize
        max_length: Maximum length to truncate to
        
    Returns:
        str: Sanitized string
    """
    if not isinstance(value, str):
        return ''
    
    # Strip whitespace
    sanitized = value.strip()
    
    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present and non-empty
    
    Args:
        data (dict): Data to validate
        required_fields (list): List of required field names
        
    Returns:
        tuple: (is_valid, missing_fields)
    """
    if not isinstance(data, dict):
        return False, required_fields
    
    missing = []
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            missing.append(field)
    
    return len(missing) == 0, missing


def validate_file_extension(filename, allowed_extensions):
    """
    Validate file extension
    
    Args:
        filename (str): Filename to validate
        allowed_extensions (list): List of allowed extensions (e.g., ['.pdf', '.jpg'])
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not filename or not isinstance(filename, str):
        return False
    
    import os
    _, ext = os.path.splitext(filename.lower())
    return ext in [e.lower() for e in allowed_extensions]


def validate_file_size(file_size, max_size_mb=10):
    """
    Validate file size
    
    Args:
        file_size (int): File size in bytes
        max_size_mb (int): Maximum allowed size in MB
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(file_size, (int, float)) or file_size < 0:
        return False
    
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes


# Vendor-specific validators

def validate_vendor_data(data, required_only=False):
    """
    Validate vendor registration/update data
    
    Args:
        data (dict): Vendor data to validate
        required_only (bool): Only validate required fields
        
    Returns:
        tuple: (is_valid, errors_dict)
    """
    errors = {}
    
    # Required fields
    required_fields = ['business_name', 'contact_email', 'contact_phone', 'business_type']
    is_valid, missing = validate_required_fields(data, required_fields)
    
    if not is_valid:
        errors['missing_fields'] = missing
        return False, errors
    
    # Email validation
    if not validate_email(data['contact_email']):
        errors['contact_email'] = 'Invalid email format'
    
    # Phone validation
    if not validate_phone(data['contact_phone']):
        errors['contact_phone'] = 'Invalid phone number format'
    
    # Business name length
    if not validate_string_length(data['business_name'], min_len=2, max_len=200):
        errors['business_name'] = 'Business name must be between 2 and 200 characters'
    
    if not required_only:
        # Optional field validations
        if 'website' in data and data['website']:
            if not validate_url(data['website']):
                errors['website'] = 'Invalid URL format'
        
        if 'capacity' in data and data['capacity'] is not None:
            if not validate_integer_range(data['capacity'], min_val=1):
                errors['capacity'] = 'Capacity must be a positive integer'
        
        if 'base_price' in data and data['base_price'] is not None:
            if not validate_positive_number(data['base_price'], allow_zero=True):
                errors['base_price'] = 'Base price must be a non-negative number'
        
        if 'price_per_person' in data and data['price_per_person'] is not None:
            if not validate_positive_number(data['price_per_person'], allow_zero=True):
                errors['price_per_person'] = 'Price per person must be a non-negative number'
    
    return len(errors) == 0, errors


def validate_business_type(business_type):
    """
    Validate vendor business type
    
    Args:
        business_type (str): Business type to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    allowed_types = [
        'transportation',
        'accommodation',
        'activities',
        'catering',
        'tour_guide',
        'equipment_rental',
        'insurance',
        'other'
    ]
    return validate_enum(business_type, allowed_types)