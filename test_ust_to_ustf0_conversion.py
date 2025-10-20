#!/usr/bin/env python3
"""
Script per testare il trasferimento interno con conversione automatica UST->USTF0 su Bitfinex
Testa il trasferimento interno con conversione per l'utente 68b9d887c6a1151bcce4cd50
"""

import sys
import os
import logging
from datetime import datetime

# Aggiungi il percorso del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import user_manager
import ccxt

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_internal_transfer_with_conversion():
    """Testa il trasferimento interno da exchange a margin con conversione automatica UST->USTF0"""
    
    user_id = "68b9d887c6a1151bcce4cd50"
    test_amount = 10.0  # 10 USDT da trasferire e convertire
    
    logger.info("=== TEST TRASFERIMENTO INTERNO CON CONVERSIONE UST/USDT → USTF0 SU BITFINEX ===")
    logger.info(f"Utente: {user_id}")
    logger.info(f"Quantità da trasferire: {test_amount} USDT")
    
    try:
        # 1. Recupera API keys utente
        logger.info("1. Recupero API keys utente...")
        api_keys = user_manager.get_user_api_keys(user_id)
        
        # Debug: stampa struttura API keys
        logger.info(f"API keys recuperate: {api_keys}")
        logger.info(f"Tipo API keys: {type(api_keys)}")
        if api_keys:
            logger.info(f"Chiavi disponibili: {list(api_keys.keys()) if isinstance(api_keys, dict) else 'Non è un dict'}")
        
        if not api_keys or 'bitfinex_api_key' not in api_keys or 'bitfinex_api_secret' not in api_keys:
            logger.error("API keys Bitfinex non trovate per l'utente")
            return False
        
        bitfinex_api_key = api_keys['bitfinex_api_key']
        bitfinex_api_secret = api_keys['bitfinex_api_secret']
        
        if not bitfinex_api_key or not bitfinex_api_secret:
            logger.error("API key o secret Bitfinex mancanti")
            return False
        
        logger.info("✅ API keys recuperate con successo")
        
        # 2. Inizializza exchange Bitfinex
        logger.info("2. Inizializzazione exchange Bitfinex...")
        exchange = ccxt.bitfinex({
            'apiKey': bitfinex_api_key,
            'secret': bitfinex_api_secret,
            'sandbox': False,
            'enableRateLimit': True,
        })
        
        logger.info("✅ Exchange Bitfinex inizializzato")
        
        # 3. Funzione per leggere correttamente i bilanci dal campo info
        def get_balance_from_info(balance_data, wallet_type, currency):
            """Estrae il bilancio dal campo info di Bitfinex"""
            if 'info' not in balance_data or not isinstance(balance_data['info'], list):
                return 0
            
            for balance_entry in balance_data['info']:
                if len(balance_entry) >= 5:
                    entry_wallet = balance_entry[0]  # wallet type
                    entry_currency = balance_entry[1]  # currency
                    entry_amount = float(balance_entry[4]) if balance_entry[4] else 0  # amount
                    
                    if entry_wallet == wallet_type and entry_currency == currency:
                        return entry_amount
            return 0
        
        # 4. Controlla bilanci iniziali
        logger.info("3. Controllo bilanci iniziali...")
        
        # Bilancio exchange wallet
        exchange_balance = exchange.fetch_balance({'type': 'exchange'})
        initial_ust_exchange = get_balance_from_info(exchange_balance, 'exchange', 'UST')
        initial_usdt_exchange = get_balance_from_info(exchange_balance, 'exchange', 'USDT')
        
        # Bilancio margin wallet
        margin_balance = exchange.fetch_balance({'type': 'margin'})
        initial_ust_margin = get_balance_from_info(margin_balance, 'margin', 'UST')
        initial_ustf0_margin = get_balance_from_info(margin_balance, 'margin', 'USTF0')
        
        logger.info(f"Exchange wallet - UST: {initial_ust_exchange}")
        logger.info(f"Exchange wallet - USDT: {initial_usdt_exchange}")
        logger.info(f"Margin wallet - UST: {initial_ust_margin}")
        logger.info(f"Margin wallet - USTF0: {initial_ustf0_margin}")
        
        # Determina quale valuta e wallet usare per il test
        source_wallet = None
        source_currency = None
        
        # Priorità: UST da exchange, poi USDT da exchange, poi UST da margin
        if initial_ust_exchange >= test_amount:
            source_wallet = 'exchange'
            source_currency = 'UST'
            available_amount = initial_ust_exchange
        elif initial_usdt_exchange >= test_amount:
            source_wallet = 'exchange'
            source_currency = 'USDT'
            available_amount = initial_usdt_exchange
        elif initial_ust_margin >= test_amount:
            source_wallet = 'margin'
            source_currency = 'UST'
            available_amount = initial_ust_margin
        else:
            logger.error(f"Fondi insufficienti in tutti i wallet per il test di {test_amount} USDT")
            return False
        
        logger.info(f"✅ Usando {source_currency} dal wallet {source_wallet}: {available_amount} >= {test_amount}")
        
        # 5. Esegui trasferimento interno con conversione automatica (come fa l'opener)
        logger.info("4. Esecuzione trasferimento interno con conversione automatica...")
        logger.info(f"Trasferimento: {test_amount} {source_currency} da {source_wallet} a margin (conversione automatica in USTF0)")
        
        transfer_success = False
        
        try:
            # Usa l'API privata di Bitfinex per il trasferimento interno con conversione
            # Questo è lo stesso metodo usato dall'opener
            
            # Determina le valute di origine e destinazione
            currency_from = source_currency
            currency_to = "USTF0"  # Sempre USTF0 quando si va verso margin per derivatives
            
            params = {
                "from": source_wallet,
                "to": "margin",
                "currency": currency_from,
                "amount": str(test_amount)
            }
            
            # Aggiungi currency_to se diversa da currency_from (conversione)
            if currency_from != currency_to:
                params["currency_to"] = currency_to
                logger.info(f"🔄 Conversione automatica: {currency_from} -> {currency_to}")
            
            logger.info(f"Parametri trasferimento: {params}")
            
            # Esegui trasferimento usando l'API privata (stesso metodo dell'opener)
            if hasattr(exchange, 'privatePostAuthWTransfer'):
                result = exchange.privatePostAuthWTransfer(params)
                logger.info(f"Risultato trasferimento: {result}")
                
                if result and isinstance(result, list) and len(result) > 0:
                    status = result[6] if len(result) > 6 else "UNKNOWN"
                    
                    if status == "SUCCESS":
                        logger.info("✅ Trasferimento interno con conversione completato con successo!")
                        transfer_success = True
                    else:
                        error_msg = result[7] if len(result) > 7 else "Errore sconosciuto"
                        logger.error(f"❌ Trasferimento fallito: {status} - {error_msg}")
                        transfer_success = False
                else:
                    logger.error("❌ Risposta trasferimento non valida")
                    transfer_success = False
            else:
                logger.error("❌ Metodo privatePostAuthWTransfer non disponibile")
                transfer_success = False
                
        except Exception as e:
            logger.error(f"❌ Trasferimento interno fallito: {e}")
            transfer_success = False
        
        # Attendi un momento per permettere al trasferimento di essere processato
        import time
        time.sleep(2)
        
        # 6. Controlla bilanci finali
        logger.info("5. Controllo bilanci finali...")
        
        # Bilancio exchange wallet finale
        final_exchange_balance = exchange.fetch_balance({'type': 'exchange'})
        final_ust_exchange = get_balance_from_info(final_exchange_balance, 'exchange', 'UST')
        final_usdt_exchange = get_balance_from_info(final_exchange_balance, 'exchange', 'USDT')
        
        # Bilancio margin wallet finale
        final_margin_balance = exchange.fetch_balance({'type': 'margin'})
        final_ust_margin = get_balance_from_info(final_margin_balance, 'margin', 'UST')
        final_ustf0_margin = get_balance_from_info(final_margin_balance, 'margin', 'USTF0')
        
        logger.info(f"Exchange wallet - UST: {final_ust_exchange}")
        logger.info(f"Exchange wallet - USDT: {final_usdt_exchange}")
        logger.info(f"Margin wallet - UST: {final_ust_margin}")
        logger.info(f"Margin wallet - USTF0: {final_ustf0_margin}")
        
        # Calcola variazioni
        ust_exchange_change = final_ust_exchange - initial_ust_exchange
        usdt_exchange_change = final_usdt_exchange - initial_usdt_exchange
        ust_margin_change = final_ust_margin - initial_ust_margin
        ustf0_margin_change = final_ustf0_margin - initial_ustf0_margin
        
        logger.info("=== VARIAZIONI ===")
        logger.info(f"Exchange UST: {ust_exchange_change:+.8f}")
        logger.info(f"Exchange USDT: {usdt_exchange_change:+.8f}")
        logger.info(f"Margin UST: {ust_margin_change:+.8f}")
        logger.info(f"Margin USTF0: {ustf0_margin_change:+.8f}")
        
        # Verifica se il trasferimento e la conversione sono avvenuti
        logger.info("=== RISULTATI ===")
        
        if transfer_success:
            # Verifica che i fondi siano diminuiti dal wallet di origine
            source_decreased = False
            if source_wallet == 'exchange' and source_currency == 'UST':
                source_decreased = ust_exchange_change < -5  # Almeno 5 USDT trasferiti
            elif source_wallet == 'exchange' and source_currency == 'USDT':
                source_decreased = usdt_exchange_change < -5
            elif source_wallet == 'margin' and source_currency == 'UST':
                source_decreased = ust_margin_change < -5
            
            # Verifica che USTF0 sia aumentato nel margin wallet
            ustf0_increased = ustf0_margin_change > 5  # Almeno 5 USTF0 ricevuti
            
            if source_decreased and ustf0_increased:
                logger.info("✅ Trasferimento interno con conversione automatica UST/USDT -> USTF0 riuscito!")
                logger.info(f"✅ Convertiti circa {abs(ustf0_margin_change):.2f} USTF0 nel margin wallet")
                return True
            elif ustf0_increased:
                logger.info("✅ USTF0 aumentato nel margin wallet, conversione parzialmente riuscita")
                return True
            else:
                logger.warning("❌ Nessuna conversione significativa rilevata")
                return False
        else:
            logger.error("❌ Trasferimento interno fallito")
            return False
        
    except Exception as e:
        logger.error(f"Errore durante test trasferimento: {e}")
        return False

if __name__ == "__main__":
    success = test_internal_transfer_with_conversion()
    if success:
        print("\n🎉 Test di trasferimento interno con conversione completato con successo!")
    else:
        print("\n💥 Test di trasferimento interno fallito!")