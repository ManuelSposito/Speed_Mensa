from flask import render_template, flash, redirect, request, url_for, jsonify, current_app
from app import app, db
from app.forms import (
    LoginForm, RegistrationForm, MenuForm, PrenotazioneForm, 
    EditProfileForm, CancellaPrenotazioneForm, ResetPasswordRequestForm, ResetPasswordForm
)
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User, MenuGiornaliero, Prenotazione, Transazione
from urllib.parse import urlsplit
from datetime import date
from functools import wraps
from app.email import send_password_reset_email, send_prenotazione_conferma_email
import requests
import base64

# ... (I decoratori e le rotte login/logout/register rimangono uguali a prima) ...

def gestore_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_gestore', False):
            flash('Devi essere un gestore per accedere a questa pagina.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Username o password errati.', 'error')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        flash('Accesso effettuato.', 'success')
        return redirect(next_page)
    return render_template('login.html', title='Accedi', form=form)

@app.route('/index')
@login_required
def index():
    oggi = date.today()
    menu_query = (
        sa.select(MenuGiornaliero)
        .where(
            MenuGiornaliero.data >= oggi,
            MenuGiornaliero.disponibile == True
        )
        .order_by(MenuGiornaliero.data)
    )
    menu_disponibili = db.session.scalars(menu_query).all()
    return render_template('index.html', title='Home', menu_disponibili=menu_disponibili)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sei stato disconnesso.', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            nome=form.nome.data,
            cognome=form.cognome.data,
            matricola=form.matricola.data
        )
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Registrazione non riuscita. Riprovare più tardi.', 'error')
            return redirect(url_for('register'))
        flash('Registrazione completata! Ora puoi accedere.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registrati', form=form)

@app.route('/profilo')
@login_required
def profilo():
    pren_page = request.args.get('pren_page', default=1, type=int)
    trans_page = request.args.get('trans_page', default=1, type=int)
    per_page = 10

    prenotazioni_query = (
        sa.select(Prenotazione)
        .where(Prenotazione.utente_id == current_user.id)
        .order_by(Prenotazione.created_at.desc())
        .limit(per_page)
        .offset((pren_page - 1) * per_page)
    )
    prenotazioni = db.session.scalars(prenotazioni_query).all()

    transazioni_query = (
        sa.select(Transazione)
        .where(Transazione.utente_id == current_user.id)
        .order_by(Transazione.created_at.desc())
        .limit(per_page)
        .offset((trans_page - 1) * per_page)
    )
    transazioni = db.session.scalars(transazioni_query).all()

    form = CancellaPrenotazioneForm()
    return render_template(
        'profilo.html',
        title='Profilo',
        prenotazioni=prenotazioni,
        transazioni=transazioni,
        form=form,
        pren_page=pren_page,
        trans_page=trans_page,
        per_page=per_page
    )

@app.route('/edit_profilo', methods=['GET', 'POST'])
@login_required
def edit_profilo():
    form = EditProfileForm(current_user.username, current_user.email, current_user.matricola)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.nome = form.nome.data
        current_user.cognome = form.cognome.data
        current_user.matricola = form.matricola.data
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Aggiornamento profilo non riuscito. Riprovare più tardi.', 'error')
            return redirect(url_for('edit_profilo'))
        flash('Profilo aggiornato con successo!', 'success')
        return redirect(url_for('profilo'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.nome.data = current_user.nome
        form.cognome.data = current_user.cognome
        form.matricola.data = current_user.matricola
    return render_template('edit_profilo.html', title='Modifica Profilo', form=form)

# ... (Gestione Menu Gestore rimane uguale) ...
@app.route('/gestore/menu')
@login_required
@gestore_required
def gestore_menu():
    menu_query = (
        sa.select(MenuGiornaliero)
        .where(MenuGiornaliero.gestore_id == current_user.id)
        .order_by(MenuGiornaliero.data.desc())
    )
    menu_list = db.session.scalars(menu_query).all()
    return render_template('gestore/menu_list.html', title='I Miei Menu', menu_list=menu_list)

@app.route('/gestore/menu/nuovo', methods=['GET', 'POST'])
@login_required
@gestore_required
def crea_menu():
    form = MenuForm()
    if form.validate_on_submit():
        menu_esistente = db.session.scalar(
            sa.select(MenuGiornaliero).where(MenuGiornaliero.data == form.data.data)
        )
        if menu_esistente:
            flash('Esiste già un menu per questa data.', 'error')
            return redirect(url_for('crea_menu'))

        menu = MenuGiornaliero(
            data=form.data.data,
            primo=form.primo.data,
            secondo=form.secondo.data,
            contorno=form.contorno.data,
            frutta=form.frutta.data,
            dolce=form.dolce.data,
            prezzo=form.prezzo.data,
            disponibile=form.disponibile.data,
            gestore_id=current_user.id
        )
        try:
            db.session.add(menu)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Creazione menu non riuscita. Riprovare più tardi.', 'error')
            return redirect(url_for('crea_menu'))

        flash('Menu creato con successo!', 'success')
        return redirect(url_for('gestore_menu'))
    return render_template('gestore/crea_menu.html', title='Crea Menu', form=form)

@app.route('/gestore/menu/<int:menu_id>/modifica', methods=['GET', 'POST'])
@login_required
@gestore_required
def modifica_menu(menu_id):
    menu = db.session.get(MenuGiornaliero, menu_id)
    if not menu or menu.gestore_id != current_user.id:
        flash('Menu non trovato.', 'error')
        return redirect(url_for('gestore_menu'))

    form = MenuForm()
    if form.validate_on_submit():
        menu.data = form.data.data
        menu.primo = form.primo.data
        menu.secondo = form.secondo.data
        menu.contorno = form.contorno.data
        menu.frutta = form.frutta.data
        menu.dolce = form.dolce.data
        menu.prezzo = form.prezzo.data
        menu.disponibile = form.disponibile.data
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Aggiornamento menu non riuscito. Riprovare più tardi.', 'error')
            return redirect(url_for('modifica_menu', menu_id=menu_id))
        flash('Menu aggiornato con successo!', 'success')
        return redirect(url_for('gestore_menu'))
    elif request.method == 'GET':
        form.data.data = menu.data
        form.primo.data = menu.primo
        form.secondo.data = menu.secondo
        form.contorno.data = menu.contorno
        form.frutta.data = menu.frutta
        form.dolce.data = menu.dolce
        form.prezzo.data = menu.prezzo
        form.disponibile.data = menu.disponibile
    return render_template('gestore/modifica_menu.html', title='Modifica Menu', form=form, menu=menu, date=date)

@app.route('/gestore/menu/<int:menu_id>/prenotazioni')
@login_required
@gestore_required
def visualizza_prenotazioni_menu(menu_id):
    menu = db.session.get(MenuGiornaliero, menu_id)
    if not menu or menu.gestore_id != current_user.id:
        flash('Menu non trovato.', 'error')
        return redirect(url_for('gestore_menu'))
    prenotazioni_query = (
        sa.select(Prenotazione)
        .where(
            Prenotazione.menu_id == menu_id,
            Prenotazione.stato.in_(['confermata', 'pagata'])
        )
        .order_by(Prenotazione.orario_ritiro)
    )
    prenotazioni = db.session.scalars(prenotazioni_query).all()
    return render_template(
        'gestore/prenotazioni_menu.html',
        title='Prenotazioni Menu',
        menu=menu,
        prenotazioni=prenotazioni
    )

# ... (Prenotazioni) ...
@app.route('/prenota/<int:menu_id>', methods=['GET', 'POST'])
@login_required
def prenota(menu_id):
    menu = db.session.get(MenuGiornaliero, menu_id)
    if not menu or not menu.disponibile:
        flash('Menu non disponibile.', 'error')
        return redirect(url_for('index'))
    if menu.data < date.today():
        flash('Non puoi prenotare menu passati.', 'error')
        return redirect(url_for('index'))
    prenotazione_esistente = db.session.scalar(
        sa.select(Prenotazione).where(
            Prenotazione.utente_id == current_user.id,
            Prenotazione.menu_id == menu_id,
            Prenotazione.stato.in_(['in_attesa', 'pagata', 'confermata'])
        )
    )
    if prenotazione_esistente:
        flash('Hai già una prenotazione per questo menu.', 'info')
        return redirect(url_for('index'))

    form = PrenotazioneForm()
    if form.validate_on_submit():
        prenotazione = Prenotazione(
            utente_id=current_user.id,
            menu_id=menu_id,
            orario_ritiro=form.orario_ritiro.data,
            note=form.note.data,
            stato='in_attesa'
        )
        try:
            db.session.add(prenotazione)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Prenotazione non riuscita. Riprovare più tardi.', 'error')
            return redirect(url_for('prenota', menu_id=menu_id))
        flash('Prenotazione effettuata! Procedi al pagamento.', 'success')
        return redirect(url_for('pagamento', prenotazione_id=prenotazione.id))
    return render_template('prenota.html', title='Prenota Pasto', form=form, menu=menu)

@app.route('/prenotazione/<int:prenotazione_id>/cancella', methods=['POST'])
@login_required
def cancella_prenotazione(prenotazione_id):
    prenotazione = db.session.get(Prenotazione, prenotazione_id)
    if not prenotazione or prenotazione.utente_id != current_user.id:
        flash('Prenotazione non trovata.', 'error')
        return redirect(url_for('profilo'))
    if prenotazione.stato == 'ritirata':
        flash('Non puoi cancellare una prenotazione già ritirata.', 'error')
        return redirect(url_for('profilo'))
    if prenotazione.stato == 'pagata' and prenotazione.menu:
        flash('Non puoi cancellare una prenotazione già pagata.', 'error')
        return redirect(url_for('profilo'))
    try:
        prenotazione.cancella()
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Cancellazione non riuscita. Riprovare più tardi.', 'error')
        return redirect(url_for('profilo'))
    flash('Prenotazione cancellata.', 'success')
    return redirect(url_for('profilo'))

# --- NUOVA IMPLEMENTAZIONE PAYPAL ---

# Helper per Token PayPal
def get_paypal_token():
    client_id = app.config['PAYPAL_CLIENT_ID']
    client_secret = app.config['PAYPAL_CLIENT_SECRET']
    url = f"{app.config['PAYPAL_API_BASE']}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    data = {"grant_type": "client_credentials"}
    try:
        response = requests.post(url, auth=(client_id, client_secret), headers=headers, data=data)
        return response.json().get('access_token')
    except Exception as e:
        app.logger.error(f"Errore Token PayPal: {e}")
        return None

@app.route('/pagamento/<int:prenotazione_id>')
@login_required
def pagamento(prenotazione_id):
    prenotazione = db.session.get(Prenotazione, prenotazione_id)
    if not prenotazione or prenotazione.utente_id != current_user.id:
        flash('Prenotazione non trovata.', 'error')
        return redirect(url_for('index'))
    if prenotazione.stato != 'in_attesa':
        flash('Questa prenotazione è già stata pagata o cancellata.', 'info')
        return redirect(url_for('profilo'))
    menu = prenotazione.menu
    return render_template('pagamento.html', title='Pagamento', prenotazione=prenotazione, menu=menu)

@app.route('/api/payment/create/<int:prenotazione_id>', methods=['POST'])
@login_required
def create_payment(prenotazione_id):
    prenotazione = db.session.get(Prenotazione, prenotazione_id)
    if not prenotazione or prenotazione.utente_id != current_user.id:
        return jsonify({'error': 'Prenotazione non valida'}), 404

    token = get_paypal_token()
    if not token:
        return jsonify({'error': 'Errore configurazione PayPal'}), 500

    url = f"{app.config['PAYPAL_API_BASE']}/v2/checkout/orders"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Payload ordine
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "EUR",
                "value": f"{prenotazione.menu.prezzo:.2f}"
            },
            "description": f"Menu del {prenotazione.menu.data} - SpeedMensa"
        }]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return jsonify(response.json())

@app.route('/api/payment/execute/<int:prenotazione_id>', methods=['POST'])
@login_required
def execute_payment(prenotazione_id):
    data = request.json
    order_id = data.get('orderID')
    
    token = get_paypal_token()
    url = f"{app.config['PAYPAL_API_BASE']}/v2/checkout/orders/{order_id}/capture"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post(url, headers=headers)
    result = response.json()
    
    if result.get('status') == 'COMPLETED':
        prenotazione = db.session.get(Prenotazione, prenotazione_id)
        
        # Crea Transazione
        transazione = Transazione(
            utente_id=current_user.id,
            prenotazione_id=prenotazione.id,
            tipo='pagamento_pasto',
            importo=prenotazione.menu.prezzo,
            metodo_pagamento='PayPal',
            stato='completata',
            paypal_order_id=order_id
        )
        
        # Aggiorna Prenotazione
        prenotazione.conferma_pagamento()
        
        db.session.add(transazione)
        db.session.commit()
        
        flash('Pagamento completato con successo!', 'success')
        
        # Invia email conferma (opzionale)
        try:
            send_prenotazione_conferma_email(current_user, prenotazione, prenotazione.menu)
        except:
            pass # Non blocchiamo se l'email fallisce
            
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'failed', 'msg': 'Pagamento non completato'})

# --- FINE PAYPAL ---

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash('Controlla la tua email per le istruzioni per resettare la password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Token non valido o scaduto.', 'error')
        return redirect(url_for('login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Reset password non riuscito. Riprovare più tardi.', 'error')
            return redirect(url_for('reset_password', token=token))
        flash('La tua password è stata resettata.', 'success')
        return redirect(url_for('login'))
    # Qui usiamo il file corretto che conterrà il form
    return render_template('reset_password.html', title='Reset Password', form=form, user=user)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', title='Pagina non trovata'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html', title='Errore interno'), 500