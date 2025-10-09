"""Modulo Opener - Esegue operazioni di trading per bot con status 'ready'"""
import time
import logging
import os
import math
from typing import Dict, List
from datetime import datetime
from database.models import db_manager, user_manager, bot_manager, position_manager
from trading.exchange_manager import exchange_manager
from config.settings import BOT_STATUS

# Crea directory logs se non esiste
os.makedirs("logs", exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/opener_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingOpener:
    """Classe principale per apertura posizioni"""
    
    def __init__(self):
        self.running = False
        self.exchange_manager = exchange_manager
    
    def process_ready_bots(self) -> None:
        """Processa tutti i bot con status 'ready' o 'transfering'"""
        logger.info("Scansione bot con status 'ready' o 'transfering'...")
        
        ready_bots = bot_manager.get_ready_bots()
        logger.info(f"Trovati {len(ready_bots)} bot pronti")
        
        for bot in ready_bots:
            try:
                bot_status = bot.get('status')
                if bot_status == BOT_STATUS["TRANSFERING"]:
                    # Processa solo bot TRANSFERING con transfer_reason 'emergency_close' o 'first_start'
                    transfer_reason = bot.get('transfer_reason')
                    if transfer_reason not in ['emergency_close', 'first_start']:
                        logger.info(f"Bot TRANSFERING utente {bot['user_id']} saltato (reason: {transfer_reason})")
                        continue
                    logger.info(f"Processando bot TRANSFERING utente: {bot['user_id']} (reason: {transfer_reason})")
                else:
                    logger.info(f"Processando bot READY utente: {bot['user_id']}")
                    
                result = self.execute_trading_strategy(bot)
                
                if result == "success":
                    # Controlla se transfer_reason è "first_start" o "emergency_close" per impostarlo a "null"
                    current_transfer_reason = bot.get('transfer_reason')
                    new_transfer_reason = "null" if current_transfer_reason in ["first_start", "emergency_close"] else "waiting"
                    
                    # Aggiorna status a running con timestamp started_at e transfer_reason appropriato
                    bot_manager.update_bot_status(bot['user_id'], BOT_STATUS["RUNNING"], transfer_reason=new_transfer_reason)
                    logger.info(f"Bot {bot['user_id']} avviato con successo (transfer_reason: {current_transfer_reason} -> {new_transfer_reason})")
                elif result == "insufficient_capital":
                    # Capitale totale insufficiente - bot già fermato da _handle_balance_failure
                    logger.warning(f"Bot {bot['user_id']}: capitale totale insufficiente")
                elif result == "insufficient_capital_transfering":
                    # Bot TRANSFERING con capitale insufficiente - mantiene stato
                    logger.warning(f"Bot {bot['user_id']}: capitale insufficiente, mantengo TRANSFERING")
                elif result == "transfer_requested":
                    # Capitale sufficiente ma mal distribuito - bot già marcato per trasferimento
                    logger.info(f"Bot {bot['user_id']}: richiesto trasferimento per redistribuzione")
                elif result == "transfer_in_progress":
                    # Bot TRANSFERING con capitale mal distribuito - mantiene stato
                    logger.info(f"Bot {bot['user_id']}: capitale mal distribuito, mantengo TRANSFERING")
                elif result == "stop_loss_triggered":
                    # Bot TRANSFERING fermato per stop loss - già gestito in execute_trading_strategy
                    logger.warning(f"Bot {bot['user_id']}: fermato per stop loss")
                else:
                    # Altri errori - ferma il bot solo se non è TRANSFERING
                    if bot_status != BOT_STATUS["TRANSFERING"]:
                        bot_manager.update_bot_status(bot['user_id'], BOT_STATUS["STOPPED"], "error")
                        logger.error(f"Errore avvio bot {bot['user_id']}")
                    else:
                        logger.error(f"Errore bot TRANSFERING {bot['user_id']}, mantengo stato")
                    
            except Exception as e:
                logger.error(f"Errore processamento bot {bot['user_id']}: {e}")
                # Non fermare bot TRANSFERING in caso di errore generico
                if bot.get('status') != BOT_STATUS["TRANSFERING"]:
                    bot_manager.update_bot_status(bot['user_id'], BOT_STATUS["STOPPED"], "error")
    
    def execute_trading_strategy(self, bot_config: Dict) -> str:
        """Esegue strategia di trading per un bot specifico"""
        try:
            user_id = bot_config['user_id']
            exchange_long = bot_config['exchange_long']
            exchange_short = bot_config['exchange_short']
            capital = bot_config['capital']
            leverage = bot_config['leverage']
            bot_status = bot_config.get('status')
            stop_loss_percentage = bot_config.get('stop_loss_percentage', 20)  # Default 20% se non specificato
            
            logger.info(f"Configurazione bot: Long={exchange_long}, Short={exchange_short}, Capital={capital}, Leverage={leverage}, Status={bot_status}")
            
            # Recupera API keys utente
            api_keys = user_manager.get_user_api_keys(user_id)
            if not self.validate_api_keys(api_keys, exchange_long, exchange_short):
                logger.error("API keys mancanti o non valide")
                return False
            
            # Inizializza exchange
            if not self.initialize_exchanges(api_keys, exchange_long, exchange_short):
                logger.error("Errore inizializzazione exchange")
                return False
            
            # CONTROLLO CAPITALE TOTALE E DISTRIBUZIONE
            # Prima calcola available_balance (somma dei bilanci attuali)
            long_balance = self._get_exchange_balance(exchange_long, balance_type='total')
            short_balance = self._get_exchange_balance(exchange_short, balance_type='total')
            available_balance = long_balance + short_balance
            
            logger.info(f"Capitale configurato: {capital} USDT")
            logger.info(f"Available balance: {available_balance} USDT")
            logger.info(f"Stop loss percentage: {stop_loss_percentage}%")
            
            # CONTROLLO SPECIFICO PER BOT TRANSFERING: Verifica stop loss
            if bot_status == BOT_STATUS["TRANSFERING"]:
                stop_loss_threshold = capital - (capital * stop_loss_percentage / 100)
                logger.info(f"Bot TRANSFERING - Controllo stop loss: available_balance ({available_balance}) vs threshold ({stop_loss_threshold})")
                
                if available_balance <= stop_loss_threshold:
                    logger.warning(f"Bot TRANSFERING {user_id}: Stop loss attivato! Available balance {available_balance} <= threshold {stop_loss_threshold}")
                    bot_manager.update_bot_status(user_id, BOT_STATUS["STOPPED"], "stop_loss")
                    return "stop_loss_triggered"
                else:
                    logger.info(f"Bot TRANSFERING {user_id}: Stop loss OK, procedo con available_balance")
            
            # Determina quale valore usare per il position sizing
            if available_balance < capital:
                # Usa available_balance per position sizing
                base_amount_for_sizing = available_balance
                logger.info(f"Usando available_balance per position sizing: {base_amount_for_sizing} USDT (available_balance < capital)")
            else:
                # Usa capital per position sizing
                base_amount_for_sizing = capital
                logger.info(f"Usando capital per position sizing: {base_amount_for_sizing} USDT (available_balance >= capital)")
            
            # Calcola capital_per_exchange per position sizing
            capital_per_exchange_sizing = base_amount_for_sizing / 2
            capital_with_leverage = capital_per_exchange_sizing * leverage  # Applica leva per calcolo size
            
            # Per il controllo dei requisiti, determina il valore in base allo status del bot
            if bot_status == BOT_STATUS["READY"]:
                # Bot READY: Applica tolleranza del 2% sul capitale configurato
                tolerance_percentage = 2.0  # 2% di tolleranza
                min_capital_with_tolerance = capital * (1 - tolerance_percentage / 100)
                
                if available_balance >= min_capital_with_tolerance:
                    # Se available_balance è almeno il 98% del capitale, usa available_balance per il controllo
                    capital_per_exchange_check = available_balance / 2
                    logger.info(f"Bot READY: Tolleranza 2% applicata. Usando available_balance per controllo: {capital_per_exchange_check} USDT per exchange")
                else:
                    # Se available_balance è sotto il 98%, usa capital configurato (fallirà il controllo)
                    capital_per_exchange_check = capital / 2
                    logger.info(f"Bot READY: Available balance sotto tolleranza 2%. Usando capital configurato: {capital_per_exchange_check} USDT per exchange")
            else:
                # Bot TRANSFERING: Usa sempre available_balance per il controllo (già passato il controllo stop loss)
                capital_per_exchange_check = available_balance / 2
                logger.info(f"Bot TRANSFERING: Usando available_balance per controllo: {capital_per_exchange_check} USDT per exchange")
            
            logger.info(f"Controllo capitale richiesto per exchange: {capital_per_exchange_check} USDT")
            logger.info(f"Capitale per sizing per exchange: {capital_per_exchange_sizing} USDT")
            logger.info(f"Capitale con leva per exchange: {capital_with_leverage} USDT (per ordini)")
            
            # Usa capital_per_exchange_check per il controllo dei requisiti di capitale
            capital_check = self.check_capital_requirements(exchange_long, exchange_short, capital_per_exchange_check)
            if not capital_check['overall_success']:
                logger.error(f"Controllo capitale fallito: {capital_check}")
                return self._handle_balance_failure(capital_check, user_id)
            
            logger.info("✅ Controllo capitale completato con successo")
            
            logger.info(f"Capitale reale totale: {capital}, Per exchange: {capital_per_exchange_check}")
            logger.info(f"Capitale con leva per exchange: {capital_with_leverage} (per calcolo size)")
            
            # Ottieni prezzi SOLANA
            price_long = exchange_manager.get_solana_price(exchange_long)
            price_short = exchange_manager.get_solana_price(exchange_short)
            
            if not price_long or not price_short:
                logger.error("Errore recupero prezzi SOLANA")
                return False
            
            # Calcola size per entrambi gli exchange usando capitale con leva
            avg_price = (price_long + price_short) / 2
            size_long = exchange_manager.calculate_solana_size(capital_with_leverage, avg_price)
            size_short = exchange_manager.calculate_solana_size(capital_with_leverage, avg_price)
            
            if size_long <= 0 or size_short <= 0:
                logger.error("Size calcolate non valide")
                return False
            
            logger.info(f"Size calcolate - Long: {size_long}, Short: {size_short}")
            
            # Apri posizioni
            if self.open_positions(exchange_long, exchange_short, size_long, size_short, leverage, user_id, bot_config.get('_id'), bot_config):
                return "success"
            else:
                return "trading_error"
            
        except Exception as e:
            logger.error(f"Errore esecuzione strategia: {e}")
            return "error"
    
    def check_capital_requirements(self, exchange_long: str, exchange_short: str, required_amount: float) -> Dict:
        """Controlla capitale totale, distribuzione tra exchange e esegue automaticamente trasferimenti interni"""
        results = {
            'long_exchange': {'name': exchange_long, 'success': False, 'balance': 0},
            'short_exchange': {'name': exchange_short, 'success': False, 'balance': 0},
            'total_capital': 0,
            'required_total': required_amount * 2,
            'overall_success': False,
            'needs_transfer': False
        }
        
        try:
            # STEP 1: Controllo capitale totale da TUTTI i wallet
            # Usiamo sempre 'total' per sommare tutti i fondi disponibili
            long_balance = self._get_exchange_balance(exchange_long, balance_type='total')
            short_balance = self._get_exchange_balance(exchange_short, balance_type='total')
            
            results['long_exchange'] = {'name': exchange_long, 'balance': long_balance}
            results['short_exchange'] = {'name': exchange_short, 'balance': short_balance}
            results['total_capital'] = long_balance + short_balance
            
            logger.info(f"STEP 1 - Capitale totale: {results['total_capital']} USDT (richiesto: {results['required_total']})")
            logger.info(f"Distribuzione: {exchange_long}={long_balance}, {exchange_short}={short_balance}")
            
            # Verifica se capitale totale è sufficiente
            if results['total_capital'] < results['required_total']:
                logger.warning(f"STEP 1 FALLITO - Capitale totale insufficiente: {results['total_capital']} < {results['required_total']}")
                results['overall_success'] = False
                return results
            
            logger.info("STEP 1 OK - Capitale totale sufficiente")
            
            # STEP 2: Controllo distribuzione tra exchange (con tolleranza 1%)
            target_per_exchange = required_amount
            tolerance_percent = 1.0  # 1% di tolleranza
            tolerance_amount = target_per_exchange * (tolerance_percent / 100.0)
            min_acceptable_per_exchange = target_per_exchange - tolerance_amount
            
            long_sufficient = long_balance >= min_acceptable_per_exchange
            short_sufficient = short_balance >= min_acceptable_per_exchange
            
            # Log se viene applicata la tolleranza
            if long_balance < target_per_exchange and long_balance >= min_acceptable_per_exchange:
                logger.info(f"TOLLERANZA APPLICATA - Long: {long_balance} < {target_per_exchange} ma >= {min_acceptable_per_exchange:.4f} (tolleranza 1%)")
            if short_balance < target_per_exchange and short_balance >= min_acceptable_per_exchange:
                logger.info(f"TOLLERANZA APPLICATA - Short: {short_balance} < {target_per_exchange} ma >= {min_acceptable_per_exchange:.4f} (tolleranza 1%)")
            
            if not (long_sufficient and short_sufficient):
                logger.warning(f"STEP 2 FALLITO - Distribuzione tra exchange insufficiente (anche con tolleranza 1%)")
                logger.warning(f"Long: {long_balance}/{target_per_exchange} (min: {min_acceptable_per_exchange:.4f}), Short: {short_balance}/{target_per_exchange} (min: {min_acceptable_per_exchange:.4f})")
                results['overall_success'] = False
                results['needs_transfer'] = True
                return results
            
            logger.info("STEP 2 OK - Distribuzione tra exchange sufficiente")
            
            # STEP 3: Controllo e esecuzione automatica trasferimenti interni
            internal_transfer_success = self._check_and_execute_internal_transfers(exchange_long, exchange_short, required_amount)
            
            if internal_transfer_success:
                logger.info("STEP 3 OK - Wallet interni pronti per il trading")
                results['overall_success'] = True
                results['needs_transfer'] = False
            else:
                logger.warning("STEP 3 FALLITO - Impossibile preparare wallet interni")
                results['overall_success'] = False
                results['needs_transfer'] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Errore durante controllo capitale: {e}")
            return results
    
    def _check_and_execute_internal_transfers(self, exchange_long: str, exchange_short: str, required_amount: float) -> bool:
        """Controlla e esegue automaticamente i trasferimenti interni necessari"""
        success = True
        
        # Solo Bitfinex ha wallet separati che richiedono trasferimenti interni
        exchanges_to_check = []
        if exchange_long == 'bitfinex':
            exchanges_to_check.append(('bitfinex', 'long'))
        if exchange_short == 'bitfinex' and exchange_short != exchange_long:
            exchanges_to_check.append(('bitfinex', 'short'))
        
        for exchange, position_type in exchanges_to_check:
            try:
                # Controlla se è necessario un trasferimento interno
                transfer_needed = self._check_bitfinex_internal_transfer_needed(required_amount)
                
                if transfer_needed['needed']:
                    logger.info(f"Eseguendo trasferimento interno per Bitfinex ({position_type}): {transfer_needed['amount']} USDT")
                    
                    # Esegue il trasferimento interno
                    transfer_success = self._execute_bitfinex_internal_transfer(
                        transfer_needed['amount'],
                        transfer_needed['from_wallet'],
                        'margin'
                    )
                    
                    if not transfer_success:
                        logger.error(f"Fallito trasferimento interno Bitfinex ({position_type})")
                        success = False
                    else:
                        logger.info(f"Trasferimento interno Bitfinex ({position_type}) completato con successo")
                else:
                    logger.info(f"Bitfinex ({position_type}): wallet margin già sufficiente")
                    
            except Exception as e:
                logger.error(f"Errore durante trasferimento interno Bitfinex ({position_type}): {e}")
                success = False
        
        return success
    
    def _check_bitfinex_internal_transfer_needed(self, required_amount: float) -> Dict:
        """Controlla se è necessario un trasferimento interno in Bitfinex per derivatives"""
        try:
            # Recupera saldi derivatives (USTF0) e totali
            derivatives_balance = self._get_exchange_balance('bitfinex', balance_type='derivatives')
            total_balance = self._get_exchange_balance('bitfinex', balance_type='total')
            
            logger.info(f"Bitfinex - Saldo derivatives (USTF0): {derivatives_balance}, Saldo totale: {total_balance}")
            
            # Se il wallet derivatives ha già fondi sufficienti
            if derivatives_balance >= required_amount:
                return {'needed': False, 'derivatives_balance': derivatives_balance}
            
            # Calcola quanto trasferire
            transfer_amount = required_amount - derivatives_balance
            available_for_transfer = total_balance - derivatives_balance
            
            if available_for_transfer < transfer_amount:
                error_msg = f"Fondi insufficienti per trasferimento: disponibili {available_for_transfer}, richiesti {transfer_amount}"
                raise Exception(error_msg)
            
            result = {
                'needed': True,
                'amount': transfer_amount,
                'from_wallet': 'exchange',  # Assumiamo che i fondi extra siano nel wallet exchange
                'to_wallet': 'margin',  # Il trasferimento verso margin con USTF0 va nel derivatives wallet
                'derivatives_balance': derivatives_balance,
                'total_balance': total_balance
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Errore controllo trasferimento Bitfinex: {e}")
            raise
    
    def _execute_bitfinex_internal_transfer(self, amount: float, from_wallet: str, to_wallet: str) -> bool:
        """Esegue un trasferimento interno in Bitfinex"""
        try:
            logger.info(f"Eseguendo trasferimento Bitfinex: {amount} USDT da {from_wallet} a {to_wallet}")
            
            # Usa il metodo esistente _bitfinex_internal_transfer
            result = self._bitfinex_internal_transfer(amount, from_wallet, to_wallet)
            
            if result and result.get('success'):
                logger.info(f"Trasferimento Bitfinex completato con successo")
                return True
            else:
                logger.error(f"Trasferimento Bitfinex fallito: {result.get('error', 'Errore sconosciuto')}")
                return False
                
        except Exception as e:
            logger.error(f"Errore durante trasferimento Bitfinex: {e}")
            return False
    

    
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
                exchange = exchange_manager.exchanges['bitmex']
                balance = exchange.fetch_balance()
                return balance.get('USDT', {}).get('total', 0)
            
            elif exchange_name.lower() == 'bitfinex':
                exchange = exchange_manager.exchanges['bitfinex']
                
                if balance_type == 'derivatives':
                    # Solo USTF0 dal wallet margin (derivatives wallet)
                    # Usa l'array 'info' per rilevare correttamente i fondi USTF0
                    try:
                        balance = exchange.fetch_balance({'type': 'margin'})
                        ustf0_balance = 0
                        
                        # Controlla anche il balance standard per USTF0
                        if 'USTF0' in balance:
                            ustf0_balance = balance['USTF0'].get('free', 0)
                        
                        # Estrae i balance dall'array 'info' (metodo del balance_checker)
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
                
                elif balance_type == 'tradable':
                    # Balance dal wallet margin per trading normale (USDT, UST)
                    try:
                        balance = exchange.fetch_balance({'type': 'margin'})
                        currencies = ['USDT', 'UST']  # Escluso USTF0 che è per derivatives
                        tradable_balance = 0
                        
                        for currency in currencies:
                            if currency in balance and balance[currency]['free'] > 0:
                                tradable_balance += balance[currency]['free']
                        
                        logger.debug(f"Bitfinex tradable balance: {tradable_balance} USDT")
                        return tradable_balance
                    except Exception as e:
                        logger.error(f"Errore recupero saldo tradable Bitfinex: {e}")
                        return 0
                
                else:  # balance_type == 'total'
                    # Recupera TUTTI i fondi da TUTTI i wallet per controllo capitale totale
                    wallets = ['exchange', 'margin', 'funding']
                    currencies = ['USTF0', 'USDT', 'UST']
                    total_balance = 0
                    
                    for wallet in wallets:
                        try:
                            balance = exchange.fetch_balance({'type': wallet})
                            
                            # Somma tutti i fondi disponibili (free) di tutte le valute supportate
                            for currency in currencies:
                                if currency in balance and balance[currency]['free'] > 0:
                                    amount = balance[currency]['free']
                                    total_balance += amount
                                    logger.debug(f"Bitfinex {wallet} wallet - {currency}: {amount}")
                                    
                        except Exception as e:
                            logger.warning(f"Errore recupero saldo {wallet}: {e}")
                    
                    logger.debug(f"Bitfinex total balance (tutti i wallet): {total_balance} USDT")
                    return total_balance
            
            return 0
            
        except Exception as e:
            logger.error(f"Errore recupero saldo {exchange_name} ({balance_type}): {e}")
            return 0
    
    def _handle_balance_failure(self, capital_check: Dict, user_id: str) -> str:
        """Gestisce i diversi tipi di fallimento del controllo capitale"""
        try:
            # Recupera lo stato attuale del bot
            current_bot = bot_manager.get_user_bot(user_id)
            current_status = current_bot.get('status') if current_bot else None
            
            if capital_check['total_capital'] < capital_check['required_total']:
                # STEP 1 FALLITO: Capitale totale insufficiente
                if current_status == BOT_STATUS["TRANSFERING"]:
                    # Se è TRANSFERING, mantieni lo stato (trasferimento potrebbe essere in corso)
                    logger.warning(f"Bot {user_id}: capitale totale insufficiente, mantengo stato TRANSFERING")
                    return "insufficient_capital_transfering"
                else:
                    # Se è READY, ferma il bot
                    logger.warning(f"Bot {user_id}: capitale totale insufficiente")
                    bot_manager.update_bot_status(user_id, BOT_STATUS["STOPPED"], "not_enough_capital")
                    return "insufficient_capital"
            
            elif capital_check['needs_transfer']:
                # STEP 2 FALLITO: Capitale sufficiente ma mal distribuito tra exchange
                if current_status == BOT_STATUS["TRANSFERING"]:
                    # Se è TRANSFERING, mantieni lo stato (trasferimento potrebbe essere in corso)
                    logger.info(f"Bot {user_id}: capitale mal distribuito tra exchange, mantengo stato TRANSFERING")
                    return "transfer_in_progress"
                else:
                    # Se è READY, richiedi trasferimento tra exchange
                    logger.info(f"Bot {user_id}: richiesto trasferimento tra exchange per redistribuzione")
                    bot_manager.update_bot_status(user_id, BOT_STATUS["TRANSFER_REQUESTED"], transfer_reason="first_start")
                    return "transfer_requested"
            
            # Se arriviamo qui, significa che check_capital_requirements ha già gestito
            # automaticamente i trasferimenti interni e ha fallito
            logger.warning(f"Bot {user_id}: controllo capitale fallito dopo tentativi automatici")
            return "capital_check_failed"
            
        except Exception as e:
            logger.error(f"Errore gestione fallimento capitale: {e}")
            return "error"
    
    def validate_api_keys(self, api_keys: Dict, exchange_long: str, exchange_short: str) -> bool:
        """Valida che le API keys siano disponibili"""
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
        
        return True
    
    def initialize_exchanges(self, api_keys: Dict, exchange_long: str, exchange_short: str) -> bool:
        """Inizializza connessioni agli exchange"""
        try:
            # Inizializza exchange long
            success_long = exchange_manager.initialize_exchange(
                exchange_long,
                api_keys[f"{exchange_long}_api_key"],
                api_keys[f"{exchange_long}_api_secret"]
            )
            
            # Inizializza exchange short
            success_short = exchange_manager.initialize_exchange(
                exchange_short,
                api_keys[f"{exchange_short}_api_key"],
                api_keys[f"{exchange_short}_api_secret"]
            )
            
            return success_long and success_short
            
        except Exception as e:
            logger.error(f"Errore inizializzazione exchange: {e}")
            return False
    
    def open_positions(self, exchange_long: str, exchange_short: str, 
                      size_long: float, size_short: float, leverage: float, 
                      user_id: str, bot_id: str, bot_config: Dict) -> bool:
        """Apre posizioni sui due exchange con leva specificata"""
        try:
            logger.info(f"Apertura posizioni con leva {leverage}x...")
            
            # Apri posizione LONG
            order_long = exchange_manager.create_market_order(
                exchange_long, 'buy', size_long, leverage
            )
            
            if not order_long:
                logger.error(f"Errore apertura posizione long su {exchange_long}")
                return False
            
            logger.info(f"Posizione long aperta su {exchange_long}: {order_long}")
            
            # Salva posizione LONG nel database
            self.save_position_to_db(order_long, user_id, bot_id, exchange_long, "long", leverage, bot_config)
            
            # Apri posizione SHORT
            order_short = exchange_manager.create_market_order(
                exchange_short, 'sell', size_short, leverage
            )
            
            if not order_short:
                logger.error(f"Errore apertura posizione short su {exchange_short}")
                # Prova a chiudere posizione long già aperta
                logger.info("Tentativo chiusura posizione long...")
                exchange_manager.close_position(exchange_long)
                return False
            
            logger.info(f"Posizione short aperta su {exchange_short}: {order_short}")
            
            # Salva posizione SHORT nel database
            self.save_position_to_db(order_short, user_id, bot_id, exchange_short, "short", leverage, bot_config)
            
            logger.info("Strategia di funding arbitrage attivata con successo!")
            
            return True
            
        except Exception as e:
            logger.error(f"Errore apertura posizioni: {e}")
            return False
    
    def save_position_to_db(self, order: Dict, user_id: str, bot_id: str, exchange_name: str, 
                           side: str, leverage: float, bot_config: Dict) -> bool:
        """Salva posizione nel database dopo apertura ordine"""
        try:
            from datetime import datetime
            
            # Estrai liquidation price dall'ordine se disponibile
            liquidation_price = None
            if isinstance(order.get('info'), dict):
                # Prova diversi campi per liquidation price
                liquidation_price = (order['info'].get('liquidationPrice') or 
                                   order['info'].get('liqPrice') or 
                                   order.get('liquidationPrice'))
            
            # Se non disponibile dall'ordine, prova a recuperarlo dalla posizione
            if not liquidation_price:
                liquidation_price = self.fetch_liquidation_price(
                    exchange_name, order.get('symbol'), side
                )

            # Calcola safety_value e rebalance_value se liquidation_price è disponibile
            safety_value = None
            rebalance_value = None
            
            if liquidation_price:
                try:
                    # Recupera threshold dal bot config
                    safety_threshold = bot_config.get('safety_threshold')
                    rebalance_threshold = bot_config.get('rebalance_threshold')
                    
                    # Estrai entry_price dall'ordine
                    entry_price = float(order.get('average') or order.get('price', 0))
                    
                    if safety_threshold and entry_price > 0:
                        safety_value = self.calculate_threshold_value(liquidation_price, safety_threshold, side, entry_price)
                    
                    if rebalance_threshold and entry_price > 0:
                        rebalance_value = self.calculate_threshold_value(liquidation_price, rebalance_threshold, side, entry_price)
                        
                    logger.info(f"Valori soglia calcolati - Safety: {safety_value}, Rebalance: {rebalance_value}")
                        
                except Exception as e:
                    logger.warning(f"Errore calcolo valori soglia: {e}")

            position_data = {
                "position_id": order.get('id', f"temp_{int(time.time())}"),
                "user_id": user_id,
                "bot_id": bot_id,
                "exchange": exchange_name,
                "symbol": order.get('symbol', ''),
                "side": side,
                "size": float(order.get('amount', 0)),
                "entry_price": float(order.get('average') or order.get('price', 0)),
                "leverage": float(leverage),
                "liquidation_price": float(liquidation_price) if liquidation_price else None,
                "safety_value": float(safety_value) if safety_value else None,
                "rebalance_value": float(rebalance_value) if rebalance_value else None,
                "opened_at": datetime.utcnow(),
                "closed_at": None,
                "close_price": None,
                "realized_pnl": None,
                "status": "open"
            }
            
            success = position_manager.save_position(position_data)
            if success:
                logger.info(f"✅ Posizione {side} salvata nel database: {position_data['position_id']}")
            else:
                logger.error(f"❌ Errore salvataggio posizione {side} nel database")
            
            return success
            
        except Exception as e:
            logger.error(f"Errore salvataggio posizione {side}: {e}")
            return False
    
    def fetch_liquidation_price(self, exchange_name: str, symbol: str, side: str) -> float:
        """Recupera liquidation price dalle API dell'exchange
        
        Args:
            exchange_name: Nome dell'exchange
            symbol: Simbolo trading
            side: "long" o "short"
            
        Returns:
            float: Liquidation price o None se non disponibile
        
        Note: Funzione duplicata da threshold_monitoring.py per indipendenza del modulo
        """
        try:
            # Verifica che l'exchange sia inizializzato
            if exchange_name not in exchange_manager.exchanges:
                return None
            
            # Per BitMEX usa logica specifica con fetch_positions()
            if exchange_name.lower() == 'bitmex':
                exchange = exchange_manager.exchanges[exchange_name]
                positions = exchange.fetch_positions()
                for pos in positions:
                    # BitMEX usa 'contracts' invece di 'size'
                    contracts = pos.get('contracts', 0)
                    size = pos.get('size', 0)
                    
                    if (pos.get('symbol') == symbol and 
                        (contracts != 0 or size != 0) and
                        pos.get('side', '').lower() == side.lower()):
                        
                        liquidation_price = pos.get('liquidationPrice')
                        if liquidation_price:
                            logger.info(f"Liquidation price recuperato da {exchange_name}: {liquidation_price}")
                            return float(liquidation_price)
            else:
                # Altri exchange: usa exchange_manager.get_position() (metodo testato)
                position = exchange_manager.get_position(exchange_name)
                if position and position.get('liquidationPrice'):
                    liquidation_price = float(position['liquidationPrice'])
                    logger.info(f"Liquidation price recuperato da {exchange_name}: {liquidation_price}")
                    return liquidation_price
            
            return None
            
        except Exception as e:
            logger.error(f"Errore recupero liquidation price da {exchange_name}: {e}")
            return None
    
    def calculate_threshold_value(self, liquidation_price: float, threshold_percent: float, side: str, entry_price: float = None) -> float:
        """Calcola il valore threshold basato sulla differenza tra entry_price e liquidation_price
        
        Args:
            liquidation_price: Prezzo di liquidazione
            threshold_percent: Percentuale di threshold
            side: "long" o "short"
            entry_price: Prezzo di ingresso (opzionale per retrocompatibilità)
            
        Returns:
            float: Valore threshold calcolato
        
        Note: Nuova logica basata sulla differenza tra entry_price e liquidation_price
        """
        try:
            # Se entry_price non è fornito, usa la vecchia logica per retrocompatibilità
            if entry_price is None or entry_price <= 0:
                logger.warning("Entry price non disponibile, uso vecchia logica di calcolo")
                threshold_amount = liquidation_price * (threshold_percent / 100.0)
                if side.lower() == "long":
                    threshold_value = liquidation_price + threshold_amount
                else:  # short
                    threshold_value = liquidation_price - threshold_amount
                return round(threshold_value, 6)
            
            # Nuova logica: calcola la differenza tra entry_price e liquidation_price
            # e applica la percentuale a questa differenza
            if side.lower() == "long":
                # Per LONG: entry_price > liquidation_price
                price_difference = entry_price - liquidation_price
                threshold_amount = price_difference * (threshold_percent / 100.0)
                threshold_value = liquidation_price + threshold_amount
            else:  # short
                # Per SHORT: liquidation_price > entry_price
                price_difference = liquidation_price - entry_price
                threshold_amount = price_difference * (threshold_percent / 100.0)
                threshold_value = liquidation_price - threshold_amount
            
            logger.info(f"Calcolo threshold {side}: entry={entry_price}, liq={liquidation_price}, diff={price_difference:.4f}, threshold={threshold_value:.4f}")
            return round(threshold_value, 6)  # Arrotonda a 6 decimali
            
        except Exception as e:
            logger.error(f"Errore calcolo threshold value: {e}")
            return 0.0
    
    def check_bitmex_balance(self, required_amount: float) -> Dict:
        """Controlla saldo USDT su BitMEX"""
        try:
            balance = exchange_manager.get_balance('bitmex')
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            
            success = usdt_balance >= required_amount
            
            return {
                'name': 'bitmex',
                'success': success,
                'balance': usdt_balance,
                'required': required_amount
            }
            
        except Exception as e:
            logger.error(f"Errore controllo saldo BitMEX: {e}")
            return {'name': 'bitmex', 'success': False, 'balance': 0, 'required': required_amount}
    

    

    
    def _bitfinex_internal_transfer(self, amount, from_wallet='exchange', to_wallet='margin'):
        """Esegue un trasferimento interno su Bitfinex tra i wallet"""
        try:
            logger.info(f"Trasferimento interno Bitfinex: {amount} USDT da {from_wallet} a {to_wallet}")
            
            actual_currency = "USTF0" if from_wallet == "margin" else "UST"
            actual_currency_to = "USTF0" if to_wallet == "margin" else "UST"
            
            # Usa l'exchange manager esistente
            exchange = exchange_manager.exchanges['bitfinex']
            
            params = {
                "from": from_wallet,
                "to": to_wallet,
                "currency": actual_currency,
                "amount": str(amount)
            }
            
            if actual_currency != actual_currency_to:
                params["currency_to"] = actual_currency_to
                logger.info(f"Conversione da {actual_currency} a {actual_currency_to}")
            
            if hasattr(exchange, 'privatePostAuthWTransfer'):
                result = exchange.privatePostAuthWTransfer(params)
                
                if result and isinstance(result, list) and len(result) > 0:
                    status = result[6] if len(result) > 6 else "UNKNOWN"
                    
                    if status == "SUCCESS":
                        return {
                            "success": True,
                            "message": f"Trasferimento interno Bitfinex di {amount} USDT da {from_wallet} a {to_wallet} completato con successo",
                            "transaction_id": result[2] if len(result) > 2 else None,
                            "info": result
                        }
                    else:
                        error_msg = result[7] if len(result) > 7 else "Errore sconosciuto"
                        return {
                            "success": False,
                            "error": f"Trasferimento interno Bitfinex fallito: {status} - {error_msg}",
                            "info": result
                        }
            else:
                return {
                    "success": False,
                    "error": "Metodo privatePostAuthWTransfer non disponibile"
                }
                
        except Exception as e:
            logger.error(f"Errore durante il trasferimento interno Bitfinex: {str(e)}")
            return {
                "success": False,
                "error": f"Errore durante il trasferimento interno Bitfinex: {str(e)}"
            }


def main():
    """Funzione principale del modulo Opener"""
    opener = TradingOpener()
    
    logger.info("🚀 Avvio modulo Opener...")
    logger.info("Controllo bot con status 'ready'...")
    
    try:
        opener.process_ready_bots()
        logger.info("✅ Scansione completata")
        
    except KeyboardInterrupt:
        logger.info("❌ Modulo Opener interrotto dall'utente")
    except Exception as e:
        logger.error(f"❌ Errore generale: {e}")
    finally:
        # Chiudi connessione database
        db_manager.close()
        logger.info("🔚 Modulo Opener terminato")

if __name__ == "__main__":
    main()