from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from datetime import datetime, date
from functools import wraps
import requests
import base64
from decimal import Decimal

from app.models import Vendor, ServiceBooking as Booking, ServicePayment as Payment, Trip, ActivityLog, Review
from app.extensions import db
from app.api import api_bp as teacher_vendor_bp
from app.utils.utils import roles_required

# Utility function for error responses
def error_response(message, status_code=400, details=None):
    response = {'error': message}
    if details:
        response['details'] = details
    return jsonify(response), status_code


# Utility function for success responses
def success_response(data=None, message=None, status_code=200):
    response = {'success': True}
    if message:
        response['message'] = message
    if data is not None:
        response['data'] = data
    return jsonify(response), status_code


@teacher_vendor_bp.route('/teacher/vendors/search', methods=['GET'])
@login_required
@roles_required('teacher')
def search_vendors():
    """
    Search and filter vendors
    Query params: q (search term), type, city, verified, min_rating, page, per_page
    """
    try:
        # Get query parameters
        search_term = request.args.get('q', '').strip()
        business_type = request.args.get('type', '').strip()
        city = request.args.get('city', '').strip()
        verified_only = request.args.get('verified', 'false').lower() == 'true'
        min_rating = request.args.get('min_rating', type=float)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        
        # Base query - only active vendors
        query = Vendor.query.filter_by(is_active=True)
        
        # Apply filters
        if search_term:
            query = query.filter(
                or_(
                    Vendor.business_name.ilike(f'%{search_term}%'),
                    Vendor.description.ilike(f'%{search_term}%'),
                    Vendor.business_type.ilike(f'%{search_term}%')
                )
            )
        
        if business_type:
            query = query.filter(Vendor.business_type.ilike(f'%{business_type}%'))
        
        if city:
            query = query.filter(Vendor.city.ilike(f'%{city}%'))
        
        if verified_only:
            query = query.filter_by(is_verified=True)
        
        if min_rating:
            query = query.filter(Vendor.average_rating >= min_rating)
        
        # Order by rating and name
        query = query.order_by(Vendor.average_rating.desc(), Vendor.business_name)
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Serialize vendors
        vendors = [vendor.serialize() for vendor in pagination.items]
        
        # Log search activity
        ActivityLog.log_action(
            action='vendor_search',
            user_id=current_user.id,
            description=f"Searched vendors: {search_term or 'all'}",
            category='vendor',
            metadata={'search_term': search_term, 'filters': {
                'type': business_type,
                'city': city,
                'verified': verified_only,
                'min_rating': min_rating
            }}
        )
        
        return success_response({
            'vendors': vendors,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error searching vendors: {str(e)}")
        return error_response('Failed to search vendors', 500)


@teacher_vendor_bp.route('/teacher/vendors/<int:vendor_id>', methods=['GET'])
@login_required
@roles_required('teacher')
def get_vendor_profile(vendor_id):
    """Get detailed vendor profile"""
    try:
        vendor = Vendor.query.get(vendor_id)
        
        if not vendor:
            return error_response('Vendor not found', 404)
        
        if not vendor.is_active:
            return error_response('Vendor is not active', 400)
        
        # Get vendor data
        vendor_data = vendor.serialize()
        
        # Add additional stats
        vendor_data['stats'] = {
            'total_bookings': vendor.bookings.filter_by(status='completed').count(),
            'pending_bookings': vendor.bookings.filter_by(status='pending').count(),
            'confirmed_bookings': vendor.bookings.filter_by(status='confirmed').count()
        }
        
        # Get recent reviews
        recent_reviews = Review.get_published_reviews('vendor', vendor_id, limit=5)
        vendor_data['recent_reviews'] = [review.serialize() for review in recent_reviews]
        
        # Get documents if verified
        if vendor.is_verified:
            from app.models import Document
            documents = Document.get_vendor_documents(vendor_id)
            vendor_data['documents'] = [
                {
                    'id': doc.id,
                    'title': doc.title,
                    'document_type': doc.document_type,
                    'is_verified': doc.is_verified,
                    'expiry_date': doc.expiry_date.isoformat() if doc.expiry_date else None,
                    'is_expired': doc.is_expired
                } for doc in documents
            ]
        
        # Log activity
        ActivityLog.log_action(
            action='vendor_profile_viewed',
            user_id=current_user.id,
            entity_type='vendor',
            entity_id=vendor_id,
            description=f"Viewed vendor profile: {vendor.business_name}",
            category='vendor'
        )
        
        return success_response(vendor_data)
        
    except Exception as e:
        current_app.logger.error(f"Error fetching vendor profile: {str(e)}")
        return error_response('Failed to fetch vendor profile', 500)


@teacher_vendor_bp.route('/teacher/vendors/<int:vendor_id>/quote', methods=['POST'])
@login_required
@roles_required('teacher')
def request_vendor_quote(vendor_id):
    """Request a quote from a vendor"""
    try:
        # Validate vendor
        vendor = Vendor.query.get(vendor_id)
        if not vendor:
            return error_response('Vendor not found', 404)
        
        if not vendor.is_active:
            return error_response('Vendor is not active', 400)
        
        # Get request data
        data = request.get_json()
        if not data:
            return error_response('No data provided')
        
        # Validate required fields
        required_fields = ['trip_id', 'booking_type', 'service_description']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return error_response('Missing required fields', 400, {'missing': missing_fields})
        
        trip_id = data.get('trip_id')
        booking_type = data.get('booking_type')
        service_description = data.get('service_description')
        special_requirements = data.get('special_requirements')
        notes = data.get('notes')
        
        # Validate trip
        trip = Trip.query.get(trip_id)
        if not trip:
            return error_response('Trip not found', 404)
        
        if trip.organizer_id != current_user.id:
            return error_response('You can only request quotes for your own trips', 403)
        
        # Validate booking type
        valid_types = ['transportation', 'accommodation', 'activity']
        if booking_type not in valid_types:
            return error_response('Invalid booking type', 400, {'valid_types': valid_types})
        
        # Check vendor availability if dates provided
        if trip.start_date and trip.end_date:
            if not vendor.is_available(trip.start_date, trip.end_date):
                return error_response('Vendor is not available for the selected dates', 400)
        
        # Create quote request (as pending booking)
        booking = Booking(
            status='pending',
            booking_type=booking_type,
            service_description=service_description,
            special_requirements=special_requirements,
            notes=notes,
            trip_id=trip_id,
            vendor_id=vendor_id
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Log activity
        ActivityLog.log_booking(booking, current_user.id, 'quote_requested')
        
        # TODO: Send notification to vendor
        from app.models import Notification
        Notification.create_notification(
            recipient_id=vendor.user_id,
            sender_id=current_user.id,
            notification_type='quote_request',
            title='New Quote Request',
            message=f'{current_user.full_name} requested a quote for {trip.title}',
            entity_type='booking',
            entity_id=booking.id
        )
        
        return success_response(
            booking.serialize(),
            'Quote request sent successfully',
            201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error requesting quote: {str(e)}")
        return error_response('Failed to request quote', 500)


@teacher_vendor_bp.route('/teacher/vendors/bookings', methods=['POST'])
@login_required
@roles_required('teacher')
def create_booking():
    """Create a new vendor booking"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided')
        
        # Validate required fields
        required_fields = ['vendor_id', 'trip_id', 'booking_type', 'service_description', 'quoted_amount']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return error_response('Missing required fields', 400, {'missing': missing_fields})
        
        vendor_id = data.get('vendor_id')
        trip_id = data.get('trip_id')
        booking_type = data.get('booking_type')
        service_description = data.get('service_description')
        quoted_amount = data.get('quoted_amount')
        special_requirements = data.get('special_requirements')
        notes = data.get('notes')
        
        # Validate vendor
        vendor = Vendor.query.get(vendor_id)
        if not vendor or not vendor.is_active:
            return error_response('Vendor not found or inactive', 404)
        
        # Validate trip
        trip = Trip.query.get(trip_id)
        if not trip:
            return error_response('Trip not found', 404)
        
        if trip.organizer_id != current_user.id:
            return error_response('You can only create bookings for your own trips', 403)
        
        # Validate quoted amount
        try:
            quoted_amount = Decimal(str(quoted_amount))
            if quoted_amount <= 0:
                return error_response('Quoted amount must be greater than zero', 400)
        except (ValueError, TypeError):
            return error_response('Invalid quoted amount', 400)
        
        # Check availability
        if trip.start_date and trip.end_date:
            if not vendor.is_available(trip.start_date, trip.end_date):
                return error_response('Vendor is not available for the selected dates', 400)
        
        # Create booking
        booking = Booking(
            status='pending',
            booking_type=booking_type,
            service_description=service_description,
            special_requirements=special_requirements,
            notes=notes,
            quoted_amount=quoted_amount,
            trip_id=trip_id,
            vendor_id=vendor_id
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Log activity
        ActivityLog.log_booking(booking, current_user.id, 'created')
        
        # Notify vendor
        from app.models import Notification
        Notification.create_notification(
            recipient_id=vendor.user_id,
            sender_id=current_user.id,
            notification_type='booking_created',
            title='New Booking Request',
            message=f'{current_user.full_name} created a booking for {trip.title}',
            entity_type='booking',
            entity_id=booking.id
        )
        
        return success_response(
            booking.serialize(),
            'Booking created successfully',
            201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating booking: {str(e)}")
        return error_response('Failed to create booking', 500)


@teacher_vendor_bp.route('/teacher/vendors/bookings/<int:booking_id>/confirm', methods=['PUT'])
@login_required
@roles_required('teacher')
def confirm_booking(booking_id):
    """Confirm a vendor booking"""
    try:
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return error_response('Booking not found', 404)
        
        # Verify ownership
        if booking.trip.organizer_id != current_user.id:
            return error_response('You can only confirm your own bookings', 403)
        
        if not booking.can_be_cancelled():
            return error_response(f'Cannot confirm booking with status: {booking.status}', 400)
        
        # Get final amount if provided
        data = request.get_json() or {}
        final_amount = data.get('final_amount')
        
        if final_amount:
            try:
                final_amount = Decimal(str(final_amount))
                if final_amount <= 0:
                    return error_response('Final amount must be greater than zero', 400)
            except (ValueError, TypeError):
                return error_response('Invalid final amount', 400)
        
        # Confirm booking
        booking.confirm_booking(final_amount=final_amount)
        
        # Log activity
        ActivityLog.log_booking(booking, current_user.id, 'confirmed')
        
        # Notify vendor
        from app.models import Notification
        Notification.create_notification(
            recipient_id=booking.vendor.user_id,
            sender_id=current_user.id,
            notification_type='booking_confirmed',
            title='Booking Confirmed',
            message=f'Booking for {booking.trip.title} has been confirmed',
            entity_type='booking',
            entity_id=booking.id
        )
        
        return success_response(
            booking.serialize(),
            'Booking confirmed successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error confirming booking: {str(e)}")
        return error_response('Failed to confirm booking', 500)


@teacher_vendor_bp.route('/teacher/vendors/bookings/<int:booking_id>/cancel', methods=['PUT'])
@login_required
@roles_required('teacher')
def cancel_booking(booking_id):
    """Cancel a vendor booking"""
    try:
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return error_response('Booking not found', 404)
        
        # Verify ownership
        if booking.trip.organizer_id != current_user.id:
            return error_response('You can only cancel your own bookings', 403)
        
        if not booking.can_be_cancelled():
            return error_response(f'Cannot cancel booking with status: {booking.status}', 400)
        
        # Get cancellation reason
        data = request.get_json() or {}
        cancellation_reason = data.get('reason', 'No reason provided')
        
        # Update booking status
        old_status = booking.status
        booking.status = 'cancelled'
        booking.notes = f"{booking.notes or ''}\n\nCancelled: {cancellation_reason}".strip()
        db.session.commit()
        
        # Log activity
        ActivityLog.log_action(
            action='booking_cancelled',
            user_id=current_user.id,
            entity_type='booking',
            entity_id=booking.id,
            description=f"Booking cancelled: {booking.booking_type}",
            category='booking',
            trip_id=booking.trip_id,
            old_values={'status': old_status},
            new_values={'status': 'cancelled', 'reason': cancellation_reason}
        )
        
        # Notify vendor
        from app.models import Notification
        Notification.create_notification(
            recipient_id=booking.vendor.user_id,
            sender_id=current_user.id,
            notification_type='booking_cancelled',
            title='Booking Cancelled',
            message=f'Booking for {booking.trip.title} has been cancelled',
            entity_type='booking',
            entity_id=booking.id
        )
        
        return success_response(
            booking.serialize(),
            'Booking cancelled successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error cancelling booking: {str(e)}")
        return error_response('Failed to cancel booking', 500)


@teacher_vendor_bp.route('/teacher/vendors/bookings/<int:booking_id>/rate', methods=['POST'])
@login_required
@roles_required('teacher')
def rate_vendor(booking_id):
    """Rate a vendor after service completion"""
    try:
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return error_response('Booking not found', 404)
        
        # Verify ownership
        if booking.trip.organizer_id != current_user.id:
            return error_response('You can only rate your own bookings', 403)
        
        if booking.status != 'completed':
            return error_response('Can only rate completed bookings', 400)
        
        if booking.rating:
            return error_response('Booking has already been rated', 400)
        
        # Get rating data
        data = request.get_json()
        if not data:
            return error_response('No data provided')
        
        rating = data.get('rating')
        review_text = data.get('review', '').strip()
        title = data.get('title', '').strip()
        
        # Validate rating
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return error_response('Rating must be an integer between 1 and 5', 400)
        
        # Optional detailed ratings
        value_rating = data.get('value_rating')
        safety_rating = data.get('safety_rating')
        organization_rating = data.get('organization_rating')
        communication_rating = data.get('communication_rating')
        
        # Validate detailed ratings if provided
        for detail_rating in [value_rating, safety_rating, organization_rating, communication_rating]:
            if detail_rating is not None:
                if not isinstance(detail_rating, int) or detail_rating < 1 or detail_rating > 5:
                    return error_response('Detailed ratings must be integers between 1 and 5', 400)
        
        # Add rating to booking
        booking.add_review(rating, review_text)
        
        # Create full review entry
        review = Review.create_vendor_review(
            vendor_id=booking.vendor_id,
            reviewer_id=current_user.id,
            rating=rating,
            title=title or f'Review for {booking.vendor.business_name}',
            review_text=review_text,
            booking_id=booking_id,
            value_rating=value_rating,
            safety_rating=safety_rating,
            organization_rating=organization_rating,
            communication_rating=communication_rating
        )
        
        # Auto-approve if teacher is verified
        if current_user.is_verified:
            review.approve(current_user.id, 'Auto-approved for verified teacher')
        
        # Log activity
        ActivityLog.log_action(
            action='vendor_rated',
            user_id=current_user.id,
            entity_type='review',
            entity_id=review.id,
            description=f"Rated vendor {booking.vendor.business_name}: {rating} stars",
            category='vendor',
            trip_id=booking.trip_id,
            new_values={'rating': rating, 'vendor_id': booking.vendor_id}
        )
        
        return success_response({
            'booking': booking.serialize(),
            'review': review.serialize()
        }, 'Rating submitted successfully', 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rating vendor: {str(e)}")
        return error_response('Failed to submit rating', 500)


@teacher_vendor_bp.route('/teacher/vendors/bookings/<int:booking_id>/payment/mpesa', methods=['POST'])
@login_required
@roles_required('teacher')
def initiate_mpesa_payment(booking_id):
    """Initiate M-Pesa payment for a booking"""
    try:
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return error_response('Booking not found', 404)
        
        # Verify ownership
        if booking.trip.organizer_id != current_user.id:
            return error_response('You can only pay for your own bookings', 403)
        
        if booking.status not in ['confirmed', 'pending']:
            return error_response(f'Cannot pay for booking with status: {booking.status}', 400)
        
        # Get payment data
        data = request.get_json()
        if not data:
            return error_response('No data provided')
        
        phone_number = data.get('phone_number', '').strip()
        amount = data.get('amount')
        
        if not phone_number:
            return error_response('Phone number is required')
        
        # Validate phone number format (Kenyan)
        if not phone_number.startswith('254') or len(phone_number) != 12:
            return error_response('Invalid phone number format. Use 254XXXXXXXXX')
        
        # Validate amount
        if not amount:
            amount = float(booking.total_amount)
        else:
            try:
                amount = float(amount)
                if amount <= 0:
                    return error_response('Amount must be greater than zero', 400)
            except (ValueError, TypeError):
                return error_response('Invalid amount', 400)
        
        # Create payment record
        payment = Payment(
            amount=Decimal(str(amount)),
            currency='KES',
            payment_method='mpesa',
            status='pending',
            description=f'Payment for {booking.booking_type} - {booking.trip.title}',
            payer_name=current_user.full_name,
            payer_email=current_user.email,
            payer_phone=phone_number,
            trip_id=booking.trip_id,
            booking_id=booking_id
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # Initiate M-Pesa STK Push
        mpesa_response = initiate_mpesa_stk_push(
            phone_number=phone_number,
            amount=int(amount),
            account_reference=f'BOOKING-{booking_id}',
            transaction_desc=payment.description
        )
        
        if mpesa_response.get('success'):
            # Update payment with M-Pesa details
            payment.transaction_id = mpesa_response.get('CheckoutRequestID')
            payment.status = 'processing'
            payment.processor_response = mpesa_response
            db.session.commit()
            
            # Log activity
            ActivityLog.log_payment(payment, current_user.id)
            
            return success_response({
                'payment': payment.serialize(),
                'checkout_request_id': mpesa_response.get('CheckoutRequestID'),
                'message': 'Payment initiated. Please check your phone to complete the transaction.'
            }, 'Payment initiated successfully', 201)
        else:
            # Payment initiation failed
            payment.mark_failed(
                failure_reason=mpesa_response.get('error', 'M-Pesa initiation failed'),
                processor_response=mpesa_response
            )
            
            return error_response(
                'Failed to initiate M-Pesa payment',
                400,
                {'reason': mpesa_response.get('error')}
            )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error initiating M-Pesa payment: {str(e)}")
        return error_response('Failed to initiate payment', 500)


def initiate_mpesa_stk_push(phone_number, amount, account_reference, transaction_desc):
    """
    Initiate M-Pesa STK Push
    This is a helper function that integrates with Safaricom's Daraja API
    """
    try:
        # Get M-Pesa credentials from config
        consumer_key = current_app.config.get('MPESA_CONSUMER_KEY')
        consumer_secret = current_app.config.get('MPESA_CONSUMER_SECRET')
        business_shortcode = current_app.config.get('MPESA_SHORTCODE')
        passkey = current_app.config.get('MPESA_PASSKEY')
        callback_url = current_app.config.get('MPESA_CALLBACK_URL')
        
        if not all([consumer_key, consumer_secret, business_shortcode, passkey, callback_url]):
            current_app.logger.error('M-Pesa configuration incomplete')
            return {'success': False, 'error': 'Payment service not configured'}
        
        # Get access token
        auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        # Use production URL in production: 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        
        auth_response = requests.get(
            auth_url,
            auth=(consumer_key, consumer_secret),
            timeout=30
        )
        
        if auth_response.status_code != 200:
            current_app.logger.error(f'M-Pesa auth failed: {auth_response.text}')
            return {'success': False, 'error': 'Authentication failed'}
        
        access_token = auth_response.json().get('access_token')
        
        # Generate timestamp and password
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f'{business_shortcode}{passkey}{timestamp}'
        password = base64.b64encode(password_str.encode()).decode('utf-8')
        
        # STK Push request
        stk_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        # Use production URL in production: 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': business_shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': amount,
            'PartyA': phone_number,
            'PartyB': business_shortcode,
            'PhoneNumber': phone_number,
            'CallBackURL': callback_url,
            'AccountReference': account_reference,
            'TransactionDesc': transaction_desc
        }
        
        stk_response = requests.post(
            stk_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response_data = stk_response.json()
        
        if stk_response.status_code == 200 and response_data.get('ResponseCode') == '0':
            return {
                'success': True,
                'CheckoutRequestID': response_data.get('CheckoutRequestID'),
                'MerchantRequestID': response_data.get('MerchantRequestID'),
                'ResponseDescription': response_data.get('ResponseDescription')
            }
        else:
            current_app.logger.error(f'M-Pesa STK Push failed: {response_data}')
            return {
                'success': False,
                'error': response_data.get('errorMessage', 'STK Push failed'),
                'response': response_data
            }
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f'M-Pesa request error: {str(e)}')
        return {'success': False, 'error': 'Network error occurred'}
    except Exception as e:
        current_app.logger.error(f'M-Pesa error: {str(e)}')
        return {'success': False, 'error': 'Payment initiation failed'}


@teacher_vendor_bp.route('/teacher/vendors/payments/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """
    M-Pesa payment callback endpoint
    This endpoint receives payment confirmation from Safaricom
    """
    try:
        data = request.get_json()
        current_app.logger.info(f'M-Pesa callback received: {data}')
        
        # Extract callback data
        result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
        result_desc = data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')
        checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
        
        # Find payment by transaction ID
        payment = Payment.query.filter_by(transaction_id=checkout_request_id).first()
        
        if not payment:
            current_app.logger.warning(f'Payment not found for CheckoutRequestID: {checkout_request_id}')
            return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})
        
        if result_code == 0:
            # Payment successful
            callback_metadata = data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [])
            
            # Extract metadata
            mpesa_receipt = None
            phone_number = None
            amount = None
            
            for item in callback_metadata:
                if item.get('Name') == 'MpesaReceiptNumber':
                    mpesa_receipt = item.get('Value')
                elif item.get('Name') == 'PhoneNumber':
                    phone_number = item.get('Value')
                elif item.get('Name') == 'Amount':
                    amount = item.get('Value')
            
            # Update payment status
            payment.mark_completed(
                transaction_id=mpesa_receipt or checkout_request_id,
                processor_response=data
            )
            
            # Update booking status if confirmed
            if payment.booking and payment.booking.status == 'pending':
                payment.booking.status = 'confirmed'
                payment.booking.confirmed_date = datetime.now()
                db.session.commit()
            
            # Log activity
            ActivityLog.log_action(
                action='payment_completed',
                user_id=payment.booking.trip.organizer_id if payment.booking else None,
                entity_type='payment',
                entity_id=payment.id,
                description=f"M-Pesa payment completed: {amount} KES",
                category='payment',
                trip_id=payment.trip_id,
                new_values={
                    'amount': amount,
                    'receipt': mpesa_receipt,
                    'phone': phone_number
                },
                status='success'
            )
            
            # Notify teacher
            if payment.booking:
                from app.models import Notification
                Notification.create_notification(
                    recipient_id=payment.booking.trip.organizer_id,
                    notification_type='payment_completed',
                    title='Payment Successful',
                    message=f'Payment of KES {amount} completed successfully',
                    entity_type='payment',
                    entity_id=payment.id
                )
                
                # Notify vendor
                Notification.create_notification(
                    recipient_id=payment.booking.vendor.user_id,
                    notification_type='payment_received',
                    title='Payment Received',
                    message=f'Payment of KES {amount} received for booking',
                    entity_type='booking',
                    entity_id=payment.booking_id
                )
        
        else:
            # Payment failed
            payment.mark_failed(
                failure_reason=result_desc,
                processor_response=data
            )
            
            # Log activity
            ActivityLog.log_action(
                action='payment_failed',
                user_id=payment.booking.trip.organizer_id if payment.booking else None,
                entity_type='payment',
                entity_id=payment.id,
                description=f"M-Pesa payment failed: {result_desc}",
                category='payment',
                trip_id=payment.trip_id,
                new_values={'error': result_desc},
                status='failed',
                error_message=result_desc
            )
            
            # Notify teacher
            if payment.booking:
                from app.models import Notification
                Notification.create_notification(
                    recipient_id=payment.booking.trip.organizer_id,
                    notification_type='payment_failed',
                    title='Payment Failed',
                    message=f'Payment failed: {result_desc}',
                    entity_type='payment',
                    entity_id=payment.id
                )
        
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})
        
    except Exception as e:
        current_app.logger.error(f'M-Pesa callback error: {str(e)}')
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Failed'})


@teacher_vendor_bp.route('/teacher/vendors/bookings/<int:booking_id>/payment/status', methods=['GET'])
@login_required
@roles_required('teacher')
def check_payment_status(booking_id):
    """Check payment status for a booking"""
    try:
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return error_response('Booking not found', 404)
        
        # Verify ownership
        if booking.trip.organizer_id != current_user.id:
            return error_response('Access denied', 403)
        
        # Get all payments for this booking
        payments = booking.payments.order_by(Payment.created_at.desc()).all()
        
        payment_data = {
            'booking_id': booking_id,
            'booking_status': booking.status,
            'total_amount': float(booking.total_amount) if booking.total_amount else 0,
            'payments': [payment.serialize() for payment in payments],
            'total_paid': sum(float(p.amount) for p in payments if p.status == 'completed'),
            'pending_amount': float(booking.total_amount or 0) - sum(float(p.amount) for p in payments if p.status == 'completed')
        }
        
        return success_response(payment_data)
        
    except Exception as e:
        current_app.logger.error(f"Error checking payment status: {str(e)}")
        return error_response('Failed to check payment status', 500)


@teacher_vendor_bp.route('/teacher/vendors/bookings', methods=['GET'])
@login_required
@roles_required('teacher')
def get_teacher_bookings():
    """Get all bookings for the current teacher"""
    try:
        # Get query parameters
        status = request.args.get('status', '').strip()
        trip_id = request.args.get('trip_id', type=int)
        vendor_id = request.args.get('vendor_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Base query - bookings for teacher's trips
        query = Booking.query.join(Trip).filter(Trip.organizer_id == current_user.id)
        
        # Apply filters
        if status:
            query = query.filter(Booking.status == status)
        
        if trip_id:
            query = query.filter(Booking.trip_id == trip_id)
        
        if vendor_id:
            query = query.filter(Booking.vendor_id == vendor_id)
        
        # Order by most recent
        query = query.order_by(Booking.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Serialize bookings
        bookings = [booking.serialize() for booking in pagination.items]
        
        return success_response({
            'bookings': bookings,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching bookings: {str(e)}")
        return error_response('Failed to fetch bookings', 500)


@teacher_vendor_bp.route('/teacher/vendors/bookings/<int:booking_id>', methods=['GET'])
@login_required
@roles_required('teacher')
def get_booking_details(booking_id):
    """Get detailed information about a specific booking"""
    try:
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return error_response('Booking not found', 404)
        
        # Verify ownership
        if booking.trip.organizer_id != current_user.id:
            return error_response('Access denied', 403)
        
        # Get booking data
        booking_data = booking.serialize()
        
        # Add payment information
        payments = booking.payments.order_by(Payment.created_at.desc()).all()
        booking_data['payments'] = [payment.serialize() for payment in payments]
        booking_data['total_paid'] = sum(float(p.amount) for p in payments if p.status == 'completed')
        booking_data['balance'] = float(booking.total_amount or 0) - booking_data['total_paid']
        
        # Add activity logs
        from app.models import ActivityLog
        logs = ActivityLog.get_entity_activity('booking', booking_id, limit=20)
        booking_data['activity_logs'] = [log.serialize() for log in logs]
        
        return success_response(booking_data)
        
    except Exception as e:
        current_app.logger.error(f"Error fetching booking details: {str(e)}")
        return error_response('Failed to fetch booking details', 500)


@teacher_vendor_bp.route('/teacher/vendors/availability', methods=['POST'])
@login_required
@roles_required('teacher')
def check_vendor_availability():
    """Check vendor availability for specific dates"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided')
        
        vendor_id = data.get('vendor_id')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        
        if not all([vendor_id, start_date_str, end_date_str]):
            return error_response('vendor_id, start_date, and end_date are required')
        
        # Validate vendor
        vendor = Vendor.query.get(vendor_id)
        if not vendor or not vendor.is_active:
            return error_response('Vendor not found or inactive', 404)
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return error_response('Invalid date format. Use YYYY-MM-DD')
        
        if start_date > end_date:
            return error_response('Start date must be before end date')
        
        if start_date < date.today():
            return error_response('Start date cannot be in the past')
        
        # Check availability
        is_available = vendor.is_available(start_date, end_date)
        
        # Get conflicting bookings if not available
        conflicting_bookings = []
        if not is_available:
            conflicts = Booking.query.join(Trip).filter(
                Booking.vendor_id == vendor_id,
                Booking.status.in_(['confirmed', 'in_progress']),
                db.not_(
                    db.or_(
                        Trip.end_date < start_date,
                        Trip.start_date > end_date
                    )
                )
            ).all()
            
            conflicting_bookings = [{
                'booking_id': b.id,
                'trip_title': b.trip.title,
                'start_date': b.trip.start_date.isoformat() if b.trip.start_date else None,
                'end_date': b.trip.end_date.isoformat() if b.trip.end_date else None,
                'status': b.status
            } for b in conflicts]
        
        return success_response({
            'vendor_id': vendor_id,
            'vendor_name': vendor.business_name,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'is_available': is_available,
            'conflicting_bookings': conflicting_bookings
        })
        
    except Exception as e:
        current_app.logger.error(f"Error checking availability: {str(e)}")
        return error_response('Failed to check availability', 500)


@teacher_vendor_bp.route('/teacher/vendors/stats', methods=['GET'])
@login_required
@roles_required('teacher')
def get_vendor_statistics():
    """Get vendor management statistics for the teacher"""
    try:
        # Get all bookings for teacher's trips
        all_bookings = Booking.query.join(Trip).filter(
            Trip.organizer_id == current_user.id
        ).all()
        
        # Calculate statistics
        stats = {
            'total_bookings': len(all_bookings),
            'by_status': {
                'pending': len([b for b in all_bookings if b.status == 'pending']),
                'confirmed': len([b for b in all_bookings if b.status == 'confirmed']),
                'in_progress': len([b for b in all_bookings if b.status == 'in_progress']),
                'completed': len([b for b in all_bookings if b.status == 'completed']),
                'cancelled': len([b for b in all_bookings if b.status == 'cancelled'])
            },
            'by_type': {},
            'total_spent': 0,
            'pending_payments': 0,
            'unique_vendors': len(set(b.vendor_id for b in all_bookings)),
            'average_rating': 0
        }
        
        # Calculate by type and financials
        type_counts = {}
        total_spent = Decimal('0')
        pending_amount = Decimal('0')
        rated_bookings = []
        
        for booking in all_bookings:
            # Count by type
            type_counts[booking.booking_type] = type_counts.get(booking.booking_type, 0) + 1
            
            # Calculate financials
            if booking.status == 'completed' and booking.total_amount:
                completed_payments = sum(
                    p.amount for p in booking.payments.all() 
                    if p.status == 'completed'
                )
                total_spent += completed_payments
            
            if booking.status in ['confirmed', 'in_progress'] and booking.total_amount:
                paid_amount = sum(
                    p.amount for p in booking.payments.all() 
                    if p.status == 'completed'
                )
                pending_amount += (booking.total_amount - paid_amount)
            
            # Collect ratings
            if booking.rating:
                rated_bookings.append(booking.rating)
        
        stats['by_type'] = type_counts
        stats['total_spent'] = float(total_spent)
        stats['pending_payments'] = float(pending_amount)
        stats['average_rating'] = round(sum(rated_bookings) / len(rated_bookings), 2) if rated_bookings else 0
        
        return success_response(stats)
        
    except Exception as e:
        current_app.logger.error(f"Error fetching vendor statistics: {str(e)}")
        return error_response('Failed to fetch statistics', 500)