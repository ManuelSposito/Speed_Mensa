from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DateField, FloatField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length, NumberRange, Optional
from app.models import User
from app import db
import sqlalchemy as sa
from datetime import date

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ricordami')
    submit = SubmitField('Accedi')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    nome = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    cognome = StringField('Cognome', validators=[DataRequired(), Length(max=100)])
    matricola = StringField('Matricola', validators=[DataRequired(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Ripeti Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrati')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Username già utilizzato. Scegline un altro.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Email già registrata.')

    def validate_matricola(self, matricola):
        user = db.session.scalar(sa.select(User).where(User.matricola == matricola.data))
        if user is not None:
            raise ValidationError('Matricola già registrata.')

class MenuForm(FlaskForm):
    data = DateField('Data', validators=[DataRequired()], format='%Y-%m-%d')
    primo = StringField('Primo Piatto', validators=[DataRequired(), Length(max=200)])
    secondo = StringField('Secondo Piatto', validators=[DataRequired(), Length(max=200)])
    contorno = StringField('Contorno', validators=[DataRequired(), Length(max=200)])
    frutta = StringField('Frutta', validators=[Optional(), Length(max=200)])
    dolce = StringField('Dolce', validators=[Optional(), Length(max=200)])
    prezzo = FloatField('Prezzo (€)', validators=[DataRequired(), NumberRange(min=0.0, max=50.0)])
    disponibile = BooleanField('Disponibile', default=True)
    submit = SubmitField('Salva Menu')

    def validate_data(self, data):
        if data.data < date.today():
            raise ValidationError('Non puoi creare menu per date passate.')

class PrenotazioneForm(FlaskForm):
    orario_ritiro = SelectField('Orario di Ritiro', validators=[DataRequired()])
    note = TextAreaField('Note (allergie, intolleranze, ecc.)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Prenota')
    
    def __init__(self, orari_disponibili=None, *args, **kwargs):
        super(PrenotazioneForm, self).__init__(*args, **kwargs)
        if orari_disponibili:
            self.orario_ritiro.choices = [(orario, orario) for orario in orari_disponibili]

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    nome = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    cognome = StringField('Cognome', validators=[DataRequired(), Length(max=100)])
    matricola = StringField('Matricola', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Salva Modifiche')

    def __init__(self, original_username, original_email, original_matricola, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        self.original_matricola = original_matricola

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(User.username == username.data))
            if user is not None:
                raise ValidationError('Username già utilizzato.')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = db.session.scalar(sa.select(User).where(User.email == email.data))
            if user is not None:
                raise ValidationError('Email già registrata.')
    
    def validate_matricola(self, matricola):
        if matricola.data != self.original_matricola:
            user = db.session.scalar(sa.select(User).where(User.matricola == matricola.data))
            if user is not None:
                raise ValidationError('Matricola già registrata.')


class CancellaPrenotazioneForm(FlaskForm):
    submit = SubmitField('Cancella Prenotazione')