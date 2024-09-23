from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from .models import User  # Import User model separately
from .routes.auth import auth_bp
from .routes.main import main_bp
from config import Config
import os
from dotenv import load_dotenv

# Create the SQLAlchemy object
db = SQLAlchemy()

def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize the database with the app
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # Redirect to login page if unauthorized
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  # Adjust based on your User model

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()  # Create database tables

    return app
