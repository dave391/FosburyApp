"""
Applicazione principale Streamlit per Trading Bot
"""
import streamlit as st
from pages.auth import show_auth_page
from pages.settings import show_settings_page
from pages.control import show_control_page
from pages.history import show_history_page
from pages.performance import main as show_performance_page

# Configurazione pagina
st.set_page_config(
    page_title="Trading APP",
    page_icon="assets/favicon.jpeg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carica CSS personalizzato per il font Space Grotesk
def load_css():
    with open('.streamlit/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

def show_sidebar():
    """Mostra sidebar con navigazione"""
    with st.sidebar:
        
        if 'user_id' in st.session_state:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image("assets/logo_night_.jpeg", width=130)
            
            # Titolo centrato sotto il logo
            st.markdown("<h2 style='text-align: center; margin-top: 10px; margin-bottom: 20px; font-size: 1.5rem;'>FOSBURY APP</h2>", unsafe_allow_html=True)
            
            st.divider()
            st.info(f"User: {st.session_state.get('user_email', 'Utente')}")
            st.divider()
            
            # Inizializza la pagina corrente se non esiste
            if 'current_page' not in st.session_state:
                st.session_state.current_page = "Controllo"
            
            # Pulsanti di navigazione
            if st.button("Start/Stop", use_container_width=True, type="secondary"):
                st.session_state.current_page = "Controllo"
                st.rerun()
            
            if st.button("Performance", use_container_width=True, type="secondary"):
                st.session_state.current_page = "Performance"
                st.rerun()
            
            if st.button("Impostazioni", use_container_width=True, type="secondary"):
                st.session_state.current_page = "Impostazioni"
                st.rerun()
            
            if st.button("Cronologia", use_container_width=True, type="secondary"):
                st.session_state.current_page = "Cronologia"
                st.rerun()
            
            st.divider()
            
            # Pulsante logout
            if st.button("Logout", use_container_width=True):
                # Clear session
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
            
            return st.session_state.current_page
        else:
            # Logo centrato nella sidebar per utenti non loggati
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image("assets/logo_night_.jpeg", width=130)
            
            # Titolo centrato sotto il logo
            st.markdown("<h2 style='text-align: center; margin-top: 10px; margin-bottom: 20px; font-size: 1.5rem;'>FOSBURY APP</h2>", unsafe_allow_html=True)
            
            return "Login"

def main():
    """Funzione principale"""
    
    # Router delle pagine
    if 'user_id' not in st.session_state:
        # Utente non loggato - mostra solo auth
        show_sidebar()
        if not show_auth_page():
            st.stop()
    else:
        # Utente loggato - mostra sidebar e pagina selezionata
        current_page = show_sidebar()
        
        if current_page == "Controllo":
            show_control_page()
        elif current_page == "Impostazioni":
            st.header("Impostazioni")
            show_settings_page()
        elif current_page == "Cronologia":
            show_history_page()
        elif current_page == "Performance":
            show_performance_page()

if __name__ == "__main__":
    main()