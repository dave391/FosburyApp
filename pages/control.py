"""
Pagina controllo APP (Start/Stop bot)
"""
import streamlit as st
from database.models import bot_manager, user_manager
from config.settings import (MIN_CAPITAL, MAX_LEVERAGE, MIN_LEVERAGE, SUPPORTED_EXCHANGES, BOT_STATUS,
                            MIN_REBALANCE_THRESHOLD, MAX_REBALANCE_THRESHOLD, DEFAULT_REBALANCE_THRESHOLD,
                            MIN_SAFETY_THRESHOLD, MAX_SAFETY_THRESHOLD, DEFAULT_SAFETY_THRESHOLD,
                            MIN_STOP_LOSS, MAX_STOP_LOSS, DEFAULT_STOP_LOSS)

def validate_config(exchange_long: str, exchange_short: str, capital: float, leverage: float, 
                   rebalance_threshold: float, safety_threshold: float, stop_loss_percentage: float) -> tuple[bool, str]:
    """Valida configurazione APP"""
    
    if exchange_long == exchange_short:
        return False, "Gli exchange long e short devono essere diversi"
    
    if exchange_long not in SUPPORTED_EXCHANGES or exchange_short not in SUPPORTED_EXCHANGES:
        return False, "Exchange non supportato"
    
    if capital < MIN_CAPITAL:
        return False, f"Capitale minimo: {MIN_CAPITAL} USDT"
    
    if leverage < MIN_LEVERAGE or leverage > MAX_LEVERAGE:
        return False, f"Leva deve essere tra {MIN_LEVERAGE} e {MAX_LEVERAGE}"
    
    if rebalance_threshold < MIN_REBALANCE_THRESHOLD or rebalance_threshold > MAX_REBALANCE_THRESHOLD:
        return False, f"Soglia Bilanciamento deve essere tra {MIN_REBALANCE_THRESHOLD}% e {MAX_REBALANCE_THRESHOLD}%"
    
    if safety_threshold < MIN_SAFETY_THRESHOLD or safety_threshold > MAX_SAFETY_THRESHOLD:
        return False, f"Safety Percentage deve essere tra {MIN_SAFETY_THRESHOLD}% e {MAX_SAFETY_THRESHOLD}%"
    
    if stop_loss_percentage < MIN_STOP_LOSS or stop_loss_percentage > MAX_STOP_LOSS:
        return False, f"Stop Loss deve essere tra {MIN_STOP_LOSS}% e {MAX_STOP_LOSS}%"
    
    return True, ""

def check_api_keys_configured(user_id: str, exchange_long: str, exchange_short: str) -> tuple[bool, str]:
    """Verifica che le API keys siano configurate per gli exchange selezionati"""
    api_keys = user_manager.get_user_api_keys(user_id)
    
    missing_keys = []
    
    # Verifica exchange long
    if not api_keys.get(f"{exchange_long}_api_key") or not api_keys.get(f"{exchange_long}_api_secret"):
        missing_keys.append(exchange_long.capitalize())
    
    # Verifica exchange short
    if not api_keys.get(f"{exchange_short}_api_key") or not api_keys.get(f"{exchange_short}_api_secret"):
        missing_keys.append(exchange_short.capitalize())
    
    if missing_keys:
        return False, f"API Keys mancanti per: {', '.join(missing_keys)}"
    
    return True, ""

def show_control_page():
    """Mostra pagina controllo APP"""
    st.title("Fosbury App")
    
    if 'user_id' not in st.session_state:
        st.error("Devi effettuare il login per accedere al controllo APP")
        return

    user_id = st.session_state.user_id
    
    # Recupera configurazione esistente
    current_bot = bot_manager.get_user_bot(user_id)
    
    # Mostra sezione controllo per tutti gli status tranne "stopped"
    if current_bot and current_bot.get("status") != BOT_STATUS["STOPPED"]:
        show_bot_control_section(current_bot, user_id)
        return
    
    # Mostra popup di conferma se richiesto
    if st.session_state.get('show_confirmation_popup', False):
        show_confirmation_popup()
    
    # Form configurazione
    st.subheader("Configurazione APP")
    
    with st.form("bot_config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            exchange_long = st.selectbox(
                "Exchange Long",
                options=SUPPORTED_EXCHANGES,
                index=0 if not current_bot else SUPPORTED_EXCHANGES.index(current_bot.get("exchange_long", SUPPORTED_EXCHANGES[0])),
                help="Exchange dove aprire posizione long"
            )
        
        with col2:
            exchange_short = st.selectbox(
                "Exchange Short",
                options=SUPPORTED_EXCHANGES,
                index=1 if not current_bot else SUPPORTED_EXCHANGES.index(current_bot.get("exchange_short", SUPPORTED_EXCHANGES[1])),
                help="Exchange dove aprire posizione short"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            capital = st.number_input(
                "Capitale Totale (USDT)",
                min_value=float(MIN_CAPITAL),
                value=float(current_bot.get("capital", MIN_CAPITAL)) if current_bot else float(MIN_CAPITAL),
                step=1.0,
                help=f"Capitale minimo: {MIN_CAPITAL} USDT"
            )
        
        with col2:
            leverage = st.number_input(
                "Leva",
                min_value=float(MIN_LEVERAGE),
                max_value=float(MAX_LEVERAGE),
                value=float(current_bot.get("leverage", MIN_LEVERAGE)) if current_bot else float(MIN_LEVERAGE),
                step=0.1,
                help=f"Leva da {MIN_LEVERAGE}x a {MAX_LEVERAGE}x"
            )
        
        # Nuovi parametri di configurazione
        col1, col2, col3 = st.columns(3)
        
        with col1:
            rebalance_threshold = st.slider(
                "Soglia Bilanciamento Margine (%)",
                min_value=MIN_REBALANCE_THRESHOLD,
                max_value=MAX_REBALANCE_THRESHOLD,
                value=int(current_bot.get("rebalance_threshold", DEFAULT_REBALANCE_THRESHOLD)) if current_bot else DEFAULT_REBALANCE_THRESHOLD,
                step=1,
                help=f"Soglia per il bilanciamento del margine da {MIN_REBALANCE_THRESHOLD}% a {MAX_REBALANCE_THRESHOLD}%"
            )
        
        with col2:
            safety_threshold = st.slider(
                "Safety Percentage (%)",
                min_value=MIN_SAFETY_THRESHOLD,
                max_value=MAX_SAFETY_THRESHOLD,
                value=int(current_bot.get("safety_threshold", DEFAULT_SAFETY_THRESHOLD)) if current_bot else DEFAULT_SAFETY_THRESHOLD,
                step=1,
                help=f"Percentuale di sicurezza da {MIN_SAFETY_THRESHOLD}% a {MAX_SAFETY_THRESHOLD}%"
            )
        
        with col3:
            stop_loss_percentage = st.slider(
                "Stop Loss (%)",
                min_value=MIN_STOP_LOSS,
                max_value=MAX_STOP_LOSS,
                value=int(current_bot.get("stop_loss_percentage", DEFAULT_STOP_LOSS)) if current_bot else DEFAULT_STOP_LOSS,
                step=1,
                help=f"Soglia di stop loss da {MIN_STOP_LOSS}% a {MAX_STOP_LOSS}%"
            )
        
        start_app = st.form_submit_button("START APP", use_container_width=True)
        
        if start_app:
            # Validazioni
            is_valid, error_msg = validate_config(exchange_long, exchange_short, capital, leverage, rebalance_threshold, safety_threshold, stop_loss_percentage)
            if not is_valid:
                st.error(error_msg)
            else:
                # Verifica API keys prima di procedere
                keys_valid, keys_error = check_api_keys_configured(user_id, exchange_long, exchange_short)
                if not keys_valid:
                    st.error(f"{keys_error}. Configura le API keys prima di avviare.")
                else:
                    # Salva parametri in session_state e mostra popup di conferma
                    st.session_state.config_params = {
                        'exchange_long': exchange_long,
                        'exchange_short': exchange_short,
                        'capital': capital,
                        'leverage': leverage,
                        'rebalance_threshold': rebalance_threshold,
                        'safety_threshold': safety_threshold,
                        'stop_loss_percentage': stop_loss_percentage
                    }
                    st.session_state.show_confirmation_popup = True
                    st.rerun()

def show_bot_control_section(current_bot, user_id):
    """Mostra sezione di controllo per bot attivo"""
    st.subheader("APP Attiva")
    
    # Mostra status del bot
    status = current_bot.get("status", "unknown")
    stopped_type = current_bot.get("stopped_type", "")
    
    # Se è in stop_requested con stopped_type manual, mostra status di chiusura
    if status == BOT_STATUS["STOP_REQUESTED"] and stopped_type == "manual":
        st.info(f"**Status:** 🟠 Chiusura posizioni in corso")
    else:
        # Per tutti gli altri stati attivi mostra "In Esecuzione"
        st.info(f"**Status:** 🟢 In Esecuzione")
    
    # Mostra configurazione corrente
    with st.expander("Configurazione Corrente", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Exchange Long:** {current_bot.get('exchange_long', 'N/A')}")
            st.write(f"**Exchange Short:** {current_bot.get('exchange_short', 'N/A')}")
            st.write(f"**Capitale:** {current_bot.get('capital', 'N/A')} USDT")
            st.write(f"**Leva:** {current_bot.get('leverage', 'N/A')}x")
        
        with col2:
            st.write(f"**Soglia Bilanciamento:** {current_bot.get('rebalance_threshold', 'N/A')}%")
            st.write(f"**Safety Percentage:** {current_bot.get('safety_threshold', 'N/A')}%")
            st.write(f"**Stop Loss:** {current_bot.get('stop_loss_percentage', 'N/A')}%")
    
    # Sezione incremento capitale
    st.subheader("Incremento Capitale")
    
    # Controllo del campo increase per mostrare l'interfaccia appropriata
    if current_bot.get('increase', False):
        # Se increase è True, mostra messaggio di operazioni in corso
        st.warning("In questo momento stiamo effettuando operazioni sui tuoi account, torna più tardi per incrementare la tua posizione")
    else:
        # Se increase è False, mostra l'interfaccia di incremento
        with st.form("capital_increase_form"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                capital_increase = st.number_input(
                    "Importo da aggiungere (USDT)",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    help="Inserisci l'importo da aggiungere al capitale esistente"
                )
            
            with col2:
                st.write("")  # Spazio vuoto per allineamento
                st.write("")  # Spazio vuoto per allineamento
                increase_capital = st.form_submit_button("Incrementa", use_container_width=True)
            
            if increase_capital:
                if capital_increase <= 0:
                    st.error("L'importo deve essere maggiore di 0")
                else:
                    # Salva i dati per il pop-up di conferma
                    st.session_state.capital_increase_amount = capital_increase
                    st.session_state.current_capital = current_bot.get('capital', 0)
                    st.session_state.show_increment_confirmation = True
                    st.rerun()
    
    # Mostra il pop-up di conferma se richiesto
    if st.session_state.get('show_increment_confirmation', False):
        show_increment_confirmation_popup(user_id)
    
    # Form per fermare il bot
    if status not in [BOT_STATUS["STOP_REQUESTED"], BOT_STATUS["TRANSFER_REQUESTED"]]:
        st.subheader("Controllo APP")
        
        with st.form("stop_bot_form"):
            stop_app = st.form_submit_button("STOP APP", use_container_width=True)
            
            if stop_app:
                # Aggiorna status a STOP_REQUESTED con motivo di default "manual"
                if bot_manager.update_bot_status(user_id, BOT_STATUS["STOP_REQUESTED"], "manual"):
                    st.success("Richiesta di stop inviata. L'APP si fermerà dopo aver chiuso le posizioni.")
                    st.rerun()
                else:
                    st.error("Errore nell'invio della richiesta di stop.")
    else:
        st.info("L'APP si sta fermando. Chiuderemo le posizioni ottimizzando il risultato. Torna più tardi.")
        
        # Bottone per aggiornare lo status
        if st.button("Aggiorna Status", use_container_width=True):
            st.rerun()

@st.dialog("Conferma Avvio APP")
def show_confirmation_popup():
    """Mostra popup di conferma con riepilogo parametri"""
    st.write("### Riepilogo Configurazione")
    
    # Recupera parametri salvati in session_state
    config = st.session_state.get('config_params', {})
    
    # Mostra riepilogo in due colonne
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Exchange Long:**")
        st.write(config.get('exchange_long', 'N/A'))
        
        st.write("**Exchange Short:**")
        st.write(config.get('exchange_short', 'N/A'))
        
        st.write("**Capitale Totale:**")
        st.write(f"{config.get('capital', 'N/A')} USDT")
        
        st.write("**Leva:**")
        st.write(f"{config.get('leverage', 'N/A')}x")
    
    with col2:
        st.write("**Soglia Bilanciamento:**")
        st.write(f"{config.get('rebalance_threshold', 'N/A')}%")
        
        st.write("**Safety Percentage:**")
        st.write(f"{config.get('safety_threshold', 'N/A')}%")
        
        st.write("**Stop Loss:**")
        st.write(f"{config.get('stop_loss_percentage', 'N/A')}%")
    
    st.divider()
    
    # Bottoni di azione
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Cambia Parametri", use_container_width=True):
            # Chiudi popup e torna alla configurazione
            st.session_state.show_confirmation_popup = False
            st.rerun()
    
    with col2:
        if st.button("Conferma Avvio APP", use_container_width=True):
            # Procedi con l'avvio del bot
            user_id = st.session_state.user_id
            config = st.session_state.config_params
            
            # Crea bot con i parametri salvati
            if bot_manager.create_bot_config(
                user_id, 
                config['exchange_long'], 
                config['exchange_short'], 
                config['capital'], 
                config['leverage'], 
                config['rebalance_threshold'], 
                config['safety_threshold'], 
                config['stop_loss_percentage']
            ):
                st.success("APP avviata con successo!")
                # Pulisci session state
                st.session_state.show_confirmation_popup = False
                if 'config_params' in st.session_state:
                    del st.session_state.config_params
                st.rerun()
            else:
                st.error("Errore nell'avvio dell'APP")

@st.dialog("Conferma Incremento Capitale")
def show_increment_confirmation_popup(user_id):
    """Mostra il pop-up di conferma per l'incremento del capitale"""
    
    # Recupera i dati dal session state
    capital_increase_amount = st.session_state.get('capital_increase_amount', 0)
    current_capital = st.session_state.get('current_capital', 0)
    new_total_capital = current_capital + capital_increase_amount
    
    st.write("### Riepilogo Incremento")
    st.write("Conferma i dettagli dell'incremento del capitale:")
    
    # Mostra il riepilogo in formato tabella
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Importo da aggiungere:**")
        st.write("**Capitale attuale:**")
        st.write("**Nuovo capitale totale:**")
    
    with col2:
        st.write(f"{capital_increase_amount:.2f} USDT")
        st.write(f"{current_capital:.2f} USDT")
        st.write(f"**{new_total_capital:.2f} USDT**")
    
    st.divider()
    
    # Bottoni di conferma
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Modifica Parametri", use_container_width=True):
            # Chiudi il pop-up e torna al form
            st.session_state.show_increment_confirmation = False
            st.rerun()
    
    with col2:
        if st.button("Conferma Incremento", use_container_width=True):
            # Esegui l'incremento del capitale
            if bot_manager.update_capital_increase(user_id, capital_increase_amount, True):
                st.session_state.show_increment_confirmation = False
                st.success(f"Richiesta di incremento capitale di {capital_increase_amount} USDT inviata con successo!")
                st.info("L'incremento verrà applicato al prossimo ciclo di elaborazione del bot.")
                st.rerun()
            else:
                st.error("Errore nell'invio della richiesta di incremento capitale.")