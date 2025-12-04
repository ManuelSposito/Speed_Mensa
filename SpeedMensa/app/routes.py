from flask import render_template, flash, redirect, request, url_for
from app import app, db
from app.forms import LoginForm, RegistrationForm, MenuForm, PrenotazioneForm, EditProfileForm, CancellaPrenotazioneForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User, MenuGiornaliero, Prenotazione, Transazione
from urllib.parse import urlsplit
from datetime import datetime, timezone, date, timedelta
from functools import wraps

# Decorator per verificare se l'utente è un gestore
def gestore_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_gestore:
            flash('Devi essere un gestore per accedere a questa pagina.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@app.route('/index')
@login_required
def index():
    """Homepage con i menu disponibili"""
    oggi = date.today()
    # Ottieni i menu dalla data odierna in poi
    menu_query = sa.select(MenuGiornaliero).where(
        MenuGiornaliero.data >= oggi,
        MenuGiornaliero.disponibile == True
    ).order_by(MenuGiornaliero.data)
    menu_disponibili = db.session.scalars(menu_query).all()
    
    return render_template('index.html', title='Home', menu_disponibili=menu_disponibili)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Username o password errati')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Accedi', form=form)


@app.route('/logout')
def logout():
    logout_user()
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
        db.session.add(user)
        db.session.commit()
        flash('Registrazione completata! Ora puoi accedere.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registrati', form=form)


@app.route('/profilo')
@login_required
def profilo():
    """Pagina profilo utente con prenotazioni e transazioni"""
    # Ottieni le prenotazioni dell'utente
    prenotazioni_query = sa.select(Prenotazione).where(
        Prenotazione.utente_id == current_user.id
    ).order_by(Prenotazione.created_at.desc())
    prenotazioni = db.session.scalars(prenotazioni_query).all()
    
    # Ottieni le transazioni dell'utente
    transazioni_query = sa.select(Transazione).where(
        Transazione.utente_id == current_user.id
    ).order_by(Transazione.created_at.desc()).limit(10)
    transazioni = db.session.scalars(transazioni_query).all()
    
    return render_template('profilo.html', title='Profilo', 
                          prenotazioni=prenotazioni, transazioni=transazioni)


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
        db.session.commit()
        flash('Profilo aggiornato con successo!')
        return redirect(url_for('profilo'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.nome.data = current_user.nome
        form.cognome.data = current_user.cognome
        form.matricola.data = current_user.matricola
    return render_template('edit_profilo.html', title='Modifica Profilo', form=form)


# ===== GESTIONE MENU (solo per gestori) =====

@app.route('/gestore/menu')
@login_required
@gestore_required
def gestore_menu():
    """Lista dei menu creati dal gestore"""
    menu_query = sa.select(MenuGiornaliero).where(
        MenuGiornaliero.gestore_id == current_user.id
    ).order_by(MenuGiornaliero.data.desc())
    menu_list = db.session.scalars(menu_query).all()
    return render_template('gestore/menu_list.html', title='I Miei Menu', menu_list=menu_list)


@app.route('/gestore/menu/nuovo', methods=['GET', 'POST'])
@login_required
@gestore_required
def crea_menu():
    """Crea un nuovo menu giornaliero"""
    form = MenuForm()
    if form.validate_on_submit():
        # Verifica se esiste già un menu per quella data
        menu_esistente = db.session.scalar(
            sa.select(MenuGiornaliero).where(MenuGiornaliero.data == form.data.data)
        )
        if menu_esistente:
            flash('Esiste già un menu per questa data.')
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
        db.session.add(menu)
        db.session.commit()
        flash('Menu creato con successo!')
        return redirect(url_for('gestore_menu'))
    return render_template('gestore/crea_menu.html', title='Crea Menu', form=form)


@app.route('/gestore/menu/<int:menu_id>/modifica', methods=['GET', 'POST'])
@login_required
@gestore_required
def modifica_menu(menu_id):
    """Modifica un menu esistente"""
    menu = db.session.get(MenuGiornaliero, menu_id)
    if not menu or menu.gestore_id != current_user.id:
        flash('Menu non trovato.')
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
        db.session.commit()
        flash('Menu aggiornato con successo!')
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
    return render_template('gestore/modifica_menu.html', title='Modifica Menu', form=form, menu=menu)


@app.route('/gestore/menu/<int:menu_id>/prenotazioni')
@login_required
@gestore_required
def visualizza_prenotazioni_menu(menu_id):
    """Visualizza tutte le prenotazioni per un menu specifico"""
    menu = db.session.get(MenuGiornaliero, menu_id)
    if not menu or menu.gestore_id != current_user.id:
        flash('Menu non trovato.')
        return redirect(url_for('gestore_menu'))
    
    prenotazioni_query = sa.select(Prenotazione).where(
        Prenotazione.menu_id == menu_id,
        Prenotazione.stato.in_(['confermata', 'pagata'])
    ).order_by(Prenotazione.orario_ritiro)
    prenotazioni = db.session.scalars(prenotazioni_query).all()
    
    return render_template('gestore/prenotazioni_menu.html', 
                          title='Prenotazioni Menu', menu=menu, prenotazioni=prenotazioni)


# ===== PRENOTAZIONI =====

@app.route('/prenota/<int:menu_id>', methods=['GET', 'POST'])
@login_required
def prenota(menu_id):
    """Prenota un pasto"""
    menu = db.session.get(MenuGiornaliero, menu_id)
    if not menu or not menu.disponibile:
        flash('Menu non disponibile.')
        return redirect(url_for('index'))
    
    if menu.data < date.today():
        flash('Non puoi prenotare menu passati.')
        return redirect(url_for('index'))
    
    # Verifica se l'utente ha già una prenotazione per questo menu
    prenotazione_esistente = db.session.scalar(
        sa.select(Prenotazione).where(
            Prenotazione.utente_id == current_user.id,
            Prenotazione.menu_id == menu_id,
            Prenotazione.stato.in_(['in_attesa', 'pagata', 'confermata'])
        )
    )
    if prenotazione_esistente:
        flash('Hai già una prenotazione per questo menu.')
        return redirect(url_for('index'))
    
    # Prepara gli orari disponibili
    orari_con_disponibilita = []
    for orario in app.config['ORARI_RITIRO']:
        posti = menu.posti_disponibili_per_orario(orario)
        if posti > 0:
            orari_con_disponibilita.append(orario)
    
    if not orari_con_disponibilita:
        flash('Tutti gli orari sono al completo.')
        return redirect(url_for('index'))
    
    form = PrenotazioneForm(orari_disponibili=orari_con_disponibilita)
    
    if form.validate_on_submit():
        # Verifica ancora la disponibilità
        posti_disponibili = menu.posti_disponibili_per_orario(form.orario_ritiro.data)
        if posti_disponibili <= 0:
            flash('Spiacenti, questo orario è ora completo.')
            return redirect(url_for('prenota', menu_id=menu_id))
        
        prenotazione = Prenotazione(
            utente_id=current_user.id,
            menu_id=menu_id,
            orario_ritiro=form.orario_ritiro.data,
            note=form.note.data,
            stato='in_attesa'
        )
        db.session.add(prenotazione)
        db.session.commit()
        
        flash('Prenotazione effettuata! Procedi al pagamento.')
        return redirect(url_for('pagamento', prenotazione_id=prenotazione.id))
    
    return render_template('prenota.html', title='Prenota Pasto', form=form, menu=menu)


@app.route('/prenotazione/<int:prenotazione_id>/cancella', methods=['POST'])
@login_required
def cancella_prenotazione(prenotazione_id):
    """Cancella una prenotazione"""
    prenotazione = db.session.get(Prenotazione, prenotazione_id)
    if not prenotazione or prenotazione.utente_id != current_user.id:
        flash('Prenotazione non trovata.')
        return redirect(url_for('profilo'))
    
    if prenotazione.stato == 'ritirata':
        flash('Non puoi cancellare una prenotazione già ritirata.')
        return redirect(url_for('profilo'))
    
    # Se la prenotazione era pagata, non è possibile cancellarla
    if prenotazione.stato == 'pagata' and prenotazione.menu:
        flash('Non puoi cancellare una prenotazione già pagata')
        
    
    prenotazione.cancella()
    db.session.commit()
    flash('Prenotazione cancellata.')
    return redirect(url_for('profilo'))


# ===== PAGAMENTI =====

@app.route('/pagamento/<int:prenotazione_id>')
@login_required
def pagamento(prenotazione_id):
    """Pagina di pagamento per una prenotazione"""
    prenotazione = db.session.get(Prenotazione, prenotazione_id)
    if not prenotazione or prenotazione.utente_id != current_user.id:
        flash('Prenotazione non trovata.')
        return redirect(url_for('index'))
    
    if prenotazione.stato != 'in_attesa':
        flash('Questa prenotazione è già stata pagata o cancellata.')
        return redirect(url_for('profilo'))
    
    menu = prenotazione.menu
    
    # TODO: Implementare integrazione PayPal
    # Per ora mostriamo solo l'interfaccia
    
    return render_template('pagamento.html', title='Pagamento', 
                          prenotazione=prenotazione, menu=menu)




@app.route('/pagamento/paypal/<int:prenotazione_id>')
@login_required
def paga_con_paypal(prenotazione_id):
    """Pagamento tramite PayPal - DA IMPLEMENTARE"""
    # TODO: Implementare integrazione PayPal SDK
    flash('Il pagamento PayPal verrà implementato prossimamente.')
    return redirect(url_for('pagamento', prenotazione_id=prenotazione_id))
