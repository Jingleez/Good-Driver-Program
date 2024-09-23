from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os
from dotenv import load_dotenv

# Create the Flask app instance
app = Flask(__name__)
app.config.from_object(Config)

# Initialize the SQLAlchemy instance here
db = SQLAlchemy(app)

def create_app():
    load_dotenv()

    # Initialize the LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User  # Import here to avoid circular import
        return User.query.get(int(user_id))

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()  # Create database tables

    return app
