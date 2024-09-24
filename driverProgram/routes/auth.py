# driverProgram/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ..forms import LoginForm, SignupForm, ResetRequestForm, ResetPasswordForm
from ..models import User
from ..email import send_email
from .. import db 

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            session['user_role'] = user.role
            session['username'] = form.username.data
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.dashboard'))  
        else:
            flash('Invalid username or password.', 'danger')
    else:
        if 'username' in session:
            form.username.data = session['username']
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

        new_user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            address=form.address.data,
            phone=form.phone.data,
            email=form.email.data,
            username=form.username.data,
            role=form.role.data,
            sponsor_code=form.sponsor_code.data if form.role.data == 'sponsor' else None
        )
        new_user.set_password(form.password.data)
        
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('Destination/signup.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_role', None) 
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.destination'))

@auth_bp.route("/reset_request", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.destination'))
    form = ResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_email(user)
            flash('An email with instructions to reset your password has been sent to you.', 'info')
        else:
            flash('Email not found.', 'warning')
        return redirect(url_for('auth.login'))
    return render_template('password/reset_request.html', title='Reset Password', form=form)

@auth_bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_token(token) 
    if not user:
        flash('That is an invalid or expired token.', 'warning')
        return redirect(url_for('main.destination'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('password/reset_password.html', title='Reset Password', form=form)
