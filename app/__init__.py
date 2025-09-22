import os
from flask import Flask, render_template, request
from flask_login import current_user
import logging
from logging.handlers import RotatingFileHandler

def create_app(config_name=None):
    """Create and configure Flask application"""
    app = Flask(__name__)

    # ------------ Logging setup ------------------------------

    # Creation of logs folder 
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    # File handler (resets after certain file size, to prevent infinite growth)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"), maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Stream handler (console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Attach handlers to app.logger
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    # --------------- End logging setup ------------------

    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    from app.extensions import db, migrate, login_manager, mail, jwt, socketio, cors
    
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    socketio.init_app(app, 
                     cors_allowed_origins="*",
                     async_mode=app.config['SOCKETIO_ASYNC_MODE'])
    
    # Configure Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.blueprints import register_blueprints
    register_blueprints(app)

    # Register Jinja filters and globals
    from app.temp_vars import register_jinja_extensions
    register_jinja_extensions(app)
    
    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    # Register CLI commands
    from app.cli import register_cli_commands
    register_cli_commands(app)

    # Add SocketIO event handlers
    from app.sockets import register_socketio_events
    register_socketio_events(socketio)
    
    return app

# Import models to ensure they are registered with SQLAlchemy
from app import models

# Export socketio for run.py
from app.extensions import socketio