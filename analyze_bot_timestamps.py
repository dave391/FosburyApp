#!/usr/bin/env python3
"""
Script per analizzare i timestamp nella collection bots
Verifica il fuso orario utilizzato per created_at e started_at
"""

import os
import sys
import time
from datetime import datetime, timezone
from database.models import db_manager

def analyze_bot_timestamps():
    """Analizza i timestamp dei bot nel database"""
    
    print("=== ANALISI TIMESTAMP COLLECTION BOTS ===")
    print()
    
    # Informazioni sul sistema
    print("=== INFORMAZIONI SISTEMA ===")
    print(f"Fuso orario sistema (TZ): {os.environ.get('TZ', 'Non impostato')}")
    print(f"time.timezone: {time.timezone} secondi ({time.timezone/3600} ore da UTC)")
    print(f"time.tzname: {time.tzname}")
    print(f"datetime.now(): {datetime.now()}")
    print(f"datetime.utcnow(): {datetime.utcnow()}")
    print(f"Differenza locale-UTC: {datetime.now() - datetime.utcnow()}")
    print()
    
    try:
        # Connetti al database
        db_manager.connect()
        
        # Recupera tutti i bot ordinati per created_at
        bots_cursor = db_manager.db.bots.find({}).sort("created_at", -1)
        bots = list(bots_cursor)
        
        if not bots:
            print("❌ Nessun bot trovato nel database")
            return
        
        print(f"=== TROVATI {len(bots)} BOT NEL DATABASE ===")
        print()
        
        # Analizza ogni bot
        for i, bot in enumerate(bots[:10]):  # Limita ai primi 10
            print(f"--- BOT {i+1} ---")
            print(f"ID: {bot['_id']}")
            print(f"User ID: {bot['user_id']}")
            print(f"Status: {bot.get('status', 'N/A')}")
            
            # Analizza created_at
            created_at = bot.get('created_at')
            if created_at:
                print(f"Created at (raw): {created_at}")
                print(f"Created at (type): {type(created_at)}")
                
                # Verifica se ha timezone info
                if hasattr(created_at, 'tzinfo') and created_at.tzinfo:
                    print(f"Created at timezone: {created_at.tzinfo}")
                else:
                    print("Created at timezone: NAIVE (nessun fuso orario)")
                
                # Converti in timestamp
                timestamp_ms = int(created_at.replace(tzinfo=timezone.utc).timestamp() * 1000)
                print(f"Created at timestamp: {timestamp_ms}")
                
                # Mostra in diversi formati
                print(f"Created at UTC: {created_at.strftime('%Y-%m-%d %H:%M:%S.%f')} (assumendo UTC)")
                print(f"Created at locale: {created_at.replace(tzinfo=timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S.%f %Z')}")
            else:
                print("Created at: NON PRESENTE")
            
            # Analizza started_at
            started_at = bot.get('started_at')
            if started_at:
                print(f"Started at (raw): {started_at}")
                print(f"Started at (type): {type(started_at)}")
                
                # Verifica se ha timezone info
                if hasattr(started_at, 'tzinfo') and started_at.tzinfo:
                    print(f"Started at timezone: {started_at.tzinfo}")
                else:
                    print("Started at timezone: NAIVE (nessun fuso orario)")
                
                # Converti in timestamp
                timestamp_ms = int(started_at.replace(tzinfo=timezone.utc).timestamp() * 1000)
                print(f"Started at timestamp: {timestamp_ms}")
                
                # Mostra in diversi formati
                print(f"Started at UTC: {started_at.strftime('%Y-%m-%d %H:%M:%S.%f')} (assumendo UTC)")
                print(f"Started at locale: {started_at.replace(tzinfo=timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S.%f %Z')}")
            else:
                print("Started at: NON PRESENTE")
            
            print()
        
        # Analisi generale
        print("=== ANALISI GENERALE ===")
        
        # Controlla se tutti i timestamp sono naive
        naive_created = 0
        naive_started = 0
        total_created = 0
        total_started = 0
        
        for bot in bots:
            created_at = bot.get('created_at')
            started_at = bot.get('started_at')
            
            if created_at:
                total_created += 1
                if not (hasattr(created_at, 'tzinfo') and created_at.tzinfo):
                    naive_created += 1
            
            if started_at:
                total_started += 1
                if not (hasattr(started_at, 'tzinfo') and started_at.tzinfo):
                    naive_started += 1
        
        print(f"Created_at: {naive_created}/{total_created} sono NAIVE (senza timezone)")
        print(f"Started_at: {naive_started}/{total_started} sono NAIVE (senza timezone)")
        
        if naive_created == total_created and naive_started == total_started:
            print()
            print("🔍 CONCLUSIONE:")
            print("Tutti i timestamp sono NAIVE (senza informazioni di fuso orario).")
            print("MongoDB memorizza i datetime Python come UTC quando sono naive.")
            print("Il codice usa datetime.utcnow() che restituisce un datetime naive in UTC.")
            print("Quindi i timestamp nel DB sono effettivamente in UTC.")
        
    except Exception as e:
        print(f"❌ Errore durante l'analisi: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_manager.close()

if __name__ == "__main__":
    analyze_bot_timestamps()