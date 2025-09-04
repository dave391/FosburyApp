#!/usr/bin/env python3
"""
Script di debug per analizzare la struttura del balance di Bitfinex
tra ambiente locale e Render
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ccxt
import json
from database.models import db_manager, user_manager
from utils.crypto_utils import crypto_utils

def get_user_credentials():
    """Recupera le credenziali dell'utente dal database"""
    try:
        # Connetti al database
        db_manager.connect()
        
        # Trova il primo utente direttamente dalla collezione
        user = user_manager.users.find_one()
        if not user:
            print("❌ Nessun utente trovato nel database")
            return None, None
        print(f"✅ Utente trovato: {user['_id']}")
        
        # Recupera e decripta le credenziali Bitfinex
        bitfinex_api_key = crypto_utils.decrypt_api_key(user['bitfinex_api_key'])
        bitfinex_api_secret = crypto_utils.decrypt_api_key(user['bitfinex_api_secret'])
        
        return bitfinex_api_key, bitfinex_api_secret
        
    except Exception as e:
        print(f"❌ Errore recupero credenziali: {e}")
        return None, None

def analyze_balance_structure(exchange):
    """Analizza la struttura dettagliata del balance di Bitfinex"""
    print("\n=== ANALISI STRUTTURA BALANCE BITFINEX ===")
    
    wallets = ['exchange', 'margin', 'funding']
    
    for wallet in wallets:
        print(f"\n--- WALLET: {wallet.upper()} ---")
        try:
            balance = exchange.fetch_balance({'type': wallet})
            
            print(f"Chiavi principali del balance: {list(balance.keys())}")
            
            # Analizza la struttura 'info'
            if 'info' in balance:
                print(f"Tipo di 'info': {type(balance['info'])}")
                
                if isinstance(balance['info'], list):
                    print(f"Numero di elementi in 'info': {len(balance['info'])}")
                    
                    # Mostra i primi 3 elementi per capire la struttura
                    for i, entry in enumerate(balance['info'][:3]):
                        print(f"  Elemento {i}: {entry}")
                        if len(entry) >= 5:
                            print(f"    Wallet: {entry[0]}, Currency: {entry[1]}, Balance: {entry[4]}")
                    
                    # Cerca specificamente USTF0
                    ustf0_found = False
                    for entry in balance['info']:
                        if len(entry) >= 5 and entry[1] == 'USTF0':
                            print(f"  ✅ USTF0 trovato: Wallet={entry[0]}, Balance={entry[4]}")
                            ustf0_found = True
                    
                    if not ustf0_found:
                        print(f"  ❌ USTF0 non trovato in wallet {wallet}")
                        
                elif isinstance(balance['info'], dict):
                    print(f"Info è un dict con chiavi: {list(balance['info'].keys())}")
                else:
                    print(f"Info ha un formato inaspettato: {balance['info']}")
            
            # Analizza anche le valute standard
            currencies = ['USDT', 'UST', 'USTF0']
            print(f"\nValute standard nel wallet {wallet}:")
            for currency in currencies:
                if currency in balance:
                    print(f"  {currency}: free={balance[currency].get('free', 0)}, total={balance[currency].get('total', 0)}")
                else:
                    print(f"  {currency}: NON PRESENTE")
                    
        except Exception as e:
            print(f"❌ Errore analisi wallet {wallet}: {e}")

def test_derivatives_balance_detection(exchange):
    """Testa specificamente la logica di rilevamento del balance derivatives"""
    print("\n=== TEST RILEVAMENTO BALANCE DERIVATIVES ===")
    
    try:
        balance = exchange.fetch_balance({'type': 'margin'})
        ustf0_balance = 0
        
        print("Logica di rilevamento USTF0 (come nel codice originale):")
        
        # Replica la logica esatta del codice originale
        if 'info' in balance and isinstance(balance['info'], list):
            print(f"✅ 'info' è una lista con {len(balance['info'])} elementi")
            
            for i, balance_entry in enumerate(balance['info']):
                print(f"  Elemento {i}: {balance_entry}")
                
                if len(balance_entry) >= 5:
                    entry_wallet = balance_entry[0]
                    entry_currency = balance_entry[1]
                    entry_total = float(balance_entry[4]) if balance_entry[4] else 0
                    
                    print(f"    Wallet: {entry_wallet}, Currency: {entry_currency}, Total: {entry_total}")
                    
                    # Cerca USTF0 nel wallet margin
                    if entry_wallet == 'margin' and entry_currency == 'USTF0' and entry_total > 0:
                        ustf0_balance = entry_total
                        print(f"    ✅ USTF0 TROVATO! Balance: {ustf0_balance}")
                        break
                else:
                    print(f"    ❌ Elemento troppo corto: {len(balance_entry)} elementi")
        else:
            print("❌ 'info' non è una lista o non esiste")
            
        print(f"\nRisultato finale: USTF0 balance = {ustf0_balance}")
        return ustf0_balance
        
    except Exception as e:
        print(f"❌ Errore test derivatives balance: {e}")
        return 0

def main():
    print("🔍 DEBUG: Analisi struttura balance Bitfinex")
    print(f"Versione CCXT: {ccxt.__version__}")
    
    # Recupera credenziali
    api_key, api_secret = get_user_credentials()
    if not api_key or not api_secret:
        print("❌ Impossibile recuperare le credenziali")
        return
    
    # Inizializza Bitfinex
    try:
        exchange = ccxt.bitfinex({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': False,
            'enableRateLimit': True,
            'timeout': 30000
        })
        
        exchange.load_markets()
        print("✅ Connessione Bitfinex stabilita")
        
    except Exception as e:
        print(f"❌ Errore connessione Bitfinex: {e}")
        return
    
    # Esegui analisi
    analyze_balance_structure(exchange)
    derivatives_balance = test_derivatives_balance_detection(exchange)
    
    print(f"\n=== RIEPILOGO ===")
    print(f"Balance derivatives rilevato: {derivatives_balance} USTF0")
    
    if derivatives_balance > 0:
        print("✅ Il sistema dovrebbe funzionare correttamente")
    else:
        print("❌ Il sistema non rileva fondi derivatives - questo spiega il problema su Render")
        print("\n💡 POSSIBILI CAUSE:")
        print("- Account Bitfinex vuoto o fondi in wallet diversi")
        print("- Credenziali API diverse tra locale e Render")
        print("- Struttura API response diversa tra ambienti")
        print("- Permessi API insufficienti")

if __name__ == "__main__":
    main()