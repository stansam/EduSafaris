from flask import request, jsonify, make_response
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, case
from app.extensions import db
from app.models.trip import Trip
from app.models.participant import Participant
from app.models.activity_log import ActivityLog
from app.utils.utils import roles_required
import csv
import io
from datetime import datetime

from app.api import api_bp


@api_bp.route('/participants/teacher/trips', methods=['GET'])
@login_required
@roles_required('teacher')
def get_teacher_trips():
    """
    Get all trips organized by the current teacher with participant statistics
    
    Query Parameters:
    - include_stats: Include participant statistics (default: true)
    - status: Filter by trip status (upcoming, ongoing, completed, cancelled)
    - search: Search by trip title or destination
    - sort_by: Sort field (start_date, title, participant_count)
    - order: Sort order (asc, desc)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 100)
    """
    try:
        # Get query parameters
        include_stats = request.args.get('include_stats', 'true').lower() == 'true'
        status_filter = request.args.get('status', type=str)
        search_query = request.args.get('search', type=str)
        sort_by = request.args.get('sort_by', 'start_date', type=str)
        order = request.args.get('order', 'desc', type=str)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        # Validate parameters
        valid_sort_fields = ['start_date', 'title', 'participant_count', 'created_at']
        if sort_by not in valid_sort_fields:
            return jsonify({
                'success': False,
                'error': 'Invalid parameter',
                'message': f'Invalid sort field. Must be one of: {", ".join(valid_sort_fields)}'
            }), 400
        
        # Build base query - only trips organized by current teacher
        query = Trip.query.filter_by(organizer_id=current_user.id)
        
        # Apply status filter
        if status_filter:
            today = datetime.now().date()
            if status_filter == 'upcoming':
                query = query.filter(Trip.start_date > today)
            elif status_filter == 'ongoing':
                query = query.filter(
                    Trip.start_date <= today,
                    Trip.end_date >= today
                )
            elif status_filter == 'completed':
                query = query.filter(Trip.end_date < today)
            elif status_filter == 'cancelled':
                query = query.filter(Trip.status == 'cancelled')
        
        # Apply search filter
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Trip.title.ilike(search_pattern),
                    Trip.destination.ilike(search_pattern),
                    Trip.description.ilike(search_pattern)
                )
            )
        
        # Apply sorting
        if sort_by == 'participant_count' and include_stats:
            # Join with participants for sorting by count
            query = query.outerjoin(Participant).group_by(Trip.id)
            sort_column = func.count(Participant.id)
        elif sort_by == 'title':
            sort_column = Trip.title
        elif sort_by == 'created_at':
            sort_column = Trip.created_at
        else:  # default to start_date
            sort_column = Trip.start_date
        
        if order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Execute query with pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        trips = pagination.items
        
        # Serialize trips with statistics
        trips_data = []
        for trip in trips:
            trip_dict = {
                'id': trip.id,
                'title': trip.title,
                'destination': trip.destination,
                'description': trip.description,
                'start_date': trip.start_date.isoformat() if trip.start_date else None,
                'end_date': trip.end_date.isoformat() if trip.end_date else None,
                'status': trip.status if hasattr(trip, 'status') else 'active',
                'price_per_student': float(trip.price_per_student) if hasattr(trip, 'price_per_student') and trip.price_per_student else None,
                'max_participants': trip.max_participants if hasattr(trip, 'max_participants') else None,
                'created_at': trip.created_at.isoformat() if trip.created_at else None
            }
            
            # Add participant statistics if requested
            if include_stats:
                # Get participant counts with a single query per trip
                participant_stats = db.session.query(
                    func.count(Participant.id).label('total'),
                    func.sum(case((Participant.status == 'confirmed', 1), else_=0)).label('confirmed'),
                    func.sum(case((Participant.payment_status == 'paid', 1), else_=0)).label('paid'),
                    func.sum(case((Participant.status == 'cancelled', 1), else_=0)).label('cancelled')
                ).filter(Participant.trip_id == trip.id).first()
                
                trip_dict['participant_count'] = participant_stats.total or 0
                trip_dict['confirmed_count'] = participant_stats.confirmed or 0
                trip_dict['paid_count'] = participant_stats.paid or 0
                trip_dict['cancelled_count'] = participant_stats.cancelled or 0
                
                # Calculate capacity percentage
                if trip_dict['max_participants']:
                    trip_dict['capacity_percentage'] = round(
                        (trip_dict['participant_count'] / trip_dict['max_participants']) * 100, 
                        1
                    )
                else:
                    trip_dict['capacity_percentage'] = None
            
            trips_data.append(trip_dict)
        
        # Calculate overall statistics
        total_trips = Trip.query.filter_by(organizer_id=current_user.id).count()
        today = datetime.now().date()
        
        overall_stats = {
            'total_trips': total_trips,
            'upcoming_trips': Trip.query.filter(
                Trip.organizer_id == current_user.id,
                Trip.start_date > today
            ).count(),
            'ongoing_trips': Trip.query.filter(
                Trip.organizer_id == current_user.id,
                Trip.start_date <= today,
                Trip.end_date >= today
            ).count(),
            'completed_trips': Trip.query.filter(
                Trip.organizer_id == current_user.id,
                Trip.end_date < today
            ).count()
        }
        
        # Log activity
        try:
            ActivityLog.log_action(
                action='view_trips',
                user_id=current_user.id,
                entity_type='trip',
                description=f'Viewed trips list',
                category='trip',
                metadata={
                    'filters': {
                        'status': status_filter,
                        'search': search_query
                    },
                    'page': page,
                    'per_page': per_page
                },
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                request_method=request.method,
                request_url=request.url
            )
        except Exception as log_error:
            print(f"Logging error: {str(log_error)}")
        
        return jsonify({
            'success': True,
            'data': {
                'trips': trips_data,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                },
                'statistics': overall_stats
            }
        }), 200
    
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'An error occurred while fetching trips'
        }), 500
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500


@api_bp.route('/participants/trip/<int:trip_id>/export', methods=['GET'])
@login_required
@roles_required('teacher')
def export_participants(trip_id):
    """
    Export participants for a specific trip to CSV format
    
    Query Parameters:
    - status: Filter by participant status
    - payment_status: Filter by payment status
    - search: Search by name or email
    - format: Export format (csv, xlsx) - currently only CSV supported
    - fields: Comma-separated list of fields to include (default: all)
    """
    try:
        # Verify trip ownership
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found',
                'message': f'No trip found with ID {trip_id}'
            }), 404
        
        if trip.organizer_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized',
                'message': 'You do not have permission to export participants for this trip'
            }), 403
        
        # Get query parameters
        status_filter = request.args.get('status', type=str)
        payment_status_filter = request.args.get('payment_status', type=str)
        search_query = request.args.get('search', type=str)
        export_format = request.args.get('format', 'csv', type=str)
        fields_param = request.args.get('fields', type=str)
        
        # Validate export format
        if export_format not in ['csv', 'xlsx']:
            return jsonify({
                'success': False,
                'error': 'Invalid parameter',
                'message': 'Export format must be either csv or xlsx'
            }), 400
        
        # Build query
        query = Participant.query.filter_by(trip_id=trip_id)
        
        # Apply filters
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        if payment_status_filter:
            query = query.filter_by(payment_status=payment_status_filter)
        
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Participant.first_name.ilike(search_pattern),
                    Participant.last_name.ilike(search_pattern),
                    Participant.email.ilike(search_pattern)
                )
            )
        
        # Order by name
        query = query.order_by(Participant.last_name, Participant.first_name)
        
        # Get all participants
        participants = query.all()
        
        if not participants:
            return jsonify({
                'success': False,
                'error': 'No data',
                'message': 'No participants found matching the criteria'
            }), 404
        
        # Define available fields
        all_fields = [
            'id', 'full_name', 'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'age', 'grade_level', 'student_id',
            'status', 'payment_status', 'amount_paid', 'outstanding_balance',
            'registration_date', 'confirmation_date',
            'medical_conditions', 'medications', 'allergies', 'dietary_restrictions',
            'emergency_contact_1_name', 'emergency_contact_1_phone', 'emergency_contact_1_relationship',
            'emergency_contact_2_name', 'emergency_contact_2_phone', 'emergency_contact_2_relationship',
            'special_requirements', 'has_all_consents'
        ]
        
        # Determine which fields to include
        if fields_param:
            requested_fields = [f.strip() for f in fields_param.split(',')]
            fields_to_export = [f for f in requested_fields if f in all_fields]
            if not fields_to_export:
                fields_to_export = all_fields
        else:
            fields_to_export = all_fields
        
        # Generate CSV
        if export_format == 'csv':
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header row
            headers = [field.replace('_', ' ').title() for field in fields_to_export]
            writer.writerow(headers)
            
            # Write data rows
            for participant in participants:
                row = []
                for field in fields_to_export:
                    if field == 'full_name':
                        value = participant.full_name
                    elif field == 'age':
                        value = participant.age or 'N/A'
                    elif field == 'outstanding_balance':
                        value = float(participant.outstanding_balance) if hasattr(participant, 'outstanding_balance') else 0
                    elif field == 'amount_paid':
                        value = float(participant.amount_paid) if participant.amount_paid else 0
                    elif field == 'has_all_consents':
                        value = 'Yes' if participant.has_all_consents() else 'No'
                    elif field == 'registration_date':
                        value = participant.registration_date.strftime('%Y-%m-%d %H:%M:%S') if participant.registration_date else ''
                    elif field == 'confirmation_date':
                        value = participant.confirmation_date.strftime('%Y-%m-%d %H:%M:%S') if participant.confirmation_date else ''
                    elif field == 'date_of_birth':
                        value = participant.date_of_birth.strftime('%Y-%m-%d') if participant.date_of_birth else ''
                    else:
                        value = getattr(participant, field, '')
                    
                    # Handle None values
                    row.append(value if value is not None else '')
                
                writer.writerow(row)
            
            # Prepare response
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=participants_trip_{trip_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            # Log the export
            try:
                ActivityLog.log_action(
                    action='export_participants',
                    user_id=current_user.id,
                    entity_type='trip',
                    entity_id=trip_id,
                    description=f'Exported {len(participants)} participants for trip: {trip.title}',
                    category='export',
                    trip_id=trip_id,
                    metadata={
                        'participant_count': len(participants),
                        'filters': {
                            'status': status_filter,
                            'payment_status': payment_status_filter,
                            'search': search_query
                        },
                        'format': export_format,
                        'fields': fields_to_export
                    },
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    request_method=request.method,
                    request_url=request.url
                )
            except Exception as log_error:
                print(f"Logging error: {str(log_error)}")
            
            return response
        
        # XLSX format (if needed in future)
        elif export_format == 'xlsx':
            return jsonify({
                'success': False,
                'error': 'Not implemented',
                'message': 'XLSX export is not yet implemented'
            }), 501
    
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'An error occurred while exporting participants'
        }), 500
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500


# Optional: Batch export for multiple trips
@api_bp.route('/participants/export-all', methods=['GET'])
@login_required
@roles_required('teacher')
def export_all_participants():
    """
    Export participants from all trips organized by the teacher
    
    Query Parameters:
    - trip_ids: Comma-separated list of trip IDs (optional, exports all if not provided)
    - format: Export format (csv only for now)
    """
    try:
        trip_ids_param = request.args.get('trip_ids', type=str)
        export_format = request.args.get('format', 'csv', type=str)
        
        # Build query for trips
        trips_query = Trip.query.filter_by(organizer_id=current_user.id)
        
        # Filter by specific trip IDs if provided
        if trip_ids_param:
            try:
                trip_ids = [int(tid.strip()) for tid in trip_ids_param.split(',')]
                trips_query = trips_query.filter(Trip.id.in_(trip_ids))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid parameter',
                    'message': 'Invalid trip IDs format'
                }), 400
        
        trips = trips_query.all()
        
        if not trips:
            return jsonify({
                'success': False,
                'error': 'No data',
                'message': 'No trips found'
            }), 404
        
        # Get all participants for these trips
        trip_ids = [trip.id for trip in trips]
        participants = Participant.query.filter(
            Participant.trip_id.in_(trip_ids)
        ).order_by(Participant.trip_id, Participant.last_name, Participant.first_name).all()
        
        if not participants:
            return jsonify({
                'success': False,
                'error': 'No data',
                'message': 'No participants found'
            }), 404
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = [
            'Trip ID', 'Trip Title', 'Participant ID', 'Full Name', 'Email', 'Phone',
            'Age', 'Grade', 'Status', 'Payment Status', 'Amount Paid', 'Balance',
            'Registration Date', 'Has All Consents'
        ]
        writer.writerow(headers)
        
        # Create trip lookup
        trip_lookup = {trip.id: trip.title for trip in trips}
        
        # Write data
        for participant in participants:
            row = [
                participant.trip_id,
                trip_lookup.get(participant.trip_id, 'Unknown'),
                participant.id,
                participant.full_name,
                participant.email or '',
                participant.phone or '',
                participant.age or 'N/A',
                participant.grade_level or 'N/A',
                participant.status,
                participant.payment_status,
                float(participant.amount_paid) if participant.amount_paid else 0,
                float(participant.outstanding_balance) if hasattr(participant, 'outstanding_balance') else 0,
                participant.registration_date.strftime('%Y-%m-%d %H:%M:%S') if participant.registration_date else '',
                'Yes' if participant.has_all_consents() else 'No'
            ]
            writer.writerow(row)
        
        # Prepare response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=all_participants_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Log the export
        try:
            ActivityLog.log_action(
                action='export_all_participants',
                user_id=current_user.id,
                entity_type='trip',
                description=f'Exported {len(participants)} participants from {len(trips)} trips',
                category='export',
                metadata={
                    'trip_count': len(trips),
                    'participant_count': len(participants),
                    'trip_ids': trip_ids
                },
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                request_method=request.method,
                request_url=request.url
            )
        except Exception as log_error:
            print(f"Logging error: {str(log_error)}")
        
        return response
    
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': 'An error occurred while exporting participants'
        }), 500
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500