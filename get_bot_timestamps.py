#!/usr/bin/env python3
"""
Script per recuperare i timestamp di un bot specifico
"""

import sys
from datetime import datetime, timezone
from bson import ObjectId
from database.models import db_manager

def get_bot_timestamps(bot_id_str):
    """Recupera i timestamp di un bot specifico"""
    
    try:
        # Connetti al database
        db_manager.connect()
        
        # Converti l'ID stringa in ObjectId
        bot_id = ObjectId(bot_id_str)
        
        # Cerca il bot nel database
        bot = db_manager.db.bots.find_one({"_id": bot_id})
        
        if not bot:
            print(f"❌ Bot con ID {bot_id_str} non trovato")
            return
        
        print(f"=== TIMESTAMP BOT ID: {bot_id_str} ===")
        print()
        
        # Informazioni generali del bot
        print(f"User ID: {bot['user_id']}")
        print(f"Status: {bot.get('status', 'N/A')}")
        print(f"Exchange Long: {bot.get('exchange_long', 'N/A')}")
        print(f"Exchange Short: {bot.get('exchange_short', 'N/A')}")
        print()
        
        # Analizza created_at
        created_at = bot.get('created_at')
        if created_at:
            print("=== CREATED_AT ===")
            print(f"Raw value: {created_at}")
            print(f"Type: {type(created_at)}")
            print(f"UTC: {created_at.strftime('%Y-%m-%d %H:%M:%S.%f')} UTC")
            print(f"Timestamp (ms): {int(created_at.replace(tzinfo=timezone.utc).timestamp() * 1000)}")
            print(f"Locale (CEST): {created_at.replace(tzinfo=timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S.%f %Z')}")
            print()
        else:
            print("=== CREATED_AT ===\nNON PRESENTE\n")
        
        # Analizza started_at
        started_at = bot.get('started_at')
        if started_at:
            print("=== STARTED_AT ===")
            print(f"Raw value: {started_at}")
            print(f"Type: {type(started_at)}")
            print(f"UTC: {started_at.strftime('%Y-%m-%d %H:%M:%S.%f')} UTC")
            print(f"Timestamp (ms): {int(started_at.replace(tzinfo=timezone.utc).timestamp() * 1000)}")
            print(f"Locale (CEST): {started_at.replace(tzinfo=timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S.%f %Z')}")
            print()
        else:
            print("=== STARTED_AT ===\nNON PRESENTE\n")
        
        # Analizza stopped_at
        stopped_at = bot.get('stopped_at')
        if stopped_at:
            print("=== STOPPED_AT ===")
            print(f"Raw value: {stopped_at}")
            print(f"Type: {type(stopped_at)}")
            print(f"UTC: {stopped_at.strftime('%Y-%m-%d %H:%M:%S.%f')} UTC")
            print(f"Timestamp (ms): {int(stopped_at.replace(tzinfo=timezone.utc).timestamp() * 1000)}")
            print(f"Locale (CEST): {stopped_at.replace(tzinfo=timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S.%f %Z')}")
            print()
        else:
            print("=== STOPPED_AT ===\nNON PRESENTE\n")
        
        # Calcola durate se possibile
        if created_at and started_at:
            duration = started_at - created_at
            print(f"=== DURATE ===")
            print(f"Tempo tra creazione e avvio: {duration}")
            print(f"Secondi: {duration.total_seconds()}")
            
            if stopped_at:
                run_duration = stopped_at - started_at
                total_duration = stopped_at - created_at
                print(f"Tempo di esecuzione: {run_duration}")
                print(f"Tempo totale: {total_duration}")
            print()
        
    except ValueError as e:
        print(f"❌ ID non valido: {e}")
    except Exception as e:
        print(f"❌ Errore durante il recupero: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_manager.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python get_bot_timestamps.py <bot_id>")
        print("Esempio: python get_bot_timestamps.py 68b9e33a932c3d1eed90970d")
        sys.exit(1)
    
    bot_id = sys.argv[1]
    get_bot_timestamps(bot_id)