from flask import Blueprint, jsonify, request
from sqlalchemy import or_, and_, func
from datetime import datetime, date
from app.models.trip import Trip
from app.extensions import db
from app.api.main.utils import get_trip_image_url
from app.api import api_bp as trips_api


@trips_api.route('/trips', methods=['GET'])
def get_trips():
    """
    Get trips with filtering, sorting, and pagination
    Query params:
    - search: search term for title, description, destination
    - category: filter by category
    - duration: filter by duration (half, full, multi, week)
    - min_price: minimum price filter
    - max_price: maximum price filter
    - grade_level: filter by grade level
    - status: filter by status (default: active)
    - sort_by: sorting option (popular, price-low, price-high, duration, rating)
    - page: page number (default: 1)
    - per_page: items per page (default: 12)
    """
    try:
        # Get query parameters
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        duration = request.args.get('duration', '').strip()
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        grade_level = request.args.get('grade_level', '').strip()
        status = request.args.get('status', 'active')
        sort_by = request.args.get('sort_by', 'popular')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        # Start with base query
        query = Trip.query
        
        # Apply status filter (default to active trips)
        if status:
            query = query.filter(Trip.status == status)
        
        # Apply search filter
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                or_(
                    Trip.title.ilike(search_pattern),
                    Trip.description.ilike(search_pattern),
                    Trip.destination.ilike(search_pattern),
                    Trip.category.ilike(search_pattern)
                )
            )
        
        # Apply category filter
        if category and category != 'all':
            # Map frontend categories to database categories
            category_map = {
                'science': ['science', 'nature', 'wildlife', 'marine'],
                'history': ['history', 'cultural', 'heritage'],
                'art': ['art', 'museums', 'cultural'],
                'adventure': ['adventure', 'sports', 'outdoor'],
                'technology': ['technology', 'innovation', 'stem']
            }
            
            if category in category_map:
                categories = category_map[category]
                query = query.filter(Trip.category.in_(categories))
            else:
                query = query.filter(Trip.category == category)
        
        # Apply duration filter
        if duration and duration != 'all':
            today = date.today()
            if duration == 'half':
                # Half day trips (duration_days == 0 or 1)
                query = query.filter(
                    func.datediff(Trip.end_date, Trip.start_date) <= 0
                )
            elif duration == 'full':
                # Full day trips (duration_days == 1)
                query = query.filter(
                    func.datediff(Trip.end_date, Trip.start_date) == 0
                )
            elif duration == 'multi':
                # Multi-day trips (2-6 days)
                query = query.filter(
                    and_(
                        func.datediff(Trip.end_date, Trip.start_date) >= 1,
                        func.datediff(Trip.end_date, Trip.start_date) <= 5
                    )
                )
            elif duration == 'week':
                # Week long trips (7+ days)
                query = query.filter(
                    func.datediff(Trip.end_date, Trip.start_date) >= 6
                )
        
        # Apply price filters
        if min_price is not None:
            query = query.filter(Trip.price_per_student >= min_price)
        if max_price is not None:
            query = query.filter(Trip.price_per_student <= max_price)
        
        # Apply grade level filter
        if grade_level and grade_level != 'all':
            query = query.filter(Trip.grade_level == grade_level)
        
        # Apply sorting
        if sort_by == 'popular':
            # Sort by featured first, then by number of participants
            query = query.outerjoin(Trip.participants).group_by(Trip.id)\
                .order_by(Trip.featured.desc(), func.count(Trip.participants).desc())
        elif sort_by == 'price-low':
            query = query.order_by(Trip.price_per_student.asc())
        elif sort_by == 'price-high':
            query = query.order_by(Trip.price_per_student.desc())
        elif sort_by == 'duration':
            query = query.order_by(
                func.datediff(Trip.end_date, Trip.start_date).asc()
            )
        elif sort_by == 'rating':
            # If you have ratings, implement here. For now, sort by featured
            query = query.order_by(Trip.featured.desc())
        else:
            # Default sorting
            query = query.order_by(Trip.created_at.desc())
        
        # Paginate results
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Serialize trips
        trips = []
        for trip in pagination.items:
            trip_data = trip.serialize()
            # Add additional computed fields
            trip_data['rating'] = 4.8  # Replace with actual rating calculation
            trip_data['image_url'] = get_trip_image_url(trip)
            trips.append(trip_data)
        
        return jsonify({
            'success': True,
            'trips': trips,
            'pagination': {
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': pagination.page,
                'per_page': pagination.per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'filters': {
                'search': search,
                'category': category,
                'duration': duration,
                'min_price': min_price,
                'max_price': max_price,
                'grade_level': grade_level,
                'sort_by': sort_by
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trips_api.route('/trips/<int:trip_id>', methods=['GET'])
def get_trips_details(trip_id):
    """Get detailed information about a specific trip"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        
        trip_data = trip.serialize()
        trip_data['rating'] = 4.8  # Replace with actual rating
        trip_data['image_url'] = get_trip_image_url(trip)
        trip_data['itinerary'] = trip.itinerary or []
        trip_data['locations'] = [loc.serialize() for loc in trip.locations]
        
        return jsonify({
            'success': True,
            'trip': trip_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@trips_api.route('/trips/categories', methods=['GET'])
def get_trips_categories():
    """Get all available trip categories with counts"""
    try:
        categories = db.session.query(
            Trip.category,
            func.count(Trip.id).label('count')
        ).filter(
            Trip.status == 'active'
        ).group_by(
            Trip.category
        ).all()
        
        return jsonify({
            'success': True,
            'categories': [
                {'name': cat[0], 'count': cat[1]} 
                for cat in categories if cat[0]
            ]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trips_api.route('/price-range', methods=['GET'])
def get_price_range():
    """Get min and max prices for filtering"""
    try:
        result = db.session.query(
            func.min(Trip.price_per_student).label('min_price'),
            func.max(Trip.price_per_student).label('max_price')
        ).filter(
            Trip.status == 'active'
        ).first()
        
        return jsonify({
            'success': True,
            'min_price': float(result.min_price) if result.min_price else 0,
            'max_price': float(result.max_price) if result.max_price else 10000
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trips_api.route('/grade-levels', methods=['GET'])
def get_grade_levels():
    """Get all available grade levels"""
    try:
        grade_levels = db.session.query(
            Trip.grade_level,
            func.count(Trip.id).label('count')
        ).filter(
            Trip.status == 'active',
            Trip.grade_level.isnot(None)
        ).group_by(
            Trip.grade_level
        ).all()
        
        return jsonify({
            'success': True,
            'grade_levels': [
                {'name': gl[0], 'count': gl[1]} 
                for gl in grade_levels
            ]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


