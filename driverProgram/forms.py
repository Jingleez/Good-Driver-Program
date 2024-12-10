# driverProgram/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, IntegerField, TextAreaField, SubmitField, SelectField, BooleanField, DateField, FileField, FieldList, FormField
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
    title = StringField('Job Title', validators=[DataRequired()])  # Changed from 'job_title' to 'title'
    description = TextAreaField('Job Description', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    salary = StringField('Salary', validators=[DataRequired()])  # Changed from FloatField to StringField to match your model
    hours = StringField('Required Hours', validators=[DataRequired()])  # Changed from 'required_hours' to 'hours'
    experience = StringField('Required Experience', validators=[DataRequired()])
    submit = SubmitField('Create Job Posting')


class SponsorProfileForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    website = StringField('Website', validators=[Optional()])
    bio = TextAreaField('Company Bio', validators=[Optional()])
    #profile_picture = FileField('Upload Profile Picture', validators=[Optional()])
    submit = SubmitField('Save Profile')


class BehaviorForm(FlaskForm):
    name = StringField('Behavior Name', validators=[DataRequired()])
    type = SelectField('Type', choices=[('Good', 'Good'), ('Bad', 'Bad')], validators=[DataRequired()])
    point_value = IntegerField('Point Worth', validators=[DataRequired()])
    submit = SubmitField('Add Behavior')

class PointTransactionForm(FlaskForm):
    driver_id = SelectField('Driver', coerce=int, validators=[DataRequired()])
    behavior_id = SelectField('Behavior', coerce=int, validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[DataRequired()])
    submit = SubmitField('Submit')