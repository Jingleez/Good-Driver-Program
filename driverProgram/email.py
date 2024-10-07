"""
from flask_mail import Message
from flask import current_app, url_for
from . import mail 

def send_email(user):
    token = user.get_reset_token()
    msg = Message(
        subject='Reset Your Password',
        sender=current_app.config['MAIL_USERNAME'],  
        recipients=[user.email]
    )
    msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg) 

"""