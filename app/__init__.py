"""
Flask Application Factory for Edu Safaris
"""
import os
from flask import Flask, render_template, request
from flask_login import current_user

def create_app(config_name=None):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
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
    register_blueprints(app)
    
    # Register Jinja filters and globals
    register_jinja_extensions(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    # Add SocketIO event handlers
    register_socketio_events(socketio)
    
    return app

def register_blueprints(app):
    """Register application blueprints"""
    
    # Main/Home blueprint
    from app.main import main_bp
    app.register_blueprint(main_bp)
    
    # Authentication blueprint
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Profiles blueprint
    from app.profiles import profiles_bp
    app.register_blueprint(profiles_bp, url_prefix='/profiles')
    
    # Trips blueprint
    from app.trips import trips_bp
    app.register_blueprint(trips_bp, url_prefix='/trips')
    
    # Admin blueprint
    from app.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Vendor blueprint
    from app.vendor import vendor_bp
    app.register_blueprint(vendor_bp, url_prefix='/vendor')
    
    # API blueprint
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

def register_jinja_extensions(app):
    """Register Jinja2 filters and global functions"""
    
    @app.template_filter('currency')
    def currency_filter(amount, currency='USD'):
        """Format currency for display"""
        from app.utils import format_currency
        return format_currency(amount, currency)
    
    @app.template_filter('phone')
    def phone_filter(phone):
        """Format phone number for display"""
        from app.utils import format_phone
        return format_phone(phone)
    
    @app.template_filter('datetime')
    def datetime_filter(datetime_obj, format='%Y-%m-%d %H:%M'):
        """Format datetime for display"""
        if datetime_obj:
            return datetime_obj.strftime(format)
        return ''
    
    @app.template_filter('date')
    def date_filter(date_obj, format='%Y-%m-%d'):
        """Format date for display"""
        if date_obj:
            return date_obj.strftime(format)
        return ''
    
    @app.template_global()
    def get_active_ads(placement=None):
        """Get active advertisements for current user"""
        from app.models import Advertisement
        return Advertisement.get_active_ads_for_user(current_user, placement)
    
    @app.template_global()
    def get_unread_notifications():
        """Get unread notifications for current user"""
        if current_user.is_authenticated:
            from app.models import Notification
            return Notification.query.filter_by(
                recipient_id=current_user.id,
                is_read=False
            ).order_by(Notification.created_at.desc()).limit(5).all()
        return []

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        from app.extensions import db
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def file_too_large_error(error):
        return render_template('errors/413.html'), 413

def register_cli_commands(app):
    """Register CLI commands"""
    
    @app.cli.command()
    def init_db():
        """Initialize the database"""
        from app.extensions import db
        db.create_all()
        print('Database initialized.')
    
    @app.cli.command()
    def seed_db():
        """Seed the database with initial data"""
        from app.seed import seed_database
        seed_database()
        print('Database seeded with initial data.')
    
    @app.cli.command()
    def create_admin():
        """Create admin user"""
        from app.models import User
        from app.extensions import db
        
        email = os.environ.get('ADMIN_EMAIL', 'admin@edusafaris.com')
        password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        # Check if admin already exists
        admin = User.query.filter_by(email=email).first()
        if admin:
            print(f'Admin user {email} already exists.')
            return
        
        # Create admin user
        admin = User(
            email=email,
            first_name='Admin',
            last_name='User',
            role='admin',
            is_active=True,
            is_verified=True
        )
        admin.password = password
        
        db.session.add(admin)
        db.session.commit()
        
        print(f'Admin user created: {email}')

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

# Import models to ensure they are registered with SQLAlchemy
from app import models

# Export socketio for run.py
from app.extensions import socketio