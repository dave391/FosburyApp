# Trading APP - Funding Arbitrage Bot

Applicazione web multi-utente per trading automatizzato con strategia di funding arbitrage su SOLANA/USDT.

## Stack Tecnologico

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: MongoDB
- **Exchange**: Bitfinex, Bitmex
- **Trading Library**: CCXT

## Installazione

1. **Installa le dipendenze:**
```bash
pip install -r requirements.txt
```

2. **Configura variabili d'ambiente:**
   - Crea file `.env` nella root del progetto
   - Inserisci le seguenti variabili:
```env
DB_PASSWORD=your_database_password_here
ENCRYPTION_KEY=your_encryption_key_here
ENVIRONMENT=production
DEBUG=false
```

3. **Setup database:**
```bash
python database/setup_db.py
```

4. **Test configurazione:**
```bash
python test_setup.py
```

5. **Avvia l'applicazione:**
```bash
streamlit run app.py
```

## Struttura Progetto

```
trading_bot_app/
├── app.py                          # App principale Streamlit
├── opener.py                       # Modulo Opener indipendente
├── config/
│   └── settings.py                 # Configurazioni
├── database/
│   └── models.py                   # Modelli MongoDB
├── pages/
│   ├── auth.py                     # Login/Registrazione
│   ├── settings.py                 # Impostazioni API Keys
│   └── control.py                  # Controllo APP
├── trading/
│   └── exchange_manager.py         # Gestione Exchange CCXT
└── utils/
    └── crypto_utils.py             # Utility crittografia
```

## Utilizzo

### 1. Registrazione/Login
- Registrati con email e password
- Accetta i termini e condizioni
- Effettua il login

### 2. Configurazione API Keys
- Vai alla pagina "Impostazioni"
- Inserisci le API keys di Bitfinex e/o Bitmex
- Testa la connessione prima di salvare

### 3. Controllo APP
- Configura exchange long/short
- Imposta capitale e leva
- Premi START per rendere l'APP pronta
- Il modulo Opener rileverà e eseguirà la strategia

### 4. Esecuzione Modulo Opener
```bash
python opener.py
```

## Script di Manutenzione

### Setup Database
```bash
python database/setup_db.py
```
Crea le collections necessarie con indici ottimizzati.

### Pulizia Database
```bash
python database/cleanup_db.py
```
Pulizia interattiva per eliminare collections non necessarie e bot vecchi.

### Test Configurazione
```bash
python test_setup.py
```
Valida tutto il setup e testa tutte le funzionalità.

### Migrazione Bot Esistenti
```bash
PYTHONPATH=. python database/migrate_existing_bots.py
```
Aggiorna bot esistenti con i nuovi campi del database.

## Strategia Trading

**Funding Arbitrage su SOLANA/USDT Perpetual Futures**

1. Capitale totale = capitale × leva
2. Divisione equa tra due exchange
3. Apertura posizioni opposte (long su uno, short sull'altro)
4. Size SOLANA arrotondata per difetto a 0.1

## Configurazioni

### Limiti Trading
- Capitale minimo: 10 USDT
- Leva: 0-20
- Precision SOLANA: 0.1

### Stati APP
- `ready`: Pronta per l'avvio
- `running`: In esecuzione
- `stopped`: Fermata

## Sicurezza

- Password hashate con bcrypt
- API keys crittografate nel database
- Chiave di crittografia fissa (configurabile)

## Logging

Il modulo Opener salva i log in `opener.log` con livello INFO per operazioni e errori.

## Note Importanti

⚠️ **ATTENZIONE**: Questa è una versione di sviluppo. Prima dell'uso in produzione:

1. Testa su sandbox degli exchange
2. Verifica tutte le configurazioni
3. Implementa gestione errori avanzata
4. Considera limiti di rate delle API
5. Implementa stop-loss e take-profit

## Supporto

Per problemi o domande, verificare i log dell'applicazione e del modulo Opener.