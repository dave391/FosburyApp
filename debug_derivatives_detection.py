#!/usr/bin/env python3
"""
Script per diagnosticare il rilevamento del balance derivatives su Bitfinex
"""

import ccxt
import os
from dotenv import load_dotenv
from database.models import UserManager, DatabaseManager
from utils.crypto_utils import CryptoUtils

# Carica variabili d'ambiente
load_dotenv()

def debug_derivatives_detection():
    """Debug specifico per il rilevamento del balance derivatives"""
    print("=== DEBUG RILEVAMENTO BALANCE DERIVATIVES ===")
    print(f"Versione CCXT: {ccxt.__version__}")
    print(f"Ambiente: {'RENDER' if os.getenv('RENDER') else 'LOCALE'}")
    
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
        
        if not api_keys:
            print("❌ API keys non trovate")
            return
        
        api_key = api_keys.get('bitfinex_api_key')
        api_secret = api_keys.get('bitfinex_api_secret')
        
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
        
        # Recupera balance completo
        print("\n--- Recupero Balance Completo ---")
        balance = exchange.fetch_balance()
        
        print(f"Chiavi principali del balance: {list(balance.keys())}")
        
        # Analizza struttura balance
        print("\n--- Analisi Struttura Balance ---")
        
        # Verifica presenza di 'info'
        if 'info' in balance:
            info = balance['info']
            print(f"Tipo di 'info': {type(info)}")
            
            if isinstance(info, list):
                print(f"Numero di elementi in 'info': {len(info)}")
                
                # Analizza primi elementi
                for i, item in enumerate(info[:5]):
                    print(f"Elemento {i}: {item}")
                    
                    # Cerca USTF0 specificamente
                    if isinstance(item, list) and len(item) >= 2:
                        wallet_type = item[0] if len(item) > 0 else ''
                        currency = item[1] if len(item) > 1 else ''
                        amount = item[2] if len(item) > 2 else '0'
                        
                        if currency == 'USTF0':
                            print(f"🎯 TROVATO USTF0: wallet={wallet_type}, currency={currency}, amount={amount}")
                    elif isinstance(item, dict):
                        currency = item.get('currency', item.get('CURRENCY', ''))
                        if currency == 'USTF0':
                            print(f"🎯 TROVATO USTF0 (dict): {item}")
                
                # Cerca tutti gli elementi USTF0 (sia array che dict)
                ustf0_items = []
                for item in info:
                    if isinstance(item, list) and len(item) >= 2 and item[1] == 'USTF0':
                        ustf0_items.append(item)
                    elif isinstance(item, dict) and item.get('currency', item.get('CURRENCY', '')) == 'USTF0':
                        ustf0_items.append(item)
                
                print(f"\n--- Elementi USTF0 trovati: {len(ustf0_items)} ---")
                for i, item in enumerate(ustf0_items):
                    print(f"USTF0 #{i+1}: {item}")
                    
                    if isinstance(item, list):
                        # Formato array: [wallet_type, currency, amount, available, total, ...]
                        wallet_type = item[0] if len(item) > 0 else ''
                        currency = item[1] if len(item) > 1 else ''
                        amount = item[2] if len(item) > 2 else '0'
                        available = item[3] if len(item) > 3 else '0'
                        
                        print(f"  - Wallet: {wallet_type}")
                        print(f"  - Currency: {currency}")
                        print(f"  - Amount: {amount}")
                        print(f"  - Available: {available}")
                        
                        # Verifica se è derivatives
                        if wallet_type in ['derivatives', 'DERIVATIVES']:
                            print(f"  🎯 DERIVATIVES WALLET TROVATO!")
                            if float(amount) > 0 or float(available) > 0:
                                print(f"  💰 CON FONDI: amount={amount}, available={available}")
                            else:
                                print(f"  💸 SENZA FONDI: amount={amount}, available={available}")
                    
                    elif isinstance(item, dict):
                        # Formato dizionario
                        wallet_type = item.get('type', item.get('TYPE', ''))
                        amount = item.get('amount', item.get('AMOUNT', 0))
                        available = item.get('available', item.get('AVAILABLE', 0))
                        
                        print(f"  - Wallet: {wallet_type}")
                        print(f"  - Amount: {amount}")
                        print(f"  - Available: {available}")
                        
                        # Verifica se è derivatives
                        if wallet_type in ['derivatives', 'DERIVATIVES']:
                            print(f"  🎯 DERIVATIVES WALLET TROVATO!")
                            if float(amount) > 0 or float(available) > 0:
                                print(f"  💰 CON FONDI: amount={amount}, available={available}")
                            else:
                                print(f"  💸 SENZA FONDI: amount={amount}, available={available}")
            
            elif isinstance(info, dict):
                print(f"'info' è un dizionario con chiavi: {list(info.keys())}")
        
        # Verifica balance unificato
        print("\n--- Balance Unificato ---")
        if 'USTF0' in balance:
            ustf0_balance = balance['USTF0']
            print(f"USTF0 nel balance unificato: {ustf0_balance}")
        else:
            print("USTF0 non trovato nel balance unificato")
        
        # Test logica di rilevamento derivatives
        print("\n--- Test Logica Rilevamento Derivatives ---")
        
        derivatives_balance = 0
        
        if 'info' in balance and isinstance(balance['info'], list):
            for wallet in balance['info']:
                if isinstance(wallet, list) and len(wallet) >= 3:
                    # Formato array: [wallet_type, currency, amount, available, total, ...]
                    wallet_type = wallet[0] if len(wallet) > 0 else ''
                    currency = wallet[1] if len(wallet) > 1 else ''
                    amount = float(wallet[2]) if len(wallet) > 2 and wallet[2] else 0
                    
                    print(f"Controllo wallet (array): type={wallet_type}, currency={currency}, amount={amount}")
                    
                    # CORREZIONE: La logica corretta cerca USTF0 nel wallet 'margin', non 'derivatives'
                    if currency == 'USTF0' and wallet_type in ['margin', 'MARGIN']:
                        derivatives_balance += amount
                        print(f"  ✅ Aggiunto al derivatives_balance: {amount} (wallet: {wallet_type})")
                        
                elif isinstance(wallet, dict):
                    currency = wallet.get('currency', wallet.get('CURRENCY', ''))
                    wallet_type = wallet.get('type', wallet.get('TYPE', ''))
                    amount = float(wallet.get('amount', wallet.get('AMOUNT', 0)))
                    
                    print(f"Controllo wallet (dict): currency={currency}, type={wallet_type}, amount={amount}")
                    
                    # CORREZIONE: La logica corretta cerca USTF0 nel wallet 'margin', non 'derivatives'
                    if currency == 'USTF0' and wallet_type in ['margin', 'MARGIN']:
                        derivatives_balance += amount
                        print(f"  ✅ Aggiunto al derivatives_balance: {amount} (wallet: {wallet_type})")
        
        print(f"\n🎯 DERIVATIVES BALANCE FINALE: {derivatives_balance}")
        
        if derivatives_balance > 0:
            print("✅ DERIVATIVES BALANCE RILEVATO CORRETTAMENTE")
        else:
            print("❌ DERIVATIVES BALANCE NON RILEVATO")
        
        # Verifica anche altri wallet types
        print("\n--- Tutti i Wallet Types per USTF0 ---")
        if 'info' in balance and isinstance(balance['info'], list):
            ustf0_wallets = {}
            for wallet in balance['info']:
                if isinstance(wallet, list) and len(wallet) >= 3:
                    # Formato array: [wallet_type, currency, amount, available, total, ...]
                    wallet_type = wallet[0] if len(wallet) > 0 else ''
                    currency = wallet[1] if len(wallet) > 1 else ''
                    amount = float(wallet[2]) if len(wallet) > 2 and wallet[2] else 0
                    
                    if currency == 'USTF0':
                        ustf0_wallets[wallet_type] = amount
                        
                elif isinstance(wallet, dict):
                    currency = wallet.get('currency', wallet.get('CURRENCY', ''))
                    if currency == 'USTF0':
                        wallet_type = wallet.get('type', wallet.get('TYPE', ''))
                        amount = float(wallet.get('amount', wallet.get('AMOUNT', 0)))
                        ustf0_wallets[wallet_type] = amount
            
            print(f"Tutti i wallet USTF0: {ustf0_wallets}")
            
            # Verifica se derivatives è presente ma con nome diverso
            for wallet_type, amount in ustf0_wallets.items():
                if 'deriv' in wallet_type.lower() or 'future' in wallet_type.lower():
                    print(f"🔍 Possibile wallet derivatives con nome diverso: {wallet_type} = {amount}")
        
        print("\n=== FINE DEBUG ===")
        
    except Exception as e:
        print(f"❌ Errore durante il debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_derivatives_detection()