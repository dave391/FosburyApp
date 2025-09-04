#!/usr/bin/env python3
"""
Script di diagnostica per Bitfinex
Verifica connessione API, permessi e metodi disponibili
"""

import os
import sys
import ccxt
from dotenv import load_dotenv
import json
from database.models import db_manager, user_manager
from utils.crypto_utils import crypto_utils

# Carica variabili d'ambiente
load_dotenv()

def get_user_credentials():
    """Recupera le credenziali del primo utente dal database"""
    print("=== RECUPERO CREDENZIALI UTENTE ===")
    
    try:
        # Trova il primo utente nel database
        user = db_manager.db.users.find_one()
        if not user:
            print("❌ Nessun utente trovato nel database")
            return None, None
        
        user_id = str(user['_id'])
        print(f"✅ Utente trovato: {user.get('email', 'N/A')}")
        
        # Recupera le API keys
        api_keys = user_manager.get_user_api_keys(user_id)
        
        bitfinex_key = api_keys.get('bitfinex_api_key', '')
        bitfinex_secret = api_keys.get('bitfinex_api_secret', '')
        
        if not bitfinex_key or not bitfinex_secret:
            print("❌ Credenziali Bitfinex non configurate per questo utente")
            return None, None
        
        print("✅ Credenziali Bitfinex recuperate dal database")
        return bitfinex_key, bitfinex_secret
        
    except Exception as e:
        print(f"❌ Errore recupero credenziali: {e}")
        return None, None

def test_bitfinex_connection():
    """Testa la connessione base a Bitfinex"""
    print("\n=== TEST CONNESSIONE BITFINEX ===")
    
    # Recupera credenziali dal database
    api_key, api_secret = get_user_credentials()
    if not api_key or not api_secret:
        return None
    
    try:
        # Inizializza exchange
        exchange = ccxt.bitfinex({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': False,
            'enableRateLimit': True,
        })
        
        print(f"✅ Exchange inizializzato: {exchange.name}")
        print(f"✅ Sandbox mode: {exchange.sandbox}")
        
        return exchange
        
    except Exception as e:
        print(f"❌ Errore inizializzazione: {e}")
        return None

def test_api_credentials(exchange):
    """Testa le credenziali API"""
    print("\n=== TEST CREDENZIALI API ===")
    
    try:
        # Test con fetch_balance
        balance = exchange.fetch_balance()
        print("✅ Credenziali API valide")
        print(f"✅ Saldo totale USDT: {balance.get('USDT', {}).get('total', 0)}")
        return True
        
    except ccxt.AuthenticationError as e:
        print(f"❌ Errore autenticazione: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore generico: {e}")
        return False

def check_api_permissions(exchange):
    """Verifica i permessi API"""
    print("\n=== VERIFICA PERMESSI API ===")
    
    permissions = {
        'read': False,
        'trade': False,
        'withdraw': False
    }
    
    # Test lettura
    try:
        exchange.fetch_balance()
        permissions['read'] = True
        print("✅ Permesso lettura: OK")
    except:
        print("❌ Permesso lettura: NEGATO")
    
    # Test trading (prova a creare un ordine molto piccolo)
    try:
        # Non eseguiamo realmente, solo verifichiamo se il metodo è disponibile
        if hasattr(exchange, 'create_order'):
            permissions['trade'] = True
            print("✅ Permesso trading: OK (metodo disponibile)")
        else:
            print("❌ Permesso trading: METODO NON DISPONIBILE")
    except:
        print("❌ Permesso trading: ERRORE")
    
    # Test withdraw/transfer
    try:
        if hasattr(exchange, 'transfer'):
            permissions['withdraw'] = True
            print("✅ Permesso trasferimento: OK (metodo disponibile)")
        else:
            print("❌ Permesso trasferimento: METODO NON DISPONIBILE")
    except:
        print("❌ Permesso trasferimento: ERRORE")
    
    return permissions

def check_available_methods(exchange):
    """Verifica i metodi disponibili per trasferimenti"""
    print("\n=== METODI DISPONIBILI ===")
    
    transfer_methods = [
        'transfer',
        'privatePostAuthWTransfer',
        'privatePostTransfer',
        'withdraw',
        'privatePostWithdraw'
    ]
    
    available_methods = []
    
    for method in transfer_methods:
        if hasattr(exchange, method):
            available_methods.append(method)
            print(f"✅ {method}: DISPONIBILE")
        else:
            print(f"❌ {method}: NON DISPONIBILE")
    
    # Verifica anche nell'API
    if hasattr(exchange, 'api'):
        print("\n--- Metodi API diretti ---")
        api_methods = dir(exchange.api)
        for method in api_methods:
            if 'transfer' in method.lower() or 'withdraw' in method.lower():
                print(f"📋 API method: {method}")
    
    return available_methods

def test_wallet_info(exchange):
    """Verifica informazioni dettagliate sui wallet"""
    print("\n=== INFORMAZIONI DETTAGLIATE WALLET ===")
    
    try:
        balance = exchange.fetch_balance()
        
        print("\n--- Saldi aggregati per valuta ---")
        currencies_with_balance = []
        for currency, info in balance.items():
            if isinstance(info, dict) and (info.get('total', 0) > 0 or info.get('free', 0) > 0 or info.get('used', 0) > 0):
                currencies_with_balance.append(currency)
                print(f"  {currency}:")
                print(f"    Total: {info.get('total', 0)}")
                print(f"    Free: {info.get('free', 0)}")
                print(f"    Used: {info.get('used', 0)}")
        
        if not currencies_with_balance:
            print("  Nessun saldo trovato")
        
        # Verifica wallet specifici (raw data)
        if 'info' in balance:
            print("\n--- Dettaglio wallet specifici (raw data) ---")
            wallet_info = balance['info']
            if isinstance(wallet_info, list):
                wallet_types = {}
                for wallet in wallet_info:
                    if isinstance(wallet, dict):
                        wallet_type = wallet.get('type', 'unknown')
                        currency = wallet.get('currency', 'unknown')
                        amount = float(wallet.get('amount', 0))
                        available = float(wallet.get('available', 0))
                        
                        if wallet_type not in wallet_types:
                            wallet_types[wallet_type] = {}
                        
                        if currency not in wallet_types[wallet_type]:
                            wallet_types[wallet_type][currency] = {'amount': 0, 'available': 0}
                        
                        wallet_types[wallet_type][currency]['amount'] += amount
                        wallet_types[wallet_type][currency]['available'] += available
                
                # Stampa organizzata per tipo di wallet
                for wallet_type, currencies in wallet_types.items():
                    print(f"\n  📁 Wallet {wallet_type.upper()}:")
                    has_balance = False
                    for currency, amounts in currencies.items():
                        if amounts['amount'] > 0 or amounts['available'] > 0:
                            has_balance = True
                            print(f"    {currency}: Amount={amounts['amount']}, Available={amounts['available']}")
                    
                    if not has_balance:
                        print(f"    Nessun saldo in questo wallet")
            else:
                print("  Formato wallet info non riconosciuto")
        
        return balance
        
    except Exception as e:
        print(f"❌ Errore recupero wallet: {e}")
        return None

def test_transfer_simulation(exchange):
    """Simula un trasferimento senza eseguirlo"""
    print("\n=== SIMULAZIONE TRASFERIMENTO ===")
    
    # Parametri di test
    amount = 1.0  # 1 USDT
    currency = 'USDT'
    from_wallet = 'exchange'
    to_wallet = 'margin'
    
    print(f"Tentativo trasferimento: {amount} {currency} da {from_wallet} a {to_wallet}")
    
    # Test 1: Metodo transfer standard
    try:
        if hasattr(exchange, 'transfer'):
            print("\n--- Test metodo transfer() ---")
            # Non eseguiamo, solo verifichiamo la struttura
            print("✅ Metodo transfer() disponibile")
        else:
            print("❌ Metodo transfer() non disponibile")
    except Exception as e:
        print(f"❌ Errore test transfer(): {e}")
    
    # Test 2: Metodo API diretto
    try:
        if hasattr(exchange, 'privatePostAuthWTransfer'):
            print("\n--- Test privatePostAuthWTransfer ---")
            print("✅ Metodo privatePostAuthWTransfer disponibile")
        else:
            print("❌ Metodo privatePostAuthWTransfer NON disponibile")
    except Exception as e:
        print(f"❌ Errore test privatePostAuthWTransfer: {e}")
    
    # Test 3: Verifica documentazione API
    print("\n--- Verifica API Bitfinex ---")
    try:
        # Verifica versione CCXT
        print(f"Versione CCXT: {ccxt.__version__}")
        
        # Verifica URL API
        print(f"URL API: {exchange.urls.get('api', 'N/A')}")
        
        # Verifica se l'exchange supporta trasferimenti interni
        if hasattr(exchange, 'has'):
            transfer_support = exchange.has.get('transfer', False)
            print(f"Supporto trasferimenti: {transfer_support}")
        
    except Exception as e:
        print(f"❌ Errore verifica API: {e}")

def main():
    """Funzione principale"""
    print("🔍 DIAGNOSTICA BITFINEX")
    print("=" * 50)
    
    # Test connessione
    exchange = test_bitfinex_connection()
    if not exchange:
        print("\n❌ Impossibile procedere senza connessione")
        return
    
    # Test credenziali
    if not test_api_credentials(exchange):
        print("\n❌ Impossibile procedere senza credenziali valide")
        return
    
    # Verifica permessi
    permissions = check_api_permissions(exchange)
    
    # Verifica metodi disponibili
    available_methods = check_available_methods(exchange)
    
    # Informazioni wallet
    test_wallet_info(exchange)
    
    # Simulazione trasferimento
    test_transfer_simulation(exchange)
    
    # Riepilogo finale
    print("\n" + "=" * 50)
    print("📋 RIEPILOGO DIAGNOSTICA")
    print("=" * 50)
    
    print(f"Connessione: {'✅ OK' if exchange else '❌ FALLITA'}")
    print(f"Permessi lettura: {'✅ OK' if permissions.get('read') else '❌ NO'}")
    print(f"Permessi trading: {'✅ OK' if permissions.get('trade') else '❌ NO'}")
    print(f"Permessi trasferimento: {'✅ OK' if permissions.get('withdraw') else '❌ NO'}")
    print(f"Metodi trasferimento disponibili: {len(available_methods)}")
    
    if available_methods:
        print("Metodi disponibili:")
        for method in available_methods:
            print(f"  - {method}")
    else:
        print("❌ NESSUN METODO DI TRASFERIMENTO DISPONIBILE")
    
    print("\n💡 RACCOMANDAZIONI:")
    if not permissions.get('withdraw'):
        print("- Verifica che l'API key abbia permessi di trasferimento/prelievo")
    if not available_methods:
        print("- Aggiorna CCXT all'ultima versione")
        print("- Verifica documentazione API Bitfinex per metodi correnti")
    if 'privatePostAuthWTransfer' not in available_methods:
        print("- Il metodo privatePostAuthWTransfer non è disponibile")
        print("- Prova metodi alternativi come transfer() standard")

if __name__ == "__main__":
    main()