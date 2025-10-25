from flask import Blueprint, jsonify, request
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import joinedload
from app.models import Trip,  User
from app.extensions import db
from datetime import date, datetime, timedelta
from app.api import api_bp as trips_bp
from app.api.main.utils import get_trip_image_url, calculate_trip_rating


@trips_bp.route('/trips/featured', methods=['GET'])
def get_featured_trips():
    """
    Get featured trips with optional filtering
    Query params:
    - limit: number of trips to return (default: 6)
    - category: filter by category
    - grade_level: filter by grade level
    - include_past: include past trips (default: false)
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 6, type=int)
        category = request.args.get('category', type=str)
        grade_level = request.args.get('grade_level', type=str)
        include_past = request.args.get('include_past', 'false').lower() == 'true'
        
        # Validate limit
        if limit < 1 or limit > 50:
            return jsonify({
                'success': False,
                'error': 'Limit must be between 1 and 50'
            }), 400
        
        # Build base query
        query = Trip.query.filter_by(featured=True)
        
        # Filter by status - only active trips
        query = query.filter(Trip.status.in_(['active', 'in_progress']))
        
        # Filter out past trips unless specified
        if not include_past:
            today = date.today()
            query = query.filter(Trip.end_date >= today)
        
        # Apply optional filters
        if category:
            query = query.filter_by(category=category)
        
        if grade_level:
            query = query.filter_by(grade_level=grade_level)
        
        # Order by start date (soonest first) and created date
        query = query.order_by(Trip.start_date.asc(), Trip.created_at.desc())
        
        # Get trips with limit
        featured_trips = query.limit(limit).all()
        
        # Check if we have any trips
        if not featured_trips:
            return jsonify({
                'success': True,
                'data': [],
                'count': 0,
                'message': 'No featured trips found'
            }), 200
        
        # Serialize trips with additional computed fields
        trips_data = []
        for trip in featured_trips:
            trip_dict = trip.serialize()
            
            # Add additional fields for frontend
            trip_dict.update({
                'duration_text': f"{trip.duration_days} Day{'s' if trip.duration_days != 1 else ''}",
                'participant_range': f"{trip.min_participants}-{trip.max_participants} Students",
                'spots_remaining': trip.available_spots,
                'is_filling_fast': trip.available_spots <= 5 and trip.available_spots > 0,
                'image_url': get_trip_image_url(trip),
                'rating': calculate_trip_rating(trip),
                'price_formatted': f"Kshs. {float(trip.price_per_student):,.0f}/student"
            })
            
            trips_data.append(trip_dict)
        
        return jsonify({
            'success': True,
            'data': trips_data,
            'count': len(trips_data)
        }), 200
        
    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Error fetching featured trips: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'An error occurred while fetching featured trips'
        }), 500


# @trips_bp.route('/trips/<int:trip_id>', methods=['GET'])
# def get_trips_details(trip_id):
#     """Get detailed information about a specific trip"""
#     try:
#         trip = Trip.query.get(trip_id)
        
#         if not trip:
#             return jsonify({
#                 'success': False,
#                 'error': 'Trip not found'
#             }), 404
        
#         # Serialize with full details
#         trip_data = trip.serialize()
#         trip_data.update({
#             'itinerary': trip.itinerary,
#             'medical_info_required': trip.medical_info_required,
#             'consent_required': trip.consent_required,
#             'registration_deadline': trip.registration_deadline.isoformat() if trip.registration_deadline else None,
#             'duration_text': f"{trip.duration_days} Day{'s' if trip.duration_days != 1 else ''}",
#             'image_url': get_trip_image_url(trip),
#             'rating': calculate_trip_rating(trip)
#         })
        
#         return jsonify({
#             'success': True,
#             'data': trip_data
#         }), 200
        
#     except Exception as e:
#         print(f"Error fetching trip details: {str(e)}")
        
#         return jsonify({
#             'success': False,
#             'error': 'An error occurred while fetching trip details'
#         }), 500


@trips_bp.route('/trips/categories', methods=['GET'])
def get_categories():
    """Get all available trip categories"""
    try:
        categories = db.session.query(Trip.category).filter(
            Trip.category.isnot(None),
            Trip.featured == True
        ).distinct().all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return jsonify({
            'success': True,
            'data': category_list
        }), 200
        
    except Exception as e:
        print(f"Error fetching categories: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'An error occurred while fetching categories'
        }), 500


