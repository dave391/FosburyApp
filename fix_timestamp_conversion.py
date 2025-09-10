#!/usr/bin/env python3
"""
Script per dimostrare il problema e la soluzione per la conversione timestamp
"""

import sys
from datetime import datetime, timezone
from bson import ObjectId
from database.models import DatabaseManager

def demonstrate_timestamp_issue(bot_id):
    """Dimostra il problema della conversione timestamp e la soluzione"""
    
    try:
        # Connessione al database
        db_manager = DatabaseManager()
        
        # Recupera il bot
        bot = db_manager.db.bots.find_one({"_id": ObjectId(bot_id)})
        
        if not bot:
            print(f"Bot con ID {bot_id} non trovato")
            return
            
        print(f"=== PROBLEMA CONVERSIONE TIMESTAMP BOT {bot_id} ===")
        print()
        
        started_at = bot.get('started_at')
        
        if started_at:
            print("=== VALORE DAL DATABASE ===")
            print(f"started_at: {started_at}")
            print(f"Tipo: {type(started_at)}")
            print(f"Timezone: {started_at.tzinfo} (None = naive)")
            print()
            
            print("=== PROBLEMA ATTUALE ===")
            # Metodo SBAGLIATO usato nel codice attuale
            wrong_timestamp = int(started_at.timestamp() * 1000)
            print(f"❌ METODO SBAGLIATO: started_at.timestamp() * 1000")
            print(f"   Risultato: {wrong_timestamp}")
            print(f"   Interpreta il datetime naive come ORA LOCALE")
            
            # Verifica che ora locale viene interpretata
            local_interpretation = datetime.fromtimestamp(wrong_timestamp / 1000)
            print(f"   Riconversione: {local_interpretation} (ora locale)")
            print()
            
            print("=== SOLUZIONE CORRETTA ===")
            # Metodo CORRETTO
            correct_timestamp = int(started_at.replace(tzinfo=timezone.utc).timestamp() * 1000)
            print(f"✅ METODO CORRETTO: started_at.replace(tzinfo=timezone.utc).timestamp() * 1000")
            print(f"   Risultato: {correct_timestamp}")
            print(f"   Interpreta il datetime naive come UTC")
            
            # Verifica che UTC viene interpretata correttamente
            utc_interpretation = datetime.utcfromtimestamp(correct_timestamp / 1000)
            print(f"   Riconversione: {utc_interpretation} (UTC)")
            print(f"   Corrisponde all'originale: {started_at == utc_interpretation}")
            print()
            
            print("=== DIFFERENZA ===")
            diff_ms = correct_timestamp - wrong_timestamp
            diff_hours = diff_ms / (1000 * 60 * 60)
            print(f"Differenza: {diff_ms} ms ({diff_hours} ore)")
            print(f"Il metodo sbagliato è {abs(diff_hours)} ore {'avanti' if diff_ms < 0 else 'indietro'}")
            print()
            
            print("=== IMPATTO SUL FILTRO FEE ===")
            print("Quando si filtrano le fee dopo started_at:")
            print(f"- Metodo sbagliato cerca fee dopo: {wrong_timestamp}")
            print(f"- Metodo corretto cerca fee dopo: {correct_timestamp}")
            print(f"- Differenza di {abs(diff_hours)} ore nel filtro!")
            print()
            
            print("=== ESEMPIO PRATICO ===")
            # Simula una fee che dovrebbe essere inclusa
            example_fee_time = started_at.replace(minute=33)  # 1 minuto dopo
            example_fee_timestamp_wrong = int(example_fee_time.timestamp() * 1000)
            example_fee_timestamp_correct = int(example_fee_time.replace(tzinfo=timezone.utc).timestamp() * 1000)
            
            print(f"Fee di esempio (1 minuto dopo started_at):")
            print(f"- Timestamp con metodo sbagliato: {example_fee_timestamp_wrong}")
            print(f"- Timestamp con metodo corretto: {example_fee_timestamp_correct}")
            print()
            print(f"Filtro con metodo sbagliato:")
            print(f"- Fee dopo started_at? {example_fee_timestamp_wrong > wrong_timestamp}")
            print(f"- Fee dopo started_at? {example_fee_timestamp_correct > wrong_timestamp}")
            print()
            print(f"Filtro con metodo corretto:")
            print(f"- Fee dopo started_at? {example_fee_timestamp_wrong > correct_timestamp}")
            print(f"- Fee dopo started_at? {example_fee_timestamp_correct > correct_timestamp}")
            
        else:
            print("started_at non presente per questo bot")
            
    except Exception as e:
        print(f"Errore: {e}")
        import traceback
        traceback.print_exc()

def show_fix_recommendation():
    """Mostra le modifiche da fare nel codice"""
    print("\n" + "="*60)
    print("=== RACCOMANDAZIONI PER FIXARE IL CODICE ===")
    print("="*60)
    print()
    print("1. Nel file utils/funding_data.py, SOSTITUIRE:")
    print("   ❌ since_timestamp = int(since_date.timestamp() * 1000)")
    print("   ✅ since_timestamp = int(since_date.replace(tzinfo=timezone.utc).timestamp() * 1000)")
    print()
    print("2. Oppure, ancora meglio, usare datetime.utcnow() invece di datetime.now():")
    print("   ❌ since_date = datetime.now() - timedelta(days=since_days)")
    print("   ✅ since_date = datetime.utcnow() - timedelta(days=since_days)")
    print("   ✅ since_timestamp = int(since_date.timestamp() * 1000)")
    print()
    print("3. Per i timestamp dei bot (started_at), SOSTITUIRE:")
    print("   ❌ started_timestamp = int(started_at.timestamp() * 1000)")
    print("   ✅ started_timestamp = int(started_at.replace(tzinfo=timezone.utc).timestamp() * 1000)")
    print()
    print("4. Importare timezone se non già presente:")
    print("   from datetime import datetime, timezone")
    print()
    print("MOTIVO: I datetime naive dal database sono in UTC, ma .timestamp()")
    print("li interpreta come ora locale, causando errori di fuso orario.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python fix_timestamp_conversion.py <bot_id>")
        sys.exit(1)
        
    bot_id = sys.argv[1]
    demonstrate_timestamp_issue(bot_id)
    show_fix_recommendation()