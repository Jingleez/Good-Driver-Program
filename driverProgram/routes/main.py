from datetime import datetime
from flask import Blueprint, logging, render_template, redirect, url_for, session, flash, request, current_app, jsonify
import requests
from driverProgram import db, check_database_connection
from sqlalchemy import text
from flask_login import login_required, current_user
import jwt
from driverProgram.models import JobPosting, Sponsor, Application, Notification, ApplicationSponsor, SponsorCatalog, Behavior, ReviewBoard
from driverProgram.forms import ApplyToJobPosting, JobPostForm, SponsorProfileForm, RewardSystemForm, BehaviorForm
from werkzeug.utils import secure_filename
import os
from ebaysdk.finding import Connection as Finding
from flask_cors import CORS

# Define the blueprint
main_bp = Blueprint('main', __name__)
CORS(main_bp)

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
    load_view_job_postings = session.get('load_view_job_postings', False)
    session.pop('load_view_job_postings', None)

    return render_template('dashboard/driver_dash.html', load_view_job_postings=load_view_job_postings)

@main_bp.route('/sponsor/dashboard')
@login_required
def sponsor_dash():
    load_public_profile = session.get('load_public_profile', False)
    session.pop('load_public_profile', None)

    load_job_postings = session.get('load_job_postings', False)
    session.pop('load_job_postings', None)

    load_approve_applications = session.get('load_approve_applications', False)
    session.pop('load_approve_applications', None)

    load_reward_system = session.get('load_reward_system', False)
    session.pop('load_reward_system', None)

    return render_template('dashboard/sponsor_dash.html',  load_public_profile=load_public_profile, load_job_postings=load_job_postings, load_approve_applications=load_approve_applications, load_reward_system=load_reward_system)

@main_bp.route('/admin/dashboard')
@login_required
def admin_dash():
    return render_template('dashboard/admin_dash.html')




# Routes for displaying the profile, editing the profile, updating the profile information.
@main_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@main_bp.route('/edit_profile', methods=['GET'])
@login_required
def edit_profile():
    return render_template('edit_profile.html', user=current_user)

@main_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    current_user.username = request.form['username']
    current_user.email = request.form['email']
    current_user.phone = request.form.get('phone')
    current_user.address = request.form.get('address')
    current_user.gender = request.form.get('gender')
    current_user.date_of_birth = request.form.get('date_of_birth')
    try:
        db.session.commit()
        flash('Your profile has been updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
    return redirect(url_for('main.profile'))

# Routes for the about page
@main_bp.route('/about')
def about():
    db_status = 'connected' if check_database_connection() else 'disconnected'
    return render_template('Destination/about.html', db_status=db_status)



# Routing links for Admin dashboard
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


# Routing links for sponsor dashboard : { approve applications(Reject, Deny), Participating Drivers, public profile, Job Postings, generate reports, product catalog, notifications }
@main_bp.route('/approve_applications', methods=['GET'])
@login_required
def approve_applications():
    sponsor = current_user.sponsor
    if not sponsor:
        flash('Sponsor profile not found.', 'danger')
        return redirect(url_for('main.dashboard'))
    Notification.query.filter_by(sponsor_id=sponsor.id, is_read=False).update({'is_read': True})
    db.session.commit()
    pending_applications = Application.query.filter_by(status='Pending').all()
    return render_template('sponsor/approve_applications.html', applications=pending_applications)

@main_bp.route('/approve_application/<int:application_id>', methods=['POST'])
@login_required
def approve_application(application_id):
    application = Application.query.get_or_404(application_id)
    application.status = 'Approved'
    db.session.commit()
    flash('Application approved.', 'success')
    session['load_approve_applications'] = True
    return redirect(url_for('main.sponsor_dash')) 

@main_bp.route('/reject_application/<int:application_id>', methods=['POST'])
@login_required
def reject_application(application_id):
    application = Application.query.get_or_404(application_id)
    application.status = 'Denied'
    db.session.commit()
    flash('Application rejected.', 'info')
    session['load_approve_applications'] = True
    return redirect(url_for('main.sponsor_dash')) 

@main_bp.route('/participating-drivers')
@login_required
def participating_drivers():
    approved_drivers = Application.query.join(JobPosting).filter(
        Application.status == 'Approved',
    ).all() 
    return render_template('sponsor/participating_drivers.html',drivers=approved_drivers)

@main_bp.route('/sponsor/public_profile', methods=['GET', 'POST']) 
@login_required
def public_profile():
    form = SponsorProfileForm()
    sponsor = Sponsor.query.filter_by(user_id=current_user.id).first()
    if sponsor is None:
        sponsor = Sponsor(user_id=current_user.id)
    if request.method == 'GET':
        form.company_name.data = sponsor.company_name or ""
        form.location.data = sponsor.location or ""
        form.phone.data = sponsor.phone or ""
        form.email.data = sponsor.email or current_user.email
        form.website.data = sponsor.website or ""
        form.bio.data = sponsor.bio or ""
    if form.validate_on_submit():
        sponsor.company_name = form.company_name.data
        sponsor.location = form.location.data
        sponsor.phone = form.phone.data
        sponsor.email = form.email.data
        sponsor.website = form.website.data
        sponsor.bio = form.bio.data
        if sponsor.id is None:
            db.session.add(sponsor)
        db.session.commit()
        flash('Public profile updated successfully!', 'success')
        session['load_public_profile'] = True
        return redirect(url_for('main.sponsor_dash'))  
    return render_template('sponsor/public_profile.html', sponsor=sponsor, form=form)

@main_bp.route('/job_postings', methods=['GET', 'POST'])
@login_required
def job_postings():
    form = JobPostForm()
    if form.validate_on_submit() and request.method == 'POST':
        new_job = JobPosting(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            salary=form.salary.data,
            hours=form.hours.data,
            experience=form.experience.data,
            sponsor_id=current_user.sponsor.id
        )
        db.session.add(new_job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        session['load_job_postings'] = True
        return redirect(url_for('main.sponsor_dash'))  
    job_postings = JobPosting.query.all()
    return render_template('sponsor/job_postings.html', form=form, job_postings=job_postings)

@main_bp.route('/sponsor/reports')
def sponsor_reports():
    return render_template('sponsor/sponsor_reports.html')


@main_bp.route('/product-catalog', methods=['GET'])
@login_required
def sponsor_product_catalog():
    search_term = request.args.get('searchTerm')
    media_type = request.args.get('mediaType', 'music')

    if search_term:
        url = f"https://itunes.apple.com/search?term={search_term}&media={media_type}&limit=10"
        try:
            response = requests.get(url)
            data = response.json()
            return render_template('sponsor/product_catalog.html', results=data.get("results", []))
        except Exception as e:
            print("Error fetching data from iTunes API:", e)
            return render_template('sponsor/product_catalog.html', error="Error fetching data from iTunes API.")
    
    return render_template('sponsor/product_catalog.html')

@main_bp.route('/add_to_catalog', methods=['POST'])
@login_required
def add_to_catalog():
    data = request.get_json()
    product_id = data.get('product_id')
    product_name = data.get('name')
    product_image = data.get('image')
    product_price = data.get('price')

    # Fetch the sponsor associated with the current user
    sponsor = Sponsor.query.filter_by(user_id=current_user.id).first()
    if not sponsor:
        return jsonify({'error': 'Sponsor account not found'}), 400

    # Validate product price
    if product_price is None:
        return jsonify({'error': 'Product price is missing'}), 400

    try:
        price_in_points = float(product_price) * 100  # Convert to points if required
    except ValueError:
        return jsonify({'error': 'Invalid price format'}), 400

    existing_product = SponsorCatalog.query.filter_by(
        sponsor_id=current_user.sponsor_code,
        product_id=product_id
    ).first()
    if existing_product:
        return jsonify({'message': 'Product already in catalog'}), 400
    new_product = SponsorCatalog(
        sponsor_id=sponsor.id,
        product_id=product_id,
        name=product_name,
        image=product_image,
        price=price_in_points
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product added to catalog'}), 200


@main_bp.route('/sponsor_items')
@login_required
def sponsor_items():
    sponsor = Sponsor.query.filter_by(user_id=current_user.id).first()
    if not sponsor:
        return render_template('error.html', message="Sponsor account not found.")
    sponsor_products = SponsorCatalog.query.filter_by(sponsor_id=sponsor.id).all()
    return render_template('sponsor/sponsor_items.html', products=sponsor_products)



@main_bp.route('/remove_from_catalog', methods=['POST'])
@login_required
def remove_from_catalog():
    data = request.get_json()
    product_id = data.get('product_id')
    sponsor = Sponsor.query.filter_by(user_id=current_user.id).first()
    if not sponsor:
        return jsonify({'error': 'Sponsor account not found'}), 400
    product = SponsorCatalog.query.filter_by(
        sponsor_id=sponsor.id,
        product_id=product_id
    ).first()
    if not product:
        return jsonify({'error': 'Product not found or unauthorized'}), 404
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product removed successfully'}), 200






@main_bp.route('/notifications', methods=['GET'])
@login_required
def view_notifications():
    sponsor = current_user.sponsor
    notifications_list = Notification.query.filter_by(
        sponsor_id=sponsor.id
    ).order_by(Notification.created_at.desc()).all()
    return render_template('sponsor/notification.html', notifications=notifications_list)

@main_bp.route('/notification_details/<int:notification_id>', methods=['GET'])
@login_required
def notification_details(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    application = Application.query.get(notification.application_id)
    if application:
        return jsonify({
            'first_name': application.first_name,
            'last_name': application.last_name,
            'email': application.email,
            'phone': application.phone,
            'date_submitted': application.date_submitted.strftime('%Y-%m-%d')
        })
    return jsonify({'error': 'Application not found'}), 404

@main_bp.route('/archive_notification/<int:notification_id>', methods=['POST'])
@login_required
def archive_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    db.session.delete(notification)
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/reward_system', methods=['GET', 'POST'])
@login_required
def reward_system():
    form = BehaviorForm()
    if form.validate_on_submit() and request.method == 'POST':
        new_behavior = Behavior(
            name=form.name.data,
            type=form.type.data,
            point_value=form.point_value.data,
            sponsor_id=current_user.sponsor.id  # Assuming the sponsor adds the behavior
        )
        db.session.add(new_behavior)
        db.session.commit()
        flash('Behavior added successfully!', 'success')
        session['load_reward_system'] = True
        return redirect(url_for('main.sponsor_dash'))  # Redirect to sponsor dashboard or desired page

    behaviors = Behavior.query.all()  # Fetch all behaviors from the database
    return render_template('sponsor/reward_system.html', form=form, behaviors=behaviors)





# Routing links for driver dashboard { view : {organizations, Job Postings, submitted applications, } , apply to job postings  }
@main_bp.route('/driver/points')
@login_required
def view_points():
    return render_template('driver/view_points.html') 

@main_bp.route('/redeem_rewards')
@login_required
def redeem_rewards():
    if current_user.role != "Driver" or not current_user.sponsor_code:
        return render_template('driver/redeem_rewards.html', rewards=[], error="No associated sponsor or catalog found.")
    sponsor_products = SponsorProduct.query.filter_by(sponsor_id=current_user.sponsor_code).all()
    return render_template('driver/redeem_rewards.html', rewards=sponsor_products)

@main_bp.route('/driver/review-purchases')
@login_required
def review_purchases():
    return render_template('driver/review_purchases.html') 

@main_bp.route('/view_organizations', methods=['GET'])
@login_required
def view_organizations():
    organizations = Sponsor.query.all()  
    return render_template('Destination/view_organizations.html', organizations=organizations)

@main_bp.route('/view_job_postings', methods=['GET'])
@login_required
def view_job_postings():
    company = request.args.get('company')
    title = request.args.get('title')
    location = request.args.get('location')
    salary = request.args.get('salary')
    hours = request.args.get('hours')
    experience = request.args.get('experience')
    query = JobPosting.query
    if company:
        query = query.filter(JobPosting.company.ilike(f'%{company}%'))
    if title:
        query = query.filter(JobPosting.title.ilike(f'%{title}%'))
    if location:
        query = query.filter(JobPosting.location.ilike(f'%{location}%'))
    if salary:
        query = query.filter(JobPosting.salary == salary)
    if hours:
        query = query.filter(JobPosting.hours == hours)
    if experience:
        query = query.filter(JobPosting.experience == experience)
    job_postings = JobPosting.query.all()
    return render_template('Destination/view_job_postings.html', job_postings=job_postings)

@main_bp.route('/apply_to_job_posting/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_to_job_posting(job_id):
    form = ApplyToJobPosting()
    job = JobPosting.query.get_or_404(job_id)
    if form.validate_on_submit():
        resume_file = form.resume.data
        filename = secure_filename(resume_file.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        resume_path = os.path.join(upload_folder, filename)
        resume_file.save(resume_path)
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
        sponsor = job.sponsor
        notification_message = f"New application from {new_application.first_name} {new_application.last_name} for the job '{job.title}'."
        notification = Notification(
            message=notification_message,
            sponsor_id=sponsor.id,
            job_id=job.id,
            application_id=new_application.id,
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.session.add(notification)
        db.session.commit()
        flash('Your application has been submitted successfully.', 'success')
        session['load_view_job_postings'] = True
        return redirect(url_for('main.driver_dash'))  
    return render_template('driver/apply_to_job_posting.html', form=form, job=job)

@main_bp.route('/driver/submitted_applications', methods=['GET'])
@login_required
def submitted_applications():
    applications = Application.query.filter_by(user_id=current_user.id).all()
    return render_template('driver/submitted_applications.html', applications=applications)
