from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login, app
from datetime import datetime, timezone, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    nome: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    cognome: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    matricola: so.Mapped[Optional[str]] = so.mapped_column(sa.String(20), unique=True)
    is_gestore: so.Mapped[bool] = so.mapped_column(default=False)
    created_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relazioni
    prenotazioni: so.WriteOnlyMapped['Prenotazione'] = so.relationship(back_populates='utente')
    transazioni: so.WriteOnlyMapped['Transazione'] = so.relationship(back_populates='utente')
    menu_creati: so.WriteOnlyMapped['MenuGiornaliero'] = so.relationship(back_populates='gestore')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MenuGiornaliero(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    data: so.Mapped[date] = so.mapped_column(sa.Date, index=True, unique=True)
    primo: so.Mapped[str] = so.mapped_column(sa.String(200))
    secondo: so.Mapped[str] = so.mapped_column(sa.String(200))
    contorno: so.Mapped[str] = so.mapped_column(sa.String(200))
    frutta: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200))
    dolce: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200))
    prezzo: so.Mapped[float] = so.mapped_column(default=5.0)
    disponibile: so.Mapped[bool] = so.mapped_column(default=True)
    gestore_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    created_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relazioni
    gestore: so.Mapped[User] = so.relationship(back_populates='menu_creati')
    prenotazioni: so.WriteOnlyMapped['Prenotazione'] = so.relationship(back_populates='menu')

    def __repr__(self):
        return f'<MenuGiornaliero {self.data}>'

class Prenotazione(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    utente_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    menu_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(MenuGiornaliero.id), index=True)
    orario_ritiro: so.Mapped[str] = so.mapped_column(sa.String(10))
    stato: so.Mapped[str] = so.mapped_column(sa.String(20), default='in_attesa')  # in_attesa, pagata, confermata, ritirata, cancellata
    note: so.Mapped[Optional[str]] = so.mapped_column(sa.String(500))
    created_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    utente: so.Mapped[User] = so.relationship(back_populates='prenotazioni')
    menu: so.Mapped[MenuGiornaliero] = so.relationship(back_populates='prenotazioni')
    transazione: so.Mapped[Optional['Transazione']] = so.relationship(back_populates='prenotazione', uselist=False)

    def __repr__(self):
        return f'<Prenotazione {self.id} - User {self.utente_id}>'
    
    def conferma_pagamento(self):
        """Conferma il pagamento della prenotazione"""
        self.stato = 'pagata'
        self.updated_at = datetime.now(timezone.utc)
    
    def cancella(self):
        """Cancella la prenotazione"""
        self.stato = 'cancellata'
        self.updated_at = datetime.now(timezone.utc)

class Transazione(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    utente_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    prenotazione_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey(Prenotazione.id), index=True)
    tipo: so.Mapped[str] = so.mapped_column(sa.String(50))  # pagamento_pasto
    importo: so.Mapped[float] = so.mapped_column()
    metodo_pagamento: so.Mapped[str] = so.mapped_column(sa.String(50))  # paypal
    stato: so.Mapped[str] = so.mapped_column(sa.String(20), default='completata')  # completata, fallita, in_attesa
    paypal_order_id: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200))
    created_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    utente: so.Mapped[User] = so.relationship(back_populates='transazioni')
    prenotazione: so.Mapped[Optional[Prenotazione]] = so.relationship(back_populates='transazione')

    def __repr__(self):
        return f'<Transazione {self.id} - {self.tipo} - €{self.importo}>'


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))