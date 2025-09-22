from flask import jsonify
from app.api import api_bp

@api_bp.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'edu-safaris-api'})
