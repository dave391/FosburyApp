"""
Applicazione principale Streamlit per Trading Bot
"""
import streamlit as st
from pages.auth import show_auth_page
from pages.settings import show_settings_page
from pages.control import show_control_page

# Configurazione pagina
st.set_page_config(
    page_title="Trading APP",
    layout="wide",
    initial_sidebar_state="expanded"
)

def show_sidebar():
    """Mostra sidebar con navigazione"""
    with st.sidebar:
        st.title("Trading APP")
        
        if 'user_id' in st.session_state:
            st.success(f"Loggato: {st.session_state.get('user_email', 'Utente')}")
            
            # Solo pulsante logout
            if st.button("Logout", use_container_width=True):
                # Clear session
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
            
            return "Main"
        else:
            st.info("Non loggato")
            return "Login"

def main():
    """Funzione principale"""
    
    # Mostra sidebar
    show_sidebar()
    
    # Router delle pagine
    if 'user_id' not in st.session_state:
        # Utente non loggato - mostra solo auth
        if not show_auth_page():
            st.stop()
    else:
        # Utente loggato - mostra tutte le funzionalità in una pagina
        st.header("Controllo APP")
        show_control_page()
        
        st.divider()
        st.header("Impostazioni")
        show_settings_page()

if __name__ == "__main__":
    main()