"""
Pagina controllo APP (Start/Stop bot)
"""
import streamlit as st
from database.models import bot_manager, user_manager
from config.settings import (MIN_CAPITAL, MAX_LEVERAGE, MIN_LEVERAGE, SUPPORTED_EXCHANGES, BOT_STATUS,
                            MIN_REBALANCE_THRESHOLD, MAX_REBALANCE_THRESHOLD, DEFAULT_REBALANCE_THRESHOLD,
                            MIN_SAFETY_THRESHOLD, MAX_SAFETY_THRESHOLD, DEFAULT_SAFETY_THRESHOLD)

def validate_config(exchange_long: str, exchange_short: str, capital: float, leverage: float, 
                   rebalance_threshold: float, safety_threshold: float) -> tuple[bool, str]:
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
    
    if 'user_id' not in st.session_state:
        st.error("Devi effettuare il login per accedere al controllo APP")
        return
    
    user_id = st.session_state.user_id
    
    st.title("Controllo APP Trading")
    st.write("Configura e gestisci la tua APP di trading automatizzata.")
    
    # Recupera configurazione esistente
    current_bot = bot_manager.get_user_bot(user_id)
    
    # Mostra status corrente se esiste
    if current_bot:
        status = current_bot.get("status", "unknown")
        started_at = current_bot.get("started_at")
        stopped_at = current_bot.get("stopped_at")
        stopped_type = current_bot.get("stopped_type")
        
        # Status principale
        if status == BOT_STATUS["READY"]:
            st.info("**Status APP**: Pronta per l'avvio")
        elif status == BOT_STATUS["RUNNING"]:
            st.success("**Status APP**: In esecuzione")
            if started_at:
                st.caption(f"Avviata il: {started_at.strftime('%d/%m/%Y alle %H:%M:%S')}")
        elif status == BOT_STATUS["STOP_REQUESTED"]:
            st.warning("**Status APP**: Chiusura in corso...")
            if started_at:
                st.caption(f"Avviata il: {started_at.strftime('%d/%m/%Y alle %H:%M:%S')}")
            st.caption("In attesa del modulo Closer per la chiusura delle posizioni")
        elif status == BOT_STATUS["STOPPED"]:
            st.error("**Status APP**: Fermata")
            if stopped_at:
                st.caption(f"Fermata il: {stopped_at.strftime('%d/%m/%Y alle %H:%M:%S')}")
            if stopped_type:
                if stopped_type == "manual":
                    st.caption("Motivo: Stop manuale")
                elif stopped_type == "success":
                    st.caption("Motivo: Chiusura completata")
                elif stopped_type == "new_instance":
                    st.caption("Motivo: Nuova istanza avviata")
                elif stopped_type == "safety":
                    st.caption("Motivo: Safety trigger attivato")
                else:
                    st.caption(f"Motivo: {stopped_type}")
        elif status == BOT_STATUS["READY_TO_RESTART"]:
            st.warning("**Status APP**: Pronta per riavvio automatico")
            if stopped_at:
                st.caption(f"Fermata il: {stopped_at.strftime('%d/%m/%Y alle %H:%M:%S')}")
            st.caption("Motivo: Safety trigger - posizioni chiuse per sicurezza")
            st.info("L'APP è pronta per essere riavviata automaticamente quando le condizioni di mercato migliorano")
        else:
            st.warning(f"**Status APP**: {status}")
        
        # Informazioni aggiuntive
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Exchange Long", current_bot.get("exchange_long", "N/A"))
        with col2:
            st.metric("Exchange Short", current_bot.get("exchange_short", "N/A"))
        with col3:
            capital = current_bot.get("capital", 0)
            leverage = current_bot.get("leverage", 1)
            capital_per_exchange = capital / 2
            st.metric("Capitale Reale", f"{capital:.1f} USDT")
            st.caption(f"({capital_per_exchange:.1f} per exchange, leva {leverage}x)")
        
        st.divider()
    
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
                value=float(current_bot.get("leverage", 1)) if current_bot else 1.0,
                step=0.1,
                help=f"Leva da {MIN_LEVERAGE} a {MAX_LEVERAGE}"
            )
        
        # Nuovi parametri di configurazione
        col1, col2 = st.columns(2)
        
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
        
        # Calcolo capitale reale e sizing
        capital_per_exchange = capital / 2
        capital_with_leverage = capital_per_exchange * leverage
        
        st.info(f"**Investimento reale**: {capital:.1f} USDT ({capital_per_exchange:.1f} USDT per exchange)")
        st.info(f"**Size calculation**: {capital_with_leverage:.1f} USDT per exchange (con leva {leverage}x)")
        
        col1, col2 = st.columns(2)
        with col1:
            save_config = st.form_submit_button("Salva Configurazione", use_container_width=True)
        with col2:
            start_app = st.form_submit_button("START APP", use_container_width=True, type="primary")
        
        if save_config:
            # Validazioni
            is_valid, error_msg = validate_config(exchange_long, exchange_short, capital, leverage, rebalance_threshold, safety_threshold)
            if not is_valid:
                st.error(error_msg)
            else:
                # Verifica API keys
                keys_valid, keys_error = check_api_keys_configured(user_id, exchange_long, exchange_short)
                if not keys_valid:
                    st.error(f"{keys_error}. Vai alla pagina Impostazioni per configurarle.")
                else:
                    # Salva configurazione
                    if bot_manager.create_bot_config(user_id, exchange_long, exchange_short, capital, leverage, rebalance_threshold, safety_threshold):
                        st.success("Configurazione salvata! APP pronta per l'avvio.")
                        st.rerun()
                    else:
                        st.error("Errore nel salvataggio della configurazione")
        
        if start_app:
            # Validazioni
            is_valid, error_msg = validate_config(exchange_long, exchange_short, capital, leverage, rebalance_threshold, safety_threshold)
            if not is_valid:
                st.error(error_msg)
            else:
                # Verifica API keys prima di avviare
                keys_valid, keys_error = check_api_keys_configured(user_id, exchange_long, exchange_short)
                if not keys_valid:
                    st.error(f"{keys_error}. Configura le API keys prima di avviare.")
                else:
                    # Crea SEMPRE una nuova istanza del bot con status READY
                    if bot_manager.create_bot_config(user_id, exchange_long, exchange_short, capital, leverage, rebalance_threshold, safety_threshold):
                        st.success("Nuova APP avviata! Il modulo Opener rileverà la configurazione.")
                        st.rerun()
                    else:
                        st.error("Errore nell'avvio della nuova APP")
    
    st.divider()
    
    # Controllo Stop APP
    st.subheader("Controllo Stop APP")
    
    if st.button("STOP APP", use_container_width=True, type="secondary"):
        if not current_bot:
            st.warning("Nessuna APP configurata")
        elif current_bot.get("status") == BOT_STATUS["STOPPED"]:
            st.warning("L'APP è già fermata!")
        elif current_bot.get("status") == BOT_STATUS["STOP_REQUESTED"]:
            st.warning("Chiusura dell'APP già richiesta! In attesa del modulo Closer...")
        else:
            # Richiedi la chiusura impostando lo stato a "stop_requested"
            with st.spinner("Richiesta chiusura in corso..."):
                try:
                    # Aggiorna lo stato del bot a "stop_requested"
                    if bot_manager.update_bot_status(user_id, BOT_STATUS["STOP_REQUESTED"], "manual"):
                        st.success("Richiesta di chiusura inviata! Il modulo Closer chiuderà le posizioni a breve.")
                        st.info("Puoi verificare lo stato dell'APP nella sezione 'Cronologia APP'")
                        # Non fare st.rerun() per evitare problemi con lo stato
                    else:
                        st.error("Errore nell'invio della richiesta di chiusura")
                except Exception as e:
                    import traceback
                    st.error(f"Errore non gestito: {str(e)}")
                    st.code(traceback.format_exc())
    
    # Informazioni di sistema
    st.divider()
    st.subheader("Informazioni")
    st.info("""
    **Come funziona:**
    1. Configura gli exchange e i parametri di trading
    2. Assicurati che le API keys siano configurate nella pagina Impostazioni
    3. Premi START per rendere l'APP pronta all'esecuzione
    4. Il modulo Opener (eseguito separatamente) rileverà la configurazione e avvierà il trading
    5. Usa STOP per richiedere la chiusura dell'APP
    6. Il modulo Closer (eseguito separatamente) rileverà la richiesta e chiuderà le posizioni
    """)
    
    st.warning("**Strategia**: Funding Arbitrage su SOLANA/USDT Perpetual Futures")
    st.info("**Calcolo Size**: Il capitale viene diviso equamente tra i due exchange e convertito in SOLANA (arrotondato per difetto a 0.1)")
    
    # Sezione cronologia bot
    st.divider()
    st.subheader("Cronologia APP")
    
    bot_history = bot_manager.get_user_bot_history(user_id, limit=5)
    if bot_history:
        for i, bot in enumerate(bot_history):
            # Determina stato
            status = bot.get('status', 'unknown')
                
            with st.expander(f"APP #{i+1} - {status.upper()} (creata: {bot.get('created_at', 'N/A').strftime('%d/%m/%Y %H:%M') if bot.get('created_at') else 'N/A'})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Exchange Long**: {bot.get('exchange_long', 'N/A')}")
                    st.write(f"**Exchange Short**: {bot.get('exchange_short', 'N/A')}")
                
                with col2:
                    st.write(f"**Capitale**: {bot.get('capital', 0)} USDT")
                    st.write(f"**Leva**: {bot.get('leverage', 1)}x")
                
                with col3:
                    if bot.get('started_at'):
                        st.write(f"**Avviata**: {bot['started_at'].strftime('%d/%m/%Y %H:%M')}")
                    if status == BOT_STATUS["STOP_REQUESTED"]:
                        st.write("**Stato**: Chiusura in corso...")
                    if bot.get('stopped_at'):
                        st.write(f"**Fermata**: {bot['stopped_at'].strftime('%d/%m/%Y %H:%M')}")
                        if bot.get('stopped_type'):
                            st.write(f"**Motivo**: {bot['stopped_type']}")
    else:
        st.info("Nessuna cronologia APP disponibile")