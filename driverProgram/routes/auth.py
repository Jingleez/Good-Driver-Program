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
from datetime import datetime
from ..forms import ConfirmResetForm

load_dotenv()

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# AWS Cognito configuration
CognitoUserPoolId = os.environ.get('COGNITO_USER_POOL_ID')
CognitoClientId = os.environ.get('COGNITO_CLIENT_ID')
CognitoRegion = os.environ.get('COGNITO_REGION')

# Create a Cognito client
cognito_client = boto3.client('cognito-idp', region_name=CognitoRegion)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            response = cognito_client.admin_initiate_auth( UserPoolId=CognitoUserPoolId, ClientId=CognitoClientId, AuthFlow='ADMIN_USER_PASSWORD_AUTH',
                        AuthParameters={ 'USERNAME': form.username.data, 'PASSWORD': form.password.data, }
            )
            id_token = response['AuthenticationResult']['IdToken']
            session['id_token'] = id_token
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        except cognito_client.exceptions.NotAuthorizedException:
            flash('Invalid username or password.', 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')

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

            # Once the user signs up, the program adds the user with Cognito
            response = cognito_client.sign_up( ClientId=CognitoClientId, Username=form.username.data, Password=form.password.data,
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
                username=form.username.data, email=form.email.data, role=form.role.data,
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
    session.pop('id_token', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.destination'))

# This function implements the password reset and confirmation functionality using Cognito
@auth_bp.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        email = form.email.data
        print(f"Email submitted: {email}") 
        cognito_region = os.getenv('COGNITO_REGION')
        cognito_client_id = os.getenv('COGNITO_CLIENT_ID')
        client = boto3.client('cognito-idp', region_name=cognito_region)
        try:
            response = client.forgot_password( ClientId=cognito_client_id, Username=email, )
            print(f"AWS Cognito response: {response}") #debug statement to see AWS response
            flash('Password reset email sent.', 'success')
            return redirect(url_for('auth.confirm_reset'))
        except client.exceptions.UserNotFoundException:
            flash('No user found with that email address.', 'error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('auth.login')) 
    return render_template('password/reset_request.html', form=form)

@auth_bp.route('/confirm_reset', methods=['GET', 'POST'])
def confirm_reset():
    form = ConfirmResetForm()  # Assuming you have a form for verification code and new password
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
        # AdminDeleteUser requires the User Pool ID and Username (usually the email).
        response = cognito_client.admin_delete_user(
            UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),  # Make sure the User Pool ID is in your environment variables
            Username=email
        )
        flash(f'User with email {email} has been deleted successfully.', 'success')
    except cognito_client.exceptions.UserNotFoundException:
        flash('No user found with that email address.', 'error')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
    return redirect(url_for('auth.login'))

