from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from app.extensions import socketio
from app.models.user import User
from app.models.participant import Participant

@socketio.on('connect', namespace='/safety')
def safety_connect(auth):
    """Handle client connection to safety namespace"""
    if not current_user.is_authenticated:
        disconnect()
        return False
    
    print(f"User {current_user.full_name} connected to safety namespace")
    emit('connected', {'message': 'Connected to safety monitoring'})

@socketio.on('disconnect', namespace='/safety')
def safety_disconnect():
    """Handle client disconnection from safety namespace"""
    if current_user.is_authenticated:
        print(f"User {current_user.full_name} disconnected from safety namespace")

@socketio.on('join_trip_room', namespace='/safety')
def on_join_trip_room(data):
    """Join a trip room for real-time updates"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    trip_id = data.get('trip_id')
    if not trip_id:
        emit('error', {'message': 'Trip ID required'})
        return
    
    # Check if user can access this trip
    can_access = False
    
    # Admins can access all trips
    if current_user.is_admin():
        can_access = True
    
    # Teachers can access trips they organize
    elif current_user.is_teacher():
        from app.models.trip import Trip
        trip = Trip.query.get(trip_id)
        if trip and trip.organizer_id == current_user.id:
            can_access = True
    
    # Parents can access trips their children are in
    elif current_user.is_parent():
        participant = Participant.query.filter_by(
            trip_id=trip_id,
            user_id=current_user.id
        ).first()
        if participant:
            can_access = True
    
    if not can_access:
        emit('error', {'message': 'Access denied for this trip'})
        return
    
    room = f'trip_{trip_id}'
    join_room(room)
    emit('joined_room', {
        'room': room,
        'message': f'Joined trip {trip_id} monitoring'
    })
    
    print(f"User {current_user.full_name} joined room {room}")

@socketio.on('leave_trip_room', namespace='/safety')
def on_leave_trip_room(data):
    """Leave a trip room"""
    if not current_user.is_authenticated:
        return
    
    trip_id = data.get('trip_id')
    if not trip_id:
        emit('error', {'message': 'Trip ID required'})
        return
    
    room = f'trip_{trip_id}'
    leave_room(room)
    emit('left_room', {
        'room': room,
        'message': f'Left trip {trip_id} monitoring'
    })
    
    print(f"User {current_user.full_name} left room {room}")

@socketio.on('request_trip_status', namespace='/safety')
def on_request_trip_status(data):
    """Request current trip status"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    trip_id = data.get('trip_id')
    if not trip_id:
        emit('error', {'message': 'Trip ID required'})
        return
    
    try:
        from app.models import Location, Emergency
        from datetime import datetime
        
        # Get latest locations
        latest_locations = Location.get_latest_for_trip(trip_id, 5)
        
        # Get active alerts
        active_alerts = Emergency.query.filter_by(
            trip_id=trip_id, 
            resolved=False
        ).order_by(Emergency.created_at.desc()).limit(10).all()
        
        emit('trip_status', {
            'trip_id': trip_id,
            'latest_locations': [loc.serialize() for loc in latest_locations],
            'active_alerts': [alert.serialize() for alert in active_alerts],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        emit('error', {'message': 'Failed to get trip status'})
        print(f"Error getting trip status: {str(e)}")

# Server-side event emitters (called from routes.py)
def emit_location_update(trip_id, location_data):
    """Emit location update to trip room"""
    socketio.emit('trip_location_update', location_data, 
                  room=f'trip_{trip_id}', namespace='/safety')

def emit_emergency_alert(trip_id, alert_data):
    """Emit emergency alert to trip room"""
    socketio.emit('trip_alert', alert_data, 
                  room=f'trip_{trip_id}', namespace='/safety')

def emit_alert_update(trip_id, alert_update):
    """Emit alert status update to trip room"""
    socketio.emit('alert_update', alert_update, 
                  room=f'trip_{trip_id}', namespace='/safety')