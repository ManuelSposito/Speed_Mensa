document.addEventListener('DOMContentLoaded', () => {
    console.log('Speed Mensa Lite - Inizializzato');
    initForms();
    initInteractions();
    checkConnection();
});


let isLoading = false;

function proceedToPayPal() {
    if (isLoading) return;
    
    const button = document.getElementById('proceed-button');
    if (!button) return;

    // Controllo preventivo: se manca l'URL, fermiamo tutto subito
    if (typeof paypalUrl === 'undefined' || !paypalUrl) {
        showNotification('Errore Configurazione: URL PayPal mancante nel codice.', 'error');
        console.error('Manca la variabile: const paypalUrl = "..." nell\'HTML');
        return;
    }

    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = '🔄 Reindirizzamento...';
    button.style.opacity = '0.7';
    isLoading = true;

    // Simuliamo un breve caricamento per feedback utente
    setTimeout(() => {
        window.location.href = paypalUrl;
    }, 500);
}


function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    // Usiamo classi CSS invece di stili inline complessi
    notification.className = `notification notification-${type}`;
    notification.innerHTML = message;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

function showLoading(message = 'Caricamento...') {
    if (document.getElementById('global-loader')) return;
    const loader = document.createElement('div');
    loader.id = 'global-loader';
    loader.innerHTML = `<div class="spinner"></div><p style="color:white;margin-top:10px">${message}</p>`;
    // Overlay scuro semplice
    Object.assign(loader.style, {
        position: 'fixed', inset: '0', background: 'rgba(0,0,0,0.7)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', zIndex: '10000'
    });
    document.body.appendChild(loader);
}

function hideLoading() {
    const loader = document.getElementById('global-loader');
    if (loader) loader.remove();
}


function initForms() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', (e) => {
            const password = form.querySelector('input[name="password"]');
            const confirm = form.querySelector('input[name="password2"]');
            
            // Unico controllo custom necessario: password match
            if (password && confirm && password.value !== confirm.value) {
                e.preventDefault();
                showNotification('Le password non corrispondono', 'error');
                confirm.focus();
            }
            
            // Gestione conferma eliminazione (attributo data-confirm)
            const confirmMsg = form.getAttribute('data-confirm');
            if (confirmMsg && !confirm(confirmMsg)) {
                e.preventDefault();
            }
        });
    });
}


function initInteractions() {
    // Dark Mode
    if (localStorage.getItem('darkMode') === 'true') document.body.classList.add('dark-mode');
    
    // Gestione click su elementi con conferma semplice
    document.querySelectorAll('[data-confirm-click]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (!confirm(btn.getAttribute('data-confirm-click'))) e.preventDefault();
        });
    });

    // Flash messages (messaggi dal server che devono sparire)
    document.querySelectorAll('.flash').forEach(flash => {
        setTimeout(() => flash.remove(), 5000);
    });
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => showNotification('Copiato!', 'success'))
        .catch(() => showNotification('Errore copia', 'error'));
}


function formatPrezzo(prezzo) {
    return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(prezzo);
}

function formatDataItaliana(dateString) {
    return new Date(dateString).toLocaleDateString('it-IT', { 
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' 
    });
}


function checkConnection() {
    window.addEventListener('offline', () => showNotification('Sei offline', 'warning'));
    window.addEventListener('online', () => showNotification('Tornato online', 'success'));
}

// Export funzioni globali se servono nell'HTML (es. onclick="SpeedMensa.toggleDarkMode()")
window.SpeedMensa = {
    toggleDarkMode,
    copyToClipboard,
    proceedToPayPal,
    formatPrezzo
};