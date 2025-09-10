#!/usr/bin/env python3

import sys
from datetime import datetime, timezone
from bson import ObjectId
from database.models import DatabaseManager

def check_timestamp_conversion(bot_id):
    """Verifica la conversione del timestamp started_at in millisecondi"""
    
    try:
        # Connessione al database
        db_manager = DatabaseManager()
        
        # Recupera il bot
        bot = db_manager.db.bots.find_one({"_id": ObjectId(bot_id)})
        
        if not bot:
            print(f"Bot con ID {bot_id} non trovato")
            return
            
        print(f"=== ANALISI CONVERSIONE TIMESTAMP BOT {bot_id} ===")
        print()
        
        # Analizza started_at
        started_at = bot.get('started_at')
        
        if started_at:
            print("=== STARTED_AT - VALORE RAW DAL DATABASE ===")
            print(f"Valore: {started_at}")
            print(f"Tipo: {type(started_at)}")
            print(f"Timezone info: {started_at.tzinfo}")
            print()
            
            print("=== CONVERSIONI TIMESTAMP ===")
            
            # Metodo 1: timestamp() diretto (assume UTC)
            timestamp_seconds = started_at.timestamp()
            timestamp_ms_1 = int(timestamp_seconds * 1000)
            print(f"Metodo 1 - started_at.timestamp() * 1000: {timestamp_ms_1}")
            
            # Metodo 2: replace timezone come UTC poi timestamp
            started_at_utc = started_at.replace(tzinfo=timezone.utc)
            timestamp_ms_2 = int(started_at_utc.timestamp() * 1000)
            print(f"Metodo 2 - replace(tzinfo=UTC).timestamp() * 1000: {timestamp_ms_2}")
            
            # Metodo 3: calcolo manuale da epoch UTC
            epoch = datetime(1970, 1, 1)
            delta = started_at - epoch
            timestamp_ms_3 = int(delta.total_seconds() * 1000)
            print(f"Metodo 3 - calcolo manuale da epoch: {timestamp_ms_3}")
            
            print()
            print("=== VERIFICA DIFFERENZE ===")
            print(f"Differenza Metodo 1 vs 2: {timestamp_ms_1 - timestamp_ms_2} ms")
            print(f"Differenza Metodo 1 vs 3: {timestamp_ms_1 - timestamp_ms_3} ms")
            print(f"Differenza Metodo 2 vs 3: {timestamp_ms_2 - timestamp_ms_3} ms")
            
            print()
            print("=== CONVERSIONI INVERSE (da timestamp a datetime) ===")
            
            # Riconversione da timestamp
            dt_from_ts_1 = datetime.fromtimestamp(timestamp_ms_1 / 1000)
            dt_from_ts_utc_1 = datetime.utcfromtimestamp(timestamp_ms_1 / 1000)
            
            print(f"Da timestamp {timestamp_ms_1}:")
            print(f"  fromtimestamp(): {dt_from_ts_1} (locale)")
            print(f"  utcfromtimestamp(): {dt_from_ts_utc_1} (UTC)")
            print(f"  Originale: {started_at}")
            
            print()
            print("=== CONFRONTO CON VALORE ATTESO ===")
            print(f"Il valore originale corrisponde a utcfromtimestamp(): {started_at == dt_from_ts_utc_1}")
            
        else:
            print("started_at non presente per questo bot")
            
    except Exception as e:
        print(f"Errore: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python check_timestamp_conversion.py <bot_id>")
        sys.exit(1)
        
    bot_id = sys.argv[1]
    check_timestamp_conversion(bot_id)