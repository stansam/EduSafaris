import csv
import io
import json
from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash, jsonify, make_response, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, func
from werkzeug.utils import secure_filename

from app.trips import trips_bp as bp
from app.extensions import db
from app.models.trip import Trip
from app.models.participant import Participant
from app.models.booking import Booking
from app.models.vendor import Vendor
from app.models.user import User
from app.trips.forms import TripForm, VendorSelectForm, ParticipantForm
from app.utils import send_notification


@bp.route('/')
@login_required
def list_trips():
    """List trips with filtering and search functionality"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Get filter parameters
    filter_type = request.args.get('filter', 'all')
    search_query = request.args.get('q', '').strip()
    
    # Base query
    query = Trip.query
    
    # Apply filters
    if filter_type == 'upcoming':
        query = query.filter(Trip.start_date > date.today())
    elif filter_type == 'past':
        query = query.filter(Trip.end_date < date.today())
    elif filter_type == 'mine':
        if current_user.is_teacher():
            query = query.filter_by(organizer_id=current_user.id)
        elif current_user.is_parent():
            # Get trips where user has participants
            participant_trip_ids = db.session.query(Participant.trip_id).filter_by(user_id=current_user.id).subquery()
            query = query.filter(Trip.id.in_(participant_trip_ids))
    
    # Apply search
    if search_query:
        query = query.filter(or_(
            Trip.title.ilike(f'%{search_query}%'),
            Trip.description.ilike(f'%{search_query}%'),
            Trip.destination.ilike(f'%{search_query}%')
        ))
    
    # Order by start date
    query = query.order_by(Trip.start_date.desc())
    
    # Paginate
    trips = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('trips/list.html', trips=trips, filter_type=filter_type, search_query=search_query)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_trip():
    """Create a new trip"""
    if not current_user.is_teacher() and not current_user.is_admin():
        flash('Only teachers can create trips.', 'error')
        return redirect(url_for('trips.list_trips'))
    
    form = TripForm()
    
    if form.validate_on_submit():
        try:
            # Parse itinerary JSON if provided
            itinerary = None
            if form.itinerary.data:
                itinerary = json.loads(form.itinerary.data)
            
            trip = Trip(
                title=form.title.data,
                description=form.description.data,
                destination=form.destination.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                registration_deadline=form.registration_deadline.data,
                max_participants=form.max_participants.data,
                min_participants=form.min_participants.data,
                price_per_student=form.price_per_student.data,
                category=form.category.data,
                grade_level=form.grade_level.data,
                medical_info_required=form.medical_info_required.data,
                consent_required=form.consent_required.data,
                itinerary=itinerary,
                organizer_id=current_user.id,
                status='draft'
            )
            
            db.session.add(trip)
            db.session.commit()
            
            flash('Trip created successfully!', 'success')
            return redirect(url_for('trips.trip_detail', id=trip.id))
            
        except json.JSONDecodeError:
            flash('Invalid itinerary format. Please provide valid JSON.', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error creating trip. Please try again.', 'error')
            current_app.logger.error(f'Error creating trip: {str(e)}')
    
    return render_template('trips/create.html', form=form)


@bp.route('/<int:id>')
@login_required
def trip_detail(id):
    """Display trip details"""
    trip = Trip.query.get_or_404(id)
    
    # Get confirmed participants
    participants = trip.participants.filter_by(status='confirmed').all()
    
    # Get bookings
    bookings = trip.bookings.all()
    
    # Check if current user can manage this trip
    can_manage = (current_user.is_admin() or 
                 (current_user.is_teacher() and trip.organizer_id == current_user.id))
    
    return render_template('trips/detail.html', trip=trip, participants=participants, 
                         bookings=bookings, can_manage=can_manage)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_trip(id):
    """Edit trip details"""
    trip = Trip.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and trip.organizer_id != current_user.id:
        flash('You do not have permission to edit this trip.', 'error')
        return redirect(url_for('trips.trip_detail', id=trip.id))
    
    form = TripForm(obj=trip)
    
    # Convert itinerary to JSON string for form
    if trip.itinerary:
        form.itinerary.data = json.dumps(trip.itinerary, indent=2)
    
    if form.validate_on_submit():
        try:
            # Parse itinerary JSON if provided
            itinerary = None
            if form.itinerary.data:
                itinerary = json.loads(form.itinerary.data)
            
            trip.title = form.title.data
            trip.description = form.description.data
            trip.destination = form.destination.data
            trip.start_date = form.start_date.data
            trip.end_date = form.end_date.data
            trip.registration_deadline = form.registration_deadline.data
            trip.max_participants = form.max_participants.data
            trip.min_participants = form.min_participants.data
            trip.price_per_student = form.price_per_student.data
            trip.category = form.category.data
            trip.grade_level = form.grade_level.data
            trip.medical_info_required = form.medical_info_required.data
            trip.consent_required = form.consent_required.data
            trip.itinerary = itinerary
            
            db.session.commit()
            flash('Trip updated successfully!', 'success')
            return redirect(url_for('trips.trip_detail', id=trip.id))
            
        except json.JSONDecodeError:
            flash('Invalid itinerary format. Please provide valid JSON.', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error updating trip. Please try again.', 'error')
            current_app.logger.error(f'Error updating trip: {str(e)}')
    
    return render_template('trips/edit.html', form=form, trip=trip)


@bp.route('/<int:id>/select_vendor', methods=['GET', 'POST'])
@login_required
def select_vendor(id):
    """Select and book vendors for trip"""
    trip = Trip.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and trip.organizer_id != current_user.id:
        flash('You do not have permission to manage vendors for this trip.', 'error')
        return redirect(url_for('trips.trip_detail', id=trip.id))
    
    form = VendorSelectForm()
    
    # Get available vendors
    vendors = Vendor.query.filter_by(is_active=True, is_verified=True).all()
    
    # Filter vendors by availability
    available_vendors = []
    for vendor in vendors:
        if vendor.is_available(trip.start_date, trip.end_date):
            available_vendors.append(vendor)
    
    if form.validate_on_submit():
        try:
            vendor = Vendor.query.get(form.vendor_id.data)
            if not vendor:
                flash('Invalid vendor selected.', 'error')
                return redirect(request.url)
            
            # Double-check availability
            if not vendor.is_available(trip.start_date, trip.end_date):
                flash('Vendor is no longer available for these dates.', 'error')
                return redirect(request.url)
            
            # Create booking
            booking = Booking(
                trip_id=trip.id,
                vendor_id=vendor.id,
                booking_type=form.booking_type.data,
                service_description=form.service_description.data,
                special_requirements=form.special_requirements.data,
                quoted_amount=form.quoted_amount.data,
                status='pending'
            )
            
            db.session.add(booking)
            db.session.commit()
            
            # Send notification to vendor
            send_notification(
                recipient_id=vendor.user_id,
                sender_id=current_user.id,
                type='booking_request',
                title='New Booking Request',
                message=f'You have a new booking request for trip "{trip.title}"',
                data={'booking_id': booking.id, 'trip_id': trip.id}
            )
            
            flash('Vendor booking request sent successfully!', 'success')
            return redirect(url_for('trips.trip_detail', id=trip.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error creating booking. Please try again.', 'error')
            current_app.logger.error(f'Error creating booking: {str(e)}')
    
    return render_template('trips/select_vendor.html', form=form, trip=trip, vendors=available_vendors)


@bp.route('/<int:id>/participants/add', methods=['POST'])
@login_required
def add_participant(id):
    """Add individual participant to trip"""
    trip = Trip.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and trip.organizer_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    form = ParticipantForm()
    
    if form.validate_on_submit():
        try:
            # Check if trip has available spots
            if trip.is_full:
                return jsonify({'error': 'Trip is already at maximum capacity'}), 400
            
            participant = Participant(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                date_of_birth=form.date_of_birth.data,
                grade_level=form.grade_level.data,
                student_id=form.student_id.data,
                email=form.email.data,
                phone=form.phone.data,
                medical_conditions=form.medical_conditions.data,
                medications=form.medications.data,
                allergies=form.allergies.data,
                dietary_restrictions=form.dietary_restrictions.data,
                emergency_contact_1_name=form.emergency_contact_1_name.data,
                emergency_contact_1_phone=form.emergency_contact_1_phone.data,
                emergency_contact_1_relationship=form.emergency_contact_1_relationship.data,
                trip_id=trip.id,
                user_id=current_user.id,
                status='registered'
            )
            
            db.session.add(participant)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'participant': participant.serialize(),
                'message': 'Participant added successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error adding participant: {str(e)}')
            return jsonify({'error': 'Failed to add participant'}), 500
    
    return jsonify({'error': 'Invalid form data', 'errors': form.errors}), 400


@bp.route('/<int:id>/participants/upload_csv', methods=['POST'])
@login_required
def upload_participants_csv(id):
    """Bulk upload participants from CSV"""
    trip = Trip.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and trip.organizer_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a valid CSV file'}), 400
    
    try:
        # Read CSV data
        csv_data = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        
        participants_added = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 to account for header
            try:
                # Check if trip has available spots
                if trip.current_participants + participants_added >= trip.max_participants:
                    errors.append(f'Row {row_num}: Trip has reached maximum capacity')
                    break
                
                # Validate required fields
                if not row.get('first_name') or not row.get('last_name'):
                    errors.append(f'Row {row_num}: Missing required fields (first_name, last_name)')
                    continue
                
                # Parse date of birth if provided
                date_of_birth = None
                if row.get('date_of_birth'):
                    try:
                        date_of_birth = datetime.strptime(row['date_of_birth'], '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            date_of_birth = datetime.strptime(row['date_of_birth'], '%m/%d/%Y').date()
                        except ValueError:
                            errors.append(f'Row {row_num}: Invalid date format for date_of_birth')
                            continue
                
                participant = Participant(
                    first_name=row['first_name'].strip(),
                    last_name=row['last_name'].strip(),
                    date_of_birth=date_of_birth,
                    grade_level=row.get('grade_level', '').strip(),
                    student_id=row.get('student_id', '').strip(),
                    email=row.get('email', '').strip(),
                    phone=row.get('phone', '').strip(),
                    medical_conditions=row.get('medical_conditions', '').strip(),
                    medications=row.get('medications', '').strip(),
                    allergies=row.get('allergies', '').strip(),
                    dietary_restrictions=row.get('dietary_restrictions', '').strip(),
                    emergency_contact_1_name=row.get('emergency_contact_1_name', '').strip(),
                    emergency_contact_1_phone=row.get('emergency_contact_1_phone', '').strip(),
                    emergency_contact_1_relationship=row.get('emergency_contact_1_relationship', '').strip(),
                    trip_id=trip.id,
                    user_id=current_user.id,
                    status='registered'
                )
                
                db.session.add(participant)
                participants_added += 1
                
            except Exception as e:
                errors.append(f'Row {row_num}: {str(e)}')
        
        if participants_added > 0:
            db.session.commit()
        
        return jsonify({
            'success': True,
            'participants_added': participants_added,
            'errors': errors,
            'message': f'Successfully added {participants_added} participants'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error uploading CSV: {str(e)}')
        return jsonify({'error': 'Failed to process CSV file'}), 500


@bp.route('/<int:id>/participants/<int:pid>/consent')
@login_required
def participant_consent(id, pid):
    """Show consent status and links for participant"""
    trip = Trip.query.get_or_404(id)
    participant = Participant.query.get_or_404(pid)
    
    if participant.trip_id != trip.id:
        flash('Participant not found for this trip.', 'error')
        return redirect(url_for('trips.trip_detail', id=trip.id))
    
    # Check if user can view consent (organizer, admin, or participant's parent)
    can_view = (current_user.is_admin() or 
               trip.organizer_id == current_user.id or
               participant.user_id == current_user.id)
    
    if not can_view:
        flash('You do not have permission to view this consent.', 'error')
        return redirect(url_for('trips.trip_detail', id=trip.id))
    
    return render_template('trips/consent.html', trip=trip, participant=participant)


@bp.route('/<int:id>/start', methods=['POST'])
@login_required
def start_trip(id):
    """Mark trip as started"""
    trip = Trip.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and trip.organizer_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    if not trip.can_start():
        return jsonify({'error': 'Trip cannot be started yet'}), 400
    
    try:
        trip.status = 'in_progress'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trip started successfully',
            'status': trip.status
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error starting trip: {str(e)}')
        return jsonify({'error': 'Failed to start trip'}), 500


@bp.route('/<int:id>/end', methods=['POST'])
@login_required
def end_trip(id):
    """Mark trip as completed"""
    trip = Trip.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and trip.organizer_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    if trip.status != 'in_progress':
        return jsonify({'error': 'Trip is not in progress'}), 400
    
    try:
        trip.status = 'completed'
        
        # Mark all confirmed bookings as completed
        for booking in trip.bookings.filter_by(status='confirmed'):
            booking.complete_booking()
        
        # Mark all participants as completed
        for participant in trip.participants.filter_by(status='confirmed'):
            participant.status = 'completed'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trip completed successfully',
            'status': trip.status
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error ending trip: {str(e)}')
        return jsonify({'error': 'Failed to end trip'}), 500


@bp.route('/<int:id>/export/participants')
@login_required
def export_participants(id):
    """Export participant list as CSV"""
    trip = Trip.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and trip.organizer_id != current_user.id:
        flash('You do not have permission to export participants.', 'error')
        return redirect(url_for('trips.trip_detail', id=trip.id))
    
    # Create CSV response
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'First Name', 'Last Name', 'Grade Level', 'Student ID', 'Email', 'Phone',
        'Status', 'Payment Status', 'Amount Paid', 'Outstanding Balance',
        'Medical Conditions', 'Medications', 'Allergies', 'Dietary Restrictions',
        'Emergency Contact 1', 'Emergency Phone 1', 'Emergency Relationship 1'
    ])
    
    # Write participant data
    for participant in trip.participants.all():
        writer.writerow([
            participant.first_name,
            participant.last_name,
            participant.grade_level or '',
            participant.student_id or '',
            participant.email or '',
            participant.phone or '',
            participant.status,
            participant.payment_status,
            float(participant.amount_paid or 0),
            participant.outstanding_balance,
            participant.medical_conditions or '',
            participant.medications or '',
            participant.allergies or '',
            participant.dietary_restrictions or '',
            participant.emergency_contact_1_name or '',
            participant.emergency_contact_1_phone or '',
            participant.emergency_contact_1_relationship or ''
        ])
    
    output.seek(0)
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename="{trip.title}_participants.csv"'
    
    return response


@bp.route('/<int:id>/report')
@login_required
def trip_report(id):
    """Generate trip report"""
    trip = Trip.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and trip.organizer_id != current_user.id:
        flash('You do not have permission to view this report.', 'error')
        return redirect(url_for('trips.trip_detail', id=trip.id))
    
    # Calculate report data
    total_participants = trip.participants.count()
    confirmed_participants = trip.participants.filter_by(status='confirmed').count()
    total_revenue = trip.get_total_revenue()
    
    # Payment statistics
    paid_participants = trip.participants.filter_by(payment_status='paid').count()
    partial_participants = trip.participants.filter_by(payment_status='partial').count()
    pending_participants = trip.participants.filter_by(payment_status='pending').count()
    
    # Booking statistics
    total_bookings = trip.bookings.count()
    confirmed_bookings = trip.bookings.filter_by(status='confirmed').count()
    
    report_data = {
        'trip': trip,
        'total_participants': total_participants,
        'confirmed_participants': confirmed_participants,
        'total_revenue': total_revenue,
        'paid_participants': paid_participants,
        'partial_participants': partial_participants,
        'pending_participants': pending_participants,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings
    }
    
    return render_template('trips/report.html', **report_data)