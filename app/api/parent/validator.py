from datetime import datetime, date
import re

def validate_email(email):
    """
    Validate email format
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone):
    """
    Validate phone number format (supports international formats)
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone:
        return False
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone.strip())
    
    # Check if it's a valid international format or local format
    # Accepts: +254712345678, 0712345678, etc.
    pattern = r'^(\+?\d{1,4})?[\d]{9,15}$'
    return bool(re.match(pattern, cleaned))

def validate_participant_data(data, is_update=False):
    """Validate participant data with detailed error messages"""
    errors = {}
    
    # Required fields for creation
    if not is_update:
        required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender',
                          'emergency_contact_1_name', 'emergency_contact_1_phone',
                          'emergency_contact_1_relationship']
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = f'{field.replace("_", " ").title()} is required'
    
    # Validate name fields
    if 'first_name' in data:
        if not data['first_name'] or len(data['first_name'].strip()) < 2:
            errors['first_name'] = 'First name must be at least 2 characters'
        elif len(data['first_name']) > 50:
            errors['first_name'] = 'First name must not exceed 50 characters'
    
    if 'last_name' in data:
        if not data['last_name'] or len(data['last_name'].strip()) < 2:
            errors['last_name'] = 'Last name must be at least 2 characters'
        elif len(data['last_name']) > 50:
            errors['last_name'] = 'Last name must not exceed 50 characters'
    
    # Validate date of birth
    if 'date_of_birth' in data:
        try:
            dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            if dob >= today:
                errors['date_of_birth'] = 'Date of birth must be in the past'
            elif age > 25:
                errors['date_of_birth'] = 'Participant must be under 25 years old'
            elif age < 3:
                errors['date_of_birth'] = 'Participant must be at least 3 years old'
        except ValueError:
            errors['date_of_birth'] = 'Invalid date format. Use YYYY-MM-DD'
    
    # Validate gender
    if 'gender' in data:
        valid_genders = ['male', 'female', 'other', 'prefer_not_to_say']
        if data['gender'] not in valid_genders:
            errors['gender'] = f'Gender must be one of: {", ".join(valid_genders)}'
    
    # Validate email if provided
    if 'email' in data and data['email']:
        if not validate_email(data['email']):
            errors['email'] = 'Invalid email format'
    
    # Validate phone numbers
    phone_fields = ['phone', 'emergency_contact_1_phone', 'emergency_contact_2_phone', 'doctor_phone']
    for field in phone_fields:
        if field in data and data[field]:
            if not validate_phone(data[field]):
                errors[field] = 'Invalid phone number format'
    
    # Validate blood type if provided
    if 'blood_type' in data and data['blood_type']:
        valid_blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if data['blood_type'] not in valid_blood_types:
            errors['blood_type'] = f'Blood type must be one of: {", ".join(valid_blood_types)}'
    
    return errors