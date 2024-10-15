from flask_login import UserMixin
from . import db  # Import db from the current package

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    sponsor_code = db.Column(db.String(6), nullable=True)
    
    sponsor = db.relationship('Sponsor', backref='user',uselist=False)

# Sponsor model for storing sponsor-specific information
class Sponsor(db.Model):
    __tablename__ = 'sponsors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign key to User table
    company_name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    website = db.Column(db.String(150), nullable=True)
    bio = db.Column(db.Text, nullable=True)

    # Relationship to job postings
    job_postings = db.relationship('JobPosting', backref='sponsor', lazy=True)

# JobPosting model for storing job postings related to sponsors
class JobPosting(db.Model):
    __tablename__ = 'job_postings'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    salary = db.Column(db.String(50), nullable=False)
    hours = db.Column(db.String(50), nullable=True)
    experience = db.Column(db.String(100), nullable=True)

    # Foreign key to the Sponsor table
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsors.id'), nullable=False)