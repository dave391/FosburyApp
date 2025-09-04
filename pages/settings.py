"""
Pagina impostazioni API Keys
"""
import streamlit as st
from database.models import user_manager
import ccxt
import time
from utils.exchange_utils import ExchangeUtils, get_exchange_config

def test_exchange_connection(exchange_name: str, api_key: str, api_secret: str) -> bool:
    """Test connessione all'exchange con gestione errori avanzata"""
    try:
        # Ottieni configurazione exchange
        config = get_exchange_config(exchange_name)
        
        if exchange_name == "bitfinex":
            exchange_config = {
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': False,
                'enableRateLimit': True,
                'timeout': 30000,
                'options': config.get('options', {})
            }
            
            # Aggiungi nonce per Bitfinex
            if config.get('requires_nonce'):
                exchange_config['nonce'] = lambda: int(time.time() * 1000)
            
            exchange = ccxt.bitfinex(exchange_config)
            
        elif exchange_name == "bitmex":
            exchange_config = {
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': False,
                'enableRateLimit': True,
                'timeout': 30000,
                'options': config.get('options', {})
            }
            
            exchange = ccxt.bitmex(exchange_config)
            
        else:
            st.error(f"Exchange {exchange_name} non supportato")
            return False
        
        # Test connessione con retry per nonce
        def test_balance():
            exchange.load_markets()  # Carica mercati prima
            balance = exchange.fetch_balance()
            return balance
        
        balance = ExchangeUtils.retry_with_nonce_fix(test_balance, max_retries=3, wait_seconds=2)
        
        st.success(f"Connessione {exchange_name} riuscita! Bilancio caricato.")
        return True
        
    except Exception as e:
        error_msg = str(e)
        
        if ExchangeUtils.is_nonce_error(error_msg):
            st.error(f"Errore nonce {exchange_name}: Le API keys potrebbero essere state usate di recente. Aspetta qualche secondo e riprova.")
            st.info("Suggerimento: Se il problema persiste, attendi 1-2 minuti prima di riprovare.")
        elif ExchangeUtils.is_auth_error(error_msg):
            st.error(f"API keys {exchange_name} non valide o permessi insufficienti")
            st.info("Verifica che le API keys abbiano permessi di trading sui futures.")
        elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
            st.error(f"Problema di connessione {exchange_name}: {error_msg}")
            st.info("Controlla la connessione internet e riprova.")
        else:
            st.error(f"Errore connessione {exchange_name}: {error_msg}")
        
        return False

def show_settings_page():
    """Mostra pagina impostazioni"""
    
    if 'user_id' not in st.session_state:
        st.error("Devi effettuare il login per accedere alle impostazioni")
        return
    
    st.title("Impostazioni API Keys e Wallet")
    st.write("Configura le tue API keys e wallet addresses per gli exchange supportati.")
    
    # Recupera API keys e wallets esistenti
    user_id = st.session_state.user_id
    current_keys = user_manager.get_user_api_keys(user_id)
    current_wallets = user_manager.get_user_wallets(user_id)
    
    # Sezione Bitfinex
    st.subheader("🔹 Bitfinex API Keys e Wallet")
    
    with st.form("bitfinex_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            bitfinex_key = st.text_input(
                "API Key Bitfinex", 
                value=current_keys.get("bitfinex_api_key", ""),
                placeholder="Inserisci API Key Bitfinex",
                type="password"
            )
        
        with col2:
            bitfinex_secret = st.text_input(
                "API Secret Bitfinex", 
                value=current_keys.get("bitfinex_api_secret", ""),
                placeholder="Inserisci API Secret Bitfinex",
                type="password"
            )
        
        # Campo wallet Bitfinex
        bitfinex_wallet = st.text_input(
            "Wallet Address Bitfinex", 
            value=current_wallets.get("bitfinex_wallet", ""),
            placeholder="Inserisci indirizzo wallet Bitfinex",
            help="Indirizzo del wallet per ricevere/inviare fondi su Bitfinex"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            test_bitfinex = st.form_submit_button("🧪 Testa Connessione", use_container_width=True)
        with col2:
            save_bitfinex = st.form_submit_button("Salva Bitfinex", use_container_width=True)
        
        if test_bitfinex:
            if bitfinex_key and bitfinex_secret:
                with st.spinner("Test connessione Bitfinex..."):
                    if test_exchange_connection("bitfinex", bitfinex_key, bitfinex_secret):
                        st.success("Connessione Bitfinex riuscita!")
            else:
                st.warning("Inserisci entrambe le chiavi per testare la connessione")
        
        if save_bitfinex:
            if bitfinex_key and bitfinex_secret:
                # Salva API keys
                api_success = user_manager.update_api_keys(user_id, "bitfinex", bitfinex_key, bitfinex_secret)
                
                # Salva wallet se presente
                wallet_success = True
                if bitfinex_wallet:
                    wallet_success = user_manager.update_wallet(user_id, "bitfinex", bitfinex_wallet)
                
                if api_success and wallet_success:
                    if bitfinex_wallet:
                        st.success("API Keys e Wallet Bitfinex salvati!")
                    else:
                        st.success("API Keys Bitfinex salvate!")
                else:
                    st.error("Errore nel salvataggio")
            else:
                st.warning("Inserisci entrambe le chiavi per salvare")
    
    st.divider()
    
    # Sezione Bitmex
    st.subheader("🔸 Bitmex API Keys e Wallet")
    
    with st.form("bitmex_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            bitmex_key = st.text_input(
                "API Key Bitmex", 
                value=current_keys.get("bitmex_api_key", ""),
                placeholder="Inserisci API Key Bitmex",
                type="password"
            )
        
        with col2:
            bitmex_secret = st.text_input(
                "API Secret Bitmex", 
                value=current_keys.get("bitmex_api_secret", ""),
                placeholder="Inserisci API Secret Bitmex",
                type="password"
            )
        
        # Campo wallet Bitmex
        bitmex_wallet = st.text_input(
            "Wallet Address Bitmex", 
            value=current_wallets.get("bitmex_wallet", ""),
            placeholder="Inserisci indirizzo wallet Bitmex",
            help="Indirizzo del wallet per ricevere/inviare fondi su Bitmex"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            test_bitmex = st.form_submit_button("🧪 Testa Connessione", use_container_width=True)
        with col2:
            save_bitmex = st.form_submit_button("Salva Bitmex", use_container_width=True)
        
        if test_bitmex:
            if bitmex_key and bitmex_secret:
                with st.spinner("Test connessione Bitmex..."):
                    if test_exchange_connection("bitmex", bitmex_key, bitmex_secret):
                        st.success("Connessione Bitmex riuscita!")
            else:
                st.warning("Inserisci entrambe le chiavi per testare la connessione")
        
        if save_bitmex:
            if bitmex_key and bitmex_secret:
                # Salva API keys
                api_success = user_manager.update_api_keys(user_id, "bitmex", bitmex_key, bitmex_secret)
                
                # Salva wallet se presente
                wallet_success = True
                if bitmex_wallet:
                    wallet_success = user_manager.update_wallet(user_id, "bitmex", bitmex_wallet)
                
                if api_success and wallet_success:
                    if bitmex_wallet:
                        st.success("API Keys e Wallet Bitmex salvati!")
                    else:
                        st.success("API Keys Bitmex salvate!")
                else:
                    st.error("Errore nel salvataggio")
            else:
                st.warning("Inserisci entrambe le chiavi per salvare")
    
    # Info di sicurezza
    st.info("Le API keys e i wallet addresses vengono salvati in modo crittografato nel database.")
    st.warning("Assicurati che le API keys abbiano i permessi di trading sui futures.")
    st.info("I wallet addresses sono opzionali e possono essere utilizzati per operazioni di deposito/prelievo.")