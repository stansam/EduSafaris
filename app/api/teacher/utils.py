from decimal import Decimal, InvalidOperation
from datetime import datetime
from app.extensions import db

def validate_date(date_string, field_name):
    """Validate and parse date string"""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format")

def validate_price(price_value, field_name):
    """Validate price value"""
    try:
        price = Decimal(str(price_value))
        if price < 0:
            raise ValueError(f"{field_name} cannot be negative")
        if price > 999999.99:
            raise ValueError(f"{field_name} exceeds maximum allowed value")
        return price
    except (InvalidOperation, TypeError, ValueError) as e:
        raise ValueError(f"{field_name} must be a valid number")

def validate_integer(value, field_name, min_val=None, max_val=None):
    """Validate integer value"""
    try:
        int_value = int(value)
        if min_val is not None and int_value < min_val:
            raise ValueError(f"{field_name} must be at least {min_val}")
        if max_val is not None and int_value > max_val:
            raise ValueError(f"{field_name} must be at most {max_val}")
        return int_value
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid integer")

def validate_trip_data(data, is_update=False):
    """Validate trip data and return cleaned data"""
    errors = []
    cleaned_data = {}
    
    # Required fields for creation
    if not is_update:
        required_fields = ['title', 'start_date', 'end_date', 'destination', 'price_per_student', 'max_participants']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field} is required")
    
    # Validate title
    if 'title' in data:
        title = data['title'].strip()
        if not title:
            errors.append("Title cannot be empty")
        elif len(title) > 200:
            errors.append("Title cannot exceed 200 characters")
        else:
            cleaned_data['title'] = title
    
    # Validate description
    if 'description' in data:
        cleaned_data['description'] = data['description'].strip() if data['description'] else None
    
    # Validate destination
    if 'destination' in data:
        destination = data['destination'].strip()
        if not destination:
            errors.append("Destination cannot be empty")
        elif len(destination) > 200:
            errors.append("Destination cannot exceed 200 characters")
        else:
            cleaned_data['destination'] = destination
    
    # Validate dates
    try:
        if 'start_date' in data:
            start_date = validate_date(data['start_date'], 'Start date')
            cleaned_data['start_date'] = start_date
            
        if 'end_date' in data:
            end_date = validate_date(data['end_date'], 'End date')
            cleaned_data['end_date'] = end_date
            
        if 'registration_deadline' in data and data['registration_deadline']:
            reg_deadline = validate_date(data['registration_deadline'], 'Registration deadline')
            cleaned_data['registration_deadline'] = reg_deadline
        
        # Validate date logic
        if 'start_date' in cleaned_data and 'end_date' in cleaned_data:
            if cleaned_data['end_date'] < cleaned_data['start_date']:
                errors.append("End date cannot be before start date")
        
        if 'registration_deadline' in cleaned_data and 'start_date' in cleaned_data:
            if cleaned_data['registration_deadline'] > cleaned_data['start_date']:
                errors.append("Registration deadline cannot be after start date")
                
    except ValueError as e:
        errors.append(str(e))
    
    # Validate price
    try:
        if 'price_per_student' in data:
            cleaned_data['price_per_student'] = validate_price(data['price_per_student'], 'Price per student')
    except ValueError as e:
        errors.append(str(e))
    
    # Validate participant counts
    try:
        if 'max_participants' in data:
            cleaned_data['max_participants'] = validate_integer(
                data['max_participants'], 'Maximum participants', min_val=1, max_val=10000
            )
        
        if 'min_participants' in data:
            cleaned_data['min_participants'] = validate_integer(
                data['min_participants'], 'Minimum participants', min_val=0, max_val=10000
            )
        
        # Validate min <= max
        if 'min_participants' in cleaned_data and 'max_participants' in cleaned_data:
            if cleaned_data['min_participants'] > cleaned_data['max_participants']:
                errors.append("Minimum participants cannot exceed maximum participants")
                
    except ValueError as e:
        errors.append(str(e))
    
    # Validate status
    if 'status' in data:
        valid_statuses = ['draft', 'active', 'full', 'in_progress', 'completed', 'cancelled']
        if data['status'] not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        else:
            cleaned_data['status'] = data['status']
    
    # Validate category
    if 'category' in data and data['category']:
        category = data['category'].strip()
        if len(category) > 50:
            errors.append("Category cannot exceed 50 characters")
        else:
            cleaned_data['category'] = category
    
    # Validate grade level
    if 'grade_level' in data and data['grade_level']:
        grade_level = data['grade_level'].strip()
        if len(grade_level) > 20:
            errors.append("Grade level cannot exceed 20 characters")
        else:
            cleaned_data['grade_level'] = grade_level
    
    # Validate boolean fields
    for field in ['medical_info_required', 'consent_required', 'featured']:
        if field in data:
            if isinstance(data[field], bool):
                cleaned_data[field] = data[field]
            else:
                errors.append(f"{field} must be a boolean value")
    
    # Validate itinerary (JSON)
    if 'itinerary' in data:
        if data['itinerary'] is None:
            cleaned_data['itinerary'] = None
        elif isinstance(data['itinerary'], (dict, list)):
            cleaned_data['itinerary'] = data['itinerary']
        else:
            errors.append("Itinerary must be a valid JSON object or array")
    
    return cleaned_data, errors