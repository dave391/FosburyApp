"""Modulo Transfer - Gestione trasferimenti automatici tra exchange
Gestisce il riequilibrio dei fondi USDT tra Bitmex e Bitfinex
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
from database.models import bot_manager, user_manager
from trading.exchange_manager import ExchangeManager
from config.settings import BOT_STATUS

logger = logging.getLogger(__name__)

class TransferManager:
    """Manager per trasferimenti automatici tra exchange"""
    
    def __init__(self):
        self.exchange_manager = ExchangeManager()
        self.min_transfer_amount = 10.0  # Importo minimo per trasferimento
        self.transfer_buffer = 1.0  # Buffer per commissioni
    
    def process_transfer_requests(self) -> Dict:
        """Processa tutte le richieste di trasferimento pendenti"""
        try:
            # Recupera bot con stato transfer_requested
            transfer_bots = bot_manager.get_transfer_requested_bots()
            
            if not transfer_bots:
                logger.info("Nessun bot in attesa di trasferimento")
                return {"processed": 0, "errors": []}
            
            processed_count = 0
            errors = []
            
            for bot in transfer_bots:
                try:
                    result = self._process_single_bot_transfer(bot)
                    if result["success"]:
                        processed_count += 1
                    else:
                        errors.append(f"Bot {bot['_id']}: {result['error']}")
                        
                except Exception as e:
                    error_msg = f"Errore processing bot {bot['_id']}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            logger.info(f"Processati {processed_count} trasferimenti, {len(errors)} errori")
            return {
                "processed": processed_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Errore process_transfer_requests: {e}")
            return {"processed": 0, "errors": [str(e)]}
    
    def _process_single_bot_transfer(self, bot: Dict) -> Dict:
        """Processa trasferimento per un singolo bot"""
        try:
            user_id = bot['user_id']
            exchange_long = bot['exchange_long']
            exchange_short = bot['exchange_short']
            capital = bot['capital']
            
            logger.info(f"Processing transfer per bot {bot['_id']}: {exchange_long} <-> {exchange_short}")
            
            # Valida dati utente
            if not self._validate_user_data(user_id, exchange_long, exchange_short):
                return {"success": False, "error": "Dati utente non validi"}
            
            # Inizializza connessioni exchange
            exchanges = self._initialize_exchanges(user_id, exchange_long, exchange_short)
            if not exchanges:
                return {"success": False, "error": "Errore inizializzazione exchange"}
            
            # Recupera bilanci
            balances = self._get_balances(exchanges)
            if not balances:
                return {"success": False, "error": "Errore recupero bilanci"}
            
            # Verifica se il capitale totale è sufficiente (incluse commissioni)
            total_balance = sum(balances.values())
            required_capital = capital + 1.0  # Capital + 1 USDT per commissioni
            
            if total_balance < required_capital:
                logger.warning(f"Bot {bot['_id']}: capitale insufficiente. Totale: {total_balance}, Richiesto: {required_capital}")
                bot_manager.update_bot_status(
                    str(bot['_id']), 
                    BOT_STATUS['STOPPED'], 
                    stopped_type="not_enough_capital"
                )
                return {"success": False, "error": f"Capitale insufficiente: {total_balance} < {required_capital}"}
            
            # Calcola trasferimento necessario
            transfer_info = self._calculate_transfer_amount(balances, capital, exchange_long, exchange_short)
            
            if transfer_info["amount"] == 0:
                logger.info(f"Bot {bot['_id']}: bilanci già equilibrati")
                return {"success": True, "message": "Bilanci già equilibrati"}
            
            # Aggiorna stato bot a transferring prima di eseguire il trasferimento
            # Mantiene il transfer_reason dal precedente stato TRANSFER_REQUESTED
            transfer_reason = bot.get('transfer_reason', 'unknown')
            bot_manager.update_bot_status(
                str(bot['_id']), 
                BOT_STATUS['TRANSFERING'], 
                started_type="restarted",
                transfer_reason=transfer_reason
            )
            logger.info(f"Bot {bot['_id']}: stato aggiornato a transferring (reason: {transfer_reason}), avvio trasferimento")
            
            # Controlla e esegui trasferimenti interni se necessari
            # Passa l'importo del trasferimento + commissioni se Bitfinex è l'exchange di origine
            required_amount_for_internal = 0
            if transfer_info["from_exchange"].lower() == "bitfinex":
                required_amount_for_internal = transfer_info["amount"] + 1.0  # deficit + commissioni
            
            internal_transfer_result = self._check_and_execute_internal_transfers(
                exchange_long, exchange_short, required_amount_for_internal
            )
            if not internal_transfer_result:
                logger.warning(f"Bot {bot['_id']}: problemi con trasferimenti interni, ma continuo")
            
            # Esegui trasferimento
            transfer_result = self._execute_transfer(
                exchanges,
                transfer_info["from_exchange"],
                transfer_info["to_exchange"],
                transfer_info["amount"],
                user_id
            )
            
            if transfer_result["success"]:
                logger.info(f"Bot {bot['_id']}: trasferimento avviato con successo")
                return {"success": True, "transfer_id": transfer_result.get("withdrawal_id")}
            else:
                return {"success": False, "error": transfer_result["error"]}
                
        except Exception as e:
            logger.error(f"Errore _process_single_bot_transfer: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_user_data(self, user_id: str, exchange_long: str, exchange_short: str) -> bool:
        """Valida API keys e wallet dell'utente"""
        try:
            # Verifica API keys
            api_keys = user_manager.get_user_api_keys(user_id)
            required_keys = [
                f"{exchange_long}_api_key",
                f"{exchange_long}_api_secret",
                f"{exchange_short}_api_key",
                f"{exchange_short}_api_secret"
            ]
            
            for key in required_keys:
                if not api_keys.get(key):
                    logger.error(f"API key mancante: {key}")
                    return False
            
            # Verifica wallet (opzionale ma consigliato)
            wallets = user_manager.get_user_wallets(user_id)
            if not wallets.get(f"{exchange_long}_wallet") or not wallets.get(f"{exchange_short}_wallet"):
                logger.warning(f"Wallet addresses mancanti per utente {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Errore validazione dati utente: {e}")
            return False
    
    def _initialize_exchanges(self, user_id: str, exchange_long: str, exchange_short: str) -> Optional[Dict]:
        """Inizializza connessioni agli exchange"""
        try:
            api_keys = user_manager.get_user_api_keys(user_id)
            
            exchanges = {}
            
            # Inizializza exchange long
            success_long = self.exchange_manager.initialize_exchange(
                exchange_long,
                api_keys[f"{exchange_long}_api_key"],
                api_keys[f"{exchange_long}_api_secret"]
            )
            
            if not success_long:
                logger.error(f"Errore inizializzazione {exchange_long}")
                return None
            
            # Recupera l'exchange dall'exchange_manager
            long_exchange = self.exchange_manager.exchanges.get(exchange_long)
            if not long_exchange:
                logger.error(f"Errore recupero exchange {exchange_long}")
                return None
            
            exchanges[exchange_long] = long_exchange
            
            # Inizializza exchange short
            success_short = self.exchange_manager.initialize_exchange(
                exchange_short,
                api_keys[f"{exchange_short}_api_key"],
                api_keys[f"{exchange_short}_api_secret"]
            )
            
            if not success_short:
                logger.error(f"Errore inizializzazione {exchange_short}")
                return None
            
            # Recupera l'exchange dall'exchange_manager
            short_exchange = self.exchange_manager.exchanges.get(exchange_short)
            if not short_exchange:
                logger.error(f"Errore recupero exchange {exchange_short}")
                return None
            
            exchanges[exchange_short] = short_exchange
            
            return exchanges
            
        except Exception as e:
            logger.error(f"Errore _initialize_exchanges: {e}")
            return None
    
    def _get_exchange_balance_detailed(self, exchange_name: str) -> dict:
        """Ottiene saldo dettagliato da un exchange (logica completa per Bitfinex)"""
        try:
            if exchange_name.lower() == 'bitmex':
                # BitMEX non ha wallet separati
                exchange = self.exchange_manager.exchanges['bitmex']
                balance = exchange.fetch_balance()
                total = balance.get('USDT', {}).get('free', 0)
                return {
                    'total': total,
                    'wallet_details': {'main': total}
                }
            
            elif exchange_name.lower() == 'bitfinex':
                exchange = self.exchange_manager.exchanges['bitfinex']
                wallets = ['exchange', 'margin', 'funding']
                currencies = ['USTF0', 'USDT', 'UST']
                total_balance = 0
                wallet_details = {}
                
                for wallet in wallets:
                    wallet_balance = 0
                    try:
                        balance = exchange.fetch_balance({'type': wallet})
                        
                        # Somma tutti i fondi disponibili (free) di tutte le valute supportate
                        for currency in currencies:
                            if currency in balance and balance[currency]['free'] > 0:
                                amount = balance[currency]['free']
                                wallet_balance += amount
                                total_balance += amount
                                logger.debug(f"{wallet} wallet - {currency}: {amount:.2f}")
                        
                        if wallet_balance > 0:
                            wallet_details[wallet] = wallet_balance
                            
                    except Exception as e:
                        logger.warning(f"Errore recupero saldo {wallet}: {e}")
                
                return {
                    'total': total_balance,
                    'wallet_details': wallet_details
                }
            
            return {'total': 0, 'wallet_details': {}}
            
        except Exception as e:
            logger.error(f"Errore recupero saldo {exchange_name}: {e}")
            return {'total': 0, 'wallet_details': {}}
    
    def _get_balances(self, exchanges: Dict) -> Optional[Dict]:
        """Recupera bilanci USDT da tutti gli exchange usando logica dettagliata"""
        try:
            balances = {}
            
            for exchange_name, exchange in exchanges.items():
                # Usa la logica dettagliata per ogni exchange
                balance_details = self._get_exchange_balance_detailed(exchange_name)
                balances[exchange_name] = balance_details['total']
                
                logger.info(f"Bilancio {exchange_name}: {balance_details['total']:.2f} USDT")
                if balance_details['wallet_details']:
                    for wallet, amount in balance_details['wallet_details'].items():
                        if amount > 0:
                            logger.info(f"  {wallet}: {amount:.2f} USDT")
            
            return balances
            
        except Exception as e:
            logger.error(f"Errore recupero bilanci: {e}")
            return None
    
    def _calculate_transfer_amount(self, balances: Dict, capital: float, exchange_long: str, exchange_short: str) -> Dict:
        """Calcola importo da trasferire per riequilibrare i fondi"""
        try:
            target_per_exchange = capital / 2  # Capitale target per exchange
            
            long_balance = balances[exchange_long]
            short_balance = balances[exchange_short]
            
            long_deficit = target_per_exchange - long_balance
            short_deficit = target_per_exchange - short_balance
            
            logger.info(f"Target per exchange: {target_per_exchange} USDT")
            logger.info(f"{exchange_long} deficit: {long_deficit} USDT (target - saldo_attuale)")
            logger.info(f"{exchange_short} deficit: {short_deficit} USDT (target - saldo_attuale)")
            
            # Caso 1: Entrambi hanno deficit - impossibile trasferire
            if long_deficit > 0 and short_deficit > 0:
                logger.warning("Entrambi gli exchange hanno deficit rispetto al target - capitale totale insufficiente")
                return {"amount": 0, "from_exchange": None, "to_exchange": None, "error": "Capitale insufficiente"}
            
            # Caso 2: Nessun deficit significativo - nessun trasferimento necessario
            if abs(long_deficit) < 0.01 and abs(short_deficit) < 0.01:
                logger.info("Entrambi gli exchange sono già al target - nessun trasferimento necessario")
                return {"amount": 0, "from_exchange": None, "to_exchange": None}
            
            # Caso 3: Trasferimento necessario
            if long_deficit > 0:  # exchange_long ha deficit
                # Verifica che exchange_short abbia fondi sufficienti
                if short_balance < long_deficit:
                    logger.error(f"{exchange_short} non ha fondi sufficienti per coprire il deficit di {exchange_long}")
                    return {"amount": 0, "from_exchange": None, "to_exchange": None, "error": "Fondi insufficienti"}
                
                transfer_amount = round(long_deficit, 2)
                return {
                    "amount": transfer_amount,
                    "from_exchange": exchange_short,
                    "to_exchange": exchange_long
                }
            
            elif short_deficit > 0:  # exchange_short ha deficit
                # Verifica che exchange_long abbia fondi sufficienti
                if long_balance < short_deficit:
                    logger.error(f"{exchange_long} non ha fondi sufficienti per coprire il deficit di {exchange_short}")
                    return {"amount": 0, "from_exchange": None, "to_exchange": None, "error": "Fondi insufficienti"}
                
                transfer_amount = round(short_deficit, 2)
                return {
                    "amount": transfer_amount,
                    "from_exchange": exchange_long,
                    "to_exchange": exchange_short
                }
            
            # Caso default: nessun trasferimento necessario
            return {"amount": 0, "from_exchange": None, "to_exchange": None}
            
        except Exception as e:
            logger.error(f"Errore calcolo trasferimento: {e}")
            return {"amount": 0, "from_exchange": None, "to_exchange": None}
    
    def _execute_transfer(self, exchanges: Dict, from_exchange: str, to_exchange: str, amount: float, user_id: str) -> Dict:
        """Esegue il trasferimento tra exchange"""
        try:
            exchange = exchanges[from_exchange]
            
            # Recupera wallet di destinazione
            wallets = user_manager.get_user_wallets(user_id)
            destination_wallet = wallets.get(f"{to_exchange}_wallet")
            
            if not destination_wallet:
                logger.error(f"Wallet {to_exchange} non configurato")
                return {"success": False, "error": f"Wallet {to_exchange} non configurato"}
            
            # Valida importo
            if amount < self.min_transfer_amount:
                return {"success": False, "error": f"Importo troppo basso: {amount}"}
            
            # Arrotonda importo a 2 decimali
            actual_amount_rounded = round(amount, 2)
            
            # Parametri per withdrawal (rete Solana)
            withdraw_params = {
                "network": "SOL",
                "tag": None
            }
            
            # Esegui withdrawal
            withdrawal_result = exchange.withdraw(
                "USDT",
                str(actual_amount_rounded),
                destination_wallet,
                params=withdraw_params
            )
            
            logger.info(f"Trasferimento {from_exchange} -> {to_exchange}: {actual_amount_rounded} USDT")
            logger.info(f"Withdrawal ID: {withdrawal_result.get('id', 'N/A')}")
            
            return {
                "success": True,
                "withdrawal_id": withdrawal_result.get("id"),
                "amount": actual_amount_rounded,
                "network": "Solana"
            }
            
        except Exception as e:
            logger.error(f"Errore _execute_transfer: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_exchange_balance(self, exchange_name: str, balance_type: str = 'total') -> float:
        """Ottiene saldo disponibile su un exchange
        
        Args:
            exchange_name: Nome dell'exchange
            balance_type: 'total' per saldo totale, 'tradable' per saldo utilizzabile per trading,
                         'derivatives' per saldo derivatives su Bitfinex (USTF0 nel margin wallet)
        
        Returns:
            float: Saldo richiesto
        """
        try:
            if exchange_name.lower() == 'bitmex':
                # BitMEX non ha wallet separati, quindi total = tradable
                exchange = self.exchange_manager.exchanges['bitmex']
                balance = exchange.fetch_balance()
                return balance.get('USDT', {}).get('total', 0)
            
            elif exchange_name.lower() == 'bitfinex':
                exchange = self.exchange_manager.exchanges['bitfinex']
                
                if balance_type == 'derivatives':
                    # Solo USTF0 dal wallet margin (derivatives wallet)
                    try:
                        balance = exchange.fetch_balance({'type': 'margin'})
                        ustf0_balance = 0
                        
                        # Estrae i balance dall'array 'info'
                        if 'info' in balance and isinstance(balance['info'], list):
                            for balance_entry in balance['info']:
                                if len(balance_entry) >= 5:
                                    entry_wallet = balance_entry[0]
                                    entry_currency = balance_entry[1]
                                    entry_total = float(balance_entry[4]) if balance_entry[4] else 0
                                    
                                    # Cerca USTF0 nel wallet margin
                                    if entry_wallet == 'margin' and entry_currency == 'USTF0' and entry_total > 0:
                                        ustf0_balance = entry_total
                                        break
                        
                        logger.debug(f"Bitfinex derivatives balance (USTF0): {ustf0_balance}")
                        return ustf0_balance
                    except Exception as e:
                        logger.error(f"Errore recupero saldo derivatives Bitfinex: {e}")
                        return 0
                
                elif balance_type == 'total':
                    # Saldo totale da tutti i wallet
                    balance_details = self._get_exchange_balance_detailed(exchange_name)
                    return balance_details['total']
            
            return 0
            
        except Exception as e:
            logger.error(f"Errore recupero saldo {exchange_name}: {e}")
            return 0
    
    def _check_and_execute_internal_transfers(self, exchange_long: str, exchange_short: str, required_amount: float) -> bool:
        """Controlla e esegue trasferimenti interni se necessari"""
        try:
            logger.info("Controllo necessità trasferimenti interni...")
            
            # Per ora gestiamo solo Bitfinex
            if 'bitfinex' in [exchange_long.lower(), exchange_short.lower()]:
                return self._check_bitfinex_internal_transfer_needed(required_amount)
            
            return True  # Nessun trasferimento interno necessario
            
        except Exception as e:
            logger.error(f"Errore controllo trasferimenti interni: {e}")
            return False
    
    def _check_bitfinex_internal_transfer_needed(self, required_amount: float) -> bool:
        """Controlla se è necessario un trasferimento interno in Bitfinex"""
        try:
            # Se non c'è importo richiesto, non serve trasferimento interno
            if required_amount <= 0:
                logger.info("Nessun trasferimento interno necessario")
                return True
            
            # Recupera saldi margin (USTF0) e exchange
            margin_balance = self._get_exchange_balance('bitfinex', balance_type='derivatives')
            exchange_balance = self._get_exchange_balance('bitfinex', balance_type='exchange')
            
            logger.info(f"Bitfinex - Saldo margin (USTF0): {margin_balance}, Saldo exchange: {exchange_balance}")
            
            # Se il wallet exchange ha già fondi sufficienti per il trasferimento
            if exchange_balance >= required_amount:
                logger.info(f"Wallet exchange Bitfinex già sufficiente: {exchange_balance} >= {required_amount}")
                return True
            
            # Calcola quanto trasferire da margin a exchange
            transfer_amount = required_amount - exchange_balance
            
            if margin_balance < transfer_amount:
                logger.error(f"Fondi insufficienti nel wallet margin per trasferimento interno Bitfinex: disponibili {margin_balance}, richiesti {transfer_amount}")
                return False
            
            # Esegui trasferimento interno da margin a exchange
            logger.info(f"Eseguendo trasferimento interno Bitfinex: {transfer_amount} USDT da margin a exchange")
            return self._execute_bitfinex_internal_transfer(transfer_amount, 'margin', 'exchange')
            
        except Exception as e:
            logger.error(f"Errore controllo trasferimento Bitfinex: {e}")
            return False
    
    def _execute_bitfinex_internal_transfer(self, amount: float, from_wallet: str, to_wallet: str) -> bool:
        """Esegue un trasferimento interno in Bitfinex da margin a exchange"""
        try:
            logger.info(f"Eseguendo trasferimento interno Bitfinex: {amount} USTF0 da {from_wallet} a {to_wallet}")
            
            # Usa la funzione di trasferimento interno
            result = self._bitfinex_internal_transfer(amount, from_wallet, to_wallet)
            
            if result:
                logger.info(f"Trasferimento interno Bitfinex completato con successo: {amount} USTF0")
                return True
            else:
                logger.error(f"Trasferimento interno Bitfinex fallito")
                return False
                
        except Exception as e:
            logger.error(f"Errore esecuzione trasferimento interno Bitfinex: {e}")
            return False
    
    def _bitfinex_internal_transfer(self, amount: float, from_wallet: str, to_wallet: str) -> bool:
        """Esegue trasferimento interno tra wallet Bitfinex"""
        try:
            exchange = self.exchange_manager.exchanges['bitfinex']
            
            # Parametri per il trasferimento interno (usando la stessa logica di opener.py)
            actual_currency = "USTF0" if from_wallet == "margin" else "UST"
            actual_currency_to = "USTF0" if to_wallet == "margin" else "UST"
            
            params = {
                "from": from_wallet,
                "to": to_wallet,
                "currency": actual_currency,
                "amount": str(amount)
            }
            
            if actual_currency != actual_currency_to:
                params["currency_to"] = actual_currency_to
                logger.info(f"Conversione da {actual_currency} a {actual_currency_to}")
            
            logger.info(f"Parametri trasferimento: {params}")
            
            # Esegui trasferimento usando l'API privata
            if hasattr(exchange, 'privatePostAuthWTransfer'):
                result = exchange.privatePostAuthWTransfer(params)
                
                if result and isinstance(result, list) and len(result) > 0:
                    status = result[6] if len(result) > 6 else "UNKNOWN"
                    
                    if status == "SUCCESS":
                        logger.info(f"Trasferimento interno Bitfinex riuscito: {result}")
                        return True
                    else:
                        logger.error(f"Trasferimento interno Bitfinex fallito - Status: {status}, Result: {result}")
                        return False
                else:
                    logger.error(f"Trasferimento interno Bitfinex fallito - Formato risposta non valido: {result}")
                    return False
            else:
                logger.error("Metodo privatePostAuthWTransfer non disponibile")
                return False
                
        except Exception as e:
            logger.error(f"Errore _bitfinex_internal_transfer: {e}")
            return False

# Istanza globale
transfer_manager = TransferManager()

def main():
    """Funzione principale per eseguire il processo di trasferimento"""
    logger.info("🚀 Avvio processo trasferimenti...")
    
    try:
        result = transfer_manager.process_transfer_requests()
        
        if result["processed"] > 0:
            logger.info(f"✅ Processati {result['processed']} trasferimenti con successo")
        else:
            logger.info("ℹ️ Nessun trasferimento da processare")
            
        if result["errors"]:
            logger.warning(f"⚠️ Errori riscontrati: {len(result['errors'])}")
            for error in result["errors"]:
                logger.error(f"❌ {error}")
                
    except Exception as e:
        logger.error(f"❌ Errore critico nel processo trasferimenti: {e}")

if __name__ == "__main__":
    main()