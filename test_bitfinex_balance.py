#!/usr/bin/env python3
"""
Script di test per analizzare i metodi di recupero balance di Bitfinex
Questo script testa diversi approcci per recuperare i saldi dai wallet Bitfinex
per identificare il problema nell'opener.
"""

import os
import sys
import json
from datetime import datetime

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading.exchange_manager import ExchangeManager
from database.models import user_manager

def print_separator(title):
    """Stampa un separatore con titolo"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_json(data, title=""):
    """Stampa dati JSON in formato leggibile"""
    if title:
        print(f"\n--- {title} ---")
    print(json.dumps(data, indent=2, default=str))

def test_fetch_balance_methods():
    """Testa diversi metodi fetch_balance"""
    print_separator("TEST METODI FETCH_BALANCE")
    
    try:
        # Recupera le API key dell'utente dal database
        user_id = "68b9d887c6a1151bcce4cd50"
        api_keys = user_manager.get_user_api_keys(user_id)
        
        # Inizializza l'exchange manager
        exchange_manager = ExchangeManager()
        
        # Inizializza Bitfinex con le API key dell'utente
        if 'bitfinex_api_key' in api_keys and 'bitfinex_api_secret' in api_keys:
            success = exchange_manager.initialize_exchange(
                'bitfinex', 
                api_keys['bitfinex_api_key'], 
                api_keys['bitfinex_api_secret']
            )
            if success:
                print("Bitfinex inizializzato con successo")
            else:
                print("ERRORE: Inizializzazione Bitfinex fallita")
                return
        else:
            print("ERRORE: API key Bitfinex non trovate per l'utente")
            return
        
        # Ottieni il riferimento all'exchange Bitfinex inizializzato
        bitfinex = exchange_manager.exchanges['bitfinex']
        print(f"Exchange Bitfinex inizializzato: {type(bitfinex)}")
        
        # Test 1: fetch_balance() standard
        print_separator("1. FETCH_BALANCE STANDARD")
        try:
            balance_standard = bitfinex.fetch_balance()
            print_json(balance_standard, "Balance Standard")
            
            # Analizza la struttura
            print(f"\nChiavi principali: {list(balance_standard.keys())}")
            if 'info' in balance_standard:
                print(f"Tipo 'info': {type(balance_standard['info'])}")
                if isinstance(balance_standard['info'], list):
                    print(f"Numero elementi in 'info': {len(balance_standard['info'])}")
                    if balance_standard['info']:
                        print(f"Primo elemento 'info': {balance_standard['info'][0]}")
                        
        except Exception as e:
            print(f"Errore fetch_balance standard: {e}")
        
        # Test 2: fetch_balance per wallet specifici
        wallets = ['exchange', 'margin', 'funding']
        for wallet in wallets:
            print_separator(f"2. FETCH_BALANCE WALLET: {wallet.upper()}")
            try:
                balance_wallet = bitfinex.fetch_balance({'type': wallet})
                print_json(balance_wallet, f"Balance {wallet}")
                
                # Cerca valute USDT
                currencies = ['USDT', 'USTF0', 'UST']
                for currency in currencies:
                    if currency in balance_wallet:
                        print(f"\n{currency} trovato in {wallet}:")
                        print(f"  Free: {balance_wallet[currency].get('free', 0)}")
                        print(f"  Used: {balance_wallet[currency].get('used', 0)}")
                        print(f"  Total: {balance_wallet[currency].get('total', 0)}")
                        
            except Exception as e:
                print(f"Errore fetch_balance {wallet}: {e}")
        
        # Test 3: Analisi dettagliata della risposta 'info'
        print_separator("3. ANALISI DETTAGLIATA RISPOSTA INFO")
        try:
            balance_full = bitfinex.fetch_balance()
            if 'info' in balance_full and isinstance(balance_full['info'], list):
                print(f"Analizzando {len(balance_full['info'])} elementi...")
                
                for i, entry in enumerate(balance_full['info']):
                    if isinstance(entry, list) and len(entry) >= 5:
                        wallet_type = entry[0]
                        currency = entry[1]
                        balance_type = entry[2] if len(entry) > 2 else "N/A"
                        available = entry[4] if len(entry) > 4 else 0
                        
                        # Filtra solo USDT-related e wallet margin
                        if (wallet_type == 'margin' or 
                            currency in ['USDT', 'USTF0', 'UST'] or 
                            float(available) > 0):
                            print(f"Entry {i}: {entry}")
                            print(f"  Wallet: {wallet_type}, Currency: {currency}")
                            print(f"  Type: {balance_type}, Available: {available}")
                            
        except Exception as e:
            print(f"Errore analisi info: {e}")
            
    except Exception as e:
        print(f"Errore inizializzazione exchange: {e}")

def test_private_api_methods():
    """Testa metodi API privati specifici"""
    print_separator("TEST METODI API PRIVATI")
    
    try:
        # Recupera le API key dell'utente dal database
        user_id = "68b9d887c6a1151bcce4cd50"
        api_keys = user_manager.get_user_api_keys(user_id)
        
        exchange_manager = ExchangeManager()
        
        # Inizializza Bitfinex con le API key dell'utente
        if 'bitfinex_api_key' in api_keys and 'bitfinex_api_secret' in api_keys:
            success = exchange_manager.initialize_exchange(
                'bitfinex', 
                api_keys['bitfinex_api_key'], 
                api_keys['bitfinex_api_secret']
            )
            if not success:
                print("ERRORE: Inizializzazione Bitfinex fallita")
                return
        else:
            print("ERRORE: API key Bitfinex non trovate per l'utente")
            return
        
        bitfinex = exchange_manager.exchanges['bitfinex']
        
        # Test metodi privati disponibili
        private_methods = [method for method in dir(bitfinex) if method.startswith('private')]
        print(f"Metodi privati disponibili: {len(private_methods)}")
        
        # Cerca metodi balance specifici
        balance_methods = [method for method in private_methods if 'balance' in method.lower() or 'wallet' in method.lower()]
        print(f"Metodi balance/wallet: {balance_methods}")
        
        # Test metodo privatePostAuthRWallets se disponibile
        if hasattr(bitfinex, 'privatePostAuthRWallets'):
            print_separator("TEST privatePostAuthRWallets")
            try:
                wallets_response = bitfinex.privatePostAuthRWallets()
                print_json(wallets_response, "Wallets Response")
            except Exception as e:
                print(f"Errore privatePostAuthRWallets: {e}")
                
    except Exception as e:
        print(f"Errore test API privati: {e}")

def test_manual_balance_calculation():
    """Testa calcolo manuale dei balance come nell'opener"""
    print_separator("TEST CALCOLO MANUALE BALANCE (COME OPENER)")
    
    try:
        # Recupera le API key dell'utente dal database
        user_id = "68b9d887c6a1151bcce4cd50"
        api_keys = user_manager.get_user_api_keys(user_id)
        
        exchange_manager = ExchangeManager()
        
        # Inizializza Bitfinex con le API key dell'utente
        if 'bitfinex_api_key' in api_keys and 'bitfinex_api_secret' in api_keys:
            success = exchange_manager.initialize_exchange(
                'bitfinex', 
                api_keys['bitfinex_api_key'], 
                api_keys['bitfinex_api_secret']
            )
            if not success:
                print("ERRORE: Inizializzazione Bitfinex fallita")
                return
        else:
            print("ERRORE: API key Bitfinex non trovate per l'utente")
            return
        
        bitfinex = exchange_manager.exchanges['bitfinex']
        
        wallets = ['exchange', 'margin', 'funding']
        currencies = ['USTF0', 'USDT', 'UST']
        distribution = {}
        
        print("Simulando logica _get_bitfinex_wallet_distribution...")
        
        for wallet in wallets:
            distribution[wallet] = {}
            print(f"\n--- Testando wallet: {wallet} ---")
            
            try:
                balance = bitfinex.fetch_balance({'type': wallet})
                print(f"Risposta fetch_balance per {wallet}:")
                print_json(balance)
                
                for currency in currencies:
                    if currency in balance and balance[currency]['free'] > 0:
                        distribution[wallet][currency] = balance[currency]['free']
                        print(f"✓ {currency}: {balance[currency]['free']}")
                    else:
                        distribution[wallet][currency] = 0
                        print(f"✗ {currency}: 0 (non trovato o zero)")
                        
            except Exception as e:
                print(f"Errore wallet {wallet}: {e}")
                for currency in currencies:
                    distribution[wallet][currency] = 0
        
        # Calcola totali
        wallet_totals = {}
        currency_totals = {}
        
        for wallet in wallets:
            wallet_totals[wallet] = sum(distribution[wallet].values())
            
        for currency in currencies:
            currency_totals[currency] = sum(distribution[wallet][currency] for wallet in wallets)
        
        distribution['totals'] = {
            'by_wallet': wallet_totals,
            'by_currency': currency_totals,
            'grand_total': sum(wallet_totals.values())
        }
        
        print_separator("RISULTATO FINALE DISTRIBUZIONE")
        print_json(distribution, "Distribuzione Completa")
        
        print(f"\nTOTALE RILEVATO: {distribution['totals']['grand_total']} USDT")
        print(f"Margin wallet totale: {wallet_totals['margin']} USDT")
        
    except Exception as e:
        print(f"Errore calcolo manuale: {e}")

def main():
    """Funzione principale"""
    print_separator("SCRIPT TEST BITFINEX BALANCE")
    print(f"Timestamp: {datetime.now()}")
    
    # Recupera le API key dell'utente dal database
    user_id = "68b9d887c6a1151bcce4cd50"
    
    try:
        # Recupera le API key dell'utente
        api_keys = user_manager.get_user_api_keys(user_id)
        print(f"API keys recuperate per utente {user_id}")
        print(f"API Key configurata: {'Sì' if 'bitfinex_api_key' in api_keys else 'No'}")
        
        # Esegui tutti i test
        test_fetch_balance_methods()
        test_private_api_methods()
        test_manual_balance_calculation()
        
    except Exception as e:
        print(f"Errore durante il recupero delle API key: {e}")
        import traceback
        traceback.print_exc()
    
    print_separator("TEST COMPLETATO")
    print("Analizza i risultati per identificare il problema nell'opener")

if __name__ == "__main__":
    main()