from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from datetime import datetime, date, timedelta
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
from app.utils.receipt_generator import ReceiptGenerator
# from app.api.parent.payments.pay_utils import validate_phone_number, validate_amount
from app.api.parent.payments.validators import validate_phone_number, validate_amount
from app.api import api_bp as parent_payment_bp 
from app.utils.utils import roles_required


# ============================================================================
# DECORATOR
# ============================================================================

def handle_errors(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BadRequest as e:
            return jsonify({
                'success': False,
                'error': 'Bad request',
                'message': str(e.description) if hasattr(e, 'description') else str(e)
            }), 400
        except NotFound as e:
            return jsonify({
                'success': False,
                'error': 'Not found',
                'message': str(e.description) if hasattr(e, 'description') else str(e)
            }), 404
        except Forbidden as e:
            return jsonify({
                'success': False,
                'error': 'Forbidden',
                'message': str(e.description) if hasattr(e, 'description') else str(e)
            }), 403
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'message': str(e)
            }), 400
        except Exception as e:
            # Log the error
            print(f"Unexpected error in {f.__name__}: {str(e)}")
            
            # Log to activity log
            try:
                ActivityLog.log_action(
                    action='payment_api_error',
                    user_id=current_user.id if current_user.is_authenticated else None,
                    description=f"Error in {f.__name__}: {str(e)}",
                    category='payment',
                    status='failed',
                    error_message=str(e)
                )
            except:
                pass
            
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'message': 'An unexpected error occurred. Please try again later.'
            }), 500
    return decorated_function


# ============================================================================
# PAYMENT SUMMARY
# ============================================================================

@parent_payment_bp.route('/parent/payments/summary', methods=['GET'])
@login_required
@roles_required('parent')
@handle_errors
def get_payment_summary():
    """
    Get comprehensive payment summary for parent
    
    Returns:
        - Total amount paid
        - Total outstanding balance
        - Number of active registrations
        - Recent payments
        - Upcoming payment deadlines
    """
    try:
        # Get all active registrations
        active_registrations = TripRegistration.query.filter(
            TripRegistration.parent_id == current_user.id,
            TripRegistration.status.in_(['pending', 'confirmed', 'waitlisted'])
        ).all()
        
        # Calculate totals
        total_owed = sum(float(reg.total_amount) for reg in active_registrations)
        total_paid = sum(float(reg.amount_paid or 0) for reg in active_registrations)
        total_outstanding = total_owed - total_paid
        
        # Get recent payments (last 5)
        recent_payments = RegistrationPayment.query.filter_by(
            parent_id=current_user.id
        ).order_by(desc(RegistrationPayment.created_at)).limit(5).all()
        
        # Get upcoming payment deadlines
        upcoming_deadlines = []
        for reg in active_registrations:
            if reg.payment_deadline and reg.outstanding_balance > 0:
                days_remaining = (reg.payment_deadline - date.today()).days
                if days_remaining >= 0:
                    upcoming_deadlines.append({
                        'registration_id': reg.id,
                        'registration_number': reg.registration_number,
                        'trip_title': reg.trip.title,
                        'participant_name': reg.participant.full_name,
                        'amount_due': float(reg.outstanding_balance),
                        'deadline': reg.payment_deadline.isoformat(),
                        'days_remaining': days_remaining,
                        'is_overdue': False
                    })
        
        # Get overdue payments
        overdue_payments = []
        for reg in active_registrations:
            if reg.payment_deadline and reg.outstanding_balance > 0:
                if reg.payment_deadline < date.today():
                    days_overdue = (date.today() - reg.payment_deadline).days
                    overdue_payments.append({
                        'registration_id': reg.id,
                        'registration_number': reg.registration_number,
                        'trip_title': reg.trip.title,
                        'participant_name': reg.participant.full_name,
                        'amount_due': float(reg.outstanding_balance),
                        'deadline': reg.payment_deadline.isoformat(),
                        'days_overdue': days_overdue,
                        'is_overdue': True
                    })
        
        # Sort deadlines by date
        upcoming_deadlines.sort(key=lambda x: x['days_remaining'])
        overdue_payments.sort(key=lambda x: x['days_overdue'], reverse=True)
        
        # Get payment statistics
        completed_payments = RegistrationPayment.query.filter_by(
            parent_id=current_user.id,
            status='completed'
        ).all()
        
        total_transactions = len(completed_payments)
        total_amount_paid_all_time = sum(float(p.amount) for p in completed_payments)
        
        summary = {
            'success': True,
            'data': {
                'overview': {
                    'total_owed': round(total_owed, 2),
                    'total_paid': round(total_paid, 2),
                    'total_outstanding': round(total_outstanding, 2),
                    'active_registrations_count': len(active_registrations),
                    'total_transactions': total_transactions,
                    'total_amount_paid_all_time': round(total_amount_paid_all_time, 2),
                    'currency': 'KES'  # Default to KES for M-Pesa
                },
                'recent_payments': [
                    {
                        'id': p.id,
                        'amount': float(p.amount),
                        'currency': p.currency,
                        'status': p.status,
                        'payment_method': p.payment_method,
                        'reference_number': p.reference_number,
                        'transaction_id': p.transaction_id,
                        'registration_number': p.registration.registration_number if p.registration else None,
                        'trip_title': p.registration.trip.title if p.registration and p.registration.trip else None,
                        'participant_name': p.registration.participant.full_name if p.registration and p.registration.participant else None,
                        'created_at': p.created_at.isoformat() if p.created_at else None
                    } for p in recent_payments
                ],
                'upcoming_deadlines': upcoming_deadlines,
                'overdue_payments': overdue_payments,
                'active_registrations': [
                    {
                        'id': reg.id,
                        'registration_number': reg.registration_number,
                        'trip_title': reg.trip.title,
                        'participant_name': reg.participant.full_name,
                        'status': reg.status,
                        'payment_status': reg.payment_status,
                        'total_amount': float(reg.total_amount),
                        'amount_paid': float(reg.amount_paid or 0),
                        'outstanding_balance': float(reg.outstanding_balance),
                        'payment_plan': reg.payment_plan,
                        'payment_deadline': reg.payment_deadline.isoformat() if reg.payment_deadline else None
                    } for reg in active_registrations
                ]
            }
        }
        
        return jsonify(summary), 200
        
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve payment summary: {str(e)}")


# ============================================================================
# MAKE PAYMENT (M-PESA INTEGRATION)
# ============================================================================

@parent_payment_bp.route('/parent/payments/initiate', methods=['POST'])
@login_required
@roles_required('parent')
@handle_errors
def initiate_payment():
    """
    Initiate M-Pesa STK Push payment
    
    Request Body:
        - registration_id: int (required)
        - amount: float (required)
        - phone_number: string (required, format: 254XXXXXXXXX)
        - payment_method: string (optional, default: 'mpesa')
    
    Returns:
        - Payment initiation details
        - M-Pesa checkout request ID
    """
    data = request.get_json()
    
    # Validate required fields
    if not data:
        raise BadRequest("Request body is required")
    
    registration_id = data.get('registration_id')
    amount = data.get('amount')
    phone_number = data.get('phone_number')
    payment_method = data.get('payment_method', 'mpesa')
    
    # Validation
    if not registration_id:
        raise BadRequest("Registration ID is required")
    
    if not amount:
        raise BadRequest("Amount is required")
    
    if not phone_number:
        raise BadRequest("Phone number is required")
    
    # Validate amount
    try:
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
    except (ValueError, TypeError) as e:
        raise BadRequest(f"Invalid amount: {str(e)}")
    
    # Validate phone number
    phone_number = validate_phone_number(phone_number)
    if not phone_number:
        raise BadRequest("Invalid phone number format. Use format: 254XXXXXXXXX")
    
    # Get registration
    registration = TripRegistration.query.filter_by(
        id=registration_id,
        parent_id=current_user.id
    ).first()
    
    if not registration:
        raise NotFound("Registration not found or access denied")
    
    # Verify registration status
    if registration.status not in ['pending', 'confirmed', 'waitlisted']:
        raise BadRequest(f"Cannot make payment for registration with status: {registration.status}")
    
    # Verify amount doesn't exceed outstanding balance
    if amount > Decimal(str(registration.outstanding_balance)):
        raise BadRequest(
            f"Payment amount ({amount}) exceeds outstanding balance ({registration.outstanding_balance})"
        )
    
    try:
        # Create payment record
        payment = RegistrationPayment(
            registration_id=registration.id,
            parent_id=current_user.id,
            amount=amount,
            currency='KES',
            payment_method=payment_method,
            status='pending',
            payer_phone=phone_number
        )
        db.session.add(payment)
        db.session.flush()  # Get payment ID without committing
        
        # Generate reference number
        payment.reference_number = f"PAY-{registration.registration_number}-{payment.id}"
        
        # Initialize M-Pesa client
        mpesa_client = MpesaClient()
        
        # Initiate STK Push
        mpesa_response = mpesa_client.stk_push(
            phone_number=phone_number,
            amount=float(amount),
            account_reference=payment.reference_number,
            transaction_desc=f"Payment for {registration.trip.title}"
        )
        
        if mpesa_response.get('success'):
            # Update payment with M-Pesa details
            payment.transaction_id = mpesa_response.get('CheckoutRequestID')
            payment.receipt_number = mpesa_response.get('MerchantRequestID')
            
            db.session.commit()
            
            # Log activity
            ActivityLog.log_action(
                action='payment_initiated',
                user_id=current_user.id,
                entity_type='registration_payment',
                entity_id=payment.id,
                description=f"Payment of {amount} KES initiated for registration {registration.registration_number}",
                category='payment',
                trip_id=registration.trip_id,
                new_values={
                    'amount': float(amount),
                    'phone_number': phone_number,
                    'reference_number': payment.reference_number
                }
            )
            
            return jsonify({
                'success': True,
                'message': 'Payment initiated successfully. Please check your phone for M-Pesa prompt.',
                'data': {
                    'payment_id': payment.id,
                    'reference_number': payment.reference_number,
                    'checkout_request_id': mpesa_response.get('CheckoutRequestID'),
                    'merchant_request_id': mpesa_response.get('MerchantRequestID'),
                    'amount': float(amount),
                    'phone_number': phone_number,
                    'registration': {
                        'id': registration.id,
                        'registration_number': registration.registration_number,
                        'trip_title': registration.trip.title,
                        'participant_name': registration.participant.full_name
                    }
                }
            }), 201
        else:
            # M-Pesa initiation failed
            db.session.rollback()
            raise InternalServerError(
                mpesa_response.get('errorMessage', 'Failed to initiate M-Pesa payment')
            )
            
    except Exception as e:
        db.session.rollback()
        raise InternalServerError(f"Payment initiation failed: {str(e)}")


@parent_payment_bp.route('/parent/payments/status/<int:payment_id>', methods=['GET'])
@login_required
@roles_required('parent')
@handle_errors
def check_parent_payment_status(payment_id):
    """
    Check M-Pesa payment status
    
    Path Parameters:
        - payment_id: int
    
    Returns:
        - Current payment status
        - Transaction details if completed
    """
    payment = RegistrationPayment.query.filter_by(
        id=payment_id,
        parent_id=current_user.id
    ).first()
    
    if not payment:
        raise NotFound("Payment not found or access denied")
    
    # If payment is still pending, query M-Pesa for status
    if payment.status == 'pending' and payment.transaction_id:
        try:
            mpesa_client = MpesaClient()
            status_response = mpesa_client.query_stk_status(payment.transaction_id)
            
            if status_response.get('success'):
                result_code = status_response.get('ResultCode')
                
                if result_code == '0':
                    # Payment successful
                    payment.status = 'completed'
                    payment.receipt_number = status_response.get('MpesaReceiptNumber')
                    payment.processed_date = datetime.now()
                    
                    # Update registration
                    registration = payment.registration
                    registration.add_payment(payment.amount)
                    
                    db.session.commit()
                    
                    # Log activity
                    ActivityLog.log_payment(payment, current_user.id)
                    
                elif result_code in ['1032', '1037']:
                    # Payment cancelled or timeout
                    payment.status = 'cancelled'
                    payment.failure_reason = status_response.get('ResultDesc', 'Payment cancelled by user')
                    db.session.commit()
                    
                elif result_code != '':
                    # Payment failed
                    payment.status = 'failed'
                    payment.failure_reason = status_response.get('ResultDesc', 'Payment failed')
                    db.session.commit()
        except Exception as e:
            print(f"Error checking M-Pesa status: {str(e)}")
    
    return jsonify({
        'success': True,
        'data': {
            'payment_id': payment.id,
            'reference_number': payment.reference_number,
            'status': payment.status,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'payment_method': payment.payment_method,
            'transaction_id': payment.transaction_id,
            'mpesa_receipt_number': payment.receipt_number,
            'transaction_date': payment.processed_date.isoformat() if payment.processed_date else None,
            'failure_reason': payment.failure_reason,
            'registration': {
                'id': payment.registration.id,
                'registration_number': payment.registration.registration_number,
                'trip_title': payment.registration.trip.title,
                'outstanding_balance': float(payment.registration.outstanding_balance),
                'participant_name': payment.registration.participant.full_name
            } if payment.registration else None
        }
    }), 200


# ============================================================================
# PAYMENT HISTORY
# ============================================================================

@parent_payment_bp.route('/parent/payments/history', methods=['GET'])
@login_required
@roles_required('parent')
@handle_errors
def get_payment_history():
    """
    Get complete payment history for parent
    
    Query Parameters:
        - page: int (default: 1)
        - per_page: int (default: 20, max: 100)
        - status: string (optional, filter by status)
        - registration_id: int (optional, filter by registration)
        - start_date: string (optional, ISO format)
        - end_date: string (optional, ISO format)
        - sort_by: string (default: 'created_at', options: created_at, amount)
        - sort_order: string (default: 'desc', options: asc, desc)
    
    Returns:
        - Paginated payment history
        - Statistics
    """
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status_filter = request.args.get('status')
    registration_id = request.args.get('registration_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Build query
    query = RegistrationPayment.query.filter_by(parent_id=current_user.id)
    
    # Apply filters
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if registration_id:
        query = query.filter_by(registration_id=registration_id)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(RegistrationPayment.created_at >= start_dt)
        except ValueError:
            raise BadRequest("Invalid start_date format. Use ISO format (YYYY-MM-DD)")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date) + timedelta(days=1)
            query = query.filter(RegistrationPayment.created_at < end_dt)
        except ValueError:
            raise BadRequest("Invalid end_date format. Use ISO format (YYYY-MM-DD)")
    
    # Apply sorting
    if sort_by == 'amount':
        sort_column = RegistrationPayment.amount
    else:
        sort_column = RegistrationPayment.created_at
    
    if sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get statistics
    all_payments = RegistrationPayment.query.filter_by(parent_id=current_user.id).all()
    
    stats = {
        'total_payments': len(all_payments),
        'completed_payments': sum(1 for p in all_payments if p.status == 'completed'),
        'pending_payments': sum(1 for p in all_payments if p.status == 'pending'),
        'failed_payments': sum(1 for p in all_payments if p.status == 'failed'),
        'total_amount_paid': sum(float(p.amount) for p in all_payments if p.status == 'completed'),
        'total_pending_amount': sum(float(p.amount) for p in all_payments if p.status == 'pending')
    }
    
    return jsonify({
        'success': True,
        'data': {
            'payments': [
                {
                    'id': payment.id,
                    'reference_number': payment.reference_number,
                    'amount': float(payment.amount),
                    'currency': payment.currency,
                    'status': payment.status,
                    'payment_method': payment.payment_method,
                    'transaction_id': payment.transaction_id,
                    'mpesa_receipt_number': payment.receipt_number,
                    'transaction_date': payment.processed_date.isoformat() if payment.processed_date else None,
                    'failure_reason': payment.failure_reason,
                    'registration': {
                        'id': payment.registration.id,
                        'registration_number': payment.registration.registration_number,
                        'trip_title': payment.registration.trip.title,
                        'participant_name': payment.registration.participant.full_name
                    } if payment.registration else None,
                    'created_at': payment.created_at.isoformat() if payment.created_at else None,
                    'can_download_receipt': payment.status == 'completed'
                } for payment in pagination.items
            ],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'statistics': stats
        }
    }), 200


# ============================================================================
# DOWNLOAD RECEIPT
# ============================================================================

@parent_payment_bp.route('/parent/payments/receipt/<int:payment_id>', methods=['GET'])
@login_required
@roles_required('parent')
@handle_errors
def download_receipt(payment_id):
    """
    Download payment receipt as PDF
    
    Path Parameters:
        - payment_id: int
    
    Query Parameters:
        - format: string (default: 'pdf', options: pdf, json)
    
    Returns:
        - PDF file or JSON receipt data
    """
    format_type = request.args.get('format', 'pdf')
    
    # Get payment
    payment = RegistrationPayment.query.filter_by(
        id=payment_id,
        parent_id=current_user.id
    ).first()
    
    if not payment:
        raise NotFound("Payment not found or access denied")
    
    if payment.status != 'completed':
        raise BadRequest("Receipt can only be generated for completed payments")
    
    # Get receipt data
    receipt_data = {
        'receipt_number': f"REC-{payment.reference_number}",
        'payment_date': payment.processed_date.strftime('%Y-%m-%d %H:%M:%S') if payment.processed_date else None,
        'parent': {
            'name': current_user.full_name,
            'email': current_user.email,
            'phone': current_user.phone
        },
        'payment': {
            'reference_number': payment.reference_number,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'payment_method': payment.payment_method,
            'mpesa_receipt': payment.receipt_number,
            'transaction_id': payment.transaction_id
        },
        'registration': {
            'registration_number': payment.registration.registration_number,
            'trip_title': payment.registration.trip.title,
            'participant_name': payment.registration.participant.full_name,
            'trip_dates': f"{payment.registration.trip.start_date.strftime('%Y-%m-%d')} to {payment.registration.trip.end_date.strftime('%Y-%m-%d')}"
        },
        'balance': {
            'total_amount': float(payment.registration.total_amount),
            'amount_paid': float(payment.registration.amount_paid),
            'outstanding_balance': float(payment.registration.outstanding_balance)
        }
    }
    
    if format_type == 'json':
        return jsonify({
            'success': True,
            'data': receipt_data
        }), 200
    
    # Generate PDF receipt
    try:
        receipt_generator = ReceiptGenerator()
        pdf_buffer = receipt_generator.generate_receipt(receipt_data)
        
        # Log activity
        ActivityLog.log_action(
            action='receipt_downloaded',
            user_id=current_user.id,
            entity_type='registration_payment',
            entity_id=payment.id,
            description=f"Receipt downloaded for payment {payment.reference_number}",
            category='payment',
            trip_id=payment.registration.trip_id if payment.registration else None
        )
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"receipt_{payment.reference_number}.pdf"
        )
    except Exception as e:
        raise InternalServerError(f"Failed to generate receipt: {str(e)}")


# ============================================================================
# PAYMENT PLAN MANAGEMENT
# ============================================================================

@parent_payment_bp.route('/parent/payments/payment-plan/<int:registration_id>', methods=['GET'])
@login_required
@roles_required('parent')
@handle_errors
def get_payment_plan(registration_id):
    """
    Get payment plan details for a registration
    
    Path Parameters:
        - registration_id: int
    
    Returns:
        - Current payment plan details
        - Payment schedule
        - Available plan options
    """
    registration = TripRegistration.query.filter_by(
        id=registration_id,
        parent_id=current_user.id
    ).first()
    
    if not registration:
        raise NotFound("Registration not found or access denied")
    
    # Get payment history for this registration
    payments = RegistrationPayment.query.filter_by(
        registration_id=registration.id
    ).order_by(RegistrationPayment.created_at).all()
    
    # Calculate available payment plans
    outstanding = float(registration.outstanding_balance)
    
    available_plans = []
    
    if outstanding > 0 and registration.trip.allows_installments:
        # Calculate installment options
        trip_start = registration.trip.start_date
        days_until_trip = (trip_start - date.today()).days
        
        if days_until_trip > 30:
            # 3-month plan
            monthly_amount = outstanding / 3
            available_plans.append({
                'plan_type': '3_months',
                'name': '3 Monthly Installments',
                'installment_count': 3,
                'installment_amount': round(monthly_amount, 2),
                'frequency': 'monthly'
            })
        
        if days_until_trip > 60:
            # 6-month plan
            monthly_amount = outstanding / 6
            available_plans.append({
                'plan_type': '6_months',
                'name': '6 Monthly Installments',
                'installment_count': 6,
                'installment_amount': round(monthly_amount, 2),
                'frequency': 'monthly'
            })
        
        # Weekly plan (if more than 4 weeks)
        if days_until_trip > 28:
            weeks = min(days_until_trip // 7, 12)  # Max 12 weeks
            weekly_amount = outstanding / weeks
            available_plans.append({
                'plan_type': 'weekly',
                'name': f'{weeks} Weekly Installments',
                'installment_count': weeks,
                'installment_amount': round(weekly_amount, 2),
                'frequency': 'weekly'
            })
    
    # Full payment option
    available_plans.insert(0, {
        'plan_type': 'full',
        'name': 'Pay Full Amount',
        'installment_count': 1,
        'installment_amount': outstanding,
        'frequency': 'one_time'
    })
    
    return jsonify({
        'success': True,
        'data': {
            'registration': {
                'id': registration.id,
                'registration_number': registration.registration_number,
                'trip_title': registration.trip.title,
                'participant_name': registration.participant.full_name
            },
            'current_plan': registration.payment_plan,
            'payment_summary': {
                'total_amount': float(registration.total_amount),
                'amount_paid': float(registration.amount_paid or 0),
                'outstanding_balance': outstanding,
                'currency': registration.currency
            },
            'payment_history': [
                {
                    'id': p.id,
                    'amount': float(p.amount),
                    'status': p.status,
                    'date': p.processed_date.isoformat() if p.processed_date else p.created_at.isoformat()
                } for p in payments if p.status == 'completed'
            ],
            'available_plans': available_plans,
            'allows_installments': registration.trip.allows_installments
        }
    }), 200


# ============================================================================
# PAYMENT PLAN MANAGEMENT (CONTINUED)
# ============================================================================

@parent_payment_bp.route('/parent/payments/payment-plan/<int:registration_id>', methods=['POST'])
@login_required
@roles_required('parent')
@handle_errors
def set_payment_plan(registration_id):
    """
    Set or update payment plan for a registration
    
    Path Parameters:
        - registration_id: int
    
    Request Body:
        - plan_type: string (required, options: full, 3_months, 6_months, weekly)
        - installment_count: int (optional, for custom plans)
        - first_payment_amount: float (optional, for custom first payment)
    
    Returns:
        - Updated payment plan details
    """
    data = request.get_json()
    
    if not data:
        raise BadRequest("Request body is required")
    
    plan_type = data.get('plan_type')
    installment_count = data.get('installment_count')
    first_payment_amount = data.get('first_payment_amount')
    
    if not plan_type:
        raise BadRequest("plan_type is required")
    
    # Get registration
    registration = TripRegistration.query.filter_by(
        id=registration_id,
        parent_id=current_user.id
    ).first()
    
    if not registration:
        raise NotFound("Registration not found or access denied")
    
    # Verify registration allows installments
    if plan_type != 'full' and not registration.trip.allows_installments:
        raise BadRequest("This trip does not allow installment payments")
    
    # Verify outstanding balance
    if registration.outstanding_balance <= 0:
        raise BadRequest("No outstanding balance for this registration")
    
    try:
        # Update payment plan
        registration.payment_plan = plan_type
        
        # Set payment deadline based on plan
        if plan_type == 'full':
            # Set deadline to 7 days or trip start date, whichever is earlier
            days_until_trip = (registration.trip.start_date - date.today()).days
            deadline_days = min(7, days_until_trip - 1)
            registration.payment_deadline = date.today() + timedelta(days=deadline_days)
        
        elif plan_type == '3_months':
            registration.payment_deadline = date.today() + timedelta(days=90)
        
        elif plan_type == '6_months':
            registration.payment_deadline = date.today() + timedelta(days=180)
        
        elif plan_type == 'weekly':
            if installment_count:
                registration.payment_deadline = date.today() + timedelta(weeks=installment_count)
            else:
                # Default to 8 weeks
                registration.payment_deadline = date.today() + timedelta(weeks=8)
        
        # Ensure deadline is before trip start
        if registration.payment_deadline >= registration.trip.start_date:
            registration.payment_deadline = registration.trip.start_date - timedelta(days=1)
        
        db.session.commit()
        
        # Log activity
        ActivityLog.log_action(
            action='payment_plan_updated',
            user_id=current_user.id,
            entity_type='trip_registration',
            entity_id=registration.id,
            description=f"Payment plan set to {plan_type} for registration {registration.registration_number}",
            category='payment',
            trip_id=registration.trip_id,
            new_values={
                'payment_plan': plan_type,
                'payment_deadline': registration.payment_deadline.isoformat() if registration.payment_deadline else None
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Payment plan updated successfully',
            'data': {
                'registration_id': registration.id,
                'payment_plan': registration.payment_plan,
                'payment_deadline': registration.payment_deadline.isoformat() if registration.payment_deadline else None,
                'outstanding_balance': float(registration.outstanding_balance)
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        raise InternalServerError(f"Failed to update payment plan: {str(e)}")


# ============================================================================
# M-PESA CALLBACK ENDPOINT
# ============================================================================

@parent_payment_bp.route('/parent/payments//mpesa/callback', methods=['POST'])
@handle_errors
def mpesa_parent_callback():
    """
    M-Pesa STK Push callback endpoint
    This endpoint receives payment notifications from M-Pesa
    
    NOTE: This endpoint should be whitelisted in M-Pesa configuration
    and should NOT require authentication
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Invalid request'}), 400
    
    try:
        # Extract callback data
        body = data.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        merchant_request_id = stk_callback.get('MerchantRequestID')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        
        # Find payment by checkout_request_id
        payment = RegistrationPayment.query.filter_by(
            transaction_id=checkout_request_id
        ).first()
        
        if not payment:
            print(f"Payment not found for CheckoutRequestID: {checkout_request_id}")
            return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200
        
        if result_code == 0:
            # Payment successful
            callback_metadata = stk_callback.get('CallbackMetadata', {})
            items = callback_metadata.get('Item', [])
            
            # Extract payment details
            mpesa_receipt = None
            transaction_date = None
            phone_number = None
            
            for item in items:
                name = item.get('Name')
                value = item.get('Value')
                
                if name == 'MpesaReceiptNumber':
                    mpesa_receipt = value
                elif name == 'TransactionDate':
                    # Convert M-Pesa date format (YYYYMMDDHHmmss) to datetime
                    transaction_date = datetime.strptime(str(value), '%Y%m%d%H%M%S')
                elif name == 'PhoneNumber':
                    phone_number = value
            
            # Update payment
            payment.status = 'completed'
            payment.receipt_number = mpesa_receipt
            payment.processed_date = transaction_date or datetime.now()
            payment.processor_response = data
            
            # Update registration
            registration = payment.registration
            registration.add_payment(payment.amount)
            
            db.session.commit()
            
            # Log activity
            ActivityLog.log_payment(payment, payment.parent_id)
            
            # Send notification to parent
            try:
                from app.utils.notifications import NotificationService
                NotificationService.send_payment_success_notification(
                    user_id=payment.parent_id,
                    payment=payment,
                    registration=registration
                )
            except Exception as e:
                print(f"Failed to send notification: {str(e)}")
        
        else:
            # Payment failed or cancelled
            payment.status = 'failed'
            payment.failure_reason = result_desc
            payment.processor_response = data
            db.session.commit()
            
            # Log activity
            ActivityLog.log_action(
                action='payment_failed',
                user_id=payment.parent_id,
                entity_type='registration_payment',
                entity_id=payment.id,
                description=f"Payment failed: {result_desc}",
                category='payment',
                trip_id=payment.registration.trip_id if payment.registration else None,
                status='failed',
                error_message=result_desc
            )
        
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200
        
    except Exception as e:
        print(f"Error processing M-Pesa callback: {str(e)}")
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Internal error'}), 500


# ============================================================================
# PAYMENT REMINDERS
# ============================================================================

@parent_payment_bp.route('/parent/payments/reminders', methods=['GET'])
@login_required
@roles_required('parent')
@handle_errors
def get_payment_reminders():
    """
    Get payment reminders for parent
    
    Returns:
        - Upcoming payment deadlines
        - Overdue payments
        - Suggested payment amounts
    """
    # Get active registrations with outstanding balance
    registrations = TripRegistration.query.filter(
        TripRegistration.parent_id == current_user.id,
        TripRegistration.status.in_(['pending', 'confirmed', 'waitlisted'])
    ).all()
    
    reminders = []
    
    for reg in registrations:
        if reg.outstanding_balance > 0:
            # Calculate urgency
            if reg.payment_deadline:
                days_remaining = (reg.payment_deadline - date.today()).days
                
                if days_remaining < 0:
                    urgency = 'overdue'
                    urgency_level = 3
                elif days_remaining <= 3:
                    urgency = 'urgent'
                    urgency_level = 2
                elif days_remaining <= 7:
                    urgency = 'soon'
                    urgency_level = 1
                else:
                    urgency = 'normal'
                    urgency_level = 0
            else:
                urgency = 'normal'
                urgency_level = 0
                days_remaining = None
            
            # Suggest payment amount based on plan
            if reg.payment_plan == 'full':
                suggested_amount = float(reg.outstanding_balance)
            elif reg.payment_plan in ['3_months', '6_months']:
                months = 3 if reg.payment_plan == '3_months' else 6
                suggested_amount = float(reg.outstanding_balance) / months
            else:
                # Default to minimum payment or 25% of outstanding
                suggested_amount = max(500, float(reg.outstanding_balance) * 0.25)
            
            reminders.append({
                'registration_id': reg.id,
                'registration_number': reg.registration_number,
                'trip_title': reg.trip.title,
                'participant_name': reg.participant.full_name,
                'outstanding_balance': float(reg.outstanding_balance),
                'payment_deadline': reg.payment_deadline.isoformat() if reg.payment_deadline else None,
                'days_remaining': days_remaining,
                'urgency': urgency,
                'urgency_level': urgency_level,
                'suggested_amount': round(suggested_amount, 2),
                'payment_plan': reg.payment_plan,
                'trip_start_date': reg.trip.start_date.isoformat()
            })
    
    # Sort by urgency level (highest first)
    reminders.sort(key=lambda x: x['urgency_level'], reverse=True)
    
    return jsonify({
        'success': True,
        'data': {
            'reminders': reminders,
            'total_reminders': len(reminders),
            'overdue_count': sum(1 for r in reminders if r['urgency'] == 'overdue'),
            'urgent_count': sum(1 for r in reminders if r['urgency'] == 'urgent')
        }
    }), 200

