from app import app 
import sqlalchemy as sa 
import sqlalchemy.orm as so 
from app.models import User, MenuGiornaliero, Prenotazione, Transazione

@app.shell_context_processor
def make_shell_context():
    return {
        'sa': sa,
        'so': so,
        'db': db,
        'User': User,
        'MenuGiornaliero': MenuGiornaliero,
        'Prenotazione': Prenotazione,
        'Transazione': Transazione
    }