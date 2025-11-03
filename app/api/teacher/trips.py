@trip_api.route('/trip/<int:trip_id>/publish', methods=['POST'])
def publish_trip(trip_id):
    """Publish a draft trip"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        
        if trip.status != 'draft':
            return jsonify({
                'success': False,
                'error': 'Only draft trips can be published'
            }), 400
        
        trip.publish()
        
        return jsonify({
            'success': True,
            'message': 'Trip published successfully',
            'trip': trip.serialize()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_api.route('/trip/<int:trip_id>/registration/open', methods=['POST'])
def open_registration(trip_id):
    """Open registration for a published trip"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        
        if trip.status != 'published':
            return jsonify({
                'success': False,
                'error': 'Only published trips can open registration'
            }), 400
        
        trip.open_registration()
        
        return jsonify({
            'success': True,
            'message': 'Registration opened successfully',
            'trip': trip.serialize()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_api.route('/trip/<int:trip_id>/registration/close', methods=['POST'])
def close_registration(trip_id):
    """Close registration for a trip"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        
        if trip.status not in ['published', 'registration_open']:
            return jsonify({
                'success': False,
                'error': 'Registration is not open for this trip'
            }), 400
        
        trip.close_registration()
        
        return jsonify({
            'success': True,
            'message': 'Registration closed successfully',
            'trip': trip.serialize()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_api.route('/trip/<int:trip_id>/start', methods=['POST'])
def start_trip(trip_id):
    """Start a trip"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        
        if not trip.can_start():
            return jsonify({
                'success': False,
                'error': 'Trip cannot be started yet'
            }), 400
        
        trip.start_trip()
        
        return jsonify({
            'success': True,
            'message': 'Trip started successfully',
            'trip': trip.serialize()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_api.route('/trip/<int:trip_id>/complete', methods=['POST'])
def complete_trip(trip_id):
    """Complete a trip"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        
        if trip.status != 'in_progress':
            return jsonify({
                'success': False,
                'error': 'Only trips in progress can be completed'
            }), 400
        
        trip.complete_trip()
        
        return jsonify({
            'success': True,
            'message': 'Trip completed successfully',
            'trip': trip.serialize()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_api.route('/trip/<int:trip_id>/cancel', methods=['POST'])
def cancel_trip(trip_id):
    """Cancel a trip"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        
        if trip.status in ['completed', 'cancelled']:
            return jsonify({
                'success': False,
                'error': 'Trip is already completed or cancelled'
            }), 400
        
        reason = request.json.get('reason') if request.json else None
        trip.cancel_trip(reason)
        
        return jsonify({
            'success': True,
            'message': 'Trip cancelled successfully',
            'trip': trip.serialize()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500