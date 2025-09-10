#!/usr/bin/env python3
"""
Script di debug per verificare i timestamp del bot e delle fee
"""

from database.models import bot_manager, user_manager
from utils.funding_data import get_bitfinex_trading_fees
from datetime import datetime, timezone
import sys
import time
import os

def debug_timestamps():
    """Debug dei timestamp del bot e delle fee"""
    
    # Debug fuso orario del sistema
    print("=== DEBUG FUSO ORARIO SISTEMA ===")
    print(f"Fuso orario sistema (TZ): {os.environ.get('TZ', 'Non impostato')}")
    print(f"time.timezone: {time.timezone} secondi")
    print(f"time.tzname: {time.tzname}")
    print(f"datetime.now(): {datetime.now()}")
    print(f"datetime.utcnow(): {datetime.utcnow()}")
    print(f"Differenza (now - utcnow): {datetime.now() - datetime.utcnow()}")
    print()
    
    # Trova tutti i bot nel database
    try:
        from database.models import db_manager
        all_bots = list(db_manager.db.bots.find({}).sort("created_at", -1).limit(5))
        
        print("=== BOT NEL DATABASE ===")
        for i, bot in enumerate(all_bots):
            print(f"Bot {i+1}:")
            print(f"  ID: {bot['_id']}")
            print(f"  User ID: {bot['user_id']}")
            print(f"  Status: {bot.get('status', 'N/A')}")
            print(f"  Created at: {bot.get('created_at', 'N/A')}")
            print(f"  Started at: {bot.get('started_at', 'N/A')}")
            print(f"  Stopped at: {bot.get('stopped_at', 'N/A')}")
            print("---")
        
        # Trova il bot più recente con started_at
        active_bot = None
        for bot in all_bots:
            if bot.get('started_at'):
                active_bot = bot
                break
        
        if not active_bot:
            print("❌ Nessun bot con started_at trovato")
            return
        
        print(f"\n=== BOT ATTIVO SELEZIONATO ===")
        print(f"Bot ID: {active_bot['_id']}")
        print(f"Started at: {active_bot['started_at']}")
        print(f"Started at UTC: {active_bot['started_at'].strftime('%Y-%m-%d %H:%M:%S.%f')} UTC")
        print(f"Started at (timestamp): {int(active_bot['started_at'].replace(tzinfo=timezone.utc).timestamp() * 1000)}")
        
        # Verifica che sia effettivamente 20:32:51.431 UTC
        expected_timestamp = 1757017971431  # 2025-09-04 20:32:51.431 UTC
        actual_timestamp = int(active_bot['started_at'].replace(tzinfo=timezone.utc).timestamp() * 1000)
        print(f"\n=== VERIFICA TIMESTAMP ===")
        print(f"Timestamp atteso (20:32:51.431 UTC): {expected_timestamp}")
        print(f"Timestamp effettivo dal DB: {actual_timestamp}")
        print(f"Differenza: {actual_timestamp - expected_timestamp} ms")
        print(f"Corrispondenza: {'✅ SI' if actual_timestamp == expected_timestamp else '❌ NO'}")
        
        # Analisi della discrepanza
        if actual_timestamp != expected_timestamp:
            diff_hours = (expected_timestamp - actual_timestamp) / (1000 * 60 * 60)
            print(f"\n=== ANALISI DISCREPANZA ===")
            print(f"Il DB mostra: {active_bot['started_at'].strftime('%Y-%m-%d %H:%M:%S.%f')} UTC")
            print(f"Tu hai detto: 2025-09-04 20:32:51.431 UTC")
            print(f"Differenza: {diff_hours:.2f} ore")
            print(f"Il timestamp nel DB potrebbe essere in un fuso orario diverso")
        
        # Trova l'utente associato
        user_id = active_bot['user_id']
        user_data = user_manager.get_user_by_id(user_id)
        
        if not user_data:
            print(f"❌ Utente {user_id} non trovato")
            return
        
        email = user_data.get('email')
        print(f"Email utente: {email}")
        
        # Recupera le API keys
        api_keys = user_manager.get_user_api_keys(user_id)
        if not api_keys:
            print(f"❌ API keys non trovate per utente {user_id}")
            return
        
        api_key = api_keys.get('bitfinex_api_key')
        api_secret = api_keys.get('bitfinex_api_secret')
        
        if not api_key or not api_secret:
            print(f"❌ API keys Bitfinex non configurate")
            return
        
        # Recupera le fee di trading
        print(f"\n=== RECUPERO FEE DI TRADING ===")
        bot_started_at = active_bot['started_at']
        print(f"Usando bot_started_at: {bot_started_at}")
        trading_fees, error = get_bitfinex_trading_fees(api_key, api_secret, bot_started_at=bot_started_at)
        
        if error:
            print(f"❌ Errore recupero fee: {error}")
            return
        
        if not trading_fees:
            print("❌ Nessuna fee di trading trovata")
            return
        
        print(f"✅ Trovate {len(trading_fees)} fee di trading")
        
        # Mostra le prime 10 fee con confronto timestamp
        started_timestamp = int(active_bot['started_at'].replace(tzinfo=timezone.utc).timestamp() * 1000)
        
        print(f"\n=== CONFRONTO TIMESTAMP ===")
        print(f"Started at timestamp: {started_timestamp}")
        print(f"Started at date: {active_bot['started_at']}")
        print(f"Started at UTC: {active_bot['started_at'].strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("\nPrime 10 fee:")
        
        for i, fee in enumerate(trading_fees[:10]):
            fee_timestamp = fee.get('timestamp', 0)
            fee_date = fee.get('date')
            is_after = fee_timestamp > started_timestamp
            
            print(f"  Fee {i+1}:")
            print(f"    Timestamp: {fee_timestamp}")
            print(f"    Date: {fee_date}")
            print(f"    Amount: {fee.get('amount', 0)}")
            print(f"    Dopo started_at: {is_after}")
            print(f"    Differenza: {fee_timestamp - started_timestamp} ms")
            print("    ---")
        
        # Conta quante fee sono dopo started_at (con buffer di 5 secondi)
        buffer_timestamp = started_timestamp - 5000  # 5 secondi in millisecondi
        valid_fees = [f for f in trading_fees if f.get('timestamp', 0) > buffer_timestamp]
        print(f"\n=== RISULTATO FILTRO ===")
        print(f"Fee totali: {len(trading_fees)}")
        print(f"Fee dopo started_at (con buffer -5s): {len(valid_fees)}")
        print(f"Started at timestamp: {started_timestamp}")
        print(f"Buffer timestamp (-5s): {buffer_timestamp}")
        print(f"Started at date: {datetime.utcfromtimestamp(started_timestamp / 1000)}")
        print(f"Buffer date (-5s): {datetime.utcfromtimestamp(buffer_timestamp / 1000)}")
        
        # DEBUG: Verifica la fee che dovrebbe essere 1 secondo prima
        target_timestamp = 1757017970000  # La fee che dovrebbe essere 1 secondo prima
        target_date = datetime.utcfromtimestamp(target_timestamp / 1000)
        print(f"\nDEBUG fee specifica:")
        print(f"Target timestamp: {target_timestamp}")
        print(f"Target date: {target_date}")
        print(f"Differenza da started_at: {target_timestamp - started_timestamp} ms")
        print(f"È dopo buffer? {target_timestamp > buffer_timestamp}")
        print(f"È dopo started_at? {target_timestamp > started_timestamp}")
        
        # Verifica fee molto vicine al started_at (entro 1 minuto)
        close_fees = [f for f in trading_fees if abs(f.get('timestamp', 0) - started_timestamp) < 60000]  # 60 secondi
        print(f"Fee entro 1 minuto da started_at: {len(close_fees)}")
        
        if close_fees:
            print(f"\n=== FEE VICINE AL STARTED_AT ===")
            for i, fee in enumerate(close_fees):
                fee_timestamp = fee.get('timestamp', 0)
                diff_ms = fee_timestamp - started_timestamp
                diff_sec = diff_ms / 1000
                print(f"Fee vicina {i+1}:")
                print(f"  Timestamp: {fee_timestamp}")
                print(f"  Date: {fee.get('date')}")
                print(f"  Amount: {fee.get('amount', 0):.6f} USDT")
                print(f"  Differenza: {diff_ms} ms ({diff_sec:.3f} secondi)")
                print(f"  Dopo started_at: {fee_timestamp > started_timestamp}")
                print("  ---")
        
        if valid_fees:
            total_amount = sum(f.get('amount', 0) for f in valid_fees)
            print(f"Totale fee valide: {total_amount:.6f} USDT")
            
            print(f"\n=== FEE VALIDE DETTAGLIATE ===")
            for i, fee in enumerate(valid_fees):
                fee_timestamp = fee.get('timestamp', 0)
                diff_from_start = fee_timestamp - started_timestamp
                diff_minutes = diff_from_start / (1000 * 60)  # Converti in minuti
                
                print(f"  DEBUG: fee_timestamp={fee_timestamp}, started_timestamp={started_timestamp}")
                
                # Verifica conversione timestamp
                utc_date = datetime.utcfromtimestamp(fee_timestamp / 1000)
                local_date = datetime.fromtimestamp(fee_timestamp / 1000)
                
                # Verifica se è dopo buffer e started_at
                after_buffer = fee_timestamp > buffer_timestamp
                after_started = fee_timestamp > started_timestamp
                
                print(f"Fee valida {i+1}:")
                print(f"  Timestamp: {fee_timestamp}")
                print(f"  Date (da fee): {fee.get('date')}")
                print(f"  Date (UTC calc): {utc_date}")
                print(f"  Date (Local calc): {local_date}")
                print(f"  Amount: {fee.get('amount', 0):.6f} USDT")
                print(f"  Differenza da started_at: {diff_from_start} ms ({diff_minutes:.2f} minuti)")
                print(f"  Dopo buffer (-5s): {after_buffer}")
                print(f"  Dopo started_at: {after_started}")
                print(f"  Description: {fee.get('description', 'N/A')}")
                print(f"  Category: {fee.get('category', 'N/A')}")
                print(f"  Type: {fee.get('type', 'N/A')}")
                print("  ---")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_timestamps()