from datetime import datetime
from flask import Blueprint, logging, render_template, redirect, url_for, session, flash, request, current_app, jsonify, Response, current_app, send_file
import requests, pandas as pd
from driverProgram import db, check_database_connection
from sqlalchemy import text
from flask_login import login_required, current_user
import jwt
from driverProgram.models import JobPosting, Sponsor, Application, Notification, ApplicationSponsor, SponsorCatalog, Behavior, ReviewBoard, Wishlist, PointTransaction, User, Cart, AuditLog
from driverProgram.forms import ApplyToJobPosting, JobPostForm, SponsorProfileForm, BehaviorForm, PointTransactionForm
from werkzeug.utils import secure_filename
import os
from ebaysdk.finding import Connection as Finding
from flask_cors import CORS
from datetime import datetime, timezone
from driverProgram.controllers.report_controller import ReportController
import csv
from io import StringIO


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
    
@main_bp.route('/download_audit_logs', methods=['GET'])
@login_required
def download_audit_logs():
    log_type = request.args.get('log_type')  # Log type to filter by
    query = AuditLog.query

    # Filter logs by log_type if provided
    if log_type:
        query = query.filter_by(log_type=log_type)

    logs = query.order_by(AuditLog.log_date.desc()).all()

    # Prepare CSV data
    import csv
    from io import StringIO

    csv_output = StringIO()
    csv_writer = csv.writer(csv_output)

    # Set header and rows based on log_type
    if log_type == "driver_app":
        csv_writer.writerow(['Date', 'Sponsor ID', 'Driver ID', 'Status', 'Reason'])
        for log in logs:
            csv_writer.writerow([
                log.log_date.strftime('%Y-%m-%d %H:%M:%S'),
                log.sponsor_id,
                log.driver_id,
                log.status,
                log.reason
            ])
    elif log_type == "point_change":
        csv_writer.writerow(['Date', 'Sponsor ID', 'Driver ID', 'Points', 'Reason'])
        for log in logs:
            csv_writer.writerow([
                log.log_date.strftime('%Y-%m-%d %H:%M:%S'),
                log.sponsor_id,
                log.driver_id,
                log.points,
                log.reason
            ])
    elif log_type == "password_change":
        csv_writer.writerow(['Date', 'User ID', 'Change Type'])
        for log in logs:
            csv_writer.writerow([
                log.log_date.strftime('%Y-%m-%d %H:%M:%S'),
                log.user_id,
                log.change_type
            ])
    elif log_type == "login_attempt":
        csv_writer.writerow(['Date', 'Username', 'Status'])
        for log in logs:
            csv_writer.writerow([
                log.log_date.strftime('%Y-%m-%d %H:%M:%S'),
                log.username,
                log.status
            ])
    else:
        # Default header for all logs
        csv_writer.writerow(['Date', 'Log Type', 'Sponsor ID', 'Driver ID', 'User ID', 'Status', 'Reason', 'Points', 'Username', 'Change Type'])
        for log in logs:
            csv_writer.writerow([
                log.log_date.strftime('%Y-%m-%d %H:%M:%S'),
                log.log_type,
                log.sponsor_id,
                log.driver_id,
                log.user_id,
                log.status,
                log.reason,
                log.points,
                log.username,
                log.change_type
            ])

    # Create a response object
    csv_output.seek(0)
    return Response(
        csv_output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename={log_type or "all"}_audit_logs.csv'}
    )

# Route for the dashboard, with authentication check and role-based redirection
@main_bp.route('/dashboard')
@login_required
def dashboard():
    user_role = session.get('user_role', current_user.role)
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
@main_bp.route('/manage_users', endpoint='manage_users')
@login_required
def sponsors_drivers():
    sponsors = Sponsor.query.all()
    sponsors_with_drivers = []
    for sponsor in sponsors:
        drivers = Application.query.join(User, Application.user_id == User.id).add_columns( Application.user_id.label('UserID'), Application.job_id.label('JobID'), (Application.first_name + ' ' + Application.last_name).label('Name') ).all()
        sponsors_with_drivers.append({ "sponsor": sponsor, "drivers": [{"UserID": d.UserID, "JobID": d.JobID, "Name": d.Name} for d in drivers] })
    return render_template('admin/manage_users.html', sponsors_with_drivers=sponsors_with_drivers)


@main_bp.route('/review-reports')
@login_required
def review_reports():
    return render_template('admin/review_reports.html')

@main_bp.route('/add-users')
@login_required
def add_users():
    return render_template('admin/add_users.html')

# Route to render the HTML page
@main_bp.route('/audit_logs_page', methods=['GET'])
@login_required
def audit_logs_page():
    return render_template('/admin/audit_logs.html')

# Route to fetch filtered logs as JSON
@main_bp.route('/audit_logs', methods=['GET'])
@login_required
def view_audit_logs():
    log_type = request.args.get('log_type')  # Optional filter
    query = AuditLog.query

    if log_type:
        query = query.filter_by(log_type=log_type)
    logs = query.order_by(AuditLog.log_date.desc()).all()
    log_data = [
        {
            'date': log.log_date.strftime('%Y-%m-%d %H:%M:%S'),
            'log_type': log.log_type,
            'sponsor_id': log.sponsor_id,
            'driver_id': log.driver_id,
            'user_id': log.user_id,
            'status': log.status,
            'reason': log.reason,
            'points': log.points,
            'username': log.username,
            'change_type': log.change_type
        }
        for log in logs
    ]
    return jsonify({'logs': log_data})


# a) Log Driver Application
def log_driver_application(sponsor_id, driver_id, status, reason):
    log_entry = AuditLog(
        log_type='driver_app',
        sponsor_id=sponsor_id,
        driver_id=driver_id,
        status=status,
        reason=reason,
        log_date=datetime.now(timezone.utc)
    )
    db.session.add(log_entry)
    db.session.commit()

# b) Log Point Changes
def log_point_change(sponsor_id, driver_id, points, reason):
    log_entry = AuditLog(
        log_type='point_change',
        sponsor_id=sponsor_id,
        driver_id=driver_id,
        points=points,
        reason=reason,
        log_date=datetime.now(timezone.utc)
    )
    db.session.add(log_entry)
    db.session.commit()

# c) Log Password Changes
def log_password_change(user_id, change_type):
    log_entry = AuditLog(
        log_type='password_change',
        user_id=user_id,
        change_type=change_type,
        log_date=datetime.now(timezone.utc)
    )
    db.session.add(log_entry)
    db.session.commit()

# d) Log Login Attempts
def log_login_attempt(username, success):
    log_entry = AuditLog(
        log_type='login_attempt',
        username=username,
        status='Success' if success else 'Failure',
        log_date=datetime.now(timezone.utc)
    )
    db.session.add(log_entry)
    db.session.commit()

@main_bp.route('/admin/reports', methods=['GET'])
@login_required
def admin_reports_page():
    # Query all sponsors from the database
    sponsors = db.session.query(Sponsor.id, Sponsor.company_name).all()
    return render_template('admin_reports.html', sponsors=sponsors)


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
    reason = request.form.get('reason', 'No specific reason provided')
    application.status = 'Approved'
    application.reason = reason
    db.session.commit()
    log_driver_application(
        sponsor_id=current_user.sponsor.id,
        driver_id=application.user_id,
        status='Approved',
        reason=reason
    )
    flash('Application approved.', 'success')
    return redirect(url_for('main.approve_applications'))


@main_bp.route('/reject_application/<int:application_id>', methods=['POST'])
@login_required
def reject_application(application_id):
    application = Application.query.get_or_404(application_id)
    reason = request.form.get('reason', 'No specific reason provided')
    application.status = 'Denied'
    application.reason = reason
    db.session.commit()
    log_driver_application(
        sponsor_id=current_user.sponsor.id,
        driver_id=application.user_id,
        status='Denied',
        reason=reason
    )
    flash('Application rejected.', 'info')
    return redirect(url_for('main.approve_applications'))



@main_bp.route('/participating-drivers')
@login_required
def participating_drivers():
    approved_drivers = Application.query.join(JobPosting).filter(
        Application.status == 'Approved',
        JobPosting.sponsor_id == current_user.sponsor.id
    ).distinct(Application.user_id).all() 
    return render_template('sponsor/participating_drivers.html',drivers=approved_drivers)

@main_bp.route('/remove_driver/<int:driver_id>', methods=['POST'])
@login_required
def remove_driver(driver_id):
    try:
        driver = Application.query.filter_by(user_id=driver_id).first()
        if driver:
            db.session.delete(driver)
            db.session.commit()
            return jsonify({"message": "Driver removed successfully."}), 200
        else:
            return jsonify({"message": "Driver not found."}), 404
    except Exception as e:
        print(f"Error removing driver: {e}")
        return jsonify({"message": "Error removing driver."}), 500


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

@main_bp.route('/sponsor/reports', methods=['GET'])
@login_required
def sponsor_reports():
    sponsor_id = current_user.sponsor.id
    approved_drivers = db.session.query(
        Application.user_id,
        Application.first_name,
        Application.last_name
    ).join(JobPosting).filter(
        JobPosting.sponsor_id == sponsor_id,
        Application.status == "Approved"
    ).distinct(Application.user_id).all()
    return render_template(
        'sponsor/sponsor_reports.html',
        approved_drivers=approved_drivers
    )

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

    sponsor = Sponsor.query.filter_by(user_id=current_user.id).first()
    if not sponsor:
        return jsonify({'error': 'Sponsor account not found'}), 400
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
        id=product_id
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


@main_bp.route('/mark_as_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    notification.is_read = True 
    db.session.commit()
    return jsonify({'success': True})


@main_bp.route('/delete_notification/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    db.session.delete(notification) 
    db.session.commit()
    return jsonify({'success': True})


@main_bp.route('/reward_system', methods=['GET', 'POST'])
@login_required
def reward_system():
    if current_user.role != 'sponsor':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('main.sponsor_dashboard'))

    approved_drivers = db.session.query(Application.user_id, Application.first_name, Application.last_name)\
        .filter(Application.status == 'Approved').all()
    sponsor_behaviors = Behavior.query.filter_by(sponsor_id=current_user.sponsor.id).all()

    behavior_form = BehaviorForm()
    transaction_form = PointTransactionForm()

    if request.method == 'POST':
        if behavior_form.validate_on_submit():
            new_behavior = Behavior(
                name=behavior_form.name.data,
                type=behavior_form.type.data,
                point_value=behavior_form.point_value.data,
                sponsor_id=current_user.sponsor.id
            )
            db.session.add(new_behavior)
            db.session.commit()

            updated_behaviors = "".join(
                f"""<div style="margin-bottom: 10px; padding: 10px; border-radius: 5px; 
                    background-color: {'#28a745' if beh.type == 'Good' else '#dc3545'}; color: white;">
                    <strong>{beh.name}</strong><br>
                    Type: {beh.type}<br>
                    Points: {beh.point_value}
                </div>"""
                for beh in Behavior.query.filter_by(sponsor_id=current_user.sponsor.id)
            )
            return jsonify({'message': 'Behavior added successfully'}), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Form validation failed.',
                'errors': behavior_form.errors
            }), 400
    return render_template('sponsor/reward_system.html',
                           behavior_form=behavior_form,
                           transaction_form=transaction_form,
                           approved_drivers=approved_drivers,
                           sponsor_behaviors=sponsor_behaviors)


# Routing links for driver dashboard { view : {organizations, Job Postings, submitted applications, } , apply to job postings  }
@main_bp.route('/driver/points')
@login_required
def view_points():
    return redirect(url_for('main.driver_points', driver_id=current_user.id))


@main_bp.route('/driver_points/<int:driver_id>')
@login_required
def driver_points(driver_id):
    try:
        total_points = (
            db.session.query(
                db.func.sum(
                    db.case(
                        (PointTransaction.transaction_type == 'Add', PointTransaction.points),
                        (PointTransaction.transaction_type == 'Deduct', -PointTransaction.points),
                        else_=0
                    )
                )
            )
            .filter(PointTransaction.driver_id == driver_id)
            .scalar()
        ) or 0
        transactions = (
            PointTransaction.query
            .filter(PointTransaction.driver_id == driver_id)
            .order_by(PointTransaction.timestamp.desc())
            .all()
        )
    except Exception as e:
        print(f"Error retrieving data for Driver ID {driver_id}: {str(e)}")
        flash('An error occurred while fetching your points.', 'danger')
        total_points = 0
        transactions = []

    return render_template(
        'driver/view_points.html',
        points=total_points,
        transactions=transactions
    )



@main_bp.route('/redeem_rewards')
@login_required
def redeem_rewards():
    sponsor = Sponsor.query.join(Application, Application.user_id == current_user.id).first()
    if not sponsor:
        return render_template(
            'driver/redeem_rewards.html', 
            rewards=[], 
            error="No associated sponsor or catalog found."
        )
    sponsor_products = SponsorCatalog.query.filter_by(sponsor_id=sponsor.id).all()
    return render_template('driver/redeem_rewards.html', rewards=sponsor_products)

@main_bp.route('/add_to_wishlist', methods=['POST'])
@login_required
def add_to_wishlist():
    data = request.get_json()
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({'error': 'Product ID is required'}), 400

    product = SponsorCatalog.query.filter_by(id=product_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    existing_wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing_wishlist_item:
        return jsonify({'message': 'Product already in wishlist'}), 400

    new_wishlist_item = Wishlist(
        user_id=current_user.id,
        product_id=product_id,
        sponsor_id=product.sponsor_id,
        product_name=product.name,
        product_price=product.price,
        product_image=product.image  # New image column
    )
    db.session.add(new_wishlist_item)
    db.session.commit()
    return jsonify({'message': 'Product added to wishlist successfully'}), 200


@main_bp.route('/remove_from_wishlist', methods=['POST'])
@login_required
def remove_from_wishlist():
    data = request.get_json()
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({'error': 'Product ID is required'}), 400
    wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not wishlist_item:
        return jsonify({'error': 'Wishlist item not found'}), 404
    db.session.delete(wishlist_item)
    db.session.commit()
    return jsonify({'message': 'Product removed from wishlist successfully'}), 200


@main_bp.route('/wishlist', methods=['GET'])
@login_required
def view_wishlist():
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('driver/wishlist.html', items=wishlist_items)


@main_bp.route('/wishlist/<int:driver_id>', methods=['GET'])
@login_required
def driver_wishlist(driver_id):
    if current_user.role != 'sponsor':
        return jsonify({'error': 'Unauthorized access'}), 403

    wishlist_items = db.session.query(
        Wishlist.product_id,
        Wishlist.product_name,
        Wishlist.product_price,
        SponsorCatalog.image 
    ).join(
        SponsorCatalog, Wishlist.product_id == SponsorCatalog.id
    ).filter(
        Wishlist.user_id == driver_id,
        Wishlist.sponsor_id == current_user.sponsor.id
    ).all()
    wishlist_data = [
        {
            'product_id': item.product_id,
            'product_name': item.product_name,
            'product_price': item.product_price,
            'image': item.image if item.image else '/static/placeholder.png'
        }
        for item in wishlist_items
    ]
    return jsonify({'wishlist': wishlist_data})


@main_bp.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    user_id = data.get('user_id')

    if not product_id or not user_id:
        return jsonify({'error': 'Product ID and User ID are required'}), 400
    wishlist_item = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
    if not wishlist_item:
        return jsonify({'error': 'Product not found in wishlist'}), 404
    print(f"Adding to cart: {wishlist_item.product_name}, {wishlist_item.product_price}, {wishlist_item.product_image}")
    new_cart_item = Cart(
        sponsor_id=current_user.id,
        driver_id=user_id,
        product_id=product_id,
        product_name=wishlist_item.product_name,
        product_price=wishlist_item.product_price,
        product_image=wishlist_item.product_image
    )
    db.session.add(new_cart_item)
    db.session.commit()
    return jsonify({'message': 'Item successfully added to cart!'}), 200


@main_bp.route('/orders', methods=['GET'])
@login_required
def view_orders():
    if current_user.role != 'sponsor':
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))
    approved_drivers = db.session.query(
        Application.user_id,
        Application.first_name,
        Application.last_name
    ).filter(Application.status == 'Approved').all()
    return render_template('/sponsor/orders.html', approved_drivers=approved_drivers)


@main_bp.route('/cart/<int:driver_id>', methods=['GET'])
@login_required
def get_driver_cart(driver_id):
    if current_user.role != 'sponsor':
        return jsonify({'error': 'Unauthorized access'}), 403
    cart_items = Cart.query.filter_by(driver_id=driver_id).all()
    cart_data = [
        {
            'cart_id': item.id,
            'product_id': item.product_id,
            'product_name': item.product_name,
            'product_price': item.product_price,
            'image': item.product_image,
        }
        for item in cart_items
    ]
    return jsonify({'cart': cart_data})


@main_bp.route('/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    data = request.get_json()
    cart_id = data.get('cart_id')
    cart_item = Cart.query.get(cart_id)
    if not cart_item:
        return jsonify({'error': 'Item not found'}), 404
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message': 'Item removed successfully'})


@main_bp.route('/driver/review-purchases', methods=['GET'])
@login_required
def review_purchases():
    print(f"Current User Role: {current_user.role}")
    notifications = Notification.query.filter_by(driver_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).all()
    return render_template('driver/review_purchases.html', notifications=notifications)


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

    existing_application = Application.query.join(JobPosting).filter(
        Application.user_id == current_user.id,
        JobPosting.sponsor_id == job.sponsor_id,
        Application.status.in_(['Pending', 'Approved'])
    ).first()
    if existing_application:
        flash('You have already applied to a job posting from this sponsor.', 'warning')
        session['load_view_job_postings'] = True
        return redirect(url_for('main.driver_dash'))
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


@main_bp.route('/point_transaction', methods=['POST'])
@login_required
def point_transaction():
    if current_user.role != 'sponsor':
        return jsonify({'success': False, 'message': 'Unauthorized action.'}), 403

    try:
        driver_id = request.form.get('driver_id')
        behavior_id = request.form.get('behavior_id')
        reason = request.form.get('reason', 'No reason provided')
        behavior = Behavior.query.get(behavior_id)
        if not behavior:
            return jsonify({'success': False, 'message': 'Invalid behavior selected.'}), 400
        if behavior.type.lower() == "bad":
            adjusted_points = -abs(behavior.point_value)
        else:
            adjusted_points = abs(behavior.point_value)
        driver = User.query.get(driver_id)
        if not driver:
            return jsonify({'success': False, 'message': 'Driver not found'}), 404
        if adjusted_points < 0:
            driver.points_balance += adjusted_points
        else:
            driver.points_balance += adjusted_points
        point_transaction = PointTransaction(
            sponsor_id=current_user.sponsor.id,
            driver_id=driver_id,
            points=abs(adjusted_points),
            reason=reason,
            transaction_type="Deduct" if adjusted_points < 0 else "Add"
        )
        db.session.add(point_transaction)
        log_point_change(
            sponsor_id=current_user.sponsor.id,
            driver_id=driver_id,
            points=adjusted_points,
            reason=reason
        )
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Points successfully updated for Driver ID {driver_id}. Current balance: {driver.points_balance}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'})


@main_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request body'}), 400
    driver_id = data.get('driverId')
    cart_items = data.get('cartItems')
    if not driver_id or not cart_items:
        return jsonify({'success': False, 'message': 'Driver ID or Cart Items missing'}), 400
    try:
        driver = User.query.get(driver_id)
        if not driver:
            return jsonify({'success': False, 'message': 'Driver not found'}), 404
        driver_points = (
            db.session.query(
                db.func.sum(
                    db.case(
                        (PointTransaction.transaction_type == 'Add', PointTransaction.points),
                        (PointTransaction.transaction_type == 'Deduct', -PointTransaction.points),
                        else_=0
                    )
                )
            )
            .filter(PointTransaction.driver_id == driver_id)
            .scalar()
        ) or 0
        total_cost = sum(item['product_price'] for item in cart_items)
        if driver_points < total_cost:
            return jsonify({
                'success': False,
                'message': f"Driver does not have enough points. Current balance: {driver_points}, required: {total_cost}"
            }), 400
        for item in cart_items:
            purchase = PointTransaction(
                sponsor_id=current_user.sponsor.id,
                driver_id=driver_id,
                points=item['product_price'],
                reason=f"Purchase of {item['product_name']}",
                transaction_type="Deduct",
            )
            db.session.add(purchase)
            log_point_change(
                sponsor_id=current_user.sponsor.id,
                driver_id=driver_id,
                points=-item['product_price'],
                reason=f"Purchase of {item['product_name']}"
            )
        notification_message = f"Your sponsor has placed an order for: " + ", ".join(
            [item['product_name'] for item in cart_items]
        )
        notification = Notification(
            message=notification_message,
            sponsor_id=current_user.sponsor.id,
            driver_id=driver_id,
            is_read=False,
        )
        db.session.add(notification)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Checkout completed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/mark_driver_notification_as_read/<int:notification_id>', methods=['POST'])
def mark_driver_notification_as_read(notification_id):
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({'success': False, 'message': 'Notification not found'}), 404
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True, 'message': 'Notification marked as read successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/generate_report_csv', methods=['GET'])
@login_required
def generate_report_csv():
    report_type = request.args.get('reportType')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    driver_id = request.args.get('driverId')

    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    controller = ReportController(db.session)

    if report_type == "driver_point_tracking":
        rows = controller.driver_point_tracking(
            sponsor_id=current_user.sponsor.id,
            start_date=start_date,
            end_date=end_date,
            driver_id=driver_id
        )
        controller.write_csv(rows)

    file = controller.get_csv_file()
    return send_file(
        file,
        as_attachment=True,
        download_name="driver_point_tracking_report.csv",
        mimetype="text/csv"
    )
    
@main_bp.route('/remove_job/<int:job_id>', methods=['DELETE'])
@login_required
def remove_job(job_id):
    try:
        if current_user.role != 'sponsor':
            return jsonify({"success": False, "message": "Unauthorized action."}), 403
        job = JobPosting.query.get_or_404(job_id)
        if job.sponsor_id != current_user.id:
            return jsonify({"success": False, "message": "You can only remove your own job postings."}), 403
        db.session.delete(job)
        db.session.commit()
        return jsonify({"success": True, "message": "Job posting removed successfully."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})
    
@main_bp.route('/remove_behavior/<int:behavior_id>', methods=['DELETE'])
@login_required
def remove_behavior(behavior_id):
    try:
        if current_user.role != 'sponsor':
            return jsonify({"success": False, "message": "Unauthorized action."}), 403
        behavior = Behavior.query.get_or_404(behavior_id)
        if behavior.sponsor_id != current_user.id:
            return jsonify({"success": False, "message": "You can only remove your own behaviors."}), 403
        db.session.delete(behavior)
        db.session.commit()
        return jsonify({"success": True, "message": "Behavior removed successfully."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})

