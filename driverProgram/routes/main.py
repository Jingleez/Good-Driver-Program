from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, session, flash, request, current_app
from driverProgram import db 
from driverProgram import check_database_connection
from sqlalchemy import text 
from flask_login import login_required, current_user
import jwt
from driverProgram.models import JobPosting, Sponsor, Application, Notification, ApplicationSponsor
from driverProgram.forms import ApplyToJobPosting, JobPostForm, SponsorProfileForm
from werkzeug.utils import secure_filename
import os

# Define the blueprint
main_bp = Blueprint('main', __name__)

# Authentication check helper function
def is_token_valid(token):
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

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




# Admin dashboard navigation links
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





# Sponsor dashboard navigation links
@main_bp.route('/approve_applications', methods=['GET'])
@login_required
def approve_applications():
    sponsor = current_user.sponsor
    if not sponsor:
        flash('Sponsor profile not found.', 'danger')
        return redirect(url_for('main.dashboard'))
    # Mark notifications related to applications as read
    Notification.query.filter_by(sponsor_id=sponsor.id, is_read=False).update({'is_read': True})
    db.session.commit()
    pending_applications = Application.query.join(ApplicationSponsor).filter(
        ApplicationSponsor.sponsor_id == sponsor.id,
        ApplicationSponsor.status == 'pending'
    ).all()
    return render_template('sponsor/approve_applications.html', applications=pending_applications)

@main_bp.route('/approve_application/<int:application_id>/<string:action>', methods=['POST'])
@login_required
def approve_application_action(application_id, action):
    sponsor = current_user.sponsor
    if not sponsor:
        flash('Sponsor profile not found.', 'danger')
        return redirect(url_for('main.dashboard'))
    association = ApplicationSponsor.query.filter_by(
        application_id=application_id,
        sponsor_id=sponsor.id
    ).first()
    if not association:
        flash('Application not found or already processed.', 'danger')
        return redirect(url_for('main.approve_applications'))
    if action == 'approve':
        association.status = 'accepted'
        db.session.commit()
        # Remove notification for this application for all sponsors in the organization
        Notification.query.filter_by(application_id=application_id).delete()
        db.session.commit()
        flash('Application approved.', 'success')
    elif action == 'reject':
        association.status = 'rejected'
        db.session.commit()
        flash('Application rejected.', 'info')
    else:
        flash('Invalid action.', 'danger')
    return redirect(url_for('main.approve_applications'))


@main_bp.route('/sponsor/product-catalog')
@login_required
def sponsor_product_catalog():
    return render_template('sponsor/product_catalog.html')

@main_bp.route('/participating-drivers')
@login_required
def participating_drivers():
    return render_template('sponsor/participating_drivers.html')

@main_bp.route('/sponsor/public_profile', methods=['GET', 'POST']) 
@login_required
def public_profile():
    form = SponsorProfileForm()

    # Check if the current user has a sponsor associated
    sponsor = Sponsor.query.filter_by(user_id=current_user.id).first()

    # If no sponsor record exists, create a blank sponsor record
    if sponsor is None:
        sponsor = Sponsor(user_id=current_user.id)  # Creating an empty sponsor object for the current user

    # Prepopulate the form with sponsor details if they exist
    if request.method == 'GET':
        form.company_name.data = sponsor.company_name or ""
        form.location.data = sponsor.location or ""
        form.phone.data = sponsor.phone or ""
        form.email.data = sponsor.email or current_user.email  # Prepopulate email with the user's email if sponsor email is not set
        form.website.data = sponsor.website or ""
        form.bio.data = sponsor.bio or ""

    if form.validate_on_submit():
        # Update sponsor record with form data
        sponsor.company_name = form.company_name.data
        sponsor.location = form.location.data
        sponsor.phone = form.phone.data
        sponsor.email = form.email.data
        sponsor.website = form.website.data
        sponsor.bio = form.bio.data

        # Add new sponsor if it's not already in the database
        if sponsor.id is None:
            db.session.add(sponsor)

        db.session.commit()
        flash('Public profile updated successfully!', 'success')

        # After updating, render the updated profile view
        return render_template('sponsor/public_profile.html', sponsor=sponsor, form=form)

    # Render the profile view (GET request)
    return render_template('sponsor/public_profile.html', sponsor=sponsor, form=form)

@main_bp.route('/job_postings', methods=['GET', 'POST'])
@login_required
def job_postings():
    form = JobPostForm()

    if form.validate_on_submit() and request.method == 'POST':
        # Create a new job posting
        new_job = JobPosting(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            salary=form.salary.data,
            hours=form.hours.data,
            experience=form.experience.data,
            sponsor_id=current_user.sponsor.id  # Ensure that sponsor_id is saved
        )
        db.session.add(new_job)
        db.session.commit()

        # Flash success message and redirect
        flash('Job posted successfully!', 'success')
        return redirect(url_for('main.job_postings'))

    # Fetch all job postings without filtering by sponsor
    job_postings = JobPosting.query.all()

    return render_template('sponsor/job_postings.html', form=form, job_postings=job_postings)



@main_bp.route('/view_job_postings', methods=['GET'])
@login_required
def view_job_postings():
    job_postings = JobPosting.query.filter_by(sponsor_id=current_user.sponsor.id).all()
    return render_template('sponsor/view_job_postings.html', job_postings=job_postings)








# Driver dashboard navigation links
@main_bp.route('/driver/points')
@login_required
def view_points():
    return render_template('driver/view_points.html') 

@main_bp.route('/driver/redeem-rewards')
@login_required
def redeem_rewards():
    return render_template('driver/redeem_rewards.html') 

@main_bp.route('/driver/product-catalog')
@login_required
def driver_product_catalog():
    return render_template('driver/product_catalog.html')  

@main_bp.route('/driver/review-purchases')
@login_required
def review_purchases():
    return render_template('driver/review_purchases.html') 



# Route for viewing all organization profiles
@main_bp.route('/view_organizations', methods=['GET'])
@login_required
def view_organizations():
    # Query the database for all organizations (sponsors)
    organizations = Sponsor.query.all()  
    return render_template('Destination/view_organizations.html', organizations=organizations)

# Route for driver applications
@main_bp.route('/apply_to_job_posting/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_to_job_posting(job_id):
    form = ApplyToJobPosting()
    job = JobPosting.query.get_or_404(job_id)
    if form.validate_on_submit():
        # Handle file saving
        resume_file = form.resume.data
        filename = secure_filename(resume_file.filename)
        resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        resume_file.save(resume_path)
        # Create a new application
        new_application = Application(
            user_id=current_user.id,
            job_id=job_id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            resume=filename,
            date_submitted=datetime.utcnow()
        )
        db.session.add(new_application)
        db.session.commit()
        # Create notifications for all sponsors in the organization
        #organization = job.organization
        #for sponsor in organization.sponsors:
        #    notification_message = f"New application from {new_application.first_name} {new_application.last_name} for the job {job.title}."
        #    notification = Notification(
        #        message=notification_message,
        #        sponsor_id=sponsor.id,
        #       job_id=job.id,
        #       application_id=new_application.id
        #   )
        #    db.session.add(notification)
        #db.session.commit()
        flash('Your application has been submitted successfully.', 'success')
        return redirect(url_for('main.job_postings'))
    return render_template('Destination/apply_to_job_posting.html', form=form, job=job)


@main_bp.route('/notifications', methods=['GET'])
@login_required
def notifications():
    #unread_notifications = Notification.query.filter_by(sponsor_id=sponsor.id, is_read=False).all()
    return render_template('sponsor/notification.html')
