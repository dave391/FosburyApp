"""File di test per recuperare funding rate reali da Bitfinex
Utilizza le API di Bitfinex per recuperare il ledger e filtrare i funding payments
"""

import streamlit as st
import pandas as pd
import ccxt
import time
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

# Configurazione pagina
st.set_page_config(
    page_title="Bitfinex Funding Test",
    page_icon="💰",
    layout="wide"
)

def get_bitfinex_ledger(api_key: str, api_secret: str, since=None, limit=100):
    """
    Recupera i dati del ledger da Bitfinex utilizzando ccxt
    
    Args:
        api_key: API Key Bitfinex
        api_secret: API Secret Bitfinex
        since: Timestamp di inizio (millisecondi)
        limit: Numero massimo di record da recuperare
    
    Returns:
        Tuple (ledger_data, error_message)
    """
    try:
        # Configurazione exchange Bitfinex
        exchange = ccxt.bitfinex({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': False,
            'enableRateLimit': True,
            'timeout': 30000,
            'nonce': lambda: int(time.time() * 1000)
        })
        
        # Carica i mercati
        exchange.load_markets()
        
        # Parametri per la chiamata
        params = {}
        if since:
            params['since'] = since
        if limit:
            params['limit'] = limit
            
        # Chiamata fetchLedger
        ledger = exchange.fetchLedger(code=None, since=since, limit=limit, params=params)
        
        return ledger, None
        
    except Exception as e:
        return None, str(e)

def filter_funding_events(ledger_data):
    """
    Filtra gli eventi di funding dal ledger
    
    Args:
        ledger_data: Lista dei dati del ledger
    
    Returns:
        Lista degli eventi di funding filtrati
    """
    funding_events = []
    
    for entry in ledger_data:
        # Cerca eventi che potrebbero essere funding
        info = entry.get('info', {})
        description = info.get('description', '').lower()
        entry_type = entry.get('type', '').lower()
        category = info.get('category')
        
        # Filtri per identificare funding events
        if 'funding' in description:
            funding_events.append(entry)
        elif 'funding' in entry_type:
            funding_events.append(entry)
        elif category == 29:  # derivatives funding event
            funding_events.append(entry)
        elif 'swap' in description and 'fee' in description:
            funding_events.append(entry)
            
    return funding_events

def filter_trading_fees(ledger_data):
    """
    Filtra le fee di trading dal ledger
    
    Args:
        ledger_data: Lista dei dati del ledger
    
    Returns:
        Lista delle fee di trading filtrate
    """
    trading_fees = []
    
    for entry in ledger_data:
        info = entry.get('info', {})
        category = info.get('category')
        description = info.get('description', '').lower()
        entry_type = entry.get('type', '').lower()
        
        # Filtri per trading fee
        if category == 201:  # Category 201 = trading fee
            trading_fees.append(entry)
        elif 'trading fee' in description:
            trading_fees.append(entry)
        elif entry_type == 'fee':  # Tipo 'fee' nel ledger
            trading_fees.append(entry)
            
    return trading_fees

def format_funding_data(funding_events: List[Dict]) -> pd.DataFrame:
    """
    Formatta i dati di funding per visualizzazione
    
    Args:
        funding_events: Lista degli eventi di funding
    
    Returns:
        DataFrame pandas con i dati formattati
    """
    if not funding_events:
        return pd.DataFrame()
    
    formatted_data = []
    for event in funding_events:
        formatted_data.append({
            "Data": datetime.fromtimestamp(event.get('timestamp', 0) / 1000).strftime("%Y-%m-%d %H:%M:%S") if event.get('timestamp') else "N/A",
            "Currency": event.get('currency', 'N/A'),
            "Amount": event.get('amount', 0),
            "Balance After": event.get('after', 0),
            "Type": event.get('type', 'N/A'),
            "Description": event.get('info', {}).get('description', 'N/A'),
            "Category": event.get('info', {}).get('category', 'N/A'),
            "Transaction ID": event.get('id', 'N/A')
        })
    
    return pd.DataFrame(formatted_data)

def format_trading_fees_data(trading_fees: List[Dict]) -> pd.DataFrame:
    """
    Formatta i dati delle fee di trading per visualizzazione
    
    Args:
        trading_fees: Lista delle fee di trading
    
    Returns:
        DataFrame pandas con i dati formattati
    """
    if not trading_fees:
        return pd.DataFrame()
    
    formatted_data = []
    for fee in trading_fees:
        formatted_data.append({
            "Data": datetime.fromtimestamp(fee.get('timestamp', 0) / 1000).strftime("%Y-%m-%d %H:%M:%S") if fee.get('timestamp') else "N/A",
            "Currency": fee.get('currency', 'N/A'),
            "Fee Amount": abs(fee.get('amount', 0)),  # Le fee sono sempre negative, mostriamo valore assoluto
            "Balance After": fee.get('after', 0),
            "Type": fee.get('type', 'N/A'),
            "Description": fee.get('info', {}).get('description', 'N/A'),
            "Category": fee.get('info', {}).get('category', 'N/A'),
            "Transaction ID": fee.get('id', 'N/A')
        })
    
    return pd.DataFrame(formatted_data)

def main():
    """Funzione principale dell'app"""
    st.title("🔍 Bitfinex Funding Rate Test")
    st.markdown("Test per recuperare funding rate reali ricevuti e pagati su Bitfinex")
    
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
    
    api_key = api_keys.get("bitfinex_api_key", "")
    api_secret = api_keys.get("bitfinex_api_secret", "")
    
    # Sidebar per informazioni
    st.sidebar.header("Configurazione API")
    st.sidebar.success(f"✅ Utente: {target_email}")
    
    if api_key and api_secret:
        st.sidebar.success("✅ Credenziali Bitfinex caricate dal database")
        st.sidebar.info(f"API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''}")
    else:
        st.sidebar.error("❌ Credenziali Bitfinex non trovate per questo utente")
        st.error("Le credenziali API Bitfinex non sono configurate per l'utente davide@fosbury.com")
        return
    
    # Parametri di ricerca
    st.sidebar.subheader("Parametri Ricerca")
    
    days_back = st.sidebar.selectbox(
        "Giorni da recuperare",
        [1, 7, 30, 90],
        index=1,
        help="Numero di giorni indietro da cui recuperare i dati"
    )
    
    limit = st.sidebar.number_input(
        "Numero massimo record",
        min_value=10,
        max_value=1000,
        value=100,
        help="Numero massimo di record da recuperare"
    )
    
    # Calcola timestamp di inizio
    since_date = datetime.now() - timedelta(days=days_back)
    since_timestamp = int(since_date.timestamp() * 1000)
    
    # Pulsante per recuperare dati
    if st.sidebar.button("🔄 Recupera Funding Data", type="primary"):
        with st.spinner("Recupero dati da Bitfinex..."):
            # Recupera ledger
            ledger_data, error = get_bitfinex_ledger(
                api_key=api_key,
                api_secret=api_secret,
                since=since_timestamp,
                limit=limit
            )
            
        if error:
            st.error(f"❌ Errore nel recupero dei dati: {error}")
            return
            
        if not ledger_data:
            st.warning("⚠️ Nessun dato trovato nel periodo selezionato")
            return
            
        st.success(f"✅ Recuperati {len(ledger_data)} record dal ledger")
        
        # Filtra eventi di funding
        funding_events = filter_funding_events(ledger_data)
        
        # Filtra fee di trading
        trading_fees = filter_trading_fees(ledger_data)
        
        if funding_events:
            st.success(f"💰 Trovati {len(funding_events)} eventi di funding")
            
            # Formatta dati per visualizzazione
            df = format_funding_data(funding_events)
            
            # Statistiche riassuntive
            st.subheader("📊 Statistiche Funding")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_funding = df["Amount"].sum()
                st.metric("Funding Totale", f"{total_funding:.6f}")
            
            with col2:
                positive_funding = df[df["Amount"] > 0]["Amount"].sum()
                st.metric("Funding Ricevuto", f"{positive_funding:.6f}")
            
            with col3:
                negative_funding = df[df["Amount"] < 0]["Amount"].sum()
                st.metric("Funding Pagato", f"{negative_funding:.6f}")
            
            with col4:
                avg_funding = df["Amount"].mean()
                st.metric("Media per Funding", f"{avg_funding:.6f}")
            
            # Tabella dettagliata
            st.subheader("📋 Dettaglio Eventi Funding")
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
                data=df_sorted.set_index('Data_dt')[['Amount']],
                use_container_width=True
            )
            
            # Distribuzione per currency
            st.subheader("💱 Distribuzione per Currency")
            currency_summary = df.groupby('Currency')['Amount'].agg(['count', 'sum', 'mean']).round(6)
            st.dataframe(currency_summary, use_container_width=True)
            
        else:
            st.warning("⚠️ Nessun evento di funding trovato nel periodo")
        
        # Sezione Fee di Trading
        st.markdown("---")
        
        if trading_fees:
            st.success(f"💳 Trovate {len(trading_fees)} fee di trading")
            
            # Formatta dati delle fee per visualizzazione
            df_fees = format_trading_fees_data(trading_fees)
            
            # Statistiche riassuntive delle fee
            st.subheader("💳 Statistiche Fee di Trading")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_fees = df_fees["Fee Amount"].sum()
                st.metric("Fee Totali Pagate", f"{total_fees:.6f}")
            
            with col2:
                avg_fee = df_fees["Fee Amount"].mean()
                st.metric("Fee Media", f"{avg_fee:.6f}")
            
            with col3:
                max_fee = df_fees["Fee Amount"].max()
                st.metric("Fee Massima", f"{max_fee:.6f}")
            
            with col4:
                num_trades = len(df_fees)
                st.metric("Numero Trade", num_trades)
            
            # Tabella dettagliata delle fee
            st.subheader("📋 Dettaglio Fee di Trading")
            st.dataframe(
                df_fees,
                use_container_width=True,
                hide_index=True
            )
            
            # Grafico temporale delle fee
            st.subheader("📈 Andamento Fee nel Tempo")
            
            # Converti data per grafico
            df_fees['Data_dt'] = pd.to_datetime(df_fees['Data'])
            df_fees_sorted = df_fees.sort_values('Data_dt')
            
            # Crea grafico
            st.line_chart(
                data=df_fees_sorted.set_index('Data_dt')[['Fee Amount']],
                use_container_width=True
            )
            
            # Distribuzione fee per currency
            st.subheader("💱 Distribuzione Fee per Currency")
            fee_currency_summary = df_fees.groupby('Currency')['Fee Amount'].agg(['count', 'sum', 'mean']).round(6)
            fee_currency_summary.columns = ['Numero Transazioni', 'Fee Totali', 'Fee Media']
            st.dataframe(fee_currency_summary, use_container_width=True)
            
        else:
            st.warning("⚠️ Nessuna fee di trading trovata nel periodo")
        
        # Mostra tutti i dati per analisi
        st.subheader("📋 Tutti i Dati del Ledger (per analisi)")
        
        # Converti in DataFrame per visualizzazione
        all_data = []
        for entry in ledger_data:
            row = {
                'ID': entry.get('id', ''),
                'Timestamp': datetime.fromtimestamp(entry.get('timestamp', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S') if entry.get('timestamp') else '',
                'Currency': entry.get('currency', ''),
                'Amount': entry.get('amount', 0),
                'Balance': entry.get('after', 0),
                'Type': entry.get('type', ''),
                'Description': entry.get('info', {}).get('description', ''),
                'Category': entry.get('info', {}).get('category', '')
            }
            all_data.append(row)
            
        if all_data:
            df_all = pd.DataFrame(all_data)
            st.dataframe(df_all, use_container_width=True)
            
            # Statistiche generali
            st.subheader("📊 Statistiche Generali")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Totale Record", len(ledger_data))
                
            with col2:
                st.metric("Eventi Funding", len(funding_events))
                
            with col3:
                st.metric("Fee di Trading", len(trading_fees))
                
            with col4:
                unique_currencies = len(set([entry.get('currency', '') for entry in ledger_data]))
                st.metric("Valute Uniche", unique_currencies)
                
            # Mostra categorie uniche per debug
            with st.expander("🔍 Analisi Categorie e Descrizioni"):
                categories = set()
                descriptions = set()
                types = set()
                
                for entry in ledger_data:
                    cat = entry.get('info', {}).get('category')
                    if cat:
                        categories.add(cat)
                    
                    desc = entry.get('info', {}).get('description', '')
                    if desc:
                        descriptions.add(desc)
                    
                    entry_type = entry.get('type', '')
                    if entry_type:
                        types.add(entry_type)
                        
                st.write("**Categorie numeriche trovate:**", sorted(list(categories)))
                st.write("**Tipi di entry trovati:**", sorted(list(types)))
                st.write("**Descrizioni uniche:**")
                for desc in sorted(list(descriptions)):
                    st.write(f"- {desc}")
            
            # Mostra dati raw per debug
            with st.expander("🔍 Dati Raw (primi 3 record)"):
                st.json(ledger_data[:3])
    
    # Informazioni sull'API
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ Info API")
    st.sidebar.markdown("""
    **Endpoint utilizzato:**
    `fetchLedger()` via ccxt
    
    **Filtri Funding:**
    - Cerca 'funding' in description
    - Cerca 'funding' in type
    - Category = 29 (derivatives funding)
    - 'swap' + 'fee' in description
    
    **Filtri Trading Fee:**
    - Category = 201 (trading fee)
    - Cerca 'trading fee' in description
    - Type = 'fee' (fee generiche)
    
    **Note:**
    - Amount positivo: Funding ricevuto
    - Amount negativo: Funding pagato
    - Fee Amount: Sempre positivo (valore assoluto)
    """)
    
    # Note tecniche
    st.markdown("---")
    st.markdown("""
    ### 📝 Note Tecniche
    
    **Eventi di Funding:**
    - **Amount positivo**: Funding ricevuto (sei stato pagato)
    - **Amount negativo**: Funding pagato (hai pagato)
    
    **Fee di Trading:**
    - **Fee Amount**: Sempre mostrato come valore positivo (fee pagate)
    - **Category 201**: Identifica le trading fee secondo l'API Bitfinex
    - Le fee sono sempre un costo (amount negativo nel ledger originale)
    
    **Campi Comuni:**
    - **Balance After**: Saldo del wallet dopo la transazione
    - **Category**: Codice numerico del tipo di transazione
    - **Description**: Descrizione testuale della transazione
    
    ### 🔗 Riferimenti
    - [Bitfinex API Documentation](https://docs.bitfinex.com/reference/rest-auth-ledgers)
    - [CCXT Bitfinex Documentation](https://docs.ccxt.com/en/latest/manual.html#bitfinex)
    - [Bitfinex Ledger Categories](https://docs.bitfinex.com/reference/rest-auth-ledgers#category-filters)
    """)

if __name__ == "__main__":
    main()