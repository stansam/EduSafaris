import re
from datetime import datetime, date

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Password validation: min 8 chars, 1 uppercase, 1 lowercase, 1 number
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')

def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    return EMAIL_REGEX.match(email.strip()) is not None

def validate_password(password):
    """Validate password strength"""
    if not password:
        return False
    return PASSWORD_REGEX.match(password) is not None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True  # Phone is optional in some cases
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15

def validate_date_of_birth(dob_str):
    """Validate and parse date of birth"""
    if not dob_str:
        return None, None  # DOB is optional
    
    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        # Check if date is not in the future
        if dob > date.today():
            return None, "Date of birth cannot be in the future"
        
        # Check if age is reasonable (at least 18 for teachers/vendors, max 120)
        age = (date.today() - dob).days / 365.25
        if age < 18:
            return None, "User must be at least 18 years old"
        if age > 120:
            return None, "Invalid date of birth"
        
        return dob, None
    except ValueError:
        return None, "Invalid date format. Use YYYY-MM-DD"

def validate_url(url):
    """Validate URL format"""
    if not url:
        return True  # URL is optional
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present and not empty
    
    Args:
        data: Dictionary of form data
        required_fields: List of required field names
        
    Returns:
        tuple: (is_valid, missing_fields)
    """
    missing_fields = []
    
    for field in required_fields:
        value = data.get(field)
        if not value or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field)
    
    return len(missing_fields) == 0, missing_fields

def sanitize_string(value):
    """Sanitize string input by stripping whitespace"""
    if value is None:
        return None
    return value.strip() if isinstance(value, str) else value

def validate_number(value, min_value=None, max_value=None):
    """
    Validate numeric input
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        
    Returns:
        tuple: (is_valid, error_message, converted_value)
    """
    if value is None or value == '':
        return True, None, None
    
    try:
        num = float(value)
        
        if min_value is not None and num < min_value:
            return False, f"Value must be at least {min_value}", None
        
        if max_value is not None and num > max_value:
            return False, f"Value must not exceed {max_value}", None
        
        return True, None, num
    except (ValueError, TypeError):
        return False, "Invalid number format", None

def validate_integer(value, min_value=None, max_value=None):
    """
    Validate integer input
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        
    Returns:
        tuple: (is_valid, error_message, converted_value)
    """
    if value is None or value == '':
        return True, None, None
    
    try:
        num = int(value)
        
        if min_value is not None and num < min_value:
            return False, f"Value must be at least {min_value}", None
        
        if max_value is not None and num > max_value:
            return False, f"Value must not exceed {max_value}", None
        
        return True, None, num
    except (ValueError, TypeError):
        return False, "Invalid integer format", None

def format_field_name(field_name):
    """Convert field name from snake_case to Title Case"""
    return field_name.replace('_', ' ').title()

def build_error_response(message, status_code=400, errors=None):
    """
    Build standardized error response
    
    Args:
        message: Main error message
        status_code: HTTP status code
        errors: Dictionary of field-specific errors (optional)
        
    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        'success': False,
        'message': message
    }
    
    if errors:
        response['errors'] = errors
    
    return response, status_code

def build_success_response(message, data=None, redirect_url=None, status_code=200):
    """
    Build standardized success response
    
    Args:
        message: Success message
        data: Additional data to include (optional)
        redirect_url: URL to redirect to (optional)
        status_code: HTTP status code
        
    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        'success': True,
        'message': message
    }
    
    if data:
        response['data'] = data
    
    if redirect_url:
        response['redirect_url'] = redirect_url
    
    return response, status_code