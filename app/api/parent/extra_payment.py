from flask import request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal
import os
import io
from functools import wraps
from werkzeug.exceptions import BadRequest, NotFound, Forbidden, InternalServerError

from app.extensions import db
from app.models import (
    User, TripRegistration, RegistrationPayment, 
    Participant, Trip, ActivityLog
)
from app.utils.mpesa import MpesaClient
from app.api.parent.payment import handle_errors
from app.api.parent.payments.validators import validate_phone_number, validate_amount

from app.api import api_bp as parent_payment_bp 
from app.utils.utils import roles_required

@parent_payment_bp.route('/methods', methods=['GET'])
@login_required
@roles_required('parent')
@handle_errors
def get_payment_methods():
    """
    Get available payment methods
    
    Returns:
        - List of available payment methods
        - Configuration for each method
    """
    methods = [
        {
            'id': 'mpesa',
            'name': 'M-Pesa',
            'description': 'Pay using M-Pesa mobile money',
            'icon': 'mpesa-icon.png',
            'enabled': True,
            'min_amount': 100,
            'max_amount': 150000,
            'currency': 'KES',
            'processing_time': 'Instant',
            'instructions': [
                'Enter your M-Pesa registered phone number',
                'Enter the amount you wish to pay',
                'You will receive a prompt on your phone',
                'Enter your M-Pesa PIN to complete payment'
            ]
        },
        {
            'id': 'bank_transfer',
            'name': 'Bank Transfer',
            'description': 'Pay via bank transfer',
            'icon': 'bank-icon.png',
            'enabled': True,
            'min_amount': 100,
            'max_amount': 999999,
            'currency': 'KES',
            'processing_time': '1-2 business days',
            'bank_details': {
                'bank_name': 'Example Bank',
                'account_name': 'EduSafaris Ltd',
                'account_number': '1234567890',
                'swift_code': 'EXAMPLEKE'
            },
            'instructions': [
                'Transfer funds to the account details provided',
                'Use your registration number as reference',
                'Upload proof of payment',
                'Payment will be verified within 1-2 business days'
            ]
        }
    ]
    
    return jsonify({
        'success': True,
        'data': {
            'payment_methods': methods,
            'default_method': 'mpesa',
            'currency': 'KES'
        }
    }), 200


@parent_payment_bp.route('/verify/<string:reference_number>', methods=['GET'])
@login_required
@roles_required('parent')
@handle_errors
def verify_payment(reference_number):
    """
    Verify payment by reference number
    
    Path Parameters:
        - reference_number: string
    
    Returns:
        - Payment details and verification status
    """
    payment = RegistrationPayment.query.filter_by(
        reference_number=reference_number,
        parent_id=current_user.id
    ).first()
    
    if not payment:
        raise NotFound("Payment not found with provided reference number")
    
    return jsonify({
        'success': True,
        'data': {
            'reference_number': payment.reference_number,
            'status': payment.status,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'payment_method': payment.payment_method,
            'transaction_id': payment.transaction_id,
            'mpesa_receipt_number': payment.receipt_number,
            'transaction_date': payment.transaction_date.isoformat() if payment.transaction_date else None,
            'registration': {
                'id': payment.registration.id,
                'registration_number': payment.registration.registration_number,
                'trip_title': payment.registration.trip.title
            } if payment.registration else None,
            'is_verified': payment.status == 'completed',
            'created_at': payment.created_at.isoformat() if payment.created_at else None
        }
    }), 200


@parent_payment_bp.route('/cancel/<int:payment_id>', methods=['POST'])
@login_required
@roles_required('parent')
@handle_errors
def cancel_payment(payment_id):
    """
    Cancel a pending payment
    
    Path Parameters:
        - payment_id: int
    
    Returns:
        - Cancellation confirmation
    """
    payment = RegistrationPayment.query.filter_by(
        id=payment_id,
        parent_id=current_user.id
    ).first()
    
    if not payment:
        raise NotFound("Payment not found or access denied")
    
    if payment.status != 'pending':
        raise BadRequest(f"Cannot cancel payment with status: {payment.status}")
    
    try:
        payment.status = 'cancelled'
        payment.failure_reason = 'Cancelled by user'
        db.session.commit()
        
        # Log activity
        ActivityLog.log_action(
            action='payment_cancelled',
            user_id=current_user.id,
            entity_type='registration_payment',
            entity_id=payment.id,
            description=f"Payment {payment.reference_number} cancelled by user",
            category='payment',
            trip_id=payment.registration.trip_id if payment.registration else None
        )
        
        return jsonify({
            'success': True,
            'message': 'Payment cancelled successfully',
            'data': {
                'payment_id': payment.id,
                'reference_number': payment.reference_number,
                'status': payment.status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        raise InternalServerError(f"Failed to cancel payment: {str(e)}")


@parent_payment_bp.route('/bulk-pay', methods=['POST'])
@login_required
@roles_required('parent')
@handle_errors
def bulk_payment():
    """
    Make payment for multiple registrations at once
    
    Request Body:
        - payments: array of objects
          - registration_id: int
          - amount: float
        - phone_number: string (required for M-Pesa)
        - payment_method: string
    
    Returns:
        - Bulk payment initiation details
    """
    data = request.get_json()
    
    if not data:
        raise BadRequest("Request body is required")
    
    payments_data = data.get('payments', [])
    phone_number = data.get('phone_number')
    payment_method = data.get('payment_method', 'mpesa')
    
    if not payments_data:
        raise BadRequest("At least one payment is required")
    
    if not phone_number:
        raise BadRequest("Phone number is required")
    
    # Validate phone number
    phone_number = validate_phone_number(phone_number)
    if not phone_number:
        raise BadRequest("Invalid phone number format")
    
    # Validate and calculate total
    total_amount = Decimal('0')
    registrations = []
    
    for payment_data in payments_data:
        registration_id = payment_data.get('registration_id')
        amount = payment_data.get('amount')
        
        if not registration_id or not amount:
            raise BadRequest("Each payment must have registration_id and amount")
        
        # Get registration
        registration = TripRegistration.query.filter_by(
            id=registration_id,
            parent_id=current_user.id
        ).first()
        
        if not registration:
            raise NotFound(f"Registration {registration_id} not found or access denied")
        
        # Validate amount
        amount = Decimal(str(amount))
        if amount > Decimal(str(registration.outstanding_balance)):
            raise BadRequest(
                f"Amount for registration {registration.registration_number} exceeds outstanding balance"
            )
        
        registrations.append({'registration': registration, 'amount': amount})
        total_amount += amount
    
    # Initiate M-Pesa payment for total amount
    try:
        # Create a bulk payment record
        bulk_reference = f"BULK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Initialize M-Pesa client
        mpesa_client = MpesaClient()
        
        # Initiate STK Push
        mpesa_response = mpesa_client.stk_push(
            phone_number=phone_number,
            amount=float(total_amount),
            account_reference=bulk_reference,
            transaction_desc="Bulk payment for multiple trips"
        )
        
        if mpesa_response.get('success'):
            # Create individual payment records
            payment_ids = []
            
            for reg_data in registrations:
                payment = RegistrationPayment(
                    registration_id=reg_data['registration'].id,
                    parent_id=current_user.id,
                    amount=reg_data['amount'],
                    currency='KES',
                    payment_method=payment_method,
                    status='pending',
                    payer_phone=phone_number,
                    transaction_id=mpesa_response.get('CheckoutRequestID'),
                    description=f"Bulk payment: {bulk_reference}"
                )
                db.session.add(payment)
                db.session.flush()
                
                payment.reference_number = f"PAY-{reg_data['registration'].registration_number}-{payment.id}"
                payment_ids.append(payment.id)
            
            db.session.commit()
            
            # Log activity
            ActivityLog.log_action(
                action='bulk_payment_initiated',
                user_id=current_user.id,
                entity_type='registration_payment',
                entity_id=payment_ids[0],
                description=f"Bulk payment of {total_amount} KES initiated for {len(registrations)} registrations",
                category='payment',
                new_values={
                    'total_amount': float(total_amount),
                    'payment_count': len(registrations),
                    'bulk_reference': bulk_reference
                }
            )
            
            return jsonify({
                'success': True,
                'message': 'Bulk payment initiated successfully. Please check your phone for M-Pesa prompt.',
                'data': {
                    'bulk_reference': bulk_reference,
                    'total_amount': float(total_amount),
                    'payment_count': len(registrations),
                    'checkout_request_id': mpesa_response.get('CheckoutRequestID'),
                    'merchant_request_id': mpesa_response.get('MerchantRequestID'),
                    'payment_ids': payment_ids
                }
            }), 201
        else:
            raise InternalServerError(
                mpesa_response.get('errorMessage', 'Failed to initiate bulk payment')
            )
            
    except Exception as e:
        db.session.rollback()
        raise InternalServerError(f"Bulk payment initiation failed: {str(e)}")


# ============================================================================
# ADMIN/TEACHER ENDPOINTS (For reconciliation)
# ============================================================================

@parent_payment_bp.route('/admin/reconcile', methods=['POST'])
@login_required
@handle_errors
def reconcile_payment():
    """
    Manually reconcile a payment (Admin/Teacher only)
    
    Request Body:
        - payment_id: int
        - status: string (completed, failed)
        - transaction_id: string (optional)
        - notes: string (optional)
    
    Returns:
        - Reconciliation confirmation
    """
    # Check if user is admin or teacher
    if current_user.role not in ['admin', 'teacher']:
        raise Forbidden("Only admins and teachers can reconcile payments")
    
    data = request.get_json()
    
    if not data:
        raise BadRequest("Request body is required")
    
    payment_id = data.get('payment_id')
    status = data.get('status')
    transaction_id = data.get('transaction_id')
    notes = data.get('notes')
    
    if not payment_id or not status:
        raise BadRequest("payment_id and status are required")
    
    if status not in ['completed', 'failed']:
        raise BadRequest("Status must be 'completed' or 'failed'")
    
    # Get payment
    payment = RegistrationPayment.query.get(payment_id)
    
    if not payment:
        raise NotFound("Payment not found")
    
    try:
        if status == 'completed':
            payment.status = 'completed'
            payment.transaction_date = datetime.now()
            if transaction_id:
                payment.receipt_number = transaction_id
            
            # Update registration
            registration = payment.registration
            registration.add_payment(payment.amount)
            
            # Log payment
            ActivityLog.log_payment(payment, current_user.id)
        
        else:  # failed
            payment.status = 'failed'
            payment.failure_reason = notes or 'Manually marked as failed'
        
        # Add admin notes
        if notes:
            if not payment.processor_response:
                payment.processor_response = {}
            payment.processor_response['admin_notes'] = notes
            payment.processor_response['reconciled_by'] = current_user.id
            payment.processor_response['reconciled_at'] = datetime.now().isoformat()
        
        db.session.commit()
        
        # Log activity
        ActivityLog.log_action(
            action='payment_reconciled',
            user_id=current_user.id,
            entity_type='registration_payment',
            entity_id=payment.id,
            description=f"Payment {payment.reference_number} manually reconciled to {status}",
            category='payment',
            trip_id=payment.registration.trip_id if payment.registration else None,
            new_values={
                'status': status,
                'notes': notes
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Payment reconciled successfully as {status}',
            'data': {
                'payment_id': payment.id,
                'reference_number': payment.reference_number,
                'status': payment.status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        raise InternalServerError(f"Failed to reconcile payment: {str(e)}")