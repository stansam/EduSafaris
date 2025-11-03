from app.config_dir.cli.init_db import init_db

def register_cli_commands(app):
    """Register CLI commands with Flask app"""
    app.cli.add_command(init_db)