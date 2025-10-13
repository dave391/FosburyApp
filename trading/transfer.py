"""Modulo Transfer - Gestione trasferimenti automatici tra exchange
Gestisce il riequilibrio dei fondi USDT tra Bitmex e Bitfinex e altri futuri exchange.
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
from database.models import bot_manager, user_manager, position_manager
from trading.exchange_manager import ExchangeManager, exchange_manager
from config.settings import BOT_STATUS

logger = logging.getLogger(__name__)

class TransferManager:
    """Manager per trasferimenti automatici tra exchange"""
    
    def __init__(self):
        self.exchange_manager = ExchangeManager()
        self.min_transfer_amount = 10.0  # Importo minimo per trasferimento
        self.transfer_buffer = 1.0  # Buffer per commissioni
    
    def process_transfer_requests(self) -> Dict:
        """Processa tutte le richieste di trasferimento pendenti - gestisce entrambi i cicli"""
        try:
            # CICLO 1: Recupera bot con stato transfer_requested (trasferimenti interni)
            transfer_bots = bot_manager.get_transfer_requested_bots()
            
            # CICLO 2: Recupera bot con stato external_transfer_pending (trasferimenti esterni)
            external_transfer_bots = bot_manager.get_external_transfer_pending_bots()
            
            if not transfer_bots and not external_transfer_bots:
                logger.info("Nessun bot in attesa di trasferimento")
                return {"processed": 0, "errors": []}
            
            processed_count = 0
            errors = []
            
            # CICLO 1: Processa trasferimenti interni (TRANSFER_REQUESTED -> EXTERNAL_TRANSFER_PENDING)
            for bot in transfer_bots:
                try:
                    result = self._process_internal_transfer(bot)
                    if result["success"]:
                        processed_count += 1
                    else:
                        errors.append(f"Bot {bot['_id']} (interno): {result['error']}")
                        
                except Exception as e:
                    error_msg = f"Errore processing interno bot {bot['_id']}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # CICLO 2: Processa trasferimenti esterni (EXTERNAL_TRANSFER_PENDING -> TRANSFERING)
            for bot in external_transfer_bots:
                try:
                    result = self._process_external_transfer(bot)
                    if result["success"]:
                        processed_count += 1
                    else:
                        errors.append(f"Bot {bot['_id']} (esterno): {result['error']}")
                        
                except Exception as e:
                    error_msg = f"Errore processing esterno bot {bot['_id']}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            logger.info(f"Processati {processed_count} trasferimenti totali, {len(errors)} errori")
            return {
                "processed": processed_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Errore process_transfer_requests: {e}")
            return {"processed": 0, "errors": [str(e)]}
    
    def _process_internal_transfer(self, bot: Dict) -> Dict:
        """CICLO 1: Processa trasferimento interno (TRANSFER_REQUESTED -> EXTERNAL_TRANSFER_PENDING)"""
        try:
            user_id = bot['user_id']
            exchange_long = bot['exchange_long']
            exchange_short = bot['exchange_short']
            capital = bot['capital']
            
            logger.info(f"CICLO 1 - Processing trasferimento interno per bot {bot['_id']}: {exchange_long} <-> {exchange_short}")
            
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
            
            # Calcola trasferimento necessario
            transfer_info = self._calculate_transfer_amount(
                balances, 
                capital, 
                exchange_long, 
                exchange_short, 
                bot.get('stop_loss_percentage', 20),
                bot.get('transfer_reason'),
                bot
            )
            
            # Controlla se è stato attivato lo stop loss
            if transfer_info.get("stop_loss_triggered", False):
                logger.warning(f"Bot {bot['_id']}: Stop loss attivato! Fermo il bot.")
                bot_manager.update_bot_status(
                    bot['user_id'], 
                    BOT_STATUS['STOPPED'], 
                    stopped_type="stop_loss"
                )
                return {"success": False, "message": "Bot fermato per stop loss attivato"}
            
            if transfer_info["amount"] == 0:
                logger.info(f"Bot {bot['_id']}: bilanci già equilibrati")
                # Aggiorna a TRANSFERING anche se non serve trasferimento per mantenere coerenza
                # Altri moduli gestiranno il passaggio a RUNNING
                transfer_reason = bot.get('transfer_reason', 'unknown')
                bot_manager.update_bot_status(
                    bot['user_id'], 
                    BOT_STATUS['TRANSFERING'], 
                    started_type="restarted",
                    transfer_reason=transfer_reason
                )
                return {"success": True, "message": "Bilanci già equilibrati"}
            
            # Determina se serve trasferimento interno (solo per Bitfinex)
            if transfer_info["from_exchange"].lower() == "bitfinex":
                # Esegui trasferimento interno su Bitfinex
                required_amount_for_internal = transfer_info["amount"]
                internal_transfer_result = self._check_and_execute_internal_transfers(
                    exchange_long, exchange_short, required_amount_for_internal
                )
                
                if not internal_transfer_result:
                    logger.error(f"Bot {bot['_id']}: trasferimento interno fallito")
                    # Riporta il bot a TRANSFER_REQUESTED per riprovare
                    bot_manager.update_bot_status(
                        bot['user_id'], 
                        BOT_STATUS['TRANSFER_REQUESTED'], 
                        transfer_reason=bot.get('transfer_reason', 'unknown')
                    )
                    return {"success": False, "error": "Trasferimento interno fallito"}
                
                # Trasferimento interno riuscito - passa a EXTERNAL_TRANSFER_PENDING
                transfer_reason = bot.get('transfer_reason', 'unknown')
                bot_manager.update_bot_status(
                    bot['user_id'], 
                    BOT_STATUS['EXTERNAL_TRANSFER_PENDING'], 
                    transfer_reason=transfer_reason,
                    transfer_amount=transfer_info["amount"]
                )
                logger.info(f"Bot {bot['_id']}: trasferimento interno completato, stato aggiornato a EXTERNAL_TRANSFER_PENDING")
                return {"success": True, "message": "Trasferimento interno completato"}
            
            else:
                # BitMEX non ha trasferimenti interni - passa direttamente a EXTERNAL_TRANSFER_PENDING
                transfer_reason = bot.get('transfer_reason', 'unknown')
                bot_manager.update_bot_status(
                    bot['user_id'], 
                    BOT_STATUS['EXTERNAL_TRANSFER_PENDING'], 
                    transfer_reason=transfer_reason,
                    transfer_amount=transfer_info["amount"]
                )
                logger.info(f"Bot {bot['_id']}: BitMEX non richiede trasferimento interno, stato aggiornato a EXTERNAL_TRANSFER_PENDING")
                return {"success": True, "message": "Pronto per trasferimento esterno"}
                
        except Exception as e:
            logger.error(f"Errore _process_internal_transfer: {e}")
            return {"success": False, "error": str(e)}
    
    def _process_external_transfer(self, bot: Dict) -> Dict:
        """CICLO 2: Processa trasferimento esterno (EXTERNAL_TRANSFER_PENDING -> TRANSFERING)"""
        try:
            user_id = bot['user_id']
            exchange_long = bot['exchange_long']
            exchange_short = bot['exchange_short']
            transfer_amount = bot.get('transfer_amount')
            
            if transfer_amount is None:
                logger.error(f"Bot {bot['_id']}: transfer_amount non trovato")
                return {"success": False, "error": "Transfer amount non trovato"}
            
            logger.info(f"CICLO 2 - Processing trasferimento esterno per bot {bot['_id']}: {transfer_amount} USDT")
            
            # Valida dati utente
            if not self._validate_user_data(user_id, exchange_long, exchange_short):
                return {"success": False, "error": "Dati utente non validi"}
            
            # Inizializza connessioni exchange
            exchanges = self._initialize_exchanges(user_id, exchange_long, exchange_short)
            if not exchanges:
                return {"success": False, "error": "Errore inizializzazione exchange"}
            
            # Recupera bilanci per determinare direzione trasferimento
            balances = self._get_balances(exchanges)
            if not balances:
                return {"success": False, "error": "Errore recupero bilanci"}
            
            # Determina direzione trasferimento basata sui bilanci attuali
            from_exchange = exchange_long if balances[exchange_long] > balances[exchange_short] else exchange_short
            to_exchange = exchange_short if from_exchange == exchange_long else exchange_long
            
            logger.info(f"Bot {bot['_id']}: trasferimento esterno {from_exchange} -> {to_exchange}: {transfer_amount} USDT")
            
            # Esegui trasferimento esterno
            transfer_result = self._execute_transfer(
                exchanges,
                from_exchange,
                to_exchange,
                transfer_amount,
                user_id
            )
            
            if transfer_result["success"]:
                # Trasferimento esterno riuscito - passa a TRANSFERING
                transfer_reason = bot.get('transfer_reason', 'unknown')
                bot_manager.update_bot_status(
                    bot['user_id'], 
                    BOT_STATUS['TRANSFERING'], 
                    transfer_reason=transfer_reason,
                    transfer_amount=None  # Reset transfer_amount
                )
                logger.info(f"Bot {bot['_id']}: trasferimento esterno completato, stato aggiornato a TRANSFERING")
                return {"success": True, "transfer_id": transfer_result.get("withdrawal_id")}
            else:
                logger.error(f"Bot {bot['_id']}: trasferimento esterno fallito: {transfer_result['error']}")
                # Mantieni stato EXTERNAL_TRANSFER_PENDING per riprovare nel prossimo ciclo
                return {"success": False, "error": transfer_result["error"]}
                
        except Exception as e:
            logger.error(f"Errore _process_external_transfer: {e}")
            return {"success": False, "error": str(e)}
    
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
            
            # Calcola trasferimento necessario
            transfer_info = self._calculate_transfer_amount(
                balances, 
                capital, 
                exchange_long, 
                exchange_short, 
                bot.get('stop_loss_percentage', 20),
                bot.get('transfer_reason'),
                bot
            )
            
            # Controlla se è stato attivato lo stop loss
            if transfer_info.get("stop_loss_triggered", False):
                logger.warning(f"Bot {bot['_id']}: Stop loss attivato! Fermo il bot.")
                bot_manager.update_bot_status(
                    bot['user_id'], 
                    BOT_STATUS['STOPPED'], 
                    stopped_type="stop_loss"
                )
                return {"success": False, "message": "Bot fermato per stop loss attivato"}
            
            if transfer_info["amount"] == 0:
                logger.info(f"Bot {bot['_id']}: bilanci già equilibrati")
                return {"success": True, "message": "Bilanci già equilibrati"}
            
            # Aggiorna stato bot a transferring prima di eseguire il trasferimento
            # Mantiene il transfer_reason dal precedente stato TRANSFER_REQUESTED
            transfer_reason = bot.get('transfer_reason', 'unknown')
            bot_manager.update_bot_status(
                bot['user_id'], 
                BOT_STATUS['TRANSFERING'], 
                started_type="restarted",
                transfer_reason=transfer_reason
            )
            logger.info(f"Bot {bot['_id']}: stato aggiornato a transferring (reason: {transfer_reason}), avvio trasferimento")
            
            # Controlla e esegui trasferimenti interni se necessari
            # L'importo è già corretto (fee già dedotte nel calcolo precedente)
            required_amount_for_internal = 0
            if transfer_info["from_exchange"].lower() == "bitfinex":
                required_amount_for_internal = transfer_info["amount"]  # Importo già corretto
            
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
    
    def _calculate_transfer_amount(self, balances: Dict, capital: float, exchange_long: str, exchange_short: str, stop_loss_percentage: float, transfer_reason: str = None, bot: Dict = None) -> Dict:
        """Calcola importo da trasferire per riequilibrare i fondi"""
        try:
            # Gestione speciale per rebalancing di posizioni aperte (mantieni solo per transfer_reason='balancer')
            if transfer_reason == "balancer" and bot:
                logger.info("Modalità rebalance: calcolo trasferimento basato su margini richiesti delle posizioni")
                return self._calculate_rebalance_transfer(bot, balances, exchange_long, exchange_short)
            # Calcola available_balance (somma dei bilanci attuali)
            long_balance = balances[exchange_long]
            short_balance = balances[exchange_short]
            available_balance = long_balance + short_balance
            
            # Calcola soglia stop loss
            stop_loss_buffer = capital * (stop_loss_percentage / 100)
            stop_loss_threshold = capital - stop_loss_buffer
            
            logger.info(f"Capitale configurato: {capital} USDT")
            logger.info(f"Available balance: {available_balance} USDT")
            logger.info(f"Stop loss threshold: {stop_loss_threshold} USDT (capitale - {stop_loss_percentage}%)")
            
            # LIVELLO 1: Controllo stop loss
            if available_balance < stop_loss_threshold:
                logger.warning(f"Stop loss attivato: available_balance ({available_balance}) < stop_loss_threshold ({stop_loss_threshold})")
                return {
                    "amount": 0, 
                    "from_exchange": None, 
                    "to_exchange": None, 
                    "stop_loss_triggered": True,
                    "error": "Stop loss attivato"
                }
            
            # LIVELLO 2: Determina base per calcoli
            if available_balance > capital:
                # Usa capital come base (caso di profitto)
                base_amount = capital
                logger.info(f"Usando capital come base: {base_amount} USDT (available_balance > capital)")
            else:
                # Usa available_balance come base
                base_amount = available_balance
                logger.info(f"Usando available_balance come base: {base_amount} USDT")
            
            # LIVELLO 3: Calcola target con commissioni di trasferimento
            # Aggiungi 2 USDT al denominatore per le commissioni
            target_per_exchange = (base_amount + 2) / 2
            
            long_deficit = target_per_exchange - long_balance
            short_deficit = target_per_exchange - short_balance
            
            logger.info(f"Target per exchange (con commissioni): {target_per_exchange} USDT")
            logger.info(f"{exchange_long} deficit: {long_deficit} USDT")
            logger.info(f"{exchange_short} deficit: {short_deficit} USDT")
            
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
                
                # Sottrai 1 USDT per commissioni dal trasferimento effettivo
                transfer_amount = round(long_deficit - 1, 2)
                if transfer_amount <= 0:
                    logger.info("Trasferimento troppo piccolo dopo deduzione commissioni")
                    return {"amount": 0, "from_exchange": None, "to_exchange": None}
                
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
                
                # Sottrai 1 USDT per commissioni dal trasferimento effettivo
                transfer_amount = round(short_deficit - 1, 2)
                if transfer_amount <= 0:
                    logger.info("Trasferimento troppo piccolo dopo deduzione commissioni")
                    return {"amount": 0, "from_exchange": None, "to_exchange": None}
                
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

    def _calculate_rebalance_transfer(self, bot: Dict, balances: Dict, exchange_long: str, exchange_short: str) -> Dict:
        """Calcola il trasferimento necessario per il rebalancing delle posizioni"""
        try:
            logger.info("Calcolo trasferimento per rebalancing posizioni...")
            
            # Recupera posizioni aperte
            bitfinex_position = self._get_bitfinex_position(bot)
            bitmex_position = self._get_bitmex_position(bot)
            
            if not bitfinex_position and not bitmex_position:
                logger.warning("Nessuna posizione aperta trovata per il rebalancing")
                return {"amount": 0, "from_exchange": None, "to_exchange": None}
            
            # Verifica che gli exchange siano già inizializzati
            if "bitfinex" not in self.exchange_manager.exchanges or "bitmex" not in self.exchange_manager.exchanges:
                logger.error("Exchange non inizializzati per rebalancing")
                return {"amount": 0, "from_exchange": None, "to_exchange": None}
            
            # Calcola margini richiesti per ogni posizione
            bitfinex_margin_needed = 0
            bitmex_margin_needed = 0
            
            target_leverage = bot.get("leverage", 3)
            
            if bitfinex_position:
                bitfinex_margin_needed = self._calculate_margin_adjustment(
                    bitfinex_position, target_leverage, "bitfinex", bot, self.exchange_manager.exchanges["bitfinex"]
                )
                
            if bitmex_position:
                bitmex_margin_needed = self._calculate_margin_adjustment(
                    bitmex_position, target_leverage, "bitmex", bot, self.exchange_manager.exchanges["bitmex"]
                )
            
            logger.info(f"Margini necessari - Bitfinex: {bitfinex_margin_needed:.2f}, BitMEX: {bitmex_margin_needed:.2f}")
            
            # Determina la direzione del trasferimento
            # Se entrambi gli exchange richiedono aggiustamenti, trasferisci dall'exchange con più margine a quello con meno
            
            if bitfinex_margin_needed > 0 and bitmex_margin_needed > 0:
                # Entrambi hanno bisogno di margine - trasferisci dall'exchange con meno bisogno a quello con più bisogno
                if bitfinex_margin_needed > bitmex_margin_needed:
                    # Bitfinex ha più bisogno, trasferisci da BitMEX a Bitfinex
                    # Sottrai 1 USDT per fee dal margine necessario
                    transfer_amount = max(bitfinex_margin_needed - 1, 0.1)  # Minimo 0.1 USDT
                    return {
                        "amount": transfer_amount,
                        "from_exchange": "bitmex",
                        "to_exchange": "bitfinex"
                    }
                else:
                    # BitMEX ha più bisogno, trasferisci da Bitfinex a BitMEX
                    # Sottrai 1 USDT per fee dal margine necessario
                    transfer_amount = max(bitmex_margin_needed - 1, 0.1)  # Minimo 0.1 USDT
                    return {
                        "amount": transfer_amount,
                        "from_exchange": "bitfinex",
                        "to_exchange": "bitmex"
                    }
            elif bitfinex_margin_needed > 0 and bitmex_margin_needed <= 0:
                # Solo Bitfinex ha bisogno di margine
                # Sottrai 1 USDT per fee dal margine necessario
                transfer_amount = max(bitfinex_margin_needed - 1, 0.1)  # Minimo 0.1 USDT
                return {
                    "amount": transfer_amount,
                    "from_exchange": "bitmex",
                    "to_exchange": "bitfinex"
                }
            elif bitmex_margin_needed > 0 and bitfinex_margin_needed <= 0:
                # Solo BitMEX ha bisogno di margine
                # Sottrai 1 USDT per fee dal margine necessario
                transfer_amount = max(bitmex_margin_needed - 1, 0.1)  # Minimo 0.1 USDT
                return {
                    "amount": transfer_amount,
                    "from_exchange": "bitfinex",
                    "to_exchange": "bitmex"
                }
            else:
                logger.info("Nessun trasferimento necessario per rebalancing - margini già equilibrati")
                return {"amount": 0, "from_exchange": None, "to_exchange": None}
                
        except Exception as e:
            logger.error(f"Errore calcolo rebalance transfer: {e}")
            return {"amount": 0, "from_exchange": None, "to_exchange": None}

    def _get_bitfinex_position(self, bot: Dict) -> Dict:
        """Recupera la posizione attiva su Bitfinex per SOL/USDT legata al bot"""
        try:
            from bson import ObjectId
            bot_id = bot.get("_id")
            # Assicurati che sia ObjectId
            if isinstance(bot_id, str):
                bot_id = ObjectId(bot_id)
            positions = position_manager.get_bot_positions(bot_id)
            
            # Cerca posizione SOL/USDT:USDT attiva su Bitfinex
            for position in positions:
                if (position.get("symbol") == "SOL/USDT:USDT" and 
                    position.get("exchange") == "bitfinex" and
                    position.get("status") == "open"):
                    logger.info(f"Posizione Bitfinex trovata per bot {bot_id}: {position}")
                    return position
                    
            logger.info(f"Nessuna posizione attiva su Bitfinex per bot {bot_id}")
            return None
            
        except Exception as e:
            logger.error(f"Errore recupero posizione Bitfinex: {e}")
            return None

    def _get_bitmex_position(self, bot: Dict) -> Dict:
        """Recupera la posizione attiva su BitMEX per SOLUSDT legata al bot"""
        try:
            from bson import ObjectId
            bot_id = bot.get("_id")
            # Assicurati che sia ObjectId
            if isinstance(bot_id, str):
                bot_id = ObjectId(bot_id)
            positions = position_manager.get_bot_positions(bot_id)
            
            # Cerca posizione SOL/USDT:USDT attiva su BitMEX
            for position in positions:
                if (position.get("symbol") == "SOL/USDT:USDT" and 
                    position.get("exchange") == "bitmex" and
                    position.get("status") == "open"):
                    logger.info(f"Posizione BitMEX trovata per bot {bot_id}: {position}")
                    return position
                    
            logger.info(f"Nessuna posizione attiva su BitMEX per bot {bot_id}")
            return None
            
        except Exception as e:
            logger.error(f"Errore recupero posizione BitMEX: {e}")
            return None

    def _get_exchange_position(self, exchange_obj, exchange_name: str) -> Optional[Dict]:
        """Recupera la posizione aperta dall'exchange (stesso metodo di balancer.py)
        
        Args:
            exchange_obj: Oggetto exchange inizializzato
            exchange_name: Nome dell'exchange
            
        Returns:
            Dict con i dati della posizione o None se non trovata
        """
        try:
            if not exchange_obj:
                logger.error(f"Exchange {exchange_name} non inizializzato")
                return None
            
            # Recupera tutte le posizioni
            positions = exchange_obj.fetch_positions()
            
            if exchange_name.lower() == "bitfinex":
                # Trova la prima posizione aperta (assumiamo ce ne sia solo una)
                for position in positions:
                    contracts = position.get('contracts', 0)
                    size = position.get('size', 0)
                    notional = position.get('notional', 0)
                    
                    # Controlla se la posizione è aperta
                    if contracts != 0 or size != 0 or notional != 0:
                        logger.info(f"Posizione trovata: {position.get('symbol')} - Size: {contracts or size} - Notional: {notional}")
                        return position
                        
            elif exchange_name.lower() == "bitmex":
                # Trova posizione aperta (currentQty != 0)
                for position in positions:
                    current_qty = position.get('contracts', 0)
                    if current_qty != 0:
                        logger.info(f"Posizione trovata: {position.get('symbol')} - Size: {current_qty}")
                        return position
            
            logger.warning(f"Nessuna posizione aperta trovata su {exchange_name}")
            return None
            
        except Exception as e:
            logger.error(f"Errore recupero posizione {exchange_name}: {e}")
            return None

    def _calculate_margin_adjustment(self, position: Dict, target_leverage: float, exchange: str, bot: Dict = None, exchange_obj = None) -> float:
        """Calcola l'aggiustamento di margine necessario per raggiungere la leva target
        Usa gli stessi metodi di balancer.py per recuperare i dati dall'exchange
        
        Args:
            position: Dati della posizione dal database (usato solo per il simbolo)
            target_leverage: Leva target
            exchange: Nome dell'exchange
            bot: Dati del bot (per ottenere API keys se necessario)
            exchange_obj: Oggetto exchange inizializzato
            
        Returns:
            Differenza di margine (positiva = aggiungere, negativa = rimuovere)
        """
        try:
            # Recupera la posizione aggiornata dall'exchange (stesso metodo di balancer.py)
            exchange_position = self._get_exchange_position(exchange_obj, exchange)
            
            if not exchange_position:
                logger.error(f"Impossibile recuperare posizione da {exchange}")
                return 0
            
            # Estrai i dati necessari dalla posizione dell'exchange
            if exchange.lower() == "bitfinex":
                # Per Bitfinex, il notional rappresenta effettivamente la size della posizione
                size = exchange_position.get('notional', 0)  # Per Bitfinex, notional = size in SOL
                entry_price = exchange_position.get('entryPrice', 0)  # Prezzo di entrata
                current_margin = exchange_position.get('collateral') or exchange_position.get('margin') or exchange_position.get('initialMargin', 0)
                unrealized_pnl = exchange_position.get('unrealizedPnl', 0)  # PnL non realizzato
                symbol = exchange_position.get('symbol', '')
                
                # Ottieni il prezzo corrente di Solana
                current_price = exchange_manager.get_solana_price(exchange)
                if not current_price:
                    logger.error(f"Impossibile ottenere prezzo corrente per {symbol}")
                    return 0
                
                if size == 0 or current_margin == 0:
                    logger.error(f"Dati insufficienti per calcolare aggiustamento: size={size}, margin={current_margin}")
                    return 0
                
                # Valore nominale della posizione usando prezzo corrente
                nominal_value = abs(size * current_price)
                
                # Calcola margine base per leva target
                base_margin = nominal_value / target_leverage
                
                # Sottrai il PnL non realizzato (se positivo riduce il collaterale necessario)
                target_margin = base_margin - unrealized_pnl
                
                # Il margine non può essere negativo o troppo basso
                target_margin = max(target_margin, 0.05)  # Minimo 0.05 USDT per evitare errore "collateral: insufficient"
                
                logger.info(f"Size posizione: {size} SOL")
                logger.info(f"Prezzo corrente: {current_price:.4f} USDT")
                logger.info(f"Prezzo entrata: {entry_price:.4f} USDT")
                logger.info(f"PnL non realizzato: {unrealized_pnl:.4f} USDT")
                logger.info(f"Valore nominale posizione: {nominal_value:.2f} USDT")
                logger.info(f"Margine base per {target_leverage}X: {base_margin:.2f} USDT")
                
                # Calcola differenza
                margin_diff = target_margin - current_margin
                
            elif exchange.lower() == "bitmex":
                # Per BitMEX, usa i dati dall'exchange
                notional = float(exchange_position.get('notional', 0))  # Valore della posizione in USDT
                current_margin = exchange_position.get('initialMargin') or exchange_position.get('collateral') or exchange_position.get('maintenanceMargin', 0)
                
                # Controlla anche il campo 'info' che potrebbe contenere dati raw
                info = exchange_position.get('info', {})
                if current_margin == 0 and info:
                    current_margin = info.get('posMargin') or info.get('posInit') or info.get('initMargin', 0)
                
                # Assicurati che current_margin sia un numero
                try:
                    current_margin = float(current_margin)
                except (TypeError, ValueError):
                    logger.error(f"Impossibile convertire current_margin a float: {current_margin}")
                    return 0
                
                # Converti da Satoshis a USDT se necessario
                if current_margin > 1000000:  # Probabilmente in Satoshis
                    current_margin = current_margin / 1_000_000  # Converti da Satoshis a USDT
                
                if notional == 0 or current_margin == 0:
                    logger.error(f"Dati insufficienti per calcolare aggiustamento: notional={notional}, margin={current_margin}")
                    return 0
                
                # Calcola margine target per leva target
                target_margin = notional / target_leverage
                
                # Calcola differenza
                margin_diff = target_margin - current_margin
                
                # Controlla margine massimo rimovibile per BitMEX quando si riduce il margine
                if margin_diff < 0:  # Solo quando si riduce il margine
                    # Usa il simbolo dalla posizione del database per compatibilità con il metodo esistente
                    symbol_to_use = position.get('symbol', '')
                    max_removable = self._get_bitmex_max_removable_margin_api(symbol_to_use, bot)
                    if max_removable is not None:
                        reduction_amount = abs(margin_diff)
                        # Applica 90% del margine massimo rimovibile per sicurezza
                        safe_max_removable = max_removable * 0.9
                        
                        if reduction_amount > safe_max_removable:
                            # Limita la riduzione al massimo sicuro
                            margin_diff = -safe_max_removable
                            logger.info(f"Riduzione limitata dal posCross di BitMEX:")
                            logger.info(f"  - Riduzione richiesta: {reduction_amount:.2f} USDT")
                            logger.info(f"  - Margine max rimovibile: {max_removable:.2f} USDT")
                            logger.info(f"  - Riduzione sicura (90%): {safe_max_removable:.2f} USDT")
                            logger.info(f"  - Riduzione finale: {abs(margin_diff):.2f} USDT")
                        else:
                            logger.info(f"Riduzione entro i limiti BitMEX: {reduction_amount:.2f} USDT (max: {max_removable:.2f} USDT)")
                    else:
                        logger.warning("Impossibile ottenere posCross da BitMEX, procedendo senza controllo")
                
            else:
                logger.error(f"Exchange {exchange} non supportato per calcolo aggiustamento margine")
                return 0
            
            logger.info(f"Margine attuale: {current_margin:.2f} USDT")
            logger.info(f"Margine target: {target_margin:.2f} USDT")
            logger.info(f"Differenza: {margin_diff:.2f} USDT")
            
            # Applica una tolleranza di 1 USDT
            if abs(margin_diff) < 1.0:
                logger.info("Differenza inferiore a 1 USDT, nessun aggiustamento necessario")
                return 0
            
            return margin_diff
            
        except Exception as e:
            logger.error(f"Errore calcolo aggiustamento margine: {e}")
            return 0

    def _get_bitmex_max_removable_margin_api(self, symbol: str, bot: Dict) -> float:
        """Recupera il margine massimo removibile da BitMEX usando le API"""
        try:
            if not bot:
                logger.warning("Bot non fornito per recupero margine BitMEX")
                return None
                
            # Ottieni le API keys dell'utente
            user_id = bot.get("user_id")
            user = user_manager.get_user_by_id(user_id)
            if not user:
                logger.error(f"Utente {user_id} non trovato")
                return None
                
            api_keys = {
                'bitmex_api_key': user.get('bitmex_api_key'),
                'bitmex_api_secret': user.get('bitmex_api_secret')
            }
            
            if not api_keys.get('bitmex_api_key') or not api_keys.get('bitmex_api_secret'):
                logger.error("API keys BitMEX non configurate")
                return None
            
            # Inizializza exchange BitMEX
            exchanges = self._initialize_exchanges(user_id)
            if not exchanges or 'bitmex' not in exchanges:
                logger.error("Impossibile inizializzare exchange BitMEX")
                return None
                
            bitmex_exchange = exchanges['bitmex']
            
            # Ottieni informazioni posizione da BitMEX
            try:
                positions = bitmex_exchange.fetch_positions([symbol])
                if not positions:
                    logger.warning(f"Nessuna posizione trovata per {symbol} su BitMEX")
                    return None
                    
                position = positions[0]
                info = position.get('info', {})
                
                # Il campo posCross indica il margine massimo removibile
                pos_cross = info.get('posCross')
                if pos_cross is not None:
                    # Converti da Satoshis a USDT se necessario
                    if pos_cross > 1000000:
                        pos_cross = pos_cross / 1_000_000
                    
                    logger.info(f"BitMEX posCross (margine removibile): {pos_cross:.2f} USDT")
                    return float(pos_cross)
                else:
                    logger.warning("Campo posCross non trovato nella risposta BitMEX")
                    return None
                    
            except Exception as api_error:
                logger.error(f"Errore API BitMEX per recupero posizione: {api_error}")
                return None
            
        except Exception as e:
            logger.error(f"Errore recupero margine removibile BitMEX: {e}")
            return None



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