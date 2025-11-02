from flask import jsonify
from app.api import api_bp

@api_bp.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'edu-safaris-api'})

@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404


@api_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500
