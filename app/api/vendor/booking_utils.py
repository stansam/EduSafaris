from app.models import ActivityLog

def serialize_booking_detailed(booking):
    """Serialize booking with full details"""
    return {
        'id': booking.id,
        'status': booking.status,
        'booking_type': booking.booking_type,
        'service_description': booking.service_description,
        'special_requirements': booking.special_requirements,
        'notes': booking.notes,
        'quoted_amount': float(booking.quoted_amount) if booking.quoted_amount else None,
        'final_amount': float(booking.final_amount) if booking.final_amount else None,
        'total_amount': float(booking.total_amount) if booking.total_amount else None,
        'currency': booking.currency,
        'payment_status': booking.payment_status,
        'service_start_date': booking.service_start_date.isoformat() if booking.service_start_date else None,
        'service_end_date': booking.service_end_date.isoformat() if booking.service_end_date else None,
        'booking_date': booking.booking_date.isoformat() if booking.booking_date else None,
        'confirmed_date': booking.confirmed_date.isoformat() if booking.confirmed_date else None,
        'completed_date': booking.completed_date.isoformat() if booking.completed_date else None,
        'cancelled_date': booking.cancelled_date.isoformat() if booking.cancelled_date else None,
        'cancellation_reason': booking.cancellation_reason,
        'rating': booking.rating,
        'review': booking.review,
        'trip': {
            'id': booking.trip.id,
            'title': booking.trip.title,
            'start_date': booking.trip.start_date.isoformat() if booking.trip.start_date else None,
            'end_date': booking.trip.end_date.isoformat() if booking.trip.end_date else None,
            'status': booking.trip.status,
            'organizer': {
                'id': booking.trip.organizer.id,
                'full_name': booking.trip.organizer.full_name,
                'email': booking.trip.organizer.email,
                'phone': booking.trip.organizer.phone
            } if booking.trip.organizer else None
        } if booking.trip else None,
        'booked_by': {
            'id': booking.booker.id,
            'full_name': booking.booker.full_name,
            'email': booking.booker.email,
            'phone': booking.booker.phone
        } if booking.booker else None,
        'payments': [
            {
                'id': payment.id,
                'amount': float(payment.amount),
                'status': payment.status,
                'payment_method': payment.payment_method,
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'reference_number': payment.reference_number
            } for payment in booking.payments.all()
        ],
        'created_at': booking.created_at.isoformat() if booking.created_at else None,
        'updated_at': booking.updated_at.isoformat() if booking.updated_at else None
    }


def log_booking_action(booking, action, description, user_id, metadata=None):
    """Helper to log booking actions"""
    try:
        ActivityLog.log_service_booking(
            booking=booking,
            user_id=user_id,
            action_type=action
        )
    except Exception as e:
        # Log error but don't fail the main operation
        print(f"Failed to log activity: {str(e)}")