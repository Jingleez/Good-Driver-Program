from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from driverProgram import db 
from driverProgram import check_database_connection
from sqlalchemy import text 
from flask_login import login_required, current_user
import jwt

# Define the blueprint
main_bp = Blueprint('main', __name__)

# Route for the dashboard, with authentication check and role-based redirection
@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Retrieve user role from the session or database
    user_role = session.get('user_role', current_user.role)
    
    # Redirect based on role
    if user_role == 'driver':
        return redirect(url_for('main.driver_dash'))
    elif user_role == 'sponsor':
        return redirect(url_for('main.sponsor_dash'))
    elif user_role == 'admin':
        return redirect(url_for('main.admin_dash'))
    else:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))
    
# Route for the home/destination page
@main_bp.route('/')
@main_bp.route('/destination')
def destination():
    return render_template('Destination/destination.html')

# Routes for each role-specific dashboard
@main_bp.route('/driver/dashboard')
@login_required
def driver_dash():
    return render_template('dashboard/driver_dash.html')

@main_bp.route('/sponsor/dashboard')
@login_required
def sponsor_dash():
    return render_template('dashboard/sponsor_dash.html')

@main_bp.route('/admin/dashboard')
@login_required
def admin_dash():
    return render_template('dashboard/admin_dash.html')

# Route for displaying the profile
@main_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    return render_template('profile.html', user=current_user)

# Route for editing the profile
@main_bp.route('/edit_profile', methods=['GET'])
@login_required
def edit_profile():
    return render_template('edit_profile.html', user=current_user)

# Route for updating the profile information
@main_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # Update user information from the form
    current_user.username = request.form['username']
    current_user.email = request.form['email']
    current_user.phone = request.form.get('phone')
    current_user.address = request.form.get('address')
    current_user.gender = request.form.get('gender')
    current_user.date_of_birth = request.form.get('date_of_birth')

    # Save changes to the database
    try:
        db.session.commit()
        flash('Your profile has been updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('main.profile'))

@main_bp.route('/about')
def about():
    db_status = 'connected' if check_database_connection() else 'disconnected'
    return render_template('Destination/about.html', db_status=db_status)

# New route for the public profile of sponsors
@main_bp.route('/public_profile', methods=['GET', 'POST'])
@login_required
def public_profile():
    if request.method == 'POST':
        # Retrieve and update sponsor details from form
        sponsor = current_user.sponsor  # Assuming current_user is linked to a Sponsor model
        sponsor.company_name = request.form['company_name']
        sponsor.location = request.form['location']
        sponsor.phone = request.form['phone']
        sponsor.email = request.form['email']
        sponsor.website = request.form['website']
        sponsor.bio = request.form['bio']
        db.session.commit()
        flash('Public profile updated successfully!', 'success')
        return redirect(url_for('main.public_profile'))
    
    sponsor = current_user.sponsor
    return render_template('sponsor/public_profile.html', sponsor=sponsor)

# New route for sponsor job postings
@main_bp.route('/job_postings', methods=['GET', 'POST'])
@login_required
def job_postings():
    if request.method == 'POST':
        # Create new job posting from form
        new_job = JobPosting(
            title=request.form['title'],
            description=request.form['description'],
            location=request.form['location'],
            salary=request.form['salary'],
            hours=request.form['hours'],
            experience=request.form['experience'],
            sponsor_id=current_user.sponsor.id
        )
        db.session.add(new_job)
        db.session.commit()
        flash('Job posting created successfully!', 'success')
        return redirect(url_for('main.job_postings'))
    
    jobs = JobPosting.query.filter_by(sponsor_id=current_user.sponsor.id).all()
    return render_template('sponsor/job_postings.html', jobs=jobs)


# Authentication check helper function
def is_token_valid(token):
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False
    
@main_bp.route('/manage_users')
@login_required
def manage_users():
    return render_template('admin/manage_users.html')

@main_bp.route('/review-reports')
@login_required
def review_reports():
    return render_template('admin/review_reports.html')

@main_bp.route('/add-users')
@login_required
def add_users():
    return render_template('admin/add_users.html')

@main_bp.route('/admin-reports')
@login_required
def admin_reports():
    return render_template('admin/admin_reports.html')

@main_bp.route('/approve-applications')
@login_required
def approve_applications():
    return render_template('partials/approve_applications.html')

@main_bp.route('/sponsor/product-catalog')
@login_required
def sponsor_product_catalog():
    return render_template('partials/product_catalog.html')

@main_bp.route('/participating-drivers')
@login_required
def participating_drivers():
    return render_template('partials/participating_drivers.html')

@main_bp.route('/driver/points')
@login_required
def view_points():
    return render_template('partials/view_points.html')  # Ensure this template exists

@main_bp.route('/driver/redeem-rewards')
@login_required
def redeem_rewards():
    return render_template('partials/redeem_rewards.html')  # Ensure this template exists

@main_bp.route('/driver/product-catalog')
@login_required
def driver_product_catalog():
    return render_template('partials/product_catalog.html')  # Ensure this template exists

@main_bp.route('/driver/review-purchases')
@login_required
def review_purchases():
    return render_template('partials/review_purchases.html')  # Ensure this template exists
