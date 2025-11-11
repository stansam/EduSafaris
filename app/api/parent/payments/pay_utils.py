from datetime import date, timedelta
from decimal import Decimal
from app.models import TripRegistration, RegistrationPayment

def calculate_payment_schedule(registration, plan_type, installments=None):
    """
    Calculate payment schedule for a registration
    
    Args:
        registration: TripRegistration object
        plan_type: string (full, 3_months, 6_months, weekly)
        installments: int (optional, number of installments)
    
    Returns:
        List of payment schedule items
    """
    outstanding = float(registration.outstanding_balance)
    trip_start = registration.trip.start_date
    
    schedule = []
    
    if plan_type == 'full':
        schedule.append({
            'installment_number': 1,
            'amount': outstanding,
            'due_date': (date.today() + timedelta(days=7)).isoformat(),
            'description': 'Full payment'
        })
    
    elif plan_type in ['3_months', '6_months']:
        months = 3 if plan_type == '3_months' else 6
        installment_amount = outstanding / months
        
        for i in range(months):
            due_date = date.today() + timedelta(days=30 * (i + 1))
            
            # Ensure due date is before trip start
            if due_date >= trip_start:
                due_date = trip_start - timedelta(days=1)
            
            schedule.append({
                'installment_number': i + 1,
                'amount': round(installment_amount, 2),
                'due_date': due_date.isoformat(),
                'description': f'Installment {i + 1} of {months}'
            })
    
    elif plan_type == 'weekly':
        weeks = installments or 8
        installment_amount = outstanding / weeks
        
        for i in range(weeks):
            due_date = date.today() + timedelta(weeks=i + 1)
            
            # Ensure due date is before trip start
            if due_date >= trip_start:
                due_date = trip_start - timedelta(days=1)
            
            schedule.append({
                'installment_number': i + 1,
                'amount': round(installment_amount, 2),
                'due_date': due_date.isoformat(),
                'description': f'Week {i + 1} payment'
            })
    
    return schedule


def validate_payment_amount(registration, amount):
    """
    Validate payment amount for a registration
    
    Args:
        registration: TripRegistration object
        amount: Decimal or float
    
    Returns:
        tuple (is_valid: bool, error_message: string or None)
    """
    try:
        amount = Decimal(str(amount))
    except (ValueError, TypeError):
        return False, "Invalid amount format"
    
    if amount <= 0:
        return False, "Amount must be greater than zero"
    
    if amount > Decimal(str(registration.outstanding_balance)):
        return False, f"Amount exceeds outstanding balance of {registration.outstanding_balance}"
    
    # Check minimum payment (if applicable)
    min_payment = Decimal('100')  # Minimum 100 KES
    if amount < min_payment and amount < Decimal(str(registration.outstanding_balance)):
        return False, f"Minimum payment amount is {min_payment} KES"
    
    return True, None


def get_payment_statistics(parent_id, start_date=None, end_date=None):
    """
    Get detailed payment statistics for a parent
    
    Args:
        parent_id: int
        start_date: datetime (optional)
        end_date: datetime (optional)
    
    Returns:
        Dictionary with payment statistics
    """
    query = RegistrationPayment.query.filter_by(parent_id=parent_id)
    
    if start_date:
        query = query.filter(RegistrationPayment.created_at >= start_date)
    
    if end_date:
        query = query.filter(RegistrationPayment.created_at <= end_date)
    
    payments = query.all()
    
    stats = {
        'total_payments': len(payments),
        'completed_payments': sum(1 for p in payments if p.status == 'completed'),
        'pending_payments': sum(1 for p in payments if p.status == 'pending'),
        'failed_payments': sum(1 for p in payments if p.status == 'failed'),
        'total_amount': sum(float(p.amount) for p in payments if p.status == 'completed'),
        'average_payment': 0,
        'largest_payment': 0,
        'smallest_payment': 0,
        'payment_methods': {}
    }
    
    completed_payments = [p for p in payments if p.status == 'completed']
    
    if completed_payments:
        amounts = [float(p.amount) for p in completed_payments]
        stats['average_payment'] = round(sum(amounts) / len(amounts), 2)
        stats['largest_payment'] = max(amounts)
        stats['smallest_payment'] = min(amounts)
        
        # Count payment methods
        for payment in completed_payments:
            method = payment.payment_method
            stats['payment_methods'][method] = stats['payment_methods'].get(method, 0) + 1
    
    return stats