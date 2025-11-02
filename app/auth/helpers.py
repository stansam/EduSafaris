import re
from datetime import datetime

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Password validation: min 8 chars, 1 uppercase, 1 lowercase, 1 number
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')

def validate_email(email):
    """Validate email format"""
    return EMAIL_REGEX.match(email) is not None

def validate_password(password):
    """Validate password strength"""
    return PASSWORD_REGEX.match(password) is not None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15

def validate_date_of_birth(dob_str):
    """Validate and parse date of birth"""
    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        # Check if date is not in the future
        if dob > datetime.now().date():
            return None, "Date of birth cannot be in the future"
        # Check if age is reasonable (e.g., at least 18 for parents/teachers)
        age = (datetime.now().date() - dob).days / 365.25
        if age < 18:
            return None, "User must be at least 18 years old"
        if age > 120:
            return None, "Invalid date of birth"
        return dob, None
    except ValueError:
        return None, "Invalid date format. Use YYYY-MM-DD"