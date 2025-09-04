"""
Pagine di autenticazione (Login e Registrazione)
"""
import streamlit as st
from database.models import user_manager
import re

def validate_email(email: str) -> bool:
    """Valida formato email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> bool:
    """Valida password (minimo 6 caratteri)"""
    return len(password) >= 6

def show_login_page():
    """Mostra pagina di login"""
    st.title("Login")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="inserisci la tua email")
        password = st.text_input("Password", type="password", placeholder="inserisci la password")
        
        submit_button = st.form_submit_button("Accedi", use_container_width=True)
        
        if submit_button:
            if not email or not password:
                st.error("Tutti i campi sono obbligatori")
                return None
            
            if not validate_email(email):
                st.error("Formato email non valido")
                return None
            
            # Tentativo di login
            user_id = user_manager.authenticate_user(email, password)
            if user_id:
                st.success("Login effettuato con successo!")
                st.session_state.user_id = user_id
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Email o password errati")
    
    return None

def show_register_page():
    """Mostra pagina di registrazione"""
    st.title("Registrazione")
    
    with st.form("register_form"):
        email = st.text_input("Email", placeholder="inserisci la tua email")
        password = st.text_input("Password", type="password", placeholder="minimo 6 caratteri")
        confirm_password = st.text_input("Conferma Password", type="password", placeholder="ripeti la password")
        
        terms_accepted = st.checkbox("Accetto i termini e le condizioni")
        
        submit_button = st.form_submit_button("Registrati", use_container_width=True)
        
        if submit_button:
            # Validazioni
            if not email or not password or not confirm_password:
                st.error("Tutti i campi sono obbligatori")
                return
            
            if not validate_email(email):
                st.error("Formato email non valido")
                return
            
            if not validate_password(password):
                st.error("La password deve avere almeno 6 caratteri")
                return
            
            if password != confirm_password:
                st.error("Le password non coincidono")
                return
            
            if not terms_accepted:
                st.error("Devi accettare i termini e le condizioni")
                return
            
            # Tentativo di registrazione
            if user_manager.create_user(email, password):
                st.success("Registrazione completata! Ora puoi effettuare il login.")
                st.balloons()
            else:
                st.error("Email già registrata o errore durante la registrazione")

def show_auth_page():
    """Pagina principale di autenticazione"""
    
    # Check se utente già loggato
    if 'user_id' in st.session_state:
        return True
    
    # Tabs per Login/Registrazione
    tab1, tab2 = st.tabs(["Login", "Registrazione"])
    
    with tab1:
        show_login_page()
    
    with tab2:
        show_register_page()
    
    return False