import logging
from flask import Flask
from smtplib import SMTPException
from flask_mail import Message
#from threading import Thread
#from flask import current_app

logger = logging.getLogger(__name__)

def _send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except SMTPException:
            logger.exception("Ocurrió un error al enviar el email")


