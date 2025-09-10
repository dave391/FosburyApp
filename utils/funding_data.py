"""Modulo per recuperare dati di funding da Bitfinex e BitMEX
Utilizzato dalla dashboard per calcolare metriche di performance del bot
"""

import ccxt
import requests
import hmac
import hashlib
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from database.models import user_manager


def get_user_api_keys(email: str) -> Tuple[Dict[str, str], Optional[str]]:
    """Recupera le API keys dell'utente dal database
    
    Args:
        email: Email dell'utente
    
    Returns:
        Tuple (api_keys_dict, error_message)
    """
    try:
        user_data = user_manager.get_user_by_email(email)
        if not user_data:
            return {}, f"Utente {email} non trovato nel database"
        
        user_id = user_data["user_id"]
        api_keys = user_manager.get_user_api_keys(user_id)
        
        return api_keys, None
        
    except Exception as e:
        return {}, f"Errore nel recupero delle API keys: {str(e)}"


def get_bitfinex_trading_fees(api_key: str, api_secret: str, bot_started_at: Optional[datetime] = None) -> Tuple[List[Dict], Optional[str]]:
    """Recupera dati delle fee di trading da Bitfinex
    
    Args:
        api_key: API Key Bitfinex
        api_secret: API Secret Bitfinex
        bot_started_at: Data di inizio del bot (se None, usa 365 giorni fa)
    
    Returns:
        Tuple (trading_fees, error_message)
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
        
        # Calcola timestamp di inizio con buffer di 2 giorni prima del bot_started_at
        if bot_started_at:
            # Buffer di 2 giorni prima dell'inizio del bot
            since_date = bot_started_at - timedelta(days=2)
        else:
            # Fallback: 365 giorni fa se bot_started_at non è fornito
            since_date = datetime.utcnow() - timedelta(days=365)
        
        since_timestamp = int(since_date.replace(tzinfo=timezone.utc).timestamp() * 1000)
        
        # Recupera ledger
        ledger = exchange.fetchLedger(code=None, since=since_timestamp, limit=1000)
        
        # Filtra fee di trading - DEBUG: includiamo più filtri per vedere cosa c'è
        trading_fees = []
        for entry in ledger:
            info = entry.get('info', {})
            category = info.get('category')
            description = info.get('description', '').lower()
            entry_type = entry.get('type', '').lower()
            
            # Filtri per trading fee (DEBUG: più ampi per vedere cosa troviamo)
            if (category == 201 or  # Category 201 = trading fee
                'trading fee' in description or
                'fee' in description or
                entry_type == 'fee'):
                
                # Timestamp di Bitfinex sono in millisecondi UTC
                original_timestamp = entry.get('timestamp', 0)
                # Converto in UTC esplicito per evitare problemi di fuso orario
                original_date = datetime.utcfromtimestamp(original_timestamp / 1000) if original_timestamp else None
                
                trading_fees.append({
                    'timestamp': original_timestamp,
                    'date': original_date,
                    'currency': entry.get('currency', ''),
                    'amount': abs(entry.get('amount', 0)),  # Fee sempre positive
                    'exchange': 'bitfinex',
                    'description': description,
                    'category': category,  # Aggiungiamo category per debug
                    'type': entry_type,  # Aggiungiamo type per debug
                    'original_date': original_date,  # DEBUG: data originale
                    'timezone_info': 'UTC (confermato)'  # Timezone confermato da documentazione Bitfinex
                })
        
        return trading_fees, None
        
    except Exception as e:
        return [], f"Errore Bitfinex trading fees: {str(e)}"


def get_bitfinex_funding_data(api_key: str, api_secret: str, bot_started_at: Optional[datetime] = None) -> Tuple[List[Dict], Optional[str]]:
    """Recupera dati di funding da Bitfinex
    
    Args:
        api_key: API Key Bitfinex
        api_secret: API Secret Bitfinex
        bot_started_at: Data di inizio del bot (se None, usa 365 giorni fa)
    
    Returns:
        Tuple (funding_events, error_message)
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
        
        # Calcola timestamp di inizio con buffer di 2 giorni prima del bot_started_at
        if bot_started_at:
            # Buffer di 2 giorni prima dell'inizio del bot
            since_date = bot_started_at - timedelta(days=2)
        else:
            # Fallback: 365 giorni fa se bot_started_at non è fornito
            since_date = datetime.utcnow() - timedelta(days=365)
        
        since_timestamp = int(since_date.replace(tzinfo=timezone.utc).timestamp() * 1000)
        
        # Recupera ledger
        ledger = exchange.fetchLedger(code=None, since=since_timestamp, limit=1000)
        
        # Filtra eventi di funding
        funding_events = []
        for entry in ledger:
            info = entry.get('info', {})
            description = info.get('description', '').lower()
            entry_type = entry.get('type', '').lower()
            category = info.get('category')
            
            # Filtri per identificare funding events
            if ('funding' in description or 
                'funding' in entry_type or 
                category == 29 or 
                ('swap' in description and 'fee' in description)):
                funding_events.append({
                    'timestamp': entry.get('timestamp', 0),
                    'date': datetime.fromtimestamp(entry.get('timestamp', 0) / 1000) if entry.get('timestamp') else None,
                    'currency': entry.get('currency', ''),
                    'amount': entry.get('amount', 0),
                    'fee': 0,  # Bitfinex non ha fee separate per funding
                    'exchange': 'bitfinex',
                    'description': description
                })
        
        return funding_events, None
        
    except Exception as e:
        return [], f"Errore Bitfinex: {str(e)}"


def create_bitmex_signature(api_secret: str, verb: str, url: str, nonce: int, data: str = '') -> str:
    """Crea la signature per autenticazione BitMEX"""
    message = verb + url + str(nonce) + data
    signature = hmac.new(
        api_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


def get_bitmex_funding_data(api_key: str, api_secret: str, currency: str = "USDt", count: int = 1000, bot_started_at: Optional[datetime] = None) -> Tuple[List[Dict], Optional[str]]:
    """Recupera dati di funding da BitMEX
    
    Args:
        api_key: API Key BitMEX
        api_secret: API Secret BitMEX
        currency: Valuta da filtrare
        count: Numero di transazioni da recuperare
        bot_started_at: Data di inizio del bot (se None, non filtra per data)
    
    Returns:
        Tuple (funding_events, error_message)
    """
    try:
        # Endpoint BitMEX
        base_url = "https://www.bitmex.com"
        endpoint = "/api/v1/user/walletHistory"
        
        # Parametri query
        params = {
            "currency": currency,
            "count": count,
            "reverse": "true"
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
        
        if response.status_code != 200:
            return [], f"Errore API BitMEX: {response.status_code} - {response.text}"
        
        transactions = response.json()
        
        # Calcola data limite se bot_started_at è fornito
        date_limit = None
        if bot_started_at:
            # Assicurati che bot_started_at abbia timezone UTC per il confronto
            if bot_started_at.tzinfo is None:
                bot_started_utc = bot_started_at.replace(tzinfo=timezone.utc)
            else:
                bot_started_utc = bot_started_at.astimezone(timezone.utc)
            date_limit = bot_started_utc - timedelta(days=2)
        
        # Filtra solo transazioni di funding completate
        funding_events = []
        for tx in transactions:
            if tx.get("transactType") == "Funding" and tx.get("transactStatus") == "Completed":
                tx_date = datetime.fromisoformat(tx["transactTime"].replace("Z", "+00:00"))
                
                # Filtra per data se bot_started_at è fornito
                if date_limit and tx_date < date_limit:
                    continue
                
                # Per BitMEX, le transazioni di funding non dovrebbero avere fee
                # La fee viene applicata solo su trades, non su funding
                funding_events.append({
                    'timestamp': int(tx_date.timestamp() * 1000),
                    'date': tx_date,
                    'currency': currency,
                    'amount': tx["amount"] / 1_000_000,  # Converti da satoshi a USDT
                    'fee': 0,  # Le transazioni di funding BitMEX non hanno fee
                    'exchange': 'bitmex',
                    'description': f"Funding {tx.get('address', '')}"
                })
        
        return funding_events, None
        
    except Exception as e:
        return [], f"Errore BitMEX: {str(e)}"


def get_bitmex_trading_fees(api_key: str, api_secret: str, currency: str = "USDt", count: int = 1000, bot_started_at: Optional[datetime] = None) -> Tuple[List[Dict], Optional[str]]:
    """Recupera dati delle fee di trading da BitMEX
    
    Args:
        api_key: API Key BitMEX
        api_secret: API Secret BitMEX
        currency: Valuta da filtrare (default: USDt)
        count: Numero di transazioni da recuperare
        bot_started_at: Data di inizio del bot (se None, non filtra per data)
    
    Returns:
        Tuple (trading_fees, error_message)
    """
    try:
        # Endpoint BitMEX
        base_url = "https://www.bitmex.com"
        endpoint = "/api/v1/user/walletHistory"
        
        # Parametri query
        params = {
            "currency": currency,
            "count": count,
            "reverse": "true"
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
        
        if response.status_code != 200:
            return [], f"Errore API BitMEX trading fees: {response.status_code} - {response.text}"
        
        transactions = response.json()
        
        # Calcola data limite se bot_started_at è fornito
        date_limit = None
        if bot_started_at:
            # Assicurati che bot_started_at abbia timezone UTC per il confronto
            if bot_started_at.tzinfo is None:
                bot_started_utc = bot_started_at.replace(tzinfo=timezone.utc)
            else:
                bot_started_utc = bot_started_at.astimezone(timezone.utc)
            date_limit = bot_started_utc - timedelta(days=2)
        
        # Filtra solo transazioni RealisedPNL con fee > 0
        trading_fees = []
        for tx in transactions:
            if (tx.get("transactType") == "RealisedPNL" and 
                tx.get("transactStatus") == "Completed" and 
                tx.get("fee", 0) > 0):  # Fee positive indica fee pagata
                
                tx_date = datetime.fromisoformat(tx["transactTime"].replace("Z", "+00:00"))
                
                # Filtra per data se bot_started_at è fornito
                if date_limit and tx_date < date_limit:
                    continue
                
                trading_fees.append({
                    'timestamp': int(tx_date.timestamp() * 1000),
                    'date': tx_date,
                    'currency': currency,
                    'amount': tx.get("fee", 0) / 1_000_000,  # Converti fee da satoshi a USDT
                    'exchange': 'bitmex',
                    'description': f"Trading fee {tx.get('address', '')}"
                })
        
        return trading_fees, None
        
    except Exception as e:
        return [], f"Errore BitMEX trading fees: {str(e)}"


def get_all_funding_data(email: str, bot_started_at: Optional[datetime] = None) -> Tuple[List[Dict], List[Dict], Optional[str]]:
    """Recupera tutti i dati di funding e fee di trading da entrambi gli exchange
    
    Args:
        email: Email dell'utente
        bot_started_at: Data di inizio del bot per ottimizzare il recupero dati
    
    Returns:
        Tuple (all_funding_events, all_trading_fees, error_message)
    """
    # Recupera API keys
    api_keys, error = get_user_api_keys(email)
    if error:
        return [], error
    
    all_funding_events = []
    all_trading_fees = []
    errors = []
    
    # Recupera da Bitfinex
    bitfinex_key = api_keys.get("bitfinex_api_key")
    bitfinex_secret = api_keys.get("bitfinex_api_secret")
    
    if bitfinex_key and bitfinex_secret:
        # Recupera funding events
        bitfinex_events, bitfinex_error = get_bitfinex_funding_data(bitfinex_key, bitfinex_secret, bot_started_at)
        if bitfinex_error:
            errors.append(f"Bitfinex funding: {bitfinex_error}")
        else:
            all_funding_events.extend(bitfinex_events)
        
        # Recupera trading fees
        bitfinex_fees, bitfinex_fees_error = get_bitfinex_trading_fees(bitfinex_key, bitfinex_secret, bot_started_at)
        if bitfinex_fees_error:
            errors.append(f"Bitfinex fees: {bitfinex_fees_error}")
        else:
            all_trading_fees.extend(bitfinex_fees)
    
    # Recupera da BitMEX
    bitmex_key = api_keys.get("bitmex_api_key")
    bitmex_secret = api_keys.get("bitmex_api_secret")
    
    if bitmex_key and bitmex_secret:
        # Recupera funding events
        bitmex_events, bitmex_error = get_bitmex_funding_data(bitmex_key, bitmex_secret, bot_started_at=bot_started_at)
        if bitmex_error:
            errors.append(f"BitMEX funding: {bitmex_error}")
        else:
            all_funding_events.extend(bitmex_events)
        
        # Recupera trading fees
        bitmex_fees, bitmex_fees_error = get_bitmex_trading_fees(bitmex_key, bitmex_secret, bot_started_at=bot_started_at)
        if bitmex_fees_error:
            errors.append(f"BitMEX fees: {bitmex_fees_error}")
        else:
            all_trading_fees.extend(bitmex_fees)
    
    # Ordina per timestamp
    all_funding_events.sort(key=lambda x: x['timestamp'])
    all_trading_fees.sort(key=lambda x: x['timestamp'])
    
    error_message = "; ".join(errors) if errors else None
    return all_funding_events, all_trading_fees, error_message


def calculate_metrics(funding_events: List[Dict], start_date: datetime, initial_capital: float, trading_fees: List[Dict] = None) -> Dict:
    """
    Calcola le metriche di performance del bot
    
    Args:
        funding_events: Lista degli eventi di funding
        start_date: Data di avvio del bot
        initial_capital: Capitale iniziale
        trading_fees: Lista delle fee di trading (opzionale)
        
    Returns:
        Dizionario con le metriche calcolate
    """
    if not funding_events:
        return {
            'total_pnl': 0.0,
            'total_fees': 0.0,
            'net_pnl': 0.0,
            'apr': 0.0,
            'days_running': 0
        }
    
    # Assicurati che start_date sia naive (senza timezone)
    if start_date.tzinfo is not None:
        start_date = start_date.replace(tzinfo=None)
    
    # Filtra eventi dalla data di avvio
    filtered_events = []
    for e in funding_events:
        if e['date']:
            event_date = e['date']
            # Assicurati che anche la data dell'evento sia naive
            if event_date.tzinfo is not None:
                event_date = event_date.replace(tzinfo=None)
            if event_date >= start_date:
                filtered_events.append(e)
    
    # Calcola PnL totale (somma di tutti i funding)
    total_pnl = sum(event['amount'] for event in filtered_events)
    
    # Calcola fee totali (fee di funding + fee di trading)
    total_fees = sum(event['fee'] for event in filtered_events)
    
    # Aggiungi fee di trading se fornite
    if trading_fees:
        # Filtra anche le fee di trading dalla data di avvio
        filtered_trading_fees = []
        for fee in trading_fees:
            if fee['date']:
                fee_date = fee['date']
                # Assicurati che anche la data della fee sia naive
                if fee_date.tzinfo is not None:
                    fee_date = fee_date.replace(tzinfo=None)
                
                # Converte start_date in naive se ha timezone per il confronto
                comparison_start_date = start_date
                if start_date.tzinfo is not None:
                    comparison_start_date = start_date.replace(tzinfo=None)
                
                # Aggiungi buffer di 5 secondi prima della data di avvio per includere fee
                # che potrebbero essere registrate leggermente prima a causa di discrepanze temporali
                buffer_start_date = comparison_start_date - timedelta(seconds=5)
                
                # Fee valide: da 5 secondi prima dell'avvio in poi
                if fee_date >= buffer_start_date:
                    filtered_trading_fees.append(fee)
        
        # Somma le fee di trading (amount rappresenta la fee pagata)
        trading_fees_total = sum(fee['amount'] for fee in filtered_trading_fees)
        total_fees += trading_fees_total
    
    # PnL netto
    net_pnl = total_pnl - total_fees
    
    # Giorni di running
    days_running = (datetime.now() - start_date).days
    if days_running == 0:
        days_running = 1  # Evita divisione per zero
    
    # APR annualizzato
    if initial_capital > 0 and days_running > 0:
        daily_return = net_pnl / initial_capital / days_running
        apr = daily_return * 365 * 100  # Percentuale annualizzata
    else:
        apr = 0.0
    
    return {
        'total_pnl': total_pnl,
        'total_fees': total_fees,
        'net_pnl': net_pnl,
        'apr': apr,
        'days_running': days_running
    }


def get_daily_pnl_data(funding_events: List[Dict], start_date: datetime, trading_fees: List[Dict] = None) -> pd.DataFrame:
    """Calcola il PnL giornaliero per il grafico
    
    Args:
        funding_events: Lista degli eventi di funding
        start_date: Data di avvio del bot
        trading_fees: Lista delle fee di trading (opzionale)
    
    Returns:
        DataFrame con date e PnL giornaliero cumulativo
    """
    if not funding_events:
        return pd.DataFrame(columns=['date', 'daily_pnl', 'cumulative_pnl'])
    
    # Assicurati che start_date sia naive (senza timezone)
    if start_date.tzinfo is not None:
        start_date = start_date.replace(tzinfo=None)
    
    # Filtra eventi dalla data di avvio
    filtered_events = []
    for e in funding_events:
        if e['date']:
            event_date = e['date']
            # Assicurati che anche la data dell'evento sia naive
            if event_date.tzinfo is not None:
                event_date = event_date.replace(tzinfo=None)
            if event_date >= start_date:
                filtered_events.append(e)
    
    # Se non ci sono funding events ma ci sono trading fees, crea DataFrame vuoto per i funding
    if not filtered_events:
        daily_data = pd.DataFrame(columns=['date_only', 'amount', 'fee', 'daily_pnl'])
    else:
        # Crea DataFrame
        df = pd.DataFrame(filtered_events)
        
        # Normalizza le date rimuovendo timezone info prima della conversione pandas
        normalized_dates = []
        for date_val in df['date']:
            if date_val and hasattr(date_val, 'tzinfo') and date_val.tzinfo is not None:
                normalized_dates.append(date_val.replace(tzinfo=None))
            else:
                normalized_dates.append(date_val)
        
        df['date'] = normalized_dates
        
        # Converti la colonna date in pandas datetime
        df['date'] = pd.to_datetime(df['date'])
        df['date_only'] = df['date'].dt.date
        
        # Raggruppa per giorno e somma PnL
        daily_data = df.groupby('date_only').agg({
            'amount': 'sum',
            'fee': 'sum'
        }).reset_index()
        
        # Calcola PnL base (funding - fee di funding)
        daily_data['daily_pnl'] = daily_data['amount'] - daily_data['fee']
        
        # Se non ci sono trading fees, il PnL netto è uguale al PnL giornaliero
        daily_data['net_daily_pnl'] = daily_data['daily_pnl']
    

    
    # Aggiungi fee di trading se disponibili
    if trading_fees:
        # Filtra fee di trading dalla data di avvio (con buffer di 5 secondi)
        from datetime import timedelta
        buffer_start_date = start_date - timedelta(seconds=5)
        filtered_trading_fees = []
        for fee in trading_fees:
            if fee['date']:
                fee_date = fee['date']
                # Assicurati che la data sia naive
                if fee_date.tzinfo is not None:
                    fee_date = fee_date.replace(tzinfo=None)
                if fee_date >= buffer_start_date:
                    filtered_trading_fees.append(fee)
        
        if filtered_trading_fees:
            # Crea DataFrame per le fee di trading
            trading_df = pd.DataFrame(filtered_trading_fees)
            
            # Normalizza le date
            normalized_trading_dates = []
            for date_val in trading_df['date']:
                if date_val and hasattr(date_val, 'tzinfo') and date_val.tzinfo is not None:
                    normalized_trading_dates.append(date_val.replace(tzinfo=None))
                else:
                    normalized_trading_dates.append(date_val)
            
            trading_df['date'] = normalized_trading_dates
            trading_df['date'] = pd.to_datetime(trading_df['date'])
            trading_df['date_only'] = trading_df['date'].dt.date
            
            # Raggruppa fee di trading per giorno
            daily_trading_fees = trading_df.groupby('date_only').agg({
                'amount': 'sum'
            }).reset_index()
            daily_trading_fees = daily_trading_fees.rename(columns={'amount': 'trading_fees'})
            
            # Unisci con i dati giornalieri usando outer join per includere tutti i giorni
            daily_data = daily_data.merge(daily_trading_fees, on='date_only', how='outer')
            
            # Riempi i valori mancanti
            daily_data['amount'] = daily_data['amount'].fillna(0)
            daily_data['fee'] = daily_data['fee'].fillna(0)
            daily_data['trading_fees'] = daily_data['trading_fees'].fillna(0)
            
            # Ricalcola il PnL giornaliero per tutti i giorni (solo funding, senza trading fees)
            daily_data['daily_pnl'] = daily_data['amount'] - daily_data['fee']
            
            # Calcola PnL netto giornaliero (funding - trading fees) per il cumulativo
            daily_data['net_daily_pnl'] = daily_data['daily_pnl'] - daily_data['trading_fees']
    
    # Se non ci sono dati dopo il merge, restituisci DataFrame vuoto
    if daily_data.empty:
        return pd.DataFrame(columns=['date', 'daily_pnl', 'cumulative_pnl'])
    
    # Rinomina colonne
    daily_data = daily_data.rename(columns={'date_only': 'date'})
    
    # Ordina per data in ordine crescente per calcolare correttamente il cumulativo
    daily_data = daily_data.sort_values('date', ascending=True)
    
    # Il PnL cumulativo considera le fee di trading come costi
    if 'net_daily_pnl' in daily_data.columns:
        daily_data['cumulative_pnl'] = daily_data['net_daily_pnl'].cumsum()
    else:
        daily_data['cumulative_pnl'] = daily_data['daily_pnl'].cumsum()
    
    # Ordina per data in ordine decrescente (dal più recente al più vecchio) per la visualizzazione
    daily_data = daily_data.sort_values('date', ascending=False)
    
    # Includi trading_fees nel risultato se presente
    if 'trading_fees' in daily_data.columns:
        return daily_data[['date', 'daily_pnl', 'cumulative_pnl', 'trading_fees']]
    else:
        return daily_data[['date', 'daily_pnl', 'cumulative_pnl']]