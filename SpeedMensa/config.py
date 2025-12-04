import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chiave-segreta-SpeedMensa-2025'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'mensa.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurazione Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'dorus0100@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'rtml qjbv wswv sdpi'
    ADMINS = ['dorus0100@gmail.com']
    
    # Configurazione Mensa
    ORARI_RITIRO = ['12:00', '12:30', '13:00', '13:30', '14:00']
    POSTI_DISPONIBILI_PER_SLOT = 50
    
    # Configurazione PayPal (da implementare)
    PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
    PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')  # 'sandbox' o 'live'