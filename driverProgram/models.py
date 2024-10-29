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

# Application model for storing driver job applications
class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    resume = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    date_submitted = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    # Relationships to job postings and users
    user = db.relationship('User', backref='applications')
    job = db.relationship('JobPosting', backref='applications')


# New ApplicationSponsor model (many-to-many between applications and sponsors)
class ApplicationSponsor(db.Model):
    __tablename__ = 'application_sponsor'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsors.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # Status of the application for this sponsor
    # Foreign key relationships
    application = db.relationship('Application', backref='application_sponsors')
    sponsor = db.relationship('Sponsor', backref='application_sponsors')

# Notification model
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsors.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # Relationships
    sponsor = db.relationship('Sponsor', backref='notifications')
