from flask import request

def register_socketio_events(socketio):
    """Register SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth):
        print(f'Client connected: {request.sid}')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'Client disconnected: {request.sid}')
    
    @socketio.on('join_trip')
    def handle_join_trip(data):
        """Join a trip room for real-time updates"""
        from flask_socketio import join_room
        trip_id = data.get('trip_id')
        if trip_id:
            join_room(f'trip_{trip_id}')
            print(f'Client {request.sid} joined trip room {trip_id}')
    
    @socketio.on('leave_trip')
    def handle_leave_trip(data):
        """Leave a trip room"""
        from flask_socketio import leave_room
        trip_id = data.get('trip_id')
        if trip_id:
            leave_room(f'trip_{trip_id}')
            print(f'Client {request.sid} left trip room {trip_id}')
    
    @socketio.on('location_update')
    def handle_location_update(data):
        """Handle real-time location updates"""
        from flask_socketio import emit
        trip_id = data.get('trip_id')
        if trip_id:
            emit('location_update', data, room=f'trip_{trip_id}', include_self=False)