#!/usr/bin/env python3
"""
Script per verificare il formato raw dei dati dal database
"""

import sys
from bson import ObjectId
from database.models import db_manager

def check_raw_db_format(bot_id_str):
    """Verifica il formato raw dei dati dal database"""
    
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
        
        print(f"=== FORMATO RAW DAL DATABASE ===")
        print(f"Bot ID: {bot_id_str}")
        print()
        
        # Mostra il valore raw di started_at
        started_at_raw = bot.get('started_at')
        
        print("=== STARTED_AT - VALORE RAW ===")
        print(f"Valore restituito dal DB: {repr(started_at_raw)}")
        print(f"Tipo Python: {type(started_at_raw)}")
        print(f"Classe: {started_at_raw.__class__}")
        print(f"Modulo: {started_at_raw.__class__.__module__}")
        print()
        
        # Verifica attributi timezone
        print("=== ATTRIBUTI TIMEZONE ===")
        print(f"Ha attributo tzinfo: {hasattr(started_at_raw, 'tzinfo')}")
        if hasattr(started_at_raw, 'tzinfo'):
            print(f"tzinfo value: {started_at_raw.tzinfo}")
            print(f"tzinfo type: {type(started_at_raw.tzinfo)}")
        print()
        
        # Mostra tutti gli attributi del datetime
        print("=== ATTRIBUTI DATETIME ===")
        print(f"year: {started_at_raw.year}")
        print(f"month: {started_at_raw.month}")
        print(f"day: {started_at_raw.day}")
        print(f"hour: {started_at_raw.hour}")
        print(f"minute: {started_at_raw.minute}")
        print(f"second: {started_at_raw.second}")
        print(f"microsecond: {started_at_raw.microsecond}")
        print()
        
        # Test di conversioni
        print("=== TEST CONVERSIONI ===")
        print(f"str(started_at): {str(started_at_raw)}")
        print(f"isoformat(): {started_at_raw.isoformat()}")
        print(f"timestamp(): {started_at_raw.timestamp()}")
        print(f"timestamp() * 1000: {int(started_at_raw.timestamp() * 1000)}")
        print()
        
        # Verifica anche created_at per confronto
        created_at_raw = bot.get('created_at')
        if created_at_raw:
            print("=== CREATED_AT - VALORE RAW (per confronto) ===")
            print(f"Valore restituito dal DB: {repr(created_at_raw)}")
            print(f"Tipo Python: {type(created_at_raw)}")
            print(f"tzinfo: {created_at_raw.tzinfo if hasattr(created_at_raw, 'tzinfo') else 'N/A'}")
            print()
        
        # Mostra il documento completo per riferimento
        print("=== DOCUMENTO COMPLETO (solo timestamp) ===")
        timestamp_fields = {k: v for k, v in bot.items() if k.endswith('_at')}
        for field, value in timestamp_fields.items():
            print(f"{field}: {repr(value)} (type: {type(value)})")
        
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
        print("Uso: python check_raw_db_format.py <bot_id>")
        print("Esempio: python check_raw_db_format.py 68b9e33a932c3d1eed90970d")
        sys.exit(1)
    
    bot_id = sys.argv[1]
    check_raw_db_format(bot_id)