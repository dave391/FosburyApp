"""Dashboard per monitorare le performance dell'app di trading
Visualizza metriche chiave, grafici e configurazioni dell'app
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from utils.funding_data import get_all_funding_data, calculate_metrics, get_daily_pnl_data

def calculate_initial_capital_from_positions(bot_id):
    """Calcola il capitale iniziale effettivo come somma dei margini iniziali
    Formula: Σ (entry_price * size) / leverage
    """
    try:
        from database.models import position_manager
        from bson import ObjectId
        
        # Se bot_id è già ObjectId, usalo direttamente, altrimenti convertilo
        if isinstance(bot_id, ObjectId):
            search_bot_id = bot_id
        else:
            search_bot_id = ObjectId(bot_id)
        
        # Recupera posizioni direttamente dal database usando ObjectId
        positions = list(position_manager.positions.find({"bot_id": search_bot_id}))
        
        if not positions:
            return 0.0
        
        total_initial_capital = 0.0
        
        for position in positions:
            entry_price = position.get('entry_price', 0)
            size = position.get('size', 0)
            leverage = position.get('leverage', 1)
            exchange = position.get('exchange', '')
            
            if entry_price > 0 and size > 0 and leverage > 0:
                # Per BitMEX, il size è in contratti (dividi per 10000)
                if exchange.lower() == 'bitmex':
                    adjusted_size = size / 10000
                else:
                    adjusted_size = size
                
                # Calcola margine iniziale per questa posizione
                initial_margin = (entry_price * adjusted_size) / leverage
                total_initial_capital += initial_margin
        
        # Arrotonda alla seconda cifra decimale
        return round(total_initial_capital, 2)
        
    except Exception as e:
        return 0.0

def load_dashboard_data():
    """Carica i dati per la dashboard"""
    # Verifica che l'utente sia loggato
    if 'user_id' not in st.session_state:
        return None, None, "Devi effettuare il login per visualizzare le performance"
    
    user_id = st.session_state.user_id
    
    # Recupera il bot attivo dell'utente
    from database.models import bot_manager, user_manager
    current_bot = bot_manager.get_user_bot(user_id)
    
    if not current_bot:
        return None, None, "Nessun bot configurato per questo utente"
    
    # Verifica lo status del bot
    bot_status = current_bot.get("status")
    if bot_status == "stopped":
        return None, None, "Nessun bot attivo al momento"
    
    if bot_status == "ready":
        return None, None, "Il bot non è ancora stato avviato. Torna più tardi."
    
    # Recupera email utente per le API keys
    user_data = user_manager.get_user_by_id(user_id)
    if not user_data:
        return None, None, "Dati utente non trovati"
    
    target_email = user_data.get("email")
    if not target_email:
        return None, None, "Email utente non trovata"
    
    # Recupera dati di funding e fee di trading
    # Passa bot_started_at per ottimizzare il recupero dati
    bot_started_at = current_bot.get('started_at')
    funding_events, trading_fees, error = get_all_funding_data(target_email, bot_started_at)
    
    return funding_events, trading_fees, current_bot, error

def display_kpi_cards(metrics: dict):
    """Visualizza le card con le metriche chiave"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="PnL Totale",
            value=f"{metrics['net_pnl']:.2f} USDT",
            delta=f"{metrics['total_pnl']:.2f} (lordo)"
        )
    
    with col2:
        st.metric(
            label="APR",
            value=f"{metrics['apr']:.2f}%",
            delta="Annualizzato"
        )
    
    with col3:
        st.metric(
            label="Fee Pagate",
            value=f"{metrics['total_fees']:.2f} USDT",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Giorni Running",
            value=f"{metrics['days_running']}",
            delta="giorni"
        )

def display_pnl_chart(daily_pnl_data: pd.DataFrame):
    """Visualizza il grafico dell'andamento PnL"""
    if daily_pnl_data.empty:
        st.warning("Nessun dato disponibile per il grafico")
        return
    
    # Crea grafico con Plotly
    fig = go.Figure()
    
    # Prepara i dati per iniziare da 0
    if not daily_pnl_data.empty:
        # Riordina i dati in ordine cronologico crescente per il grafico
        chart_data = daily_pnl_data.sort_values('date', ascending=True)
        
        # Aggiungi un punto iniziale a 0 con label "Start"
        # Converte le date in stringhe per coerenza con "Start"
        # Prima converte la colonna date in datetime se necessario
        chart_data['date'] = pd.to_datetime(chart_data['date'])
        date_strings = chart_data['date'].dt.strftime('%d/%m/%Y').tolist()
        x_values = ["Start"] + date_strings
        y_values = [0] + chart_data['cumulative_pnl'].tolist()
    else:
        x_values = []
        y_values = []
    
    # Linea PnL cumulativo
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines+markers',
        name='PnL Cumulativo',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=4)
    ))
    
    # Configurazione layout
    fig.update_layout(
        title="Andamento PnL Giornaliero Cumulativo",
        xaxis_title="Data",
        yaxis_title="PnL (USDT)",
        hovermode='x unified',
        showlegend=True,
        height=400
    )
    
    # Aggiungi linea zero per riferimento
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    st.plotly_chart(fig, use_container_width=True)



def main():
    """Funzione principale della dashboard"""
    st.title("Performance")
    
    # Valori di default per la configurazione
    leverage = 1.0
    
    # Pulsante per aggiornare i dati
    col1, col2 = st.columns([1, 4])
    with col1:
        refresh_button = st.button("Aggiorna Dati", type="secondary")
    
    # Carica dati automaticamente all'apertura della pagina o quando si clicca refresh
    if refresh_button or 'dashboard_data_loaded' not in st.session_state:
        with st.spinner("Caricamento dati..."):
            funding_events, trading_fees, current_bot, error = load_dashboard_data()
            
            if error:
                st.error(f"Errore nel caricamento dei dati: {error}")
                return
            
            if not funding_events:
                st.warning("Nessun dato di funding trovato")
                return
            
            # Recupera la data di avvio dal bot
            start_date = current_bot.get('started_at')
            if not start_date:
                st.error("Data di avvio del bot non trovata")
                return
            
            # Calcola il capitale iniziale effettivo dalle posizioni
            bot_id = current_bot.get('_id')
            initial_capital = calculate_initial_capital_from_positions(bot_id)
            
            if initial_capital <= 0:
                st.error("Impossibile calcolare il capitale iniziale dalle posizioni")
                return
            
            # Calcola metriche (incluse le fee di trading)
            metrics = calculate_metrics(funding_events, start_date, initial_capital, trading_fees)
            

            # Calcola dati per grafico
            daily_pnl_data = get_daily_pnl_data(funding_events, start_date, trading_fees)
            
            # Salva in session state
            st.session_state.dashboard_data_loaded = True
            st.session_state.funding_events = funding_events
            st.session_state.trading_fees = trading_fees
            st.session_state.current_bot = current_bot
            st.session_state.metrics = metrics
            st.session_state.daily_pnl_data = daily_pnl_data
            st.session_state.start_date = start_date
            
            pass
    
    # Visualizza dati se disponibili
    if 'dashboard_data_loaded' in st.session_state:
        # Calcola il capitale iniziale effettivo dalle posizioni
        bot_id = st.session_state.current_bot.get('_id')
        initial_capital = calculate_initial_capital_from_positions(bot_id)
        
        # Ricalcola metriche se la configurazione è cambiata
        if ('funding_events' in st.session_state and 
            st.session_state.get('last_initial_capital') != initial_capital):
            
            start_date = st.session_state.get('start_date')
            trading_fees = st.session_state.get('trading_fees', [])
            metrics = calculate_metrics(
                st.session_state.funding_events, 
                start_date, 
                initial_capital,
                trading_fees
            )
            daily_pnl_data = get_daily_pnl_data(
                st.session_state.funding_events, 
                start_date,
                trading_fees
            )
            
            st.session_state.metrics = metrics
            st.session_state.daily_pnl_data = daily_pnl_data
            st.session_state.last_initial_capital = initial_capital
        
        # Visualizza KPI cards
        display_kpi_cards(st.session_state.metrics)
        
        st.markdown("---")
        
        # Visualizza grafico PnL
        display_pnl_chart(st.session_state.daily_pnl_data)
        
        st.markdown("---")
        
        # Dettagli
        st.subheader("Dettagli")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Capitale Iniziale", f"{initial_capital:.2f} USDT")
            st.metric("PnL Lordo", f"{st.session_state.metrics['total_pnl']:.2f} USDT")
            st.metric("Capitale Effettivo", f"{initial_capital + st.session_state.metrics['net_pnl']:.2f} USDT")
        
        with col2:
            st.metric("PnL Netto", f"{st.session_state.metrics['net_pnl']:.2f} USDT")
            st.metric("Fee", f"{st.session_state.metrics['total_fees']:.2f} USDT")
            # Calcola ROI basato sul capitale iniziale effettivo
            roi_percentage = (st.session_state.metrics['net_pnl'] / initial_capital * 100) if initial_capital > 0 else 0
            st.metric("ROI Totale", f"{roi_percentage:.2f}%")
        
        # Tabella riepilogo PnL giornalieri
        st.subheader("Riepilogo PnL Giornalieri")
        
        # Tabella riepilogo PnL giornalieri ora include correttamente i dati di entrambi gli exchange
        
        if not st.session_state.daily_pnl_data.empty:
            # Prepara i dati per la tabella
            pnl_table = st.session_state.daily_pnl_data.copy()
            # Converte la colonna date in datetime se non lo è già
            pnl_table['date'] = pd.to_datetime(pnl_table['date'])
            pnl_table['Data'] = pnl_table['date'].dt.strftime('%d/%m/%Y')
            pnl_table['PnL Giornaliero'] = pnl_table['daily_pnl'].apply(lambda x: f"{x:.2f} USDT")
            pnl_table['PnL Cumulativo'] = pnl_table['cumulative_pnl'].apply(lambda x: f"{x:.2f} USDT")
            
            # Aggiungi colonna fee di trading se disponibile
            if 'trading_fees' in pnl_table.columns:
                pnl_table['Fee Trading'] = pnl_table['trading_fees'].apply(lambda x: f"{x:.2f} USDT" if x > 0 else "-")
                display_table = pnl_table[['Data', 'PnL Giornaliero', 'Fee Trading', 'PnL Cumulativo']]
            else:
                display_table = pnl_table[['Data', 'PnL Giornaliero', 'PnL Cumulativo']]
            
            # Mostra la tabella (già ordinata per data decrescente)
            st.dataframe(
                display_table.reset_index(drop=True),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Nessun dato PnL giornaliero disponibile")
        
        # Sezione Debug - Elenco Fee di Trading
        st.markdown("---")
        st.subheader("🔍 Debug - Fee di Trading Conteggiate")
        
        if 'trading_fees' in st.session_state and st.session_state.trading_fees:
            trading_fees = st.session_state.trading_fees
            start_date = st.session_state.get('start_date')
            
            # Mostra statistiche generali

            if start_date:
                st.info(f"**Bot avviato il**: {start_date.strftime('%d/%m/%Y %H:%M:%S')} UTC")
            
            # Filtra le fee dalla data di avvio (stesso filtro usato in calculate_metrics)
            filtered_fees = []
            for fee in trading_fees:
                if fee['date']:
                    fee_date = fee['date']
                    # Assicurati che entrambe le date siano naive (senza timezone) per il confronto
                    if fee_date.tzinfo is not None:
                        fee_date = fee_date.replace(tzinfo=None)
                    
                    # Converte start_date in naive se ha timezone
                    comparison_start_date = start_date
                    if start_date and start_date.tzinfo is not None:
                        comparison_start_date = start_date.replace(tzinfo=None)
                    
                    # Aggiungi buffer di 5 secondi prima della data di avvio per includere fee
                    # che potrebbero essere registrate leggermente prima a causa di discrepanze temporali
                    if comparison_start_date:
                        from datetime import timedelta
                        buffer_start_date = comparison_start_date - timedelta(seconds=5)
                        
                        # Fee valide: da 5 secondi prima dell'avvio in poi
                        if fee_date >= buffer_start_date:
                            filtered_fees.append(fee)
            
            if filtered_fees:
                # Crea DataFrame per visualizzazione
                debug_data = []
                total_fees_debug = 0
                
                for fee in filtered_fees:
                    # Mostra data e informazioni fuso orario per debug
                    date_str = fee['date'].strftime('%d/%m/%Y %H:%M') if fee['date'] else 'N/A'
                    timezone_info = fee.get('timezone_info', 'N/A')
                    
                    debug_data.append({
                        'Data': date_str,
                        'Fuso Orario': timezone_info,
                        'Exchange': fee['exchange'].upper(),
                        'Valuta': fee.get('currency', 'N/A'),
                        'Fee (USDT)': f"{fee['amount']:.6f}",
                        'Category': fee.get('category', 'N/A'),
                        'Type': fee.get('type', 'N/A'),
                        'Descrizione': fee.get('description', 'N/A')
                    })
                    total_fees_debug += fee['amount']
                
                debug_df = pd.DataFrame(debug_data)
                
                # Mostra statistiche riassuntive
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Totale Fee Trading", f"{total_fees_debug:.6f} USDT")
                with col2:
                    st.metric("Numero Transazioni", len(filtered_fees))
                with col3:
                    bitfinex_count = len([f for f in filtered_fees if f['exchange'] == 'bitfinex'])
                    bitmex_count = len([f for f in filtered_fees if f['exchange'] == 'bitmex'])
                    st.metric("Bitfinex/BitMEX", f"{bitfinex_count}/{bitmex_count}")
                
                # Mostra tabella dettagliata
                st.dataframe(
                    debug_df.sort_values('Data', ascending=False).reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Breakdown per exchange
                st.markdown("**Breakdown per Exchange:**")
                bitfinex_total = sum(f['amount'] for f in filtered_fees if f['exchange'] == 'bitfinex')
                bitmex_total = sum(f['amount'] for f in filtered_fees if f['exchange'] == 'bitmex')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Bitfinex:** {bitfinex_total:.6f} USDT ({bitfinex_count} transazioni)")
                with col2:
                    st.write(f"**BitMEX:** {bitmex_total:.6f} USDT ({bitmex_count} transazioni)")
                

                    
            else:
                if start_date:
                    st.warning(f"Nessuna fee di trading trovata dopo la data di avvio del bot ({start_date.strftime('%d/%m/%Y %H:%M:%S')} UTC)")
                else:
                    st.warning("Nessuna fee di trading trovata nel periodo selezionato")
        else:
            st.info("Nessuna fee di trading disponibile")
        
        # Sezione Debug - Tabella Funding Events per Exchange
        st.markdown("---")
        st.subheader("📊 Debug - Funding Events per Exchange")
        
        if 'funding_events' in st.session_state and st.session_state.funding_events:
            funding_events = st.session_state.funding_events
            start_date = st.session_state.get('start_date')
            
            # Filtra funding events dalla data di avvio
            filtered_funding = []
            for event in funding_events:
                if event['date']:
                    event_date = event['date']
                    if event_date.tzinfo is not None:
                        event_date = event_date.replace(tzinfo=None)
                    
                    comparison_start_date = start_date
                    if start_date and start_date.tzinfo is not None:
                        comparison_start_date = start_date.replace(tzinfo=None)
                    
                    if comparison_start_date and event_date >= comparison_start_date:
                        filtered_funding.append(event)
            
            if filtered_funding:
                # Crea DataFrame per raggruppamento giornaliero
                df_funding = pd.DataFrame(filtered_funding)
                
                # Normalizza le date rimuovendo timezone per evitare conflitti
                df_funding['date'] = pd.to_datetime(df_funding['date'], utc=True).dt.tz_localize(None)
                df_funding['date_only'] = df_funding['date'].dt.date
                
                # Raggruppa per giorno e exchange
                daily_funding = df_funding.groupby(['date_only', 'exchange']).agg({
                    'amount': 'sum',
                    'fee': 'sum'
                }).reset_index()
                
                # Pivot per avere colonne separate per exchange
                pivot_funding = daily_funding.pivot_table(
                    index='date_only', 
                    columns='exchange', 
                    values='amount', 
                    fill_value=0
                ).reset_index()
                
                # Aggiungi colonne mancanti se necessario
                if 'bitfinex' not in pivot_funding.columns:
                    pivot_funding['bitfinex'] = 0
                if 'bitmex' not in pivot_funding.columns:
                    pivot_funding['bitmex'] = 0
                
                # Merge con dati PnL giornalieri per avere il PnL totale
                daily_pnl_data = st.session_state.get('daily_pnl_data', pd.DataFrame())
                if not daily_pnl_data.empty:
                    # Converti date per il merge
                    daily_pnl_copy = daily_pnl_data.copy()
                    daily_pnl_copy['date'] = pd.to_datetime(daily_pnl_copy['date'])
                    daily_pnl_copy['date_only'] = daily_pnl_copy['date'].dt.date
                    
                    # Merge
                    funding_table = pivot_funding.merge(
                        daily_pnl_copy[['date_only', 'daily_pnl']], 
                        on='date_only', 
                        how='left'
                    )
                    funding_table['daily_pnl'] = funding_table['daily_pnl'].fillna(0)
                else:
                    funding_table = pivot_funding.copy()
                    funding_table['daily_pnl'] = 0
                
                # Formatta per visualizzazione
                funding_table['Data'] = pd.to_datetime(funding_table['date_only']).dt.strftime('%d/%m/%Y')
                funding_table['Funding BitMEX'] = funding_table['bitmex'].apply(lambda x: f"{x:.4f} USDT" if x != 0 else "-")
                funding_table['Funding Bitfinex'] = funding_table['bitfinex'].apply(lambda x: f"{x:.4f} USDT" if x != 0 else "-")
                funding_table['PnL Giornaliero'] = funding_table['daily_pnl'].apply(lambda x: f"{x:.2f} USDT")
                
                # Ordina per data decrescente
                funding_table = funding_table.sort_values('date_only', ascending=False)
                
                # Mostra tabella
                display_funding_table = funding_table[['Data', 'Funding BitMEX', 'Funding Bitfinex', 'PnL Giornaliero']]
                
                st.dataframe(
                    display_funding_table.reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Statistiche riassuntive
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_bitmex = funding_table['bitmex'].sum()
                    st.metric("Totale BitMEX", f"{total_bitmex:.4f} USDT")
                with col2:
                    total_bitfinex = funding_table['bitfinex'].sum()
                    st.metric("Totale Bitfinex", f"{total_bitfinex:.4f} USDT")
                with col3:
                    total_funding = total_bitmex + total_bitfinex
                    st.metric("Totale Funding", f"{total_funding:.4f} USDT")
                
                # Nuova sezione: Elenco dettagliato funding events
                st.subheader("📋 Elenco Dettagliato Funding Events")
                
                # Crea DataFrame per elenco dettagliato
                detail_funding = []
                for event in filtered_funding:
                    detail_funding.append({
                        'date': event['date'],
                        'exchange': event['exchange'],
                        'amount': event['amount']
                    })
                
                if detail_funding:
                    df_detail = pd.DataFrame(detail_funding)
                    
                    # Normalizza le date
                    df_detail['date'] = pd.to_datetime(df_detail['date'], utc=True).dt.tz_localize(None)
                    
                    # Formatta per visualizzazione
                    df_detail['Data'] = df_detail['date'].dt.strftime('%d/%m/%Y')
                    df_detail['Ora'] = df_detail['date'].dt.strftime('%H:%M:%S')
                    df_detail['Exchange'] = df_detail['exchange'].str.upper()
                    df_detail['Funding'] = df_detail['amount'].apply(lambda x: f"{x:.4f} USDT")
                    
                    # Ordina per data e ora decrescente
                    df_detail = df_detail.sort_values('date', ascending=False)
                    
                    # Mostra tabella dettagliata
                    display_detail_table = df_detail[['Data', 'Ora', 'Exchange', 'Funding']]
                    
                    st.dataframe(
                        display_detail_table.reset_index(drop=True),
                        use_container_width=True,
                        hide_index=True
                    )
                    

                else:
                    st.warning("Nessun funding event trovato")
                
            else:
                st.warning("Nessun funding event trovato dopo la data di avvio del bot")
        else:
            st.info("Nessun funding event disponibile")

    
    else:
        st.info("Clicca 'Aggiorna Dati' per caricare le metriche di performance")
    

if __name__ == "__main__":
    main()