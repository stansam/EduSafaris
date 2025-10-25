import os 
import click
from flask.cli import with_appcontext
from app.config_dir.cli.trips_cmd import seed_trips_command

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
            first_name='Cindy',
            last_name='Cheptoo',
            role='admin',
            is_active=True,
            is_verified=True
        )
        admin.password = password
        
        db.session.add(admin)
        db.session.commit()
        
        print(f'Admin user created: {email}')
    @app.cli.command("seed-trips")
    @click.command('seed-trips')
    @click.option('--clear', is_flag=True, help='Clear existing trips before seeding')
    @with_appcontext
    def extra_trips(clear):
        seed_trips_command(clear)
