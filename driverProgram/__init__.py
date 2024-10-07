from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os
from dotenv import load_dotenv
from flask_mail import Mail
from datetime import timedelta

def check_database_connection():
    try:
        # Test a simple query to check the connection
        db.session.execute('SELECT 1')
        return True
    except:
        return False

import boto3

load_dotenv()



app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
mail = Mail()

# AWS Cognito configuration
CognitoUserPoolId = os.environ.get('COGNITO_USER_POOL_ID')
CognitoClientId = os.environ.get('COGNITO_CLIENT_ID')
CognitoRegion = os.environ.get('COGNITO_REGION')

# Create a Cognito client
cognito_client = boto3.client('cognito-idp', region_name=CognitoRegion)

def check_database_connection():
    try:
        # Test a simple query to check the connection
        db.session.execute('SELECT 1')
        return True
    except:
        return False


# Initialize Flask-Login's LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    """This callback is used to reload the user object from the user ID stored in the session."""
    from .models import User
    return User.query.get(int(user_id))

def create_app():
    login_manager.init_app(app)

    from .routes.auth import auth_bp
    from .routes.main import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Mail configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    mail.init_app(app)

    # Remember cookie duration
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)

    # Create the database tables if they don't exist yet
    with app.app_context():
        db.create_all()

    return app