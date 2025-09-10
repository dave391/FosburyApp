"""File di test per recuperare funding rate reali da BitMEX
Utilizza le API di BitMEX per recuperare la wallet history e filtrare i funding payments
"""

import streamlit as st
import pandas as pd
import ccxt
import requests
import hmac
import hashlib
import time
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

# Configurazione pagina
st.set_page_config(
    page_title="BitMEX Funding Test",
    page_icon="💰",
    layout="wide"
)

def create_bitmex_signature(api_secret: str, verb: str, url: str, nonce: int, data: str = '') -> str:
    """Crea la signature per autenticazione BitMEX"""
    message = verb + url + str(nonce) + data
    signature = hmac.new(
        api_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def get_bitmex_wallet_history(api_key: str, api_secret: str, currency: str = "USDt", count: int = 100) -> Optional[List[Dict]]:
    """Recupera wallet history da BitMEX API
    
    Args:
        api_key: API Key BitMEX
        api_secret: API Secret BitMEX
        currency: Valuta da filtrare (default: USDt)
        count: Numero di risultati da recuperare (max: 10000)
    
    Returns:
        Lista di transazioni o None se errore
    """
    try:
        # Endpoint BitMEX
        base_url = "https://www.bitmex.com"
        endpoint = "/api/v1/user/walletHistory"
        
        # Parametri query
        params = {
            "currency": currency,
            "count": count,
            "reverse": "true"  # Inizia dalle transazioni più recenti
        }
        
        # Costruisci URL con parametri
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{endpoint}?{query_string}"
        
        # Nonce (timestamp in millisecondi)
        nonce = int(time.time() * 1000)
        
        # Crea signature
        signature = create_bitmex_signature(api_secret, "GET", full_url, nonce)
        
        # Headers per autenticazione
        headers = {
            "api-expires": str(nonce),
            "api-key": api_key,
            "api-signature": signature,
            "Content-Type": "application/json"
        }
        
        # Esegui richiesta
        response = requests.get(
            base_url + full_url,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Errore API BitMEX: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Errore nella richiesta: {str(e)}")
        return None

def filter_funding_transactions(transactions: List[Dict]) -> List[Dict]:
    """Filtra solo le transazioni di tipo Funding
    
    Args:
        transactions: Lista completa delle transazioni
    
    Returns:
        Lista delle transazioni di funding filtrate
    """
    if not transactions:
        return []
    
    funding_transactions = []
    for tx in transactions:
        if tx.get("transactType") == "Funding" and tx.get("transactStatus") == "Completed":
            funding_transactions.append(tx)
    
    return funding_transactions

def filter_fee_transactions(transactions: List[Dict]) -> List[Dict]:
    """Filtra solo le transazioni di tipo RealisedPNL per recuperare le fee pagate
    
    Args:
        transactions: Lista completa delle transazioni
    
    Returns:
        Lista delle transazioni di fee pagate filtrate
    """
    if not transactions:
        return []
    
    fee_transactions = []
    for tx in transactions:
        if (tx.get("transactType") == "RealisedPNL" and 
            tx.get("transactStatus") == "Completed" and 
            tx.get("fee", 0) > 0):  # Fee positive indica fee pagata
            fee_transactions.append(tx)
    
    return fee_transactions

def convert_amount_to_usdt(amount_satoshi: int) -> float:
    """Converte l'amount da satoshi a USDT
    
    Args:
        amount_satoshi: Amount in satoshi (es: 24476)
    
    Returns:
        Amount in USDT (es: 0.024476)
    """
    return amount_satoshi / 1_000_000

def format_funding_data(funding_transactions: List[Dict]) -> pd.DataFrame:
    """Formatta i dati di funding per visualizzazione
    
    Args:
        funding_transactions: Lista delle transazioni di funding
    
    Returns:
        DataFrame pandas con i dati formattati
    """
    if not funding_transactions:
        return pd.DataFrame()
    
    formatted_data = []
    for tx in funding_transactions:
        formatted_data.append({
            "Data": datetime.fromisoformat(tx["transactTime"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S"),
            "Simbolo": tx.get("address", "N/A"),
            "Amount (USDT)": convert_amount_to_usdt(tx["amount"]),
            "Fee (USDT)": convert_amount_to_usdt(abs(tx.get("fee", 0))),
            "Netto (USDT)": convert_amount_to_usdt(tx["amount"]) - convert_amount_to_usdt(abs(tx.get("fee", 0))),
            "Wallet Balance (USDT)": convert_amount_to_usdt(tx["walletBalance"]),
            "Transaction ID": tx.get("transactID", "N/A")
        })
    
    return pd.DataFrame(formatted_data)

def format_fee_data(fee_transactions: List[Dict]) -> pd.DataFrame:
    """Formatta i dati delle fee pagate per visualizzazione
    
    Args:
        fee_transactions: Lista delle transazioni di fee pagate (RealisedPNL)
    
    Returns:
        DataFrame pandas con i dati delle fee formattati
    """
    if not fee_transactions:
        return pd.DataFrame()
    
    formatted_data = []
    for tx in fee_transactions:
        formatted_data.append({
            "Data": datetime.fromisoformat(tx["transactTime"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S"),
            "Simbolo": tx.get("address", "N/A"),
            "PNL (USDT)": convert_amount_to_usdt(tx["amount"]),
            "Fee Pagata (USDT)": convert_amount_to_usdt(tx.get("fee", 0)),
            "Wallet Balance (USDT)": convert_amount_to_usdt(tx["walletBalance"]),
            "Order ID": tx.get("orderID", "N/A"),
            "Transaction ID": tx.get("transactID", "N/A")
        })
    
    return pd.DataFrame(formatted_data)

def main():
    """Funzione principale dell'app"""
    st.title("🔍 BitMEX Funding Rate Test")
    st.markdown("Test per recuperare funding rate reali ricevuti e pagati su BitMEX")
    
    # Recupera automaticamente le credenziali di davide@fosbury.com
    from database.models import user_manager
    
    target_email = "davide@fosbury.com"
    user_data = user_manager.get_user_by_email(target_email)
    
    if not user_data:
        st.error(f"❌ Utente {target_email} non trovato nel database")
        st.info("Assicurati che l'utente sia registrato nel sistema")
        return
    
    user_id = user_data["user_id"]
    api_keys = user_manager.get_user_api_keys(user_id)
    
    api_key = api_keys.get("bitmex_api_key", "")
    api_secret = api_keys.get("bitmex_api_secret", "")
    
    # Sidebar per informazioni
    st.sidebar.header("Configurazione API")
    st.sidebar.success(f"✅ Utente: {target_email}")
    
    if api_key and api_secret:
        st.sidebar.success("✅ Credenziali BitMEX caricate dal database")
        st.sidebar.info(f"API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''}")
    else:
        st.sidebar.error("❌ Credenziali BitMEX non trovate per questo utente")
        st.error("Le credenziali API BitMEX non sono configurate per l'utente davide@fosbury.com")
        return
    
    # Parametri di ricerca
    st.sidebar.subheader("Parametri Ricerca")
    
    currency = st.sidebar.selectbox(
        "Valuta",
        ["USDt", "XBt"],
        index=0,
        help="Valuta per filtrare le transazioni"
    )
    
    count = st.sidebar.number_input(
        "Numero transazioni",
        min_value=1,
        max_value=1000,
        value=100,
        help="Numero di transazioni da recuperare (max 1000 per test)"
    )
    
    # Pulsante per recuperare dati
    if st.sidebar.button("🔄 Recupera Funding Data", type="primary"):
        with st.spinner("Recupero dati da BitMEX..."):
            # Recupera wallet history
            transactions = get_bitmex_wallet_history(api_key, api_secret, currency, count)
            
            if transactions:
                st.success(f"✅ Recuperate {len(transactions)} transazioni totali")
                
                # Filtra solo funding
                funding_transactions = filter_funding_transactions(transactions)
                
                # Filtra fee pagate (RealisedPNL)
                fee_transactions = filter_fee_transactions(transactions)
                
                # Crea tabs per separare funding e fee
                tab1, tab2 = st.tabs(["💰 Funding Ricevuti/Pagati", "💸 Fee Pagate"])
                
                with tab1:
                    if funding_transactions:
                        st.success(f"💰 Trovate {len(funding_transactions)} transazioni di funding")
                        
                        # Formatta dati per visualizzazione
                        df = format_funding_data(funding_transactions)
                        
                        # Statistiche riassuntive
                        st.subheader("📊 Statistiche Funding")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            total_funding = df["Amount (USDT)"].sum()
                            st.metric("Funding Totale", f"{total_funding:.6f} USDT")
                        
                        with col2:
                            total_fees = df["Fee (USDT)"].sum()
                            st.metric("Fee Totali", f"{total_fees:.6f} USDT")
                        
                        with col3:
                            net_funding = df["Netto (USDT)"].sum()
                            st.metric("Netto Totale", f"{net_funding:.6f} USDT")
                        
                        with col4:
                            avg_funding = df["Amount (USDT)"].mean()
                            st.metric("Media per Funding", f"{avg_funding:.6f} USDT")
                        
                        # Tabella dettagliata
                        st.subheader("📋 Dettaglio Transazioni Funding")
                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Grafico temporale
                        st.subheader("📈 Andamento Funding nel Tempo")
                        
                        # Converti data per grafico
                        df['Data_dt'] = pd.to_datetime(df['Data'])
                        df_sorted = df.sort_values('Data_dt')
                        
                        # Crea grafico
                        st.line_chart(
                            data=df_sorted.set_index('Data_dt')[['Amount (USDT)', 'Netto (USDT)']],
                            use_container_width=True
                        )
                        
                        # Mostra dati raw per debug
                        with st.expander("🔍 Dati Raw Funding (per debug)"):
                            st.json(funding_transactions[:3])  # Mostra solo i primi 3 per non sovraccaricare
                        
                    else:
                        st.warning("⚠️ Nessuna transazione di funding trovata nel periodo")
                
                with tab2:
                    if fee_transactions:
                        st.success(f"💸 Trovate {len(fee_transactions)} transazioni con fee pagate")
                        
                        # Formatta dati delle fee per visualizzazione
                        df_fees = format_fee_data(fee_transactions)
                        
                        # Statistiche riassuntive fee
                        st.subheader("📊 Statistiche Fee Pagate")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            total_fees_paid = df_fees["Fee Pagata (USDT)"].sum()
                            st.metric("Fee Totali Pagate", f"{total_fees_paid:.6f} USDT")
                        
                        with col2:
                            avg_fee = df_fees["Fee Pagata (USDT)"].mean()
                            st.metric("Fee Media", f"{avg_fee:.6f} USDT")
                        
                        with col3:
                            max_fee = df_fees["Fee Pagata (USDT)"].max()
                            st.metric("Fee Massima", f"{max_fee:.6f} USDT")
                        
                        with col4:
                            total_pnl = df_fees["PNL (USDT)"].sum()
                            st.metric("PNL Totale", f"{total_pnl:.6f} USDT")
                        
                        # Tabella dettagliata fee
                        st.subheader("📋 Dettaglio Fee Pagate")
                        st.dataframe(
                            df_fees,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Grafico temporale fee
                        st.subheader("📈 Andamento Fee Pagate nel Tempo")
                        
                        # Converti data per grafico
                        df_fees['Data_dt'] = pd.to_datetime(df_fees['Data'])
                        df_fees_sorted = df_fees.sort_values('Data_dt')
                        
                        # Crea grafico
                        st.line_chart(
                            data=df_fees_sorted.set_index('Data_dt')[['Fee Pagata (USDT)', 'PNL (USDT)']],
                            use_container_width=True
                        )
                        
                        # Mostra dati raw per debug
                        with st.expander("🔍 Dati Raw Fee (per debug)"):
                            st.json(fee_transactions[:3])  # Mostra solo i primi 3 per non sovraccaricare
                        
                    else:
                        st.warning("⚠️ Nessuna transazione con fee pagate trovata nel periodo")
                
                # Sezione debug generale
                if not funding_transactions and not fee_transactions:
                    # Mostra comunque tutte le transazioni per debug
                    with st.expander("🔍 Tutte le transazioni (per debug)"):
                        st.json(transactions[:5])  # Mostra solo le prime 5
            else:
                st.error("❌ Errore nel recupero dei dati")
    
    # Informazioni sull'API
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ Info API")
    st.sidebar.markdown("""
    **Endpoint utilizzato:**
    `GET /api/v1/user/walletHistory`
    
    **Filtri applicati:**
    
    *Tab Funding:*
    - `currency`: USDt/XBt
    - `transactType`: Funding
    - `transactStatus`: Completed
    
    *Tab Fee Pagate:*
    - `currency`: USDt/XBt
    - `transactType`: RealisedPNL
    - `transactStatus`: Completed
    - `fee` > 0 (fee positive)
    
    **Conversione amount:**
    - BitMEX restituisce amount in satoshi
    - 1 USDT = 1,000,000 satoshi
    - Es: 24476 → 0.024476 USDT
    - Es: 121962 → 0.121962 USDT
    """)
    
    # Note tecniche
    st.markdown("---")
    st.markdown("""
    ### 📝 Note Tecniche
    
    **Tab Funding:**
    - **Amount positivo**: Funding ricevuto (sei stato pagato)
    - **Amount negativo**: Funding pagato (hai pagato)
    - **Fee**: Sempre negativa, rappresenta il costo della transazione
    - **Netto**: Amount - |Fee| (guadagno/perdita effettiva)
    
    **Tab Fee Pagate:**
    - **PNL**: Profit and Loss realizzato dalla posizione
    - **Fee Pagata**: Fee effettivamente pagata per la transazione (sempre positiva)
    - **Order ID**: ID dell'ordine che ha generato la fee
    - Le fee sono estratte da transazioni di tipo "RealisedPNL"
    
    ### 🔗 Riferimenti
    - [BitMEX API Documentation](https://www.bitmex.com/api/explorer/#!/User/User_getWalletHistory)
    - [BitMEX Funding Rate Info](https://www.bitmex.com/app/fundingHistory)
    """)

if __name__ == "__main__":
    main()