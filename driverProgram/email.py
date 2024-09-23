# driverProgram/email.py
from flask_mail import Message
from flask import render_template, current_app
from threading import Thread
from . import mail

def send_email(user):
    token = user.get_reset_token()
    msg = Message(
        "Password Reset Request",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[user.email]
    )
    msg.html = render_template('password/reset_email.html', user=user, token=token)
    Thread(target=send_email_thread, args=(msg,)).start()

def send_email_thread(msg):
    with current_app.app_context():
        mail.send(msg)
