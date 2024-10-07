# driverProgram/routes/main.py
from flask import Blueprint, render_template, redirect, url_for, session, flash
from driverProgram import db
from sqlalchemy import text 
import jwt


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def destination():
    return render_template('Destination/destination.html')

@main_bp.route('/about')  
def about():
    db_status = "Unknown"
    try:
        db.session.execute(text('SELECT 1'))
        db_status = "Database connection successful!"
    except Exception as e:
        db_status = f"Database connection failed: {str(e)}"
    return render_template('Destination/about.html', db_status=db_status)


def is_token_valid(token):
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

@main_bp.route('/dashboard')
def dashboard():
    if 'id_token' not in session or not is_token_valid(session['id_token']):
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth_bp.login'))
    return render_template('dashboard/driver_dash.html')
    
@main_bp.route('/messages')
def messages():
    return render_template('Destination/messages.html') 

@main_bp.route('/browse-organizations')
def browse_organizations():
    return render_template('Destination/browse_organizations.html')  

@main_bp.route('/current-organization')
def current_organization():
    return render_template('Destination/current_organization.html')  

@main_bp.route('/admin/dashboard', methods=['GET'])
def admin_dash():
    return render_template('dashboard/admin_dash.html')

@main_bp.route('/driver/dashboard', methods=['GET'])
def driver_dash():
    return render_template('dashboard/driver_dash.html')

@main_bp.route('/sponsor/dashboard', methods=['GET'])
def sponsor_dash():
    return render_template('dashboard/sponsor_dash.html')
