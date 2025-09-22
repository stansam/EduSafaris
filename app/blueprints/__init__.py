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