from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
from sqlalchemy import or_, and_

from app.extensions import db
from app.vendor.models import Vendor, Advertisement, Booking
from app.models.user import User
from app.models.trip import Trip

vendors = Blueprint('vendors', __name__, url_prefix='/vendors')

@vendors.route('/')
def vendor_directory():
    """Vendor directory with search and filters"""
    # Get filter parameters
    business_type = request.args.get('type', '')
    location = request.args.get('location', '')
    min_rating = request.args.get('min_rating', 0, type=float)
    search = request.args.get('search', '')
    verified_only = request.args.get('verified', False, type=bool)
    
    # Base query for active vendors
    query = Vendor.query.filter(Vendor.is_active == True)
    
    # Apply filters
    if business_type:
        query = query.filter(Vendor.business_type == business_type)
    
    if location:
        query = query.filter(or_(
            Vendor.city.ilike(f'%{location}%'),
            Vendor.state.ilike(f'%{location}%')
        ))
    
    if min_rating > 0:
        query = query.filter(Vendor.average_rating >= min_rating)
    
    if search:
        query = query.filter(or_(
            Vendor.business_name.ilike(f'%{search}%'),
            Vendor.description.ilike(f'%{search}%')
        ))
    
    if verified_only:
        query = query.filter(Vendor.is_verified == True)
    
    # Order by rating and verification status
    vendors_list = query.order_by(
        Vendor.is_verified.desc(),
        Vendor.average_rating.desc()
    ).all()
    
    # Get unique business types for filter dropdown
    business_types = db.session.query(Vendor.business_type).distinct().all()
    business_types = [bt[0] for bt in business_types if bt[0]]
    
    return render_template('vendors/directory.html',
                         vendors=vendors_list,
                         business_types=business_types,
                         filters={
                             'type': business_type,
                             'location': location,
                             'min_rating': min_rating,
                             'search': search,
                             'verified_only': verified_only
                         })

@vendors.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Vendor registration"""
    # Check if user already has a vendor profile
    existing_vendor = Vendor.query.filter_by(user_id=current_user.id).first()
    if existing_vendor:
        flash('You already have a vendor profile.', 'info')
        return redirect(url_for('vendors.profile', id=existing_vendor.id))
    
    if request.method == 'POST':
        try:
            # Create new vendor profile
            vendor = Vendor(
                business_name=request.form['business_name'],
                business_type=request.form['business_type'],
                description=request.form['description'],
                contact_email=request.form['contact_email'],
                contact_phone=request.form['contact_phone'],
                website=request.form.get('website'),
                address_line1=request.form['address_line1'],
                address_line2=request.form.get('address_line2'),
                city=request.form['city'],
                state=request.form['state'],
                postal_code=request.form['postal_code'],
                country=request.form['country'],
                license_number=request.form.get('license_number'),
                insurance_details=request.form.get('insurance_details'),
                capacity=request.form.get('capacity', type=int),
                base_price=request.form.get('base_price', type=float),
                price_per_person=request.form.get('price_per_person', type=float),
                pricing_notes=request.form.get('pricing_notes'),
                user_id=current_user.id
            )
            
            # Handle specializations as array
            specializations = request.form.getlist('specializations')
            vendor.specializations = specializations
            
            db.session.add(vendor)
            db.session.commit()
            
            flash('Vendor profile created successfully! Upload verification documents to get verified.', 'success')
            return redirect(url_for('vendors.profile', id=vendor.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating vendor profile: {str(e)}', 'error')
    
    business_types = [
        'transportation', 'accommodation', 'activities', 
        'catering', 'equipment', 'guides', 'insurance'
    ]
    
    return render_template('vendors/register.html', business_types=business_types)

@vendors.route('/<int:id>')
def profile(id):
    """Vendor profile and active advertisements"""
    vendor = Vendor.query.get_or_404(id)
    
    # Get active advertisements
    active_ads = Advertisement.query.filter(
        Advertisement.vendor_id == id,
        Advertisement.is_currently_active == True
    ).all()
    
    # Get recent reviews
    recent_reviews = Booking.query.filter(
        Booking.vendor_id == id,
        Booking.status == 'completed',
        Booking.rating.isnot(None)
    ).order_by(Booking.review_date.desc()).limit(10).all()
    
    # Check if current user owns this vendor profile
    is_owner = current_user.is_authenticated and current_user.id == vendor.user_id
    
    return render_template('vendors/profile.html',
                         vendor=vendor,
                         active_ads=active_ads,
                         recent_reviews=recent_reviews,
                         is_owner=is_owner)

@vendors.route('/<int:id>/ads/create', methods=['GET', 'POST'])
@login_required
def create_ad(id):
    """Create advertisement for vendor"""
    vendor = Vendor.query.get_or_404(id)
    
    # Check ownership
    if vendor.user_id != current_user.id:
        flash('You can only create ads for your own vendor profile.', 'error')
        return redirect(url_for('vendors.profile', id=id))
    
    if request.method == 'POST':
        try:
            ad = Advertisement(
                title=request.form['title'],
                content=request.form['content'],
                image_url=request.form.get('image_url'),
                target_audience=request.form['target_audience'],
                campaign_name=request.form.get('campaign_name'),
                start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date(),
                click_url=request.form.get('click_url'),
                call_to_action=request.form.get('call_to_action', 'Learn More'),
                ad_type=request.form.get('ad_type', 'banner'),
                placement=request.form.get('placement', 'trip_list'),
                vendor_id=vendor.id
            )
            
            # Handle grade levels as array
            grade_levels = request.form.getlist('grade_levels')
            if grade_levels:
                ad.grade_levels = grade_levels
            
            # Handle locations as array
            locations = request.form.getlist('locations')
            if locations:
                ad.locations = locations
            
            db.session.add(ad)
            db.session.commit()
            
            flash('Advertisement created successfully!', 'success')
            return redirect(url_for('vendors.profile', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating advertisement: {str(e)}', 'error')
    
    target_audiences = ['all', 'teachers', 'parents', 'students']
    grade_levels = ['K-2', '3-5', '6-8', '9-12']
    ad_types = ['banner', 'inline', 'popup']
    placements = ['header', 'sidebar', 'footer', 'trip_list']
    
    return render_template('vendors/create_ad.html',
                         vendor=vendor,
                         target_audiences=target_audiences,
                         grade_levels=grade_levels,
                         ad_types=ad_types,
                         placements=placements)

@vendors.route('/<int:id>/bookings')
@login_required
def booking_dashboard(id):
    """Vendor dashboard for managing booking requests"""
    vendor = Vendor.query.get_or_404(id)
    
    # Check ownership
    if vendor.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('vendors.profile', id=id))
    
    # Get bookings by status
    pending_bookings = vendor.bookings.filter_by(status='pending').order_by(Booking.booking_date.desc()).all()
    confirmed_bookings = vendor.bookings.filter_by(status='confirmed').order_by(Booking.confirmed_date.desc()).all()
    completed_bookings = vendor.bookings.filter_by(status='completed').order_by(Booking.completed_date.desc()).limit(20).all()
    
    # Calculate revenue statistics
    total_revenue = sum(booking.total_amount for booking in completed_bookings if booking.total_amount)
    
    return render_template('vendors/booking_dashboard.html',
                         vendor=vendor,
                         pending_bookings=pending_bookings,
                         confirmed_bookings=confirmed_bookings,
                         completed_bookings=completed_bookings,
                         total_revenue=total_revenue)

@vendors.route('/bookings/<int:booking_id>/accept', methods=['POST'])
@login_required
def accept_booking(booking_id):
    """Accept a booking request"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check ownership
    if booking.vendor.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if booking.status != 'pending':
        return jsonify({'error': 'Booking is not pending'}), 400
    
    try:
        final_amount = request.json.get('final_amount')
        booking.confirm_booking(final_amount)
        
        return jsonify({
            'success': True,
            'message': 'Booking accepted successfully',
            'booking': booking.serialize()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vendors.route('/bookings/<int:booking_id>/decline', methods=['POST'])
@login_required
def decline_booking(booking_id):
    """Decline a booking request"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check ownership
    if booking.vendor.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if booking.status != 'pending':
        return jsonify({'error': 'Booking is not pending'}), 400
    
    try:
        booking.status = 'cancelled'
        booking.notes = request.json.get('reason', 'Declined by vendor')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Booking declined',
            'booking': booking.serialize()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vendors.route('/<int:id>/verify', methods=['POST'])
@login_required
def submit_verification(id):
    """Submit verification documents"""
    vendor = Vendor.query.get_or_404(id)
    
    # Check ownership
    if vendor.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('vendors.profile', id=id))
    
    # Handle file uploads
    uploaded_files = []
    if 'verification_documents' in request.files:
        files = request.files.getlist('verification_documents')
        
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'verification', filename)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                file.save(file_path)
                uploaded_files.append(file_path)
    
    # Update vendor with verification documents
    vendor.verification_documents = uploaded_files
    db.session.commit()
    
    # TODO: Send notification to admin for verification review
    
    flash('Verification documents submitted successfully. We will review them shortly.', 'success')
    return redirect(url_for('vendors.profile', id=id))

@vendors.route('/rate/<int:booking_id>', methods=['POST'])
@login_required
def rate_vendor(booking_id):
    """Submit rating for completed booking (AJAX endpoint)"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if booking is completed and belongs to current user's trip
    if booking.status != 'completed':
        return jsonify({'error': 'Booking is not completed'}), 400
    
    # TODO: Add proper authorization check for trip organizer
    
    try:
        rating = request.json.get('rating')
        review = request.json.get('review', '')
        
        if not rating or rating < 1 or rating > 5:
            return jsonify({'error': 'Invalid rating'}), 400
        
        booking.add_review(rating, review)
        
        return jsonify({
            'success': True,
            'message': 'Rating submitted successfully',
            'vendor_rating': booking.vendor.average_rating
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin routes for verification
@vendors.route('/admin/verify/<int:id>')
@login_required
def admin_verify_vendor(id):
    """Admin route to verify vendor (placeholder)"""
    # TODO: Add admin permission check
    vendor = Vendor.query.get_or_404(id)
    vendor.is_verified = True
    db.session.commit()
    
    flash(f'Vendor {vendor.business_name} has been verified.', 'success')
    return redirect(url_for('vendors.profile', id=id))