from datetime import datetime, timedelta
from flask import request, jsonify, render_template, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_login import login_required, current_user
from sqlalchemy import and_
from app.extensions import db, socketio
from app.models import Location, Emergency, Notification, Participant, User
from . import safety_bp

# Rate limiting cache (in production, use Redis)
rate_limit_cache = {}

def is_rate_limited(device_id, trip_id, limit_seconds=5):
    """Check if device is rate limited for location updates"""
    key = f"{trip_id}:{device_id}"
    now = datetime.now()
    
    if key in rate_limit_cache:
        last_request = rate_limit_cache[key]
        if (now - last_request).total_seconds() < limit_seconds:
            return True
    
    rate_limit_cache[key] = now
    # Clean old entries periodically
    if len(rate_limit_cache) > 1000:
        cutoff = now - timedelta(hours=1)
        rate_limit_cache.clear()
    
    return False

def validate_coordinates(lat, lon):
    """Validate latitude and longitude values"""
    try:
        lat = float(lat)
        lon = float(lon)
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return None, None
        return lat, lon
    except (ValueError, TypeError):
        return None, None

def can_user_access_trip(user_id, trip_id):
    """Check if user can access trip data"""
    user = User.query.get(user_id)
    if not user:
        return False
    
    # Admins can access all trips
    if user.is_admin():
        return True
    
    # Teachers can access trips they organize
    if user.is_teacher():
        from app.models.trip import Trip
        trip = Trip.query.get(trip_id)
        if trip and trip.organizer_id == user_id:
            return True
    
    # Parents can access trips their children are in
    if user.is_parent():
        participant = Participant.query.filter_by(
            trip_id=trip_id,
            user_id=user_id
        ).first()
        if participant:
            return True
    
    return False

@safety_bp.route('/api/trips/<int:trip_id>/location', methods=['POST'])
@jwt_required()
def update_location(trip_id):
    """Endpoint for GPS location updates from devices"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['lat', 'lon', 'device_id']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get current user from JWT
        current_user_id = get_jwt_identity()
        
        # Check if user can update this trip's location
        if not can_user_access_trip(current_user_id, trip_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Validate coordinates
        lat, lon = validate_coordinates(data['lat'], data['lon'])
        if lat is None or lon is None:
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        device_id = str(data['device_id']).strip()
        if not device_id:
            return jsonify({'error': 'Invalid device_id'}), 400
        
        # Rate limiting
        if is_rate_limited(device_id, trip_id):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Create location record
        timestamp = datetime.fromtimestamp(data.get('timestamp', datetime.now().timestamp()) / 1000) \
                   if data.get('timestamp') else datetime.now()
        
        location = Location(
            trip_id=trip_id,
            latitude=lat,
            longitude=lon,
            altitude=data.get('altitude'),
            accuracy=data.get('accuracy'),
            speed=data.get('speed'),
            heading=data.get('heading'),
            device_id=device_id,
            device_type=data.get('device_type', 'mobile'),
            timestamp=timestamp,
            battery_level=data.get('battery_level'),
            signal_strength=data.get('signal_strength'),
            user_id=current_user_id
        )
        
        db.session.add(location)
        db.session.commit()
        
        # Emit real-time update via SocketIO
        socketio.emit('trip_location_update', {
            'lat': lat,
            'lon': lon,
            'device_id': device_id,
            'device_type': location.device_type,
            'timestamp': timestamp.isoformat(),
            'accuracy': location.accuracy,
            'speed': location.speed,
            'heading': location.heading,
            'battery_level': location.battery_level
        }, room=f'trip_{trip_id}', namespace='/safety')
        
        return jsonify({
            'success': True,
            'location_id': location.id,
            'timestamp': location.server_timestamp.isoformat()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Location update error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@safety_bp.route('/trips/<int:trip_id>/locations/latest', methods=['GET'])
@login_required
def get_latest_locations(trip_id):
    """Get latest locations for a trip (AJAX fallback)"""
    try:
        # Check access
        if not can_user_access_trip(current_user.id, trip_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get latest locations
        limit = min(int(request.args.get('limit', 10)), 50)
        locations = Location.get_latest_for_trip(trip_id, limit)
        
        return jsonify({
            'locations': [location.serialize() for location in locations]
        })
        
    except Exception as e:
        current_app.logger.error(f"Get locations error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@safety_bp.route('/trips/<int:trip_id>/alert', methods=['POST'])
@login_required
def create_alert(trip_id):
    """Create emergency alert"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if not data.get('message'):
            return jsonify({'error': 'Message is required'}), 400
        
        # Check access
        if not can_user_access_trip(current_user.id, trip_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Validate coordinates if provided
        lat, lon = None, None
        if data.get('lat') is not None and data.get('lon') is not None:
            lat, lon = validate_coordinates(data['lat'], data['lon'])
            if lat is None or lon is None:
                return jsonify({'error': 'Invalid coordinates'}), 400
        
        # Validate severity
        severity = data.get('severity', 'medium')
        if severity not in ['low', 'medium', 'high', 'critical']:
            severity = 'medium'
        
        # Create alert
        alert = Emergency(
            trip_id=trip_id,
            user_id=current_user.id,
            message=data['message'][:1000],  # Limit message length
            severity=severity,
            alert_type=data.get('alert_type', 'general'),
            latitude=lat,
            longitude=lon,
            location_description=data.get('location_description', '')[:300]
        )
        
        db.session.add(alert)
        db.session.commit()
        
        # Emit real-time alert via SocketIO
        socketio.emit('trip_alert', {
            'id': alert.id,
            'message': alert.message,
            'severity': alert.severity,
            'alert_type': alert.alert_type,
            'lat': alert.latitude,
            'lon': alert.longitude,
            'location_description': alert.location_description,
            'timestamp': alert.created_at.isoformat(),
            'user_name': current_user.full_name
        }, room=f'trip_{trip_id}', namespace='/safety')
        
        # Create notifications for trip participants' parents
        try:
            participants = Participant.query.filter_by(trip_id=trip_id).all()
            for participant in participants:
                if participant.user_id:  # Parent/guardian
                    notification = Notification.create_emergency_notification(
                        recipient_id=participant.user_id,
                        alert=alert,
                        sender_id=current_user.id
                    )
                    
                    # TODO: Call external helper functions
                    # send_email(participant.user, alert)
                    # send_sms(participant.user, alert)
                    
            alert.notifications_sent = True
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Notification creation error: {str(e)}")
        
        return jsonify({
            'success': True,
            'alert_id': alert.id,
            'message': 'Alert created and notifications sent'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Create alert error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@safety_bp.route('/trips/<int:trip_id>/alerts', methods=['GET'])
@login_required
def get_alerts(trip_id):
    """Get alerts for a trip"""
    try:
        # Check access
        if not can_user_access_trip(current_user.id, trip_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get alerts
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        alerts = Emergency.query.filter_by(trip_id=trip_id)\
                                  .order_by(Emergency.created_at.desc())\
                                  .paginate(page=page, per_page=per_page)
        
        return jsonify({
            'alerts': [alert.serialize() for alert in alerts.items],
            'total': alerts.total,
            'pages': alerts.pages,
            'current_page': page
        })
        
    except Exception as e:
        current_app.logger.error(f"Get alerts error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@safety_bp.route('/trips/<int:trip_id>/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert(trip_id, alert_id):
    """Acknowledge an alert"""
    try:
        # Check access
        if not can_user_access_trip(current_user.id, trip_id):
            return jsonify({'error': 'Access denied'}), 403
        
        alert = Emergency.query.filter_by(id=alert_id, trip_id=trip_id).first()
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        alert.acknowledge(current_user.id)
        
        # Emit update via SocketIO
        socketio.emit('alert_acknowledged', {
            'alert_id': alert.id,
            'acknowledged_by': current_user.full_name,
            'acknowledged_at': alert.acknowledged_at.isoformat()
        }, room=f'trip_{trip_id}', namespace='/safety')
        
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Acknowledge alert error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@safety_bp.route('/trips/<int:trip_id>/track')
@login_required
def track_trip(trip_id):
    """Trip tracking page"""
    try:
        # Check access
        if not can_user_access_trip(current_user.id, trip_id):
            from flask import abort
            current_app.logger.error('Permision Denied')
            abort(403)
        
        # Get trip info
        from app.models.trip import Trip
        trip = Trip.query.get_or_404(trip_id)
        
        # Get latest locations
        latest_locations = Location.get_latest_for_trip(trip_id, 10)
        
        # Get recent alerts
        recent_alerts = Emergency.query.filter_by(trip_id=trip_id, resolved=False)\
                                          .order_by(Emergency.created_at.desc())\
                                          .limit(5).all()
        
        return render_template('safety/track.html', 
                             trip=trip,
                             latest_locations=latest_locations,
                             recent_alerts=recent_alerts)
        
    except Exception as e:
        current_app.logger.error(f"Track trip error: {str(e)}")
        from flask import abort
        abort(500)