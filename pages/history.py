"""Pagina cronologia APP"""
import streamlit as st
from database.models import bot_manager
from config.settings import BOT_STATUS

def show_history_page():
    """Mostra pagina cronologia APP"""
    
    if 'user_id' not in st.session_state:
        st.error("Devi effettuare il login per accedere alla cronologia APP")
        return
    
    user_id = st.session_state.user_id
    
    st.title("Cronologia APP")
    st.write("Visualizza la cronologia delle tue APP di trading.")
    
    # Recupera cronologia bot
    bot_history = bot_manager.get_user_bot_history(user_id, limit=10)
    
    if bot_history:
        for i, bot in enumerate(bot_history):
            # Determina stato
            status = bot.get('status', 'unknown')
                
            created_at = bot.get('created_at')
            if created_at:
                created_str = created_at.strftime('%d/%m/%Y %H:%M')
            else:
                created_str = 'N/A'
                
            with st.expander(f"APP #{i+1} - {status.upper()} (creata: {created_str})"):
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