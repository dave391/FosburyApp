#!/usr/bin/env python3
"""
Script per testare i metodi di trasferimento disponibili in CCXT per Bitfinex
"""

import ccxt
import os
from dotenv import load_dotenv
from database.models import UserManager, DatabaseManager
from utils.crypto_utils import CryptoUtils

# Carica variabili d'ambiente
load_dotenv()

def test_bitfinex_transfer_methods():
    """Testa i metodi di trasferimento disponibili per Bitfinex"""
    print("=== TEST METODI TRASFERIMENTO BITFINEX ===")
    print(f"Versione CCXT: {ccxt.__version__}")
    
    try:
        # Inizializza database manager e user manager
        db_manager = DatabaseManager()
        user_manager = UserManager(db_manager)
        user = user_manager.users.find_one()
        
        if not user:
            print("❌ Nessun utente trovato nel database")
            return
        
        print(f"✅ Utente trovato: {user.get('username', 'N/A')}")
        
        # Recupera API keys
        api_keys = user_manager.get_user_api_keys(str(user['_id']))
        
        if not api_keys or not api_keys.get('bitfinex'):
            print("❌ API keys Bitfinex non trovate")
            return
        
        bitfinex_keys = api_keys['bitfinex']
        api_key = bitfinex_keys.get('api_key')
        api_secret = bitfinex_keys.get('api_secret')
        
        if not api_key or not api_secret:
            print("❌ Credenziali Bitfinex incomplete")
            return
        
        print("✅ Credenziali Bitfinex recuperate")
        
        # Inizializza exchange Bitfinex
        exchange = ccxt.bitfinex({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': False,
            'enableRateLimit': True,
            'timeout': 30000
        })
        
        print("✅ Exchange Bitfinex inizializzato")
        
        # Test 1: Verifica metodo transfer() unificato
        print("\n--- Test 1: Metodo transfer() unificato ---")
        if hasattr(exchange, 'transfer'):
            print("✅ Metodo transfer() disponibile")
            
            # Verifica se supporta trasferimenti interni
            if hasattr(exchange, 'has') and exchange.has.get('transfer', False):
                print("✅ Trasferimenti supportati secondo exchange.has")
            else:
                print("⚠️  Trasferimenti non indicati come supportati in exchange.has")
        else:
            print("❌ Metodo transfer() NON disponibile")
        
        # Test 2: Verifica metodo privatePostAuthWTransfer
        print("\n--- Test 2: Metodo privatePostAuthWTransfer ---")
        if hasattr(exchange, 'privatePostAuthWTransfer'):
            print("✅ Metodo privatePostAuthWTransfer disponibile")
        else:
            print("❌ Metodo privatePostAuthWTransfer NON disponibile")
        
        # Test 3: Verifica altri metodi di trasferimento
        print("\n--- Test 3: Altri metodi di trasferimento ---")
        transfer_methods = [
            'privatePostAuthTransfer',
            'privatePostTransfer', 
            'privatePostWalletTransfer',
            'privatePostAuthWalletTransfer'
        ]
        
        for method in transfer_methods:
            if hasattr(exchange, method):
                print(f"✅ Metodo {method} disponibile")
            else:
                print(f"❌ Metodo {method} NON disponibile")
        
        # Test 4: Verifica API endpoints disponibili
        print("\n--- Test 4: API endpoints disponibili ---")
        if hasattr(exchange, 'api'):
            private_endpoints = exchange.api.get('private', {})
            post_endpoints = private_endpoints.get('post', [])
            
            print(f"Endpoints POST privati disponibili: {len(post_endpoints)}")
            
            # Cerca endpoints relativi a trasferimenti
            transfer_endpoints = [ep for ep in post_endpoints if 'transfer' in ep.lower()]
            if transfer_endpoints:
                print(f"Endpoints di trasferimento trovati: {transfer_endpoints}")
            else:
                print("❌ Nessun endpoint di trasferimento trovato")
        
        # Test 5: Verifica documentazione API
        print("\n--- Test 5: Informazioni API ---")
        print(f"URL API: {exchange.urls.get('api', 'N/A')}")
        print(f"Versione API: {exchange.version if hasattr(exchange, 'version') else 'N/A'}")
        
        # Test 6: Test simulazione trasferimento con metodo unificato
        print("\n--- Test 6: Simulazione trasferimento unificato ---")
        if hasattr(exchange, 'transfer'):
            try:
                # Non eseguiamo il trasferimento, solo verifichiamo i parametri
                print("Parametri richiesti per transfer():")
                print("- code: codice valuta (es. 'USDT')")
                print("- amount: importo da trasferire")
                print("- fromAccount: wallet di origine (es. 'exchange')")
                print("- toAccount: wallet di destinazione (es. 'margin')")
                print("✅ Metodo transfer() sembra utilizzabile")
            except Exception as e:
                print(f"⚠️  Errore nella verifica del metodo transfer(): {e}")
        
        print("\n=== FINE TEST ===")
        
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bitfinex_transfer_methods()