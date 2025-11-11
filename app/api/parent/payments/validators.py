import re
from decimal import Decimal


def validate_phone_number(phone_number):
    """
    Validate and format phone number for M-Pesa
    
    Args:
        phone_number: string
    
    Returns:
        Formatted phone number (254XXXXXXXXX) or None if invalid
    """
    if not phone_number:
        return None
    
    # Remove all non-digit characters
    phone = re.sub(r'\D', '', str(phone_number))
    
    # Handle different formats
    if phone.startswith('254'):
        # Already in correct format
        if len(phone) == 12:
            return phone
    elif phone.startswith('0'):
        # Convert 0712345678 to 254712345678
        if len(phone) == 10:
            return '254' + phone[1:]
    elif phone.startswith('7') or phone.startswith('1'):
        # Convert 712345678 to 254712345678
        if len(phone) == 9:
            return '254' + phone
    
    return None


def validate_amount(amount, min_amount=1, max_amount=999999):
    """
    Validate payment amount
    
    Args:
        amount: float, int, or Decimal
        min_amount: float (minimum allowed amount)
        max_amount: float (maximum allowed amount)
    
    Returns:
        Decimal amount or raises ValueError
    """
    try:
        amount = Decimal(str(amount))
    except (ValueError, TypeError):
        raise ValueError("Invalid amount format")
    
    if amount < Decimal(str(min_amount)):
        raise ValueError(f"Amount must be at least {min_amount}")
    
    if amount > Decimal(str(max_amount)):
        raise ValueError(f"Amount cannot exceed {max_amount}")
    
    return amount


def validate_email(email):
    """
    Validate email address
    
    Args:
        email: string
    
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None