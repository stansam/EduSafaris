from flask import request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_, extract
from datetime import datetime, timedelta, date
from decimal import Decimal
import io
import csv
from functools import wraps

from app.extensions import db
from app.models import (
    Vendor, ServiceBooking, ServicePayment, User, 
    Trip, ActivityLog
)
from app.api import api_bp as vendor_financials_bp 
from app.utils.utils import roles_required


# ==================== DECORATOR ====================

def validate_date_range(start_date_str, end_date_str, max_days=365):
    """Validate and parse date range"""
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        
        if start_date and end_date:
            if start_date > end_date:
                return None, None, "Start date cannot be after end date"
            
            if (end_date - start_date).days > max_days:
                return None, None, f"Date range cannot exceed {max_days} days"
        
        return start_date, end_date, None
    except ValueError:
        return None, None, "Invalid date format. Use YYYY-MM-DD"


# ==================== BOOKING PAYMENTS API ====================

@vendor_financials_bp.route('/vendor/financials/booking-payments', methods=['GET'])
@roles_required('vendor')
def get_booking_payments():
    """
    Get all booking payments for the vendor
    Query Parameters:
        - status: Filter by payment status (pending, completed, failed, refunded)
        - start_date: Filter from date (YYYY-MM-DD)
        - end_date: Filter to date (YYYY-MM-DD)
        - booking_id: Filter by specific booking
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
        - sort: Sort field (payment_date, amount) (default: payment_date)
        - order: Sort order (asc, desc) (default: desc)
    """
    try:
        vendor = current_user.vendor_profile
        
        # Parse query parameters
        status = request.args.get('status', type=str)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        booking_id = request.args.get('booking_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        sort_by = request.args.get('sort', 'payment_date')
        order = request.args.get('order', 'desc')
        
        # Validate pagination
        if page < 1:
            return jsonify({
                'success': False,
                'error': 'Invalid Parameter',
                'message': 'Page number must be greater than 0'
            }), 400
        
        # Validate date range
        start_date, end_date, date_error = validate_date_range(start_date_str, end_date_str)
        if date_error:
            return jsonify({
                'success': False,
                'error': 'Invalid Date Range',
                'message': date_error
            }), 400
        
        # Build query
        query = ServicePayment.query.filter_by(vendor_id=vendor.id)
        
        # Apply filters
        if status:
            valid_statuses = ['pending', 'processing', 'completed', 'failed', 'refunded']
            if status not in valid_statuses:
                return jsonify({
                    'success': False,
                    'error': 'Invalid Status',
                    'message': f'Status must be one of: {", ".join(valid_statuses)}'
                }), 400
            query = query.filter_by(status=status)
        
        if booking_id:
            query = query.filter_by(service_booking_id=booking_id)
        
        if start_date:
            query = query.filter(ServicePayment.payment_date >= start_date)
        
        if end_date:
            query = query.filter(ServicePayment.payment_date <= end_date)
        
        # Apply sorting
        valid_sort_fields = ['payment_date', 'amount', 'created_at']
        if sort_by not in valid_sort_fields:
            sort_by = 'payment_date'
        
        sort_column = getattr(ServicePayment, sort_by)
        if order.lower() == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Execute pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        payments = pagination.items
        
        # Calculate summary statistics
        total_query = ServicePayment.query.filter_by(vendor_id=vendor.id)
        if start_date:
            total_query = total_query.filter(ServicePayment.payment_date >= start_date)
        if end_date:
            total_query = total_query.filter(ServicePayment.payment_date <= end_date)
        
        summary = db.session.query(
            func.count(ServicePayment.id).label('total_count'),
            func.sum(ServicePayment.amount).label('total_amount'),
            func.sum(
                db.case((ServicePayment.status == 'completed', ServicePayment.amount), else_=0)
            ).label('completed_amount'),
            func.sum(
                db.case((ServicePayment.status == 'pending', ServicePayment.amount), else_=0)
            ).label('pending_amount')
        ).filter_by(vendor_id=vendor.id)
        
        if start_date:
            summary = summary.filter(ServicePayment.payment_date >= start_date)
        if end_date:
            summary = summary.filter(ServicePayment.payment_date <= end_date)
        
        summary_result = summary.first()
        
        return jsonify({
            'success': True,
            'data': {
                'payments': [payment.serialize() for payment in payments],
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': pagination.pages,
                    'total_items': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                },
                'summary': {
                    'total_payments': summary_result.total_count or 0,
                    'total_amount': float(summary_result.total_amount or 0),
                    'completed_amount': float(summary_result.completed_amount or 0),
                    'pending_amount': float(summary_result.pending_amount or 0),
                    'currency': 'KES'  # Default currency
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching booking payments: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'An error occurred while fetching booking payments'
        }), 500


# ==================== REVENUE REPORT API ====================

@vendor_financials_bp.route('/vendor/financials/revenue-report', methods=['GET'])
@roles_required('vendor')
def get_revenue_report():
    """
    Get comprehensive revenue report
    Query Parameters:
        - period: Reporting period (daily, weekly, monthly, yearly, custom)
        - start_date: Start date for custom period (YYYY-MM-DD)
        - end_date: End date for custom period (YYYY-MM-DD)
        - group_by: Group results by (day, week, month, service_type, booking)
    """
    try:
        vendor = current_user.vendor_profile
        
        # Parse parameters
        period = request.args.get('period', 'monthly')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        group_by = request.args.get('group_by', 'month')
        
        # Set date range based on period
        if period == 'daily':
            start_date = date.today()
            end_date = date.today()
        elif period == 'weekly':
            start_date = date.today() - timedelta(days=7)
            end_date = date.today()
        elif period == 'monthly':
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
        elif period == 'yearly':
            start_date = date.today() - timedelta(days=365)
            end_date = date.today()
        elif period == 'custom':
            start_date, end_date, date_error = validate_date_range(start_date_str, end_date_str)
            if date_error:
                return jsonify({
                    'success': False,
                    'error': 'Invalid Date Range',
                    'message': date_error
                }), 400
            if not start_date or not end_date:
                return jsonify({
                    'success': False,
                    'error': 'Missing Dates',
                    'message': 'start_date and end_date required for custom period'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid Period',
                'message': 'Period must be: daily, weekly, monthly, yearly, or custom'
            }), 400
        
        # Base query for payments
        base_query = ServicePayment.query.filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.payment_date >= start_date,
            ServicePayment.payment_date <= end_date
        )
        
        # Overall statistics
        overall_stats = db.session.query(
            func.count(ServicePayment.id).label('total_transactions'),
            func.sum(
                db.case((ServicePayment.status == 'completed', ServicePayment.amount), else_=0)
            ).label('total_revenue'),
            func.sum(
                db.case((ServicePayment.status == 'pending', ServicePayment.amount), else_=0)
            ).label('pending_revenue'),
            func.sum(
                db.case((ServicePayment.status == 'refunded', ServicePayment.amount), else_=0)
            ).label('refunded_amount'),
            func.avg(
                db.case((ServicePayment.status == 'completed', ServicePayment.amount), else_=None)
            ).label('average_transaction')
        ).filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.payment_date >= start_date,
            ServicePayment.payment_date <= end_date
        ).first()
        
        # Revenue by service type
        revenue_by_service = db.session.query(
            ServiceBooking.booking_type,
            func.count(ServicePayment.id).label('count'),
            func.sum(
                db.case((ServicePayment.status == 'completed', ServicePayment.amount), else_=0)
            ).label('revenue')
        ).join(
            ServiceBooking, ServicePayment.service_booking_id == ServiceBooking.id
        ).filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.payment_date >= start_date,
            ServicePayment.payment_date <= end_date
        ).group_by(ServiceBooking.booking_type).all()
        
        # Time-based grouping
        if group_by == 'day':
            time_series = db.session.query(
                func.date(ServicePayment.payment_date).label('date'),
                func.sum(
                    db.case((ServicePayment.status == 'completed', ServicePayment.amount), else_=0)
                ).label('revenue'),
                func.count(ServicePayment.id).label('transactions')
            ).filter(
                ServicePayment.vendor_id == vendor.id,
                ServicePayment.payment_date >= start_date,
                ServicePayment.payment_date <= end_date
            ).group_by(func.date(ServicePayment.payment_date)).all()
        elif group_by == 'month':
            time_series = db.session.query(
                extract('year', ServicePayment.payment_date).label('year'),
                extract('month', ServicePayment.payment_date).label('month'),
                func.sum(
                    db.case((ServicePayment.status == 'completed', ServicePayment.amount), else_=0)
                ).label('revenue'),
                func.count(ServicePayment.id).label('transactions')
            ).filter(
                ServicePayment.vendor_id == vendor.id,
                ServicePayment.payment_date >= start_date,
                ServicePayment.payment_date <= end_date
            ).group_by(
                extract('year', ServicePayment.payment_date),
                extract('month', ServicePayment.payment_date)
            ).all()
        else:
            time_series = []
        
        # Top bookings by revenue
        top_bookings = db.session.query(
            ServiceBooking.id,
            ServiceBooking.booking_type,
            Trip.title.label('trip_title'),
            func.sum(
                db.case((ServicePayment.status == 'completed', ServicePayment.amount), else_=0)
            ).label('revenue')
        ).join(
            ServiceBooking, ServicePayment.service_booking_id == ServiceBooking.id
        ).join(
            Trip, ServiceBooking.trip_id == Trip.id
        ).filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.payment_date >= start_date,
            ServicePayment.payment_date <= end_date
        ).group_by(
            ServiceBooking.id, ServiceBooking.booking_type, Trip.title
        ).order_by(func.sum(ServicePayment.amount).desc()).limit(10).all()
        
        # Format response
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'period_type': period
                },
                'overall_statistics': {
                    'total_transactions': overall_stats.total_transactions or 0,
                    'total_revenue': float(overall_stats.total_revenue or 0),
                    'pending_revenue': float(overall_stats.pending_revenue or 0),
                    'refunded_amount': float(overall_stats.refunded_amount or 0),
                    'average_transaction': float(overall_stats.average_transaction or 0),
                    'currency': 'KES'
                },
                'revenue_by_service_type': [
                    {
                        'service_type': item.booking_type,
                        'transaction_count': item.count,
                        'revenue': float(item.revenue or 0)
                    }
                    for item in revenue_by_service
                ],
                'time_series': [
                    {
                        'period': str(item.date) if group_by == 'day' else f"{int(item.year)}-{int(item.month):02d}",
                        'revenue': float(item.revenue or 0),
                        'transactions': item.transactions
                    }
                    for item in time_series
                ],
                'top_bookings': [
                    {
                        'booking_id': item.id,
                        'booking_type': item.booking_type,
                        'trip_title': item.trip_title,
                        'revenue': float(item.revenue or 0)
                    }
                    for item in top_bookings
                ]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error generating revenue report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'An error occurred while generating revenue report'
        }), 500


# ==================== DOWNLOAD PAYMENT HISTORY API ====================

@vendor_financials_bp.route('/vendor/financials/payment-history/download', methods=['GET'])
@roles_required('vendor')
def download_payment_history():
    """
    Download payment history as CSV
    Query Parameters:
        - format: File format (csv, json) (default: csv)
        - start_date: Filter from date (YYYY-MM-DD)
        - end_date: Filter to date (YYYY-MM-DD)
        - status: Filter by payment status
    """
    try:
        vendor = current_user.vendor_profile
        
        # Parse parameters
        file_format = request.args.get('format', 'csv').lower()
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        status = request.args.get('status')
        
        # Validate format
        if file_format not in ['csv', 'json']:
            return jsonify({
                'success': False,
                'error': 'Invalid Format',
                'message': 'Format must be csv or json'
            }), 400
        
        # Validate date range
        start_date, end_date, date_error = validate_date_range(start_date_str, end_date_str, max_days=730)
        if date_error:
            return jsonify({
                'success': False,
                'error': 'Invalid Date Range',
                'message': date_error
            }), 400
        
        # Build query
        query = ServicePayment.query.filter_by(vendor_id=vendor.id)
        
        if status:
            query = query.filter_by(status=status)
        if start_date:
            query = query.filter(ServicePayment.payment_date >= start_date)
        if end_date:
            query = query.filter(ServicePayment.payment_date <= end_date)
        
        payments = query.order_by(ServicePayment.payment_date.desc()).all()
        
        # Check if there are payments
        if not payments:
            return jsonify({
                'success': False,
                'error': 'No Data',
                'message': 'No payment records found for the specified criteria'
            }), 404
        
        # Generate filename
        filename_date = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if file_format == 'csv':
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            headers = [
                'Payment ID', 'Reference Number', 'Transaction ID', 'Booking ID',
                'Trip Title', 'Service Type', 'Amount', 'Currency', 'Status',
                'Payment Method', 'Payment Date', 'Processed Date', 'Payer Name',
                'Payer Email', 'Description'
            ]
            writer.writerow(headers)
            
            # Write data
            for payment in payments:
                booking = payment.service_booking
                trip = booking.trip if booking else None
                
                writer.writerow([
                    payment.id,
                    payment.reference_number or '',
                    payment.transaction_id or '',
                    booking.id if booking else '',
                    trip.title if trip else '',
                    booking.booking_type if booking else '',
                    float(payment.amount),
                    payment.currency,
                    payment.status,
                    payment.payment_method,
                    payment.payment_date.strftime('%Y-%m-%d %H:%M:%S') if payment.payment_date else '',
                    payment.processed_date.strftime('%Y-%m-%d %H:%M:%S') if payment.processed_date else '',
                    payment.payer_name or '',
                    payment.payer_email or '',
                    payment.description or ''
                ])
            
            # Prepare response
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'payment_history_{filename_date}.csv'
            )
        
        else:  # JSON format
            payment_data = []
            for payment in payments:
                booking = payment.service_booking
                trip = booking.trip if booking else None
                
                payment_data.append({
                    'payment_id': payment.id,
                    'reference_number': payment.reference_number,
                    'transaction_id': payment.transaction_id,
                    'booking': {
                        'id': booking.id if booking else None,
                        'type': booking.booking_type if booking else None,
                        'trip_title': trip.title if trip else None
                    },
                    'amount': float(payment.amount),
                    'currency': payment.currency,
                    'status': payment.status,
                    'payment_method': payment.payment_method,
                    'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                    'processed_date': payment.processed_date.isoformat() if payment.processed_date else None,
                    'payer': {
                        'name': payment.payer_name,
                        'email': payment.payer_email,
                        'phone': payment.payer_phone
                    },
                    'description': payment.description
                })
            
            return send_file(
                io.BytesIO(jsonify(payment_data).get_data()),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'payment_history_{filename_date}.json'
            )
        
        # Log activity
        ActivityLog.log_action(
            action='payment_history_downloaded',
            user_id=current_user.id,
            entity_type='vendor',
            entity_id=vendor.id,
            description=f'Downloaded payment history ({file_format} format)',
            category='financial',
            metadata={
                'format': file_format,
                'record_count': len(payments),
                'date_range': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"Error downloading payment history: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'An error occurred while downloading payment history'
        }), 500


# ==================== INVOICE MANAGEMENT API ====================

@vendor_financials_bp.route('/vendor/financials/invoices/generate', methods=['POST'])
@roles_required('vendor')
def generate_invoice():
    """
    Generate invoice for a payment or booking
    Request Body:
        - payment_id: ID of the payment (required)
        - invoice_number: Custom invoice number (optional, auto-generated if not provided)
        - notes: Additional notes for the invoice (optional)
    """
    try:
        vendor = current_user.vendor_profile
        data = request.get_json()
        
        # Validate required fields
        if not data or 'payment_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing Required Field',
                'message': 'payment_id is required'
            }), 400
        
        payment_id = data.get('payment_id')
        
        # Fetch payment
        payment = ServicePayment.query.filter_by(
            id=payment_id,
            vendor_id=vendor.id
        ).first()
        
        if not payment:
            return jsonify({
                'success': False,
                'error': 'Payment Not Found',
                'message': 'Payment not found or does not belong to this vendor'
            }), 404
        
        # Check if payment is completed
        if payment.status != 'completed':
            return jsonify({
                'success': False,
                'error': 'Invalid Payment Status',
                'message': 'Can only generate invoices for completed payments'
            }), 400
        
        # Generate invoice number if not provided
        invoice_number = data.get('invoice_number')
        if not invoice_number:
            invoice_number = f"INV-{vendor.id}-{payment.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create invoice data structure
        booking = payment.service_booking
        trip = booking.trip if booking else None
        
        invoice_data = {
            'invoice_number': invoice_number,
            'invoice_date': datetime.now().isoformat(),
            'due_date': datetime.now().isoformat(),  # Immediate for completed payments
            'status': 'paid',
            'vendor': {
                'business_name': vendor.business_name,
                'contact_email': vendor.contact_email,
                'contact_phone': vendor.contact_phone,
                'address': vendor.full_address
            },
            'client': {
                'name': payment.payer_name,
                'email': payment.payer_email,
                'phone': payment.payer_phone
            },
            'booking_details': {
                'booking_id': booking.id if booking else None,
                'booking_type': booking.booking_type if booking else None,
                'trip_title': trip.title if trip else None,
                'service_description': booking.service_description if booking else None,
                'service_dates': {
                    'start': booking.service_start_date.isoformat() if booking and booking.service_start_date else None,
                    'end': booking.service_end_date.isoformat() if booking and booking.service_end_date else None
                }
            },
            'payment_details': {
                'payment_id': payment.id,
                'reference_number': payment.reference_number,
                'transaction_id': payment.transaction_id,
                'payment_method': payment.payment_method,
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None
            },
            'line_items': [
                {
                    'description': payment.description or f"{booking.booking_type.title()} Service" if booking else "Service",
                    'quantity': 1,
                    'unit_price': float(payment.amount),
                    'total': float(payment.amount)
                }
            ],
            'totals': {
                'subtotal': float(payment.amount),
                'tax': 0.0,  # Add tax calculation if needed
                'total': float(payment.amount),
                'amount_paid': float(payment.amount),
                'balance_due': 0.0
            },
            'currency': payment.currency,
            'notes': data.get('notes', '')
        }
        
        # Store invoice reference in payment (you may want to create a separate Invoice model)
        payment.receipt_number = invoice_number
        db.session.commit()
        
        # Log activity
        ActivityLog.log_action(
            action='invoice_generated',
            user_id=current_user.id,
            entity_type='payment',
            entity_id=payment.id,
            description=f'Invoice {invoice_number} generated for payment {payment.reference_number}',
            category='financial',
            metadata={
                'invoice_number': invoice_number,
                'amount': float(payment.amount)
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Invoice generated successfully',
            'data': {
                'invoice': invoice_data
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error generating invoice: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'An error occurred while generating invoice'
        }), 500


@vendor_financials_bp.route('/vendor/financials/invoices', methods=['GET'])
@roles_required('vendor')
def get_invoices():
    """
    Get all invoices for the vendor
    Query Parameters:
        - start_date: Filter from date
        - end_date: Filter to date
        - page: Page number
        - per_page: Items per page
    """
    try:
        vendor = current_user.vendor_profile
        
        # Parse parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Validate date range
        start_date, end_date, date_error = validate_date_range(start_date_str, end_date_str)
        if date_error:
            return jsonify({
                'success': False,
                'error': 'Invalid Date Range',
                'message': date_error
            }), 400
        
        # Query payments with invoice numbers (receipts)
        query = ServicePayment.query.filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.receipt_number.isnot(None),
            ServicePayment.status == 'completed'
        )
        
        if start_date:
            query = query.filter(ServicePayment.payment_date >= start_date)
        if end_date:
            query = query.filter(ServicePayment.payment_date <= end_date)
        
        pagination = query.order_by(ServicePayment.payment_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        invoices = []
        for payment in pagination.items:
            booking = payment.service_booking
            invoices.append({
                'invoice_number': payment.receipt_number,
                'payment_id': payment.id,
                'reference_number': payment.reference_number,
                'booking_type': booking.booking_type if booking else None,
                'amount': float(payment.amount),
                'currency': payment.currency,
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'payer_name': payment.payer_name,
                'status': 'paid'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'invoices': invoices,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': pagination.pages,
                    'total_items': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching invoices: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'An error occurred while fetching invoices'
        }), 500
    

@vendor_financials_bp.route('/vendor/financials/invoices/<int:payment_id>', methods=['GET'])
@roles_required('vendor')
def get_invoice_details(payment_id):
    """
    Get detailed invoice information for a specific payment
    """
    try:
        vendor = current_user.vendor_profile
        
        # Fetch payment
        payment = ServicePayment.query.filter_by(
            id=payment_id,
            vendor_id=vendor.id
        ).first()
        
        if not payment:
            return jsonify({
                'success': False,
                'error': 'Invoice Not Found',
                'message': 'Invoice not found or does not belong to this vendor'
            }), 404
        
        if not payment.receipt_number:
            return jsonify({
                'success': False,
                'error': 'No Invoice',
                'message': 'No invoice has been generated for this payment'
            }), 404
        
        # Build invoice details
        booking = payment.service_booking
        trip = booking.trip if booking else None
        
        invoice_details = {
            'invoice_number': payment.receipt_number,
            'invoice_date': payment.processed_date.isoformat() if payment.processed_date else payment.payment_date.isoformat(),
            'status': 'paid' if payment.status == 'completed' else payment.status,
            'vendor': {
                'business_name': vendor.business_name,
                'contact_email': vendor.contact_email,
                'contact_phone': vendor.contact_phone,
                'address': vendor.full_address,
                'license_number': vendor.license_number
            },
            'client': {
                'name': payment.payer_name,
                'email': payment.payer_email,
                'phone': payment.payer_phone
            },
            'booking_details': {
                'booking_id': booking.id if booking else None,
                'booking_type': booking.booking_type if booking else None,
                'trip_title': trip.title if trip else None,
                'service_description': booking.service_description if booking else None,
                'service_dates': {
                    'start': booking.service_start_date.isoformat() if booking and booking.service_start_date else None,
                    'end': booking.service_end_date.isoformat() if booking and booking.service_end_date else None
                }
            },
            'payment_details': {
                'payment_id': payment.id,
                'reference_number': payment.reference_number,
                'transaction_id': payment.transaction_id,
                'payment_method': payment.payment_method,
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'processed_date': payment.processed_date.isoformat() if payment.processed_date else None
            },
            'line_items': [
                {
                    'description': payment.description or f"{booking.booking_type.title()} Service" if booking else "Service",
                    'quantity': 1,
                    'unit_price': float(payment.amount),
                    'total': float(payment.amount)
                }
            ],
            'totals': {
                'subtotal': float(payment.amount),
                'tax': 0.0,
                'total': float(payment.amount),
                'amount_paid': float(payment.amount) if payment.status == 'completed' else 0.0,
                'balance_due': 0.0 if payment.status == 'completed' else float(payment.amount)
            },
            'currency': payment.currency
        }
        
        return jsonify({
            'success': True,
            'data': {
                'invoice': invoice_details
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching invoice details: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'An error occurred while fetching invoice details'
        }), 500


@vendor_financials_bp.route('/vendor/financials/payment-statistics', methods=['GET'])
@roles_required('vendor')
def get_payment_statistics():
    """
    Get detailed payment statistics
    Query Parameters:
        - period: Time period (week, month, quarter, year)
    """
    try:
        vendor = current_user.vendor_profile
        period = request.args.get('period', 'month')
        
        today = date.today()
        
        # Calculate date range based on period
        if period == 'week':
            start_date = today - timedelta(days=7)
        elif period == 'month':
            start_date = today - timedelta(days=30)
        elif period == 'quarter':
            start_date = today - timedelta(days=90)
        elif period == 'year':
            start_date = today - timedelta(days=365)
        else:
            start_date = today - timedelta(days=30)  # Default to month
        
        # Payment status breakdown
        status_breakdown = db.session.query(
            ServicePayment.status,
            func.count(ServicePayment.id).label('count'),
            func.sum(ServicePayment.amount).label('total_amount')
        ).filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.payment_date >= start_date
        ).group_by(ServicePayment.status).all()
        
        # Payment method breakdown
        method_breakdown = db.session.query(
            ServicePayment.payment_method,
            func.count(ServicePayment.id).label('count'),
            func.sum(
                db.case((ServicePayment.status == 'completed', ServicePayment.amount), else_=0)
            ).label('total_amount')
        ).filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.payment_date >= start_date
        ).group_by(ServicePayment.payment_method).all()
        
        # Average payment value
        avg_payment = db.session.query(
            func.avg(ServicePayment.amount)
        ).filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.status == 'completed',
            ServicePayment.payment_date >= start_date
        ).scalar() or 0
        
        # Payment success rate
        total_payments = db.session.query(
            func.count(ServicePayment.id)
        ).filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.payment_date >= start_date
        ).scalar() or 0
        
        successful_payments = db.session.query(
            func.count(ServicePayment.id)
        ).filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.status == 'completed',
            ServicePayment.payment_date >= start_date
        ).scalar() or 0
        
        success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'type': period,
                    'start_date': start_date.isoformat(),
                    'end_date': today.isoformat()
                },
                'status_breakdown': [
                    {
                        'status': item.status,
                        'count': item.count,
                        'total_amount': float(item.total_amount or 0)
                    }
                    for item in status_breakdown
                ],
                'payment_method_breakdown': [
                    {
                        'method': item.payment_method,
                        'count': item.count,
                        'total_amount': float(item.total_amount or 0)
                    }
                    for item in method_breakdown
                ],
                'metrics': {
                    'average_payment_value': float(avg_payment),
                    'total_payments': total_payments,
                    'successful_payments': successful_payments,
                    'success_rate': round(success_rate, 2),
                    'currency': 'KES'
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching payment statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'An error occurred while fetching payment statistics'
        }), 500
