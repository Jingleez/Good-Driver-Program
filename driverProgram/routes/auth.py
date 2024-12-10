# driverProgram/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ..forms import LoginForm, SignupForm, ResetPasswordRequestForm
from ..models import User
from .. import db
import boto3, os, re
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from datetime import datetime, timedelta
from ..forms import ConfirmResetForm
import requests
from .main import log_login_attempt, log_password_change


load_dotenv()

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# AWS Cognito configuration
CognitoUserPoolId = os.environ.get('COGNITO_USER_POOL_ID')
CognitoClientId = os.environ.get('COGNITO_CLIENT_ID')
CognitoRegion = os.environ.get('COGNITO_REGION')

# Create a Cognito client
cognito_client = boto3.client('cognito-idp', region_name=CognitoRegion)

# Max login attempts before lockout
MAX_LOGIN_ATTEMPTS = 3
LOCK_TIME_MINUTES = 1

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if 'login_attempts' not in session:
        session['login_attempts'] = 0
    if 'lock_until' not in session:
        session['lock_until'] = None

    if session['lock_until']:
        lock_until = datetime.strptime(session['lock_until'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() < lock_until:
            time_remaining = (lock_until - datetime.now()).seconds
            flash(f'Your account is locked. Try again in {time_remaining // 60} minute(s).', 'error')
            log_login_attempt(username=form.username.data, success=False)
            return render_template('Destination/login.html', form=form)

    if form.validate_on_submit():
        try:
            response = cognito_client.admin_initiate_auth(
                UserPoolId=CognitoUserPoolId,
                ClientId=CognitoClientId,
                AuthFlow='ADMIN_USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': form.username.data,
                    'PASSWORD': form.password.data,
                }
            )
            id_token = response['AuthenticationResult']['IdToken']
            session['id_token'] = id_token
            user = db.session.query(User).filter_by(username=form.username.data).first()

            if user:
                session['login_attempts'] = 0
                session['lock_until'] = None

                login_user(user, remember=True)
                user_role = user.role.strip().lower()
                session['user_role'] = user_role
                log_login_attempt(username=form.username.data, success=True)

                if user_role == 'driver':
                    flash('Logged in successfully!', 'success')
                    return redirect(url_for('main.driver_dash'))
                elif user_role == 'sponsor':
                    flash('Logged in successfully!', 'success')
                    return redirect(url_for('main.sponsor_dash'))
                elif user_role == 'admin':
                    flash('Logged in successfully!', 'success')
                    return redirect(url_for('main.admin_dash'))
                else:
                    flash('User role is not recognized.', 'danger')
                    return redirect(url_for('auth.login'))
            else:
                flash('User not found in local database.', 'danger')
                log_login_attempt(username=form.username.data, success=False)

        except cognito_client.exceptions.NotAuthorizedException:
            session['login_attempts'] += 1
            remaining_attempts = MAX_LOGIN_ATTEMPTS - session['login_attempts']
            log_login_attempt(username=form.username.data, success=False)
            if remaining_attempts <= 0:
                session['lock_until'] = (datetime.now() + timedelta(minutes=LOCK_TIME_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')
                flash(f'Too many failed login attempts. Your account is locked for {LOCK_TIME_MINUTES} minute(s).', 'danger')
            else:
                flash(f'Invalid username or password. You have {remaining_attempts} attempt(s) left.', 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
            log_login_attempt(username=form.username.data, success=False)
    return render_template('Destination/login.html', form=form)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        if form.role.data == 'sponsor':
            sponsor_code = form.sponsor_code.data
            if not sponsor_code or len(sponsor_code) != 6 or not sponsor_code.isdigit():
                flash('Invalid sponsor code.', 'danger')
                return render_template('Destination/signup.html', form=form)
        try:
            birthdate_str = form.birthdate.data.strftime('%Y-%m-%d')
            phone_number = form.phone.data
            if not phone_number.startswith('+'):
                phone_number = '+1' + re.sub(r'\D', '', phone_number)
            password_hash = generate_password_hash(form.password.data)

            response = cognito_client.sign_up(
                ClientId=CognitoClientId,
                Username=form.username.data,
                Password=form.password.data,
                UserAttributes=[
                    {'Name': 'email', 'Value': form.email.data},
                    {'Name': 'name', 'Value': form.first_name.data + " " + form.last_name.data},
                    {'Name': 'phone_number', 'Value': phone_number},
                    {'Name': 'birthdate', 'Value': birthdate_str},
                    {'Name': 'gender', 'Value': form.gender.data},
                    {'Name': 'address', 'Value': form.address.data},
                ]
            )
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=password_hash,
                role=form.role.data,
                sponsor_code=form.sponsor_code.data if form.role.data == 'sponsor' else None
            )
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully! Please verify your email to activate your account.', 'success')
            return redirect(url_for('auth.verify'))
        except ClientError as e:
            flash(f'An error occurred: {e.response["Error"]["Message"]}', 'danger')
    return render_template('Destination/signup.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# This function implements the password reset and confirmation functionality using Cognito
@auth_bp.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        email = form.email.data
        reason = request.form.get('reason') 

        cognito_region = os.getenv('COGNITO_REGION')
        cognito_client_id = os.getenv('COGNITO_CLIENT_ID')
        client = boto3.client('cognito-idp', region_name=cognito_region)
        try:
            response = client.forgot_password( ClientId=cognito_client_id, Username=email, )
            print(f"AWS Cognito response: {response}")
            flash('Password reset email sent.', 'success')
            user = User.query.filter_by(email=email).first()
            if user:
                log_password_change(user_id=user.id, change_type=f'Reset requested: {reason}')
            else:
                print("User not found for logging reset.")
            return redirect(url_for('auth.confirm_reset'))
        except client.exceptions.UserNotFoundException:
            flash('No user found with that email address.', 'error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('auth.reset_password')) 
    return render_template('password/reset_request.html', form=form)

@auth_bp.route('/confirm_reset', methods=['GET', 'POST'])
def confirm_reset():
    form = ConfirmResetForm()
    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data
        verification_code = form.verification_code.data
        new_password = form.new_password.data
        cognito_client = boto3.client('cognito-idp', region_name=os.getenv('COGNITO_REGION'))
        try:
            cognito_client.confirm_forgot_password(
                ClientId=os.getenv('COGNITO_CLIENT_ID'),
                Username=email,
                ConfirmationCode=verification_code,
                Password=new_password
            )
            flash('Your password has been reset successfully!', 'success')
            return redirect(url_for('auth.login'))
        except ClientError as e:
            flash(f"Error resetting password: {e.response['Error']['Message']}", 'danger')
    return render_template('password/reset_password.html', form=form)  # Renders the form for GET requests


@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        username = request.form['username'] 
        verification_code = request.form['verification_code']
        try:
            response = cognito_client.confirm_sign_up( ClientId=CognitoClientId, Username=username, ConfirmationCode=verification_code
            )
            flash('Your account has been verified successfully!', 'success')
            return redirect(url_for('auth.login'))
        except ClientError as e:
            flash(f'An error occurred: {e.response["Error"]["Message"]}', 'danger')
    return render_template('password/verify.html')


# To allow admin users to disable or delete users.
@auth_bp.route('/delete_user', methods=['POST'])
def delete_user():
    email = request.form['email']
    cognito_client = boto3.client('cognito-idp', region_name=os.getenv('COGNITO_REGION'))
    try:
        response = cognito_client.admin_delete_user(
            UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
            Username=email
        )
        flash(f'User with email {email} has been deleted successfully.', 'success')
    except cognito_client.exceptions.UserNotFoundException:
        flash('No user found with that email address.', 'error')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
    return redirect(url_for('auth.login'))
