# driverProgram/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, IntegerField, TextAreaField, SubmitField, SelectField, BooleanField, DateField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from .models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('Driver', 'Driver'), ('admin', 'Admin'), ('sponsor', 'Sponsor')], validators=[DataRequired()])
    sponsor_code = StringField('Sponsor Code', validators=[Optional()])
    birthdate = DateField('Birthdate', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[Optional()])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ConfirmResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    verification_code = StringField('Verification Code', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

class ApplyToJobPosting(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    resume = FileField('Upload Resume', validators=[DataRequired()])
    submit = SubmitField('Submit Application')

class JobPostForm(FlaskForm):
    job_title = StringField('Job Title', validators=[DataRequired()])
    job_description = TextAreaField('Job Description', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    salary = FloatField('Salary', validators=[DataRequired(), NumberRange(min=0)])
    required_hours = IntegerField('Required Hours Per Week', validators=[DataRequired(), NumberRange(min=1, max=168)])
    experience = StringField('Required Experience', validators=[DataRequired()])
    submit = SubmitField('Create Job Posting')

class SponsorProfileForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    website = StringField('Website', validators=[Optional()])
    bio = TextAreaField('Company Bio', validators=[Optional()])
    profile_picture = FileField('Upload Profile Picture', validators=[Optional()])
    submit = SubmitField('Save Profile')