#!/usr/bin/env python3
"""
Script per testare il rilevamento del balance derivatives su Render
"""

import ccxt
import os
from dotenv import load_dotenv
from database.models import UserManager, DatabaseManager
from utils.crypto_utils import CryptoUtils

# Carica variabili d'ambiente
load_dotenv()

def test_render_derivatives():
    """Testa il rilevamento derivatives su Render"""
    print("=== TEST DERIVATIVES SU RENDER ===")
    print(f"Versione CCXT: {ccxt.__version__}")
    print(f"Ambiente: {'RENDER' if 'RENDER' in os.environ else 'LOCALE'}")
    
    try:
        # Inizializza database
        db_manager = DatabaseManager()
        user_manager = UserManager(db_manager)
        
        # Recupera utente (assumendo che ce ne sia uno)
        user = user_manager.users.find_one()
        if not user:
            print("❌ Nessun utente trovato nel database")
            return
        print(f"✅ Utente trovato: {user.get('username', 'N/A')}")
        
        # Recupera API keys (già decriptate dal metodo)
        api_keys = user_manager.get_user_api_keys(str(user['_id']))
        if not api_keys:
            print("❌ API keys non trovate")
            return
        
        # Le chiavi sono già decriptate dal metodo get_user_api_keys
        bitfinex_api_key = api_keys.get('bitfinex_api_key', '')
        bitfinex_api_secret = api_keys.get('bitfinex_api_secret', '')
        
        if not bitfinex_api_key or not bitfinex_api_secret:
            print("❌ Credenziali Bitfinex non trovate")
            return
        
        print("✅ Credenziali Bitfinex recuperate")
        
        # Inizializza exchange Bitfinex
        exchange = ccxt.bitfinex({
            'apiKey': bitfinex_api_key,
            'secret': bitfinex_api_secret,
            'sandbox': False,
            'enableRateLimit': True,
        })
        
        print("✅ Exchange Bitfinex inizializzato")
        
        # Test 1: Balance margin completo
        print("\n--- TEST 1: Balance Margin Completo ---")
        margin_balance = exchange.fetch_balance({'type': 'margin'})
        
        print(f"Chiavi balance: {list(margin_balance.keys())}")
        print(f"Tipo 'info': {type(margin_balance.get('info', 'N/A'))}")
        
        if 'info' in margin_balance and isinstance(margin_balance['info'], list):
            print(f"Elementi in 'info': {len(margin_balance['info'])}")
            
            # Cerca USTF0
            ustf0_found = False
            for item in margin_balance['info']:
                if isinstance(item, list) and len(item) >= 2 and item[1] == 'USTF0':
                    print(f"✅ USTF0 trovato: {item}")
                    ustf0_found = True
                    break
            
            if not ustf0_found:
                print("❌ USTF0 non trovato in margin balance")
        
        # Test 2: Logica di rilevamento derivatives (come nel codice originale)
        print("\n--- TEST 2: Logica Rilevamento Derivatives ---")
        ustf0_balance = 0
        
        if 'info' in margin_balance and isinstance(margin_balance['info'], list):
            for balance_entry in margin_balance['info']:
                if len(balance_entry) >= 5:
                    entry_wallet = balance_entry[0]
                    entry_currency = balance_entry[1]
                    entry_total = float(balance_entry[4]) if balance_entry[4] else 0
                    
                    print(f"Controllo: wallet={entry_wallet}, currency={entry_currency}, total={entry_total}")
                    
                    # Cerca USTF0 nel wallet margin (logica corretta)
                    if entry_wallet == 'margin' and entry_currency == 'USTF0' and entry_total > 0:
                        ustf0_balance = entry_total
                        print(f"✅ USTF0 RILEVATO! Balance: {ustf0_balance}")
                        break
        
        print(f"\n🎯 DERIVATIVES BALANCE FINALE: {ustf0_balance}")
        
        if ustf0_balance > 0:
            print("✅ DERIVATIVES BALANCE RILEVATO CORRETTAMENTE")
        else:
            print("❌ DERIVATIVES BALANCE NON RILEVATO")
        
        # Test 3: Verifica tutti i wallet types
        print("\n--- TEST 3: Tutti i Wallet Types ---")
        if 'info' in margin_balance and isinstance(margin_balance['info'], list):
            wallet_types = set()
            for item in margin_balance['info']:
                if isinstance(item, list) and len(item) >= 1:
                    wallet_types.add(item[0])
            
            print(f"Wallet types trovati: {sorted(wallet_types)}")
        
        # Test 4: Balance unificato
        print("\n--- TEST 4: Balance Unificato ---")
        if 'USTF0' in margin_balance:
            print(f"USTF0 nel balance unificato: {margin_balance['USTF0']}")
        else:
            print("USTF0 non presente nel balance unificato")
        
        print("\n=== FINE TEST ===")
        
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_render_derivatives()