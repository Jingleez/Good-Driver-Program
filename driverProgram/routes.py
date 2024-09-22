# driverProgram/routes.py
from flask import Blueprint, render_template, flash, redirect, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from .Database.models import ifUsernameExist, pwdCheck, getRole 
from .Database.models import db_connection 
from mysql.connector import Error

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('Destination/destinationTemplate.html') 

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if ifUsernameExist(username) and pwdCheck(username, password):
            session['logged_in'] = True
            session['role'] = getRole(username)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Incorrect login credentials!', 'danger')
            return redirect(url_for('main.login'))
    else:
        return render_template('Destination/login.html') 

@main.route("/logout")
def logout():
    session['logged_in'] = False
    session.pop('role', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.home'))

@main.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_password = generate_password_hash(password, method='sha256')
        
        try:
            connection = db_connection.get_connection()
            cursor = connection.cursor()
            sql = "INSERT INTO user (user_name, pwd, role) VALUES (%s, %s, %s)"
            val = (user, hashed_password, role)
            cursor.execute(sql, val)
            connection.commit()
            cursor.close()
            flash('User successfully registered!', 'success')
            return redirect(url_for('main.login'))
        except Error as e:
            print(f"Database error during signup: {e}")
            flash('An error occurred during signup. Please try again.', 'danger')
            return redirect(url_for('main.signup'))
    return render_template('Destination/signup.html') 

@main.route("/about")
def about():
    return render_template('Destination/about.html') 
