from flask_mail import Message
from app import mail, app
from flask import render_template
from threading import Thread

def send_async_email(app, msg):
    """Invia email in modo asincrono"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    """Funzione helper per inviare email"""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()

def send_password_reset_email(user):
    """Invia email per reset password"""
    token = user.get_reset_password_token()
    send_email(
        '[Speed Mensa] Reset della Password',
        sender=app.config['ADMINS'][0],
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', user=user, token=token),
        html_body=render_template('email/reset_password.html', user=user, token=token)
    )

def send_prenotazione_conferma_email(user, prenotazione, menu):
    """Invia email di conferma prenotazione"""
    send_email(
        '[Speed Mensa] Conferma Prenotazione',
        sender=app.config['ADMINS'][0],
        recipients=[user.email],
        text_body=render_template('email/conferma_prenotazione.txt', 
                                user=user, prenotazione=prenotazione, menu=menu),
        html_body=render_template('email/conferma_prenotazione.html', 
                                 user=user, prenotazione=prenotazione, menu=menu)
    )

def send_cancellazione_prenotazione_email(user, prenotazione, menu):
    """Invia email di conferma cancellazione"""
    send_email(
        '[Speed Mensa] Prenotazione Cancellata',
        sender=app.config['ADMINS'][0],
        recipients=[user.email],
        text_body=render_template('email/cancellazione_prenotazione.txt',
                                user=user, prenotazione=prenotazione, menu=menu),
        html_body=render_template('email/cancellazione_prenotazione.html',
                                 user=user, prenotazione=prenotazione, menu=menu)
    )

def send_promemoria_ritiro_email(user, prenotazione, menu):
    """Invia promemoria per il ritiro del pasto"""
    send_email(
        '[Speed Mensa] Promemoria Ritiro Pasto',
        sender=app.config['ADMINS'][0],
        recipients=[user.email],
        text_body=render_template('email/promemoria_ritiro.txt',
                                user=user, prenotazione=prenotazione, menu=menu),
        html_body=render_template('email/promemoria_ritiro.html',
                                 user=user, prenotazione=prenotazione, menu=menu)
    )