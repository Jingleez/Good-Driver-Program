from flask_mail import Message
from flask import url_for
from . import mail

def send_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',  # Update with your sender email
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_password', token=token, _external=True)}
If you did not make this request, simply ignore this email and no changes will be made.
'''
    mail.send(msg)

