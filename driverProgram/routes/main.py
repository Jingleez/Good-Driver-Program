from flask import Blueprint, render_template, redirect, url_for, session, flash, request
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
    return render_template('dashboard/destination.html')
    
@main_bp.route('/messages')
def messages():
    return render_template('Destination/messages.html') 

@main_bp.route('/browse-organizations')
def browse_organizations():
    return render_template('Destination/browse_organizations.html')  

@main_bp.route('/current-organization')
def current_organization():
    return render_template('Destination/current_organization.html')  

@main_bp.route('/sponsor/dashboard', methods=['GET'])
def sponsor_dash():
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return only the content section for AJAX requests
        return render_template('partials/sponsor_dash_content.html')
    return render_template('dashboard/sponsor_dash.html')

@main_bp.route('/driver/dashboard', methods=['GET'])
def driver_dash():
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('partials/driver_dash_content.html')
    return render_template('dashboard/driver_dash.html')

@main_bp.route('/admin/dashboard', methods=['GET'])
def admin_dash():
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('partials/admin_dash_content.html')
    return render_template('dashboard/admin_dash.html')

@main_bp.route('/participating-drivers', methods=['GET'])
def participating_drivers():
    return render_template('partials/participating_drivers.html')

@main_bp.route('/approve-applications', methods=['GET'])
def approve_applications():
    return render_template('partials/approve_applications.html')

# Route for sponsor product catalog
@main_bp.route('/sponsor/product-catalog', methods=['GET'])
def sponsor_product_catalog():
    return render_template('partials/product_catalog.html')

# Route for managing users
@main_bp.route('/manage-users')
def manage_users():
    return render_template('admin/manage_users.html')

# Route for reviewing reports
@main_bp.route('/review-reports')
def review_reports():
    return render_template('admin/review_reports.html')

# Route for adding new users
@main_bp.route('/add-users')
def add_users():
    return render_template('admin/add_users.html')

# Route for generating reports
@main_bp.route('/admin-reports')
def admin_reports():
    return render_template('admin/admin_reports.html')

# Route for driver profile
@main_bp.route('/driver/profile')
def driver_profile():
    return render_template('partials/driver_profile.html')

# Route for viewing driver points
@main_bp.route('/driver/points')
def view_points():
    return render_template('partials/view_points.html')

# Route for redeeming rewards
@main_bp.route('/driver/redeem-rewards')
def redeem_rewards():
    return render_template('partials/redeem_rewards.html')

# Route for browsing driver-specific sponsor catalog
@main_bp.route('/driver/product-catalog')
def driver_product_catalog():
    return render_template('partials/product_catalog.html', endpoint="driver_product_catalog")

# Route for reviewing purchases
@main_bp.route('/driver/review-purchases')
def review_purchases():
    return render_template('partials/review_purchases.html')
