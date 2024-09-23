# driverProgram/models.py
import jwt
import os
import time
from flask_login import UserMixin
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    sponsor_code = db.Column(db.String(6), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires=600):
        return jwt.encode(
            {'reset_password': self.username, 'exp': time.time() + expires},
            key=os.getenv('SECRET_KEY_FLASK'),
            algorithm='HS256'
        )

    @staticmethod
    def verify_reset_token(token):
        try:
            payload = jwt.decode(token, key=os.getenv('SECRET_KEY_FLASK'), algorithms=['HS256'])
            username = payload.get('reset_password')
            if username is None:
                return None
        except Exception as e:
            print(f"Token verification error: {e}")
            return None
        return User.query.filter_by(username=username).first()

def ifUsernameExist(username):
    return User.query.filter_by(username=username).first() is not None
