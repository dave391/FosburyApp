#!/usr/bin/env python3
"""
Test per verificare che la funzione _get_exchange_balance dell'opener
rilevi correttamente i fondi Bitfinex dopo le correzioni implementate.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import user_manager
from trading.opener import TradingOpener
import logging

# Configura logging per vedere i dettagli
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_opener_balance():
    """Test della funzione _get_exchange_balance dell'opener"""
    
    # ID utente dal database
    user_id = "68b9d887c6a1151bcce4cd50"
    
    print("=" * 60)
    print("TEST FUNZIONE _get_exchange_balance DELL'OPENER")
    print("=" * 60)
    
    try:
        # Recupera le API key dell'utente
        api_keys = user_manager.get_user_api_keys(user_id)
        if not api_keys:
            print(f"❌ Nessuna API key trovata per l'utente {user_id}")
            return
        
        print(f"✅ API keys recuperate per utente {user_id}")
        print(f"🔍 Struttura API keys: {api_keys}")
        
        # Crea un'istanza dell'opener
        opener = TradingOpener()
        
        # Inizializza l'exchange manager con le API key dell'utente
        bitfinex_keys = api_keys.get('bitfinex', {})
        api_key = bitfinex_keys.get('api_key', '')
        api_secret = bitfinex_keys.get('api_secret', '')
        
        if not api_key or not api_secret:
            print(f"❌ API key o secret mancanti per Bitfinex")
            return
            
        opener.exchange_manager.initialize_exchange('bitfinex', api_key, api_secret)
        
        # Test dei diversi tipi di balance
        balance_types = ['derivatives', 'tradable', 'total']
        
        for balance_type in balance_types:
            print(f"\n--- Test balance_type: {balance_type} ---")
            
            try:
                balance = opener._get_exchange_balance('bitfinex', balance_type)
                print(f"✅ {balance_type} balance: {balance} USDT")
                
                if balance > 0:
                    print(f"🎉 SUCCESSO: Rilevato balance {balance_type} = {balance} USDT")
                else:
                    print(f"⚠️  Balance {balance_type} = 0 (potrebbe essere corretto)")
                    
            except Exception as e:
                print(f"❌ Errore nel test {balance_type}: {e}")
                logger.exception(f"Errore dettagliato per {balance_type}")
    
    except Exception as e:
        print(f"❌ Errore generale nel test: {e}")
        logger.exception("Errore dettagliato generale")

if __name__ == "__main__":
    test_opener_balance()