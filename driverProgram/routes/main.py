# driverProgram/routes/main.py
from flask import Blueprint, render_template, redirect, url_for, session, flash
from driverProgram import db
from sqlalchemy import text 

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

@main_bp.route('/dashboard')
def dashboard():
    user_role = session.get('user_role')  
    if user_role == 'driver':
        return render_template('dashboard/driver_dash.html')  
    elif user_role == 'sponsor':
        return render_template('dashboard/sponsor_dash.html')  
    else:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.destination'))
    
@main_bp.route('/messages')
def messages():
    return render_template('Destination/messages.html') 

@main_bp.route('/browse-organizations')
def browse_organizations():
    return render_template('Destination/browse_organizations.html')  

@main_bp.route('/current-organization')
def current_organization():
    return render_template('Destination/current_organization.html')  
