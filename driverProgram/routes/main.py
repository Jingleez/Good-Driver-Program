# driverProgram/routes/main.py
from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user  

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def destination():
    return render_template('Destination/destination.html')

@main_bp.route('/about')  
def about():
    db_status = "Unknown"
    try:
        db.session.execute('SELECT 1')
        db_status = "Database connection successful!"
    except Exception as e:
        db_status = f"Database connection failed: {str(e)}"

    return render_template('Destination/about.html', db_status=db_status)