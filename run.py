#!/usr/bin/env python3
import os
from app import create_app, socketio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Use SocketIO for development with proper host binding
    if os.getenv('FLASK_ENV') == 'development':
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    else:
        socketio.run(app, host='0.0.0.0', port=5000)