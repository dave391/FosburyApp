#!/usr/bin/env python3
"""
Test per verificare che la logica corretta di lettura dal campo 'info' 
funzioni come implementata nella funzione _get_exchange_balance corretta.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import user_manager
from trading.exchange_manager import ExchangeManager
import logging

# Configura logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_corrected_balance_logic():
    """Test della logica corretta per leggere i balance dal campo info"""
    
    user_id = "68b9d887c6a1151bcce4cd50"
    
    print("=" * 60)
    print("TEST LOGICA CORRETTA BALANCE DAL CAMPO INFO")
    print("=" * 60)
    
    try:
        # Recupera le API key
        api_keys = user_manager.get_user_api_keys(user_id)
        if not api_keys:
            print(f"❌ Nessuna API key trovata")
            return
        
        print(f"🔍 Struttura API keys: {api_keys}")
        print(f"🔍 Chiavi disponibili: {list(api_keys.keys())}")
        
        # Crea exchange manager e inizializza Bitfinex
        exchange_manager = ExchangeManager()
        
        # Le API key sono già decrittografate
        bitfinex_api_key = api_keys.get('bitfinex_api_key', '')
        bitfinex_secret = api_keys.get('bitfinex_secret', '')
        
        if not bitfinex_api_key or not bitfinex_secret:
            print(f"❌ API key Bitfinex mancanti")
            return
            
        # Inizializza exchange
        success = exchange_manager.initialize_exchange('bitfinex', bitfinex_api_key, bitfinex_secret)
        if not success:
            print(f"❌ Errore inizializzazione Bitfinex")
            return
            
        print(f"✅ Bitfinex inizializzato correttamente")
        
        # Test dei diversi balance types con la logica corretta
        exchange = exchange_manager.exchanges['bitfinex']
        
        # Test 1: derivatives (USTF0 dal margin wallet)
        print(f"\n--- Test derivatives balance ---")
        balance = exchange.fetch_balance({'type': 'margin'})
        ustf0_balance = 0
        
        if 'info' in balance and isinstance(balance['info'], list):
            for balance_entry in balance['info']:
                if len(balance_entry) >= 5:
                    entry_wallet = balance_entry[0]
                    entry_currency = balance_entry[1]
                    entry_total = float(balance_entry[4]) if balance_entry[4] else 0
                    
                    if entry_wallet == 'margin' and entry_currency == 'USTF0':
                        ustf0_balance = entry_total
                        print(f"✅ Trovato USTF0 nel margin: {ustf0_balance}")
                        break
        
        print(f"Derivatives balance (USTF0): {ustf0_balance}")
        
        # Test 2: tradable (USDT e UST dal margin wallet, escluso USTF0)
        print(f"\n--- Test tradable balance ---")
        balance = exchange.fetch_balance({'type': 'margin'})
        tradable_balance = 0
        currencies = ['USDT', 'UST']
        
        if 'info' in balance and isinstance(balance['info'], list):
            for balance_entry in balance['info']:
                if len(balance_entry) >= 5:
                    entry_wallet = balance_entry[0]
                    entry_currency = balance_entry[1]
                    entry_total = float(balance_entry[4]) if balance_entry[4] else 0
                    
                    if entry_wallet == 'margin' and entry_currency in currencies and entry_total > 0:
                        tradable_balance += entry_total
                        print(f"✅ Trovato {entry_currency} nel margin: {entry_total}")
        
        print(f"Tradable balance (USDT+UST): {tradable_balance}")
        
        # Test 3: total (tutti i wallet e tutte le valute)
        print(f"\n--- Test total balance ---")
        wallets = ['exchange', 'margin', 'funding']
        currencies = ['USTF0', 'USDT', 'UST']
        total_balance = 0
        
        for wallet in wallets:
            try:
                balance = exchange.fetch_balance({'type': wallet})
                wallet_balance = 0
                
                if 'info' in balance and isinstance(balance['info'], list):
                    for balance_entry in balance['info']:
                        if len(balance_entry) >= 5:
                            entry_wallet = balance_entry[0]
                            entry_currency = balance_entry[1]
                            entry_total = float(balance_entry[4]) if balance_entry[4] else 0
                            
                            if entry_wallet == wallet and entry_currency in currencies and entry_total != 0:
                                wallet_balance += entry_total
                                print(f"✅ Trovato {entry_currency} in {wallet}: {entry_total}")
                
                total_balance += wallet_balance
                print(f"Wallet {wallet} totale: {wallet_balance}")
                
            except Exception as e:
                print(f"⚠️  Errore wallet {wallet}: {e}")
        
        print(f"\nTotal balance (tutti i wallet): {total_balance}")
        
        print(f"\n🎉 TEST COMPLETATO!")
        print(f"📊 RISULTATI:")
        print(f"   - Derivatives (USTF0): {ustf0_balance}")
        print(f"   - Tradable (USDT+UST): {tradable_balance}")
        print(f"   - Total (tutto): {total_balance}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        logger.exception("Errore dettagliato")

if __name__ == "__main__":
    test_corrected_balance_logic()