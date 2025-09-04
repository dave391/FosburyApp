#!/usr/bin/env python3
"""
Script di debug per analizzare la struttura del balance Bitfinex su Render
Questo script può essere eseguito come cronjob su Render per diagnosticare
perché il balance derivatives non viene rilevato correttamente.
"""

import os
import sys
import ccxt
import logging
from datetime import datetime

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import db_manager, user_manager
from utils.crypto_utils import crypto_utils

def get_user_credentials():
    """Recupera le credenziali del primo utente dal database"""
    try:
        db_manager.connect()
        
        # Trova il primo utente direttamente dalla collezione
        user = user_manager.users.find_one()
        if not user:
            print("❌ Nessun utente trovato nel database")
            return None, None
        
        print(f"✅ Utente trovato: {user['_id']}")
        
        # Recupera le API keys di Bitfinex (già decriptate dal metodo)
        api_keys = user_manager.get_user_api_keys(str(user['_id']))
        
        if 'bitfinex_api_key' not in api_keys or 'bitfinex_api_secret' not in api_keys:
            print("❌ API keys Bitfinex non trovate")
            return None, None
        
        # Le chiavi sono già decriptate dal metodo get_user_api_keys
        api_key = api_keys['bitfinex_api_key']
        api_secret = api_keys['bitfinex_api_secret']
        
        if not api_key or not api_secret:
            print("❌ API keys Bitfinex vuote")
            return None, None
        
        return api_key, api_secret
        
    except Exception as e:
        print(f"❌ Errore recupero credenziali: {e}")
        return None, None

def analyze_bitfinex_balance():
    """Analizza la struttura del balance Bitfinex"""
    print(f"🔍 DEBUG RENDER: Analisi struttura balance Bitfinex")
    print(f"Timestamp: {datetime.now()}")
    print(f"Versione CCXT: {ccxt.__version__}")
    print(f"Python version: {sys.version}")
    print(f"Environment: {'RENDER' if 'RENDER' in os.environ else 'LOCAL'}")
    
    # Recupera credenziali
    api_key, api_secret = get_user_credentials()
    if not api_key or not api_secret:
        print("❌ Impossibile recuperare le credenziali")
        return
    
    try:
        # Inizializza Bitfinex
        exchange = ccxt.bitfinex({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': False,
            'enableRateLimit': True,
        })
        
        print("✅ Connessione Bitfinex stabilita")
        
        # Test balance per ogni wallet
        wallets = ['exchange', 'margin', 'funding']
        
        print("\n=== ANALISI STRUTTURA BALANCE BITFINEX ===")
        
        for wallet_type in wallets:
            try:
                print(f"\n--- WALLET: {wallet_type.upper()} ---")
                
                # Fetch balance per il wallet specifico
                balance = exchange.fetch_balance({'type': wallet_type})
                
                print(f"Chiavi principali del balance: {list(balance.keys())}")
                
                # Analizza la struttura 'info'
                if 'info' in balance:
                    info = balance['info']
                    print(f"Tipo di 'info': {type(info)}")
                    
                    if isinstance(info, list):
                        print(f"Numero di elementi in 'info': {len(info)}")
                        for i, item in enumerate(info):
                            print(f"  Elemento {i}: {item}")
                            if isinstance(item, list) and len(item) >= 5:
                                wallet_name = item[0] if len(item) > 0 else 'N/A'
                                currency = item[1] if len(item) > 1 else 'N/A'
                                balance_val = item[4] if len(item) > 4 else 'N/A'
                                print(f"    Wallet: {wallet_name}, Currency: {currency}, Balance: {balance_val}")
                                
                                # Controlla se è USTF0
                                if currency == 'USTF0':
                                    print(f"  ✅ USTF0 trovato: Wallet={wallet_name}, Balance={balance_val}")
                    
                    elif isinstance(info, dict):
                        print(f"Info è un dizionario con chiavi: {list(info.keys())}")
                
                # Controlla valute standard
                print(f"\nValute standard nel wallet {wallet_type}:")
                for currency in ['USDT', 'UST', 'USTF0']:
                    if currency in balance:
                        curr_data = balance[currency]
                        if isinstance(curr_data, dict):
                            free = curr_data.get('free', 0)
                            total = curr_data.get('total', 0)
                            print(f"  {currency}: free={free}, total={total}")
                        else:
                            print(f"  {currency}: {curr_data}")
                    else:
                        print(f"  {currency}: NON PRESENTE")
                        
            except Exception as e:
                print(f"❌ Errore wallet {wallet_type}: {e}")
        
        # Test specifico per USTF0 (replica logica originale)
        print("\n=== TEST RILEVAMENTO BALANCE DERIVATIVES ===")
        try:
            margin_balance = exchange.fetch_balance({'type': 'margin'})
            print("Logica di rilevamento USTF0 (come nel codice originale):")
            
            if 'info' in margin_balance and isinstance(margin_balance['info'], list):
                print(f"✅ 'info' è una lista con {len(margin_balance['info'])} elementi")
                
                ustf0_balance = 0
                for item in margin_balance['info']:
                    if isinstance(item, list) and len(item) >= 5:
                        wallet_type = item[0]
                        currency = item[1]
                        total_balance = float(item[4]) if item[4] else 0
                        
                        print(f"  Elemento: {item}")
                        print(f"    Wallet: {wallet_type}, Currency: {currency}, Total: {total_balance}")
                        
                        if currency == 'USTF0' and wallet_type == 'margin':
                            ustf0_balance = total_balance
                            print(f"    ✅ USTF0 TROVATO! Balance: {ustf0_balance}")
                            break
                
                print(f"\nRisultato finale: USTF0 balance = {ustf0_balance}")
                
            else:
                print("❌ 'info' non è una lista o non esiste")
                
        except Exception as e:
            print(f"❌ Errore test USTF0: {e}")
        
        print("\n=== RIEPILOGO ===")
        print(f"Environment: {'RENDER' if 'RENDER' in os.environ else 'LOCAL'}")
        print(f"CCXT Version: {ccxt.__version__}")
        
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_bitfinex_balance()