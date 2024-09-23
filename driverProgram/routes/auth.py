from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from ..forms import LoginForm, SignupForm
from ..models import User
from .. import db 
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.destination'))
        else:
            flash('Invalid username or password.', 'danger')
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
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.destination'))
