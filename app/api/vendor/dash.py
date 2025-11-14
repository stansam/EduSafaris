from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app.extensions import db
from app.api import api_bp as vendor_dash_bp 
from app.utils.utils import roles_required
from app.models import ServiceBooking, ServicePayment
from sqlalchemy import func


@vendor_dash_bp.route('/vendor/dash/statistics', methods=['GET'])
@login_required
@roles_required('vendor')
def get_vendor_dash_statistics():
    """
    Get detailed vendor statistics
    
    Query Parameters:
        start_date: ISO date string (optional)
        end_date: ISO date string (optional)
    
    Returns:
        200: Statistics data
        400: Invalid parameters
        500: Server error
    """
    try:
        vendor = current_user.vendor_profile
        
        # Parse date parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date).date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid parameter',
                    'message': 'Invalid start_date format. Use ISO format (YYYY-MM-DD)'
                }), 400
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date).date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid parameter',
                    'message': 'Invalid end_date format. Use ISO format (YYYY-MM-DD)'
                }), 400
        
        # Calculate statistics
        bookings_query = vendor.service_bookings
        
        if start_date and end_date:
            # Filter bookings by date range if provided
            # Note: This assumes there's a created_at or booking_date field
            bookings_query = bookings_query.filter(
                db.and_(
                    db.func.date(vendor.service_bookings.created_at) >= start_date,
                    db.func.date(vendor.service_bookings.created_at) <= end_date
                )
            )
        
        total_bookings = bookings_query.count()
        confirmed_bookings = bookings_query.filter_by(status='confirmed').count()
        completed_bookings = bookings_query.filter_by(status='completed').count()
        cancelled_bookings = bookings_query.filter_by(status='cancelled').count()
        
        statistics = {
            'total_bookings': total_bookings,
            'confirmed_bookings': confirmed_bookings,
            'completed_bookings': completed_bookings,
            'cancelled_bookings': cancelled_bookings,
            'average_rating': vendor.average_rating,
            'total_reviews': vendor.total_reviews,
            'is_verified': vendor.is_verified,
            'capacity': vendor.capacity,
            'period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            }
        }
        
        return jsonify({
            'success': True,
            'data': statistics
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching vendor statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': 'An error occurred while fetching statistics'
        }), 500
    

@vendor_dash_bp.route('/vendor/financials/dashboard-summary', methods=['GET'])
@roles_required('vendor')
def get_vendor_dashboard_summary():
    """
    Get financial dashboard summary with key metrics
    """
    try:
        vendor = current_user.vendor_profile
        today = date.today()
        
        # Current month dates
        first_day_month = today.replace(day=1)
        
        # This year dates
        first_day_year = today.replace(month=1, day=1)
        
        # Overall metrics
        total_revenue = db.session.query(
            func.sum(ServicePayment.amount)
        ).filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.status == 'completed'
        ).scalar() or 0
        
        # This month metrics
        month_revenue = db.session.query(
            func.sum(ServicePayment.amount)
        ).filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.status == 'completed',
            ServicePayment.payment_date >= first_day_month
        ).scalar() or 0
        
        # This year metrics
        year_revenue = db.session.query(
            func.sum(ServicePayment.amount)
        ).filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.status == 'completed',
            ServicePayment.payment_date >= first_day_year
        ).scalar() or 0
        
        # Pending payments
        pending_amount = db.session.query(
            func.sum(ServicePayment.amount)
        ).filter(
            ServicePayment.vendor_id == vendor.id,
            ServicePayment.status == 'pending'
        ).scalar() or 0
        
        # Total bookings
        total_bookings = ServiceBooking.query.filter_by(vendor_id=vendor.id).count()
        
        # Active bookings
        active_bookings = ServiceBooking.query.filter(
            ServiceBooking.vendor_id == vendor.id,
            ServiceBooking.status.in_(['confirmed', 'in_progress'])
        ).count()
        
        # Completed bookings
        completed_bookings = ServiceBooking.query.filter_by(
            vendor_id=vendor.id,
            status='completed'
        ).count()
        
        # Recent payments (last 5)
        recent_payments = ServicePayment.query.filter_by(
            vendor_id=vendor.id
        ).order_by(ServicePayment.payment_date.desc()).limit(5).all()
        
        # Upcoming bookings (next 30 days)
        upcoming_date = today + timedelta(days=30)
        upcoming_bookings = ServiceBooking.query.filter(
            ServiceBooking.vendor_id == vendor.id,
            ServiceBooking.status == 'confirmed',
            ServiceBooking.service_start_date >= today,
            ServiceBooking.service_start_date <= upcoming_date
        ).order_by(ServiceBooking.service_start_date).limit(5).all()
        
        return jsonify({
            'success': True,
            'data': {
                'revenue_metrics': {
                    'total_revenue': float(total_revenue),
                    'month_revenue': float(month_revenue),
                    'year_revenue': float(year_revenue),
                    'pending_amount': float(pending_amount),
                    'currency': 'USD'
                },
                'booking_metrics': {
                    'total_bookings': total_bookings,
                    'active_bookings': active_bookings,
                    'completed_bookings': completed_bookings,
                    'completion_rate': round((completed_bookings / total_bookings * 100), 2) if total_bookings > 0 else 0
                },
                'vendor_info': {
                    'business_name': vendor.business_name,
                    'average_rating': vendor.average_rating,
                    'total_reviews': vendor.total_reviews,
                    'is_verified': vendor.is_verified
                },
                'recent_payments': [
                    {
                        'payment_id': p.id,
                        'reference_number': p.reference_number,
                        'amount': float(p.amount),
                        'status': p.status,
                        'payment_date': p.payment_date.isoformat() if p.payment_date else None,
                        'payer_name': p.payer_name
                    }
                    for p in recent_payments
                ],
                'upcoming_bookings': [
                    {
                        'booking_id': b.id,
                        'booking_type': b.booking_type,
                        'trip_title': b.trip.title if b.trip else None,
                        'service_start_date': b.service_start_date.isoformat() if b.service_start_date else None,
                        'amount': float(b.total_amount) if b.total_amount else None
                    }
                    for b in upcoming_bookings
                ]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching dashboard summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'An error occurred while fetching dashboard summary'
        }), 500