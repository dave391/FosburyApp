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
            leverage = bot_config['leverage']
            bot_status = bot_config.get('status')
            stop_loss_percentage = bot_config.get('stop_loss_percentage', 20)  # Default 20% se non specificato
            
            # Determina il capitale da usare in base al flag increase
            is_increment = bot_config.get('increase', False)
            if is_increment:
                capital = bot_config.get('capital_increase', 0.0)
                logger.info(f"Modalità incremento capitale: usando capital_increase = {capital} USDT")
            else:
                capital = bot_config['capital']
                logger.info(f"Modalità normale: usando capital = {capital} USDT")
            
            logger.info(f"Configurazione bot: Long={exchange_long}, Short={exchange_short}, Capital={capital}, Leverage={leverage}, Status={bot_status}, Increment={is_increment}")
            
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
            
            # CONTROLLO SPECIFICO PER BOT TRANSFERING: Verifica stop loss (saltato per incrementi di capitale)
            if bot_status == BOT_STATUS["TRANSFERING"]:
                if is_increment:
                    logger.info(f"Bot TRANSFERING {user_id}: Incremento capitale - salto controllo stop loss")
                else:
                    stop_loss_threshold = capital - (capital * stop_loss_percentage / 100)
                    logger.info(f"Bot TRANSFERING - Controllo stop loss: available_balance ({available_balance}) vs threshold ({stop_loss_threshold})")
                    
                    if available_balance <= stop_loss_threshold:
                        logger.warning(f"Bot TRANSFERING {user_id}: Stop loss attivato! Available balance {available_balance} <= threshold {stop_loss_threshold}")
                        bot_manager.update_bot_status(user_id, BOT_STATUS["STOPPED"], "stop_loss")
                        return "stop_loss_triggered"
                    else:
                        logger.info(f"Bot TRANSFERING {user_id}: Stop loss OK, procedo con available_balance")
            
            # Determina se applicare logica READY (per bot READY o TRANSFERING con first_start)
            transfer_reason = bot_config.get('transfer_reason')
            use_ready_logic = (bot_status == BOT_STATUS["READY"]) or \
                             (bot_status == BOT_STATUS["TRANSFERING"] and transfer_reason == "first_start")
            
            # Determina quale valore usare per il position sizing
            if use_ready_logic:
                # Logica READY: usa il minore tra available_balance e capital
                if available_balance < capital:
                    base_amount_for_sizing = available_balance
                    logger.info(f"Usando available_balance per position sizing: {base_amount_for_sizing} USDT (available_balance < capital)")
                else:
                    base_amount_for_sizing = capital
                    logger.info(f"Usando capital per position sizing: {base_amount_for_sizing} USDT (available_balance >= capital)")
            else:
                # Logica TRANSFERING standard: usa sempre il minore tra available_balance e capital
                if available_balance < capital:
                    base_amount_for_sizing = available_balance
                    logger.info(f"Bot TRANSFERING: Usando available_balance per position sizing: {base_amount_for_sizing} USDT")
                else:
                    base_amount_for_sizing = capital
                    logger.info(f"Bot TRANSFERING: Usando capital per position sizing: {base_amount_for_sizing} USDT")
            
            # Calcola capital_per_exchange per position sizing
            capital_per_exchange_sizing = base_amount_for_sizing / 2
            capital_with_leverage = capital_per_exchange_sizing * leverage  # Applica leva per calcolo size
            
            # Per il controllo dei requisiti, determina il valore in base alla logica specifica
            if is_increment:
                # 🔄 MODALITÀ INCREMENTO: Usa solo il capitale aggiuntivo per il controllo
                capital_per_exchange_check = capital / 2  # capital è già capital_increase in modalità incremento
                logger.info(f"🔄 MODALITÀ INCREMENTO: Controllo solo capitale aggiuntivo: {capital_per_exchange_check} USDT per exchange")
                logger.info(f"   Capitale aggiunto dall'utente: {capital} USDT")
                logger.info(f"   Available balance totale: {available_balance} USDT")
                logger.info(f"   Distribuzione richiesta: {capital_per_exchange_check} USDT per exchange")
            elif bot_status == BOT_STATUS["READY"]:
                # Logica READY: Applica tolleranza del 2% sul capitale configurato
                tolerance_percentage = 2.0  # 2% di tolleranza
                min_capital_with_tolerance = capital * (1 - tolerance_percentage / 100)
                
                if available_balance >= min_capital_with_tolerance:
                    # Se available_balance è almeno il 98% del capitale, usa available_balance per il controllo
                    capital_per_exchange_check = available_balance / 2
                    logger.info(f"Logica READY: Tolleranza 2% applicata. Usando available_balance per controllo: {capital_per_exchange_check} USDT per exchange")
                else:
                    # Se available_balance è sotto il 98%, usa capital configurato (fallirà il controllo)
                    capital_per_exchange_check = capital / 2
                    logger.info(f"Logica READY: Available balance sotto tolleranza 2%. Usando capital configurato: {capital_per_exchange_check} USDT per exchange")
            elif bot_status == BOT_STATUS["TRANSFERING"] and transfer_reason in ["first_start", "emergency_close"]:
                # Bot TRANSFERING con first_start o emergency_close: Usa sempre capital configurato per il controllo distribuzione
                capital_per_exchange_check = capital / 2
                logger.info(f"Bot TRANSFERING {transfer_reason}: Usando capital configurato per controllo: {capital_per_exchange_check} USDT per exchange")
            else:
                # Bot TRANSFERING standard: Usa sempre available_balance per il controllo (già passato il controllo stop loss)
                capital_per_exchange_check = available_balance / 2
                logger.info(f"Bot TRANSFERING: Usando available_balance per controllo: {capital_per_exchange_check} USDT per exchange")
            
            logger.info(f"Controllo capitale richiesto per exchange: {capital_per_exchange_check} USDT")
            logger.info(f"Capitale per sizing per exchange: {capital_per_exchange_sizing} USDT")
            logger.info(f"Capitale con leva per exchange: {capital_with_leverage} USDT (per ordini)")
            
            # Usa capital_per_exchange_check per il controllo dei requisiti di capitale
            capital_check = self.check_capital_requirements(exchange_long, exchange_short, capital_per_exchange_check, is_increment=is_increment)
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
                # Se è un incremento, aggiorna il capitale nel database dopo il successo
                if is_increment:
                    capital_increase = bot_config.get('capital_increase', 0.0)
                    current_capital = bot_config.get('capital', 0.0)
                    new_capital = current_capital + capital_increase
                    
                    logger.info(f"Incremento completato con successo. Aggiornamento capitale: {current_capital} + {capital_increase} = {new_capital}")
                    
                    # Aggiorna il capitale totale nel database
                    bot_manager.bots.update_one(
                        {"_id": bot_config["_id"]},
                        {"$set": {
                            "capital": new_capital,
                            "capital_increase": 0.0,
                            "increase": False
                        }}
                    )
                    
                    logger.info(f"Capitale bot {user_id} aggiornato con successo a {new_capital} USDT")
                
                return "success"
            else:
                return "trading_error"
            
        except Exception as e:
            logger.error(f"Errore esecuzione strategia: {e}")
            return "error"
    
    def check_capital_requirements(self, exchange_long: str, exchange_short: str, required_amount: float, is_increment: bool = False) -> Dict:
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
            internal_transfer_success = self._check_and_execute_internal_transfers(exchange_long, exchange_short, required_amount, is_increment=is_increment)
            
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
    
    def _check_and_execute_internal_transfers(self, exchange_long: str, exchange_short: str, required_amount: float, is_increment: bool = False) -> bool:
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
                transfer_needed = self._check_bitfinex_internal_transfer_needed(required_amount, is_increment=is_increment)
                
                if transfer_needed['needed']:
                    logger.info(f"Eseguendo trasferimento interno per Bitfinex ({position_type}): {transfer_needed['amount']} USDT")
                    logger.info(f"Piano trasferimenti: {len(transfer_needed['transfer_plan'])} step necessari")
                    
                    # Esegue il piano di trasferimenti multipli
                    transfer_success = self._execute_bitfinex_internal_transfer(transfer_needed['transfer_plan'])
                    
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
    
    def _get_bitfinex_wallet_distribution(self) -> Dict:
        """Ottiene la distribuzione dettagliata dei fondi tra i wallet Bitfinex"""
        try:
            exchange = exchange_manager.exchanges['bitfinex']
            wallets = ['exchange', 'margin', 'funding']
            currencies = ['USTF0', 'USDT', 'UST']
            distribution = {}
            
            # Inizializza tutti i wallet e valute a 0
            for wallet in wallets:
                distribution[wallet] = {}
                for currency in currencies:
                    distribution[wallet][currency] = 0
            
            # Usa il metodo che funziona: fetch_balance senza parametri e leggi dall'array info
            try:
                logger.debug("Recupero bilanci Bitfinex usando array info...")
                balance = exchange.fetch_balance()
                logger.debug(f"Balance completo: {balance}")
                
                # Estrae i balance dall'array 'info' (metodo che funziona)
                if 'info' in balance and isinstance(balance['info'], list):
                    for balance_entry in balance['info']:
                        if len(balance_entry) >= 5:
                            entry_wallet = balance_entry[0]
                            entry_currency = balance_entry[1]
                            entry_total = float(balance_entry[4]) if balance_entry[4] else 0
                            
                            logger.debug(f"Entry: wallet={entry_wallet}, currency={entry_currency}, total={entry_total}")
                            
                            # Filtra solo i wallet e valute che ci interessano
                            if entry_wallet in wallets and entry_currency in currencies and entry_total > 0:
                                distribution[entry_wallet][entry_currency] = entry_total
                                logger.debug(f"Aggiunto: {entry_wallet}.{entry_currency} = {entry_total}")
                else:
                    logger.warning("Array 'info' non trovato nel balance Bitfinex")
                            
            except Exception as e:
                logger.error(f"Errore recupero bilanci Bitfinex: {e}")
                # Mantieni tutti i valori a 0 già inizializzati
            
            # Calcola totali per wallet e valute
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
            
            logger.debug(f"Distribuzione fondi Bitfinex: {distribution}")
            return distribution
            
        except Exception as e:
            logger.error(f"Errore recupero distribuzione wallet Bitfinex: {e}")
            return {}

    def _calculate_transfer_plan(self, distribution: Dict, required_amount: float) -> List[Dict]:
        """Calcola il piano di trasferimento ottimale da wallet multipli"""
        try:
            transfer_plan = []
            remaining_amount = required_amount
            
            # Priorità di trasferimento: exchange > funding > margin (escluso USTF0)
            # Non trasferiamo da margin USTF0 perché è la destinazione
            source_priorities = [
                ('exchange', ['UST', 'USDT']),
                ('funding', ['UST', 'USDT']),
                ('margin', ['UST', 'USDT'])  # Solo UST/USDT, non USTF0
            ]
            
            for wallet, currencies in source_priorities:
                if remaining_amount <= 0:
                    break
                    
                for currency in currencies:
                    if remaining_amount <= 0:
                        break
                        
                    available = distribution[wallet][currency]
                    if available > 0:
                        # Trasferisce il minimo tra disponibile e richiesto
                        transfer_amount = min(available, remaining_amount)
                        
                        transfer_step = {
                            'from_wallet': wallet,
                            'to_wallet': 'margin',
                            'currency_from': currency,
                            'currency_to': 'USTF0',
                            'amount': transfer_amount,
                            'available': available
                        }
                        
                        transfer_plan.append(transfer_step)
                        remaining_amount -= transfer_amount
                        
                        logger.debug(f"Piano trasferimento: {transfer_amount} {currency} da {wallet} a margin")
            
            if remaining_amount > 0:
                logger.warning(f"Piano trasferimento incompleto: mancano {remaining_amount} USDT")
            
            return transfer_plan
            
        except Exception as e:
            logger.error(f"Errore calcolo piano trasferimento: {e}")
            return []

    def _check_bitfinex_internal_transfer_needed(self, required_amount: float, is_increment: bool = False) -> Dict:
        """Controlla se è necessario un trasferimento interno in Bitfinex per derivatives"""
        try:
            # Ottiene la distribuzione dettagliata dei fondi
            distribution = self._get_bitfinex_wallet_distribution()
            if not distribution:
                raise Exception("Impossibile ottenere distribuzione wallet Bitfinex")
            
            # Saldo derivatives attuale (USTF0 + UST nel wallet margin - UST può essere convertito automaticamente)
            derivatives_balance = distribution['margin']['USTF0'] + distribution['margin']['UST']
            total_balance = distribution['totals']['grand_total']
            
            logger.info(f"Bitfinex - Saldo derivatives (USTF0+UST): {derivatives_balance} (USTF0: {distribution['margin']['USTF0']}, UST: {distribution['margin']['UST']}), Saldo totale: {total_balance}")
            logger.info(f"Distribuzione wallet: exchange={distribution['totals']['by_wallet']['exchange']:.2f}, "
                       f"margin={distribution['totals']['by_wallet']['margin']:.2f}, "
                       f"funding={distribution['totals']['by_wallet']['funding']:.2f}")
            
            # 🔄 MODALITÀ INCREMENTO: Logica speciale per incrementi
            if is_increment:
                # Per Bitfinex, margin e derivatives sono lo stesso wallet
                # Se ci sono già fondi sufficienti nel margin (che è derivatives), non serve trasferimento
                total_margin_balance = distribution['totals']['by_wallet']['margin']
                
                logger.info(f"🔄 MODALITÀ INCREMENTO - Controllo fondi esistenti nel wallet margin/derivatives")
                logger.info(f"   Fondi disponibili nel margin: {total_margin_balance} USDT")
                logger.info(f"   Fondi richiesti per incremento: {required_amount} USDT")
                
                if total_margin_balance >= required_amount:
                    logger.info(f"🔄 INCREMENTO: Fondi sufficienti già presenti nel wallet margin/derivatives ({total_margin_balance} >= {required_amount})")
                    logger.info(f"🔄 INCREMENTO: Saltando trasferimento interno - procedendo direttamente con apertura posizioni")
                    return {'needed': False, 'derivatives_balance': derivatives_balance, 'increment_mode': True}
                else:
                    logger.info(f"🔄 INCREMENTO: Fondi insufficienti nel margin/derivatives - serve trasferimento interno")
            
            # Se il wallet derivatives ha già fondi sufficienti (logica normale)
            if derivatives_balance >= required_amount:
                return {'needed': False, 'derivatives_balance': derivatives_balance}
            
            # Calcola quanto trasferire
            transfer_amount = required_amount - derivatives_balance
            available_for_transfer = total_balance - derivatives_balance
            
            # Applica tolleranza 1% per evitare blocchi per piccole differenze
            tolerance_threshold = transfer_amount * 0.99  # 99% dell'importo richiesto
            
            if available_for_transfer < tolerance_threshold:
                error_msg = f"Fondi insufficienti per trasferimento (con tolleranza 1%): disponibili {available_for_transfer}, richiesti {transfer_amount}, soglia minima {tolerance_threshold:.2f}"
                raise Exception(error_msg)
            
            # Trasferisce il minimo tra quello richiesto e quello disponibile
            actual_transfer_amount = min(transfer_amount, available_for_transfer)
            
            if actual_transfer_amount != transfer_amount:
                logger.info(f"Applicata tolleranza trasferimento: richiesti {transfer_amount}, trasferiti {actual_transfer_amount} (disponibili: {available_for_transfer})")
            
            # Calcola la strategia di trasferimento ottimale
            transfer_plan = self._calculate_transfer_plan(distribution, actual_transfer_amount)
            
            result = {
                'needed': True,
                'amount': actual_transfer_amount,
                'transfer_plan': transfer_plan,
                'derivatives_balance': derivatives_balance,
                'total_balance': total_balance,
                'distribution': distribution
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Errore controllo trasferimento Bitfinex: {e}")
            raise
    
    def _execute_bitfinex_internal_transfer(self, transfer_plan: List[Dict]) -> bool:
        """Esegue un piano di trasferimenti interni multipli in Bitfinex"""
        try:
            if not transfer_plan:
                logger.warning("Piano trasferimento vuoto")
                return False
            
            total_transferred = 0
            successful_transfers = 0
            
            for i, step in enumerate(transfer_plan):
                from_wallet = step['from_wallet']
                to_wallet = step['to_wallet']
                amount = step['amount']
                currency_from = step.get('currency_from', 'UST')
                
                logger.info(f"Eseguendo trasferimento {i+1}/{len(transfer_plan)}: {amount} {currency_from} da {from_wallet} a {to_wallet}")
                
                # Usa il metodo esistente _bitfinex_internal_transfer
                result = self._bitfinex_internal_transfer(amount, from_wallet, to_wallet)
                
                if result and result.get('success'):
                    logger.info(f"Trasferimento {i+1} completato con successo")
                    total_transferred += amount
                    successful_transfers += 1
                else:
                    error_msg = result.get('error', 'Errore sconosciuto') if result else 'Nessuna risposta'
                    logger.error(f"Trasferimento {i+1} fallito: {error_msg}")
                    
                    # Se un trasferimento fallisce, interrompiamo la sequenza
                    if successful_transfers == 0:
                        # Se il primo trasferimento fallisce, ritorna False
                        return False
                    else:
                        # Se alcuni trasferimenti sono riusciti, logga il parziale successo
                        logger.warning(f"Trasferimenti parziali completati: {successful_transfers}/{len(transfer_plan)}, totale trasferito: {total_transferred}")
                        break
            
            if successful_transfers == len(transfer_plan):
                logger.info(f"Tutti i trasferimenti completati con successo. Totale trasferito: {total_transferred}")
                return True
            elif successful_transfers > 0:
                logger.warning(f"Trasferimenti parziali: {successful_transfers}/{len(transfer_plan)} riusciti")
                return True  # Consideriamo successo parziale come successo
            else:
                logger.error("Nessun trasferimento completato con successo")
                return False
                
        except Exception as e:
            logger.error(f"Errore durante esecuzione piano trasferimenti: {e}")
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
                        
                        # Prima prova con i campi standard CCXT
                        for currency in currencies:
                            if currency in balance and balance[currency]['free'] > 0:
                                tradable_balance += balance[currency]['free']
                        
                        # Se non trova nulla, legge dall'array 'info' (correzione per il bug)
                        if tradable_balance == 0 and 'info' in balance and isinstance(balance['info'], list):
                            for balance_entry in balance['info']:
                                if len(balance_entry) >= 5:
                                    entry_wallet = balance_entry[0]
                                    entry_currency = balance_entry[1]
                                    entry_total = float(balance_entry[4]) if balance_entry[4] else 0
                                    
                                    # Cerca USDT e UST nel wallet margin
                                    if entry_wallet == 'margin' and entry_currency in currencies and entry_total > 0:
                                        tradable_balance += entry_total
                                        logger.debug(f"Bitfinex tradable balance da info: {entry_currency} = {entry_total}")
                        
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
                            wallet_balance = 0
                            
                            # Prima prova con i campi standard CCXT
                            for currency in currencies:
                                if currency in balance and balance[currency]['free'] > 0:
                                    amount = balance[currency]['free']
                                    wallet_balance += amount
                                    logger.debug(f"Bitfinex {wallet} wallet - {currency}: {amount}")
                            
                            # Se non trova nulla, legge dall'array 'info' (correzione per il bug)
                            if wallet_balance == 0 and 'info' in balance and isinstance(balance['info'], list):
                                for balance_entry in balance['info']:
                                    if len(balance_entry) >= 5:
                                        entry_wallet = balance_entry[0]
                                        entry_currency = balance_entry[1]
                                        entry_total = float(balance_entry[4]) if balance_entry[4] else 0
                                        
                                        # Cerca tutte le valute nel wallet corrente
                                        if entry_wallet == wallet and entry_currency in currencies and entry_total > 0:
                                            wallet_balance += entry_total
                                            logger.debug(f"Bitfinex {wallet} wallet da info - {entry_currency}: {entry_total}")
                            
                            total_balance += wallet_balance
                                    
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
            # Verifica se è un incremento di capitale
            is_increment = bot_config.get('increase', False)
            
            if is_increment:
                logger.info(f"🔄 MODALITÀ INCREMENTO: Aggiornamento posizioni esistenti con leva {leverage}x...")
                return self.increment_existing_positions(exchange_long, exchange_short, size_long, size_short, leverage, user_id, bot_id, bot_config)
            else:
                logger.info(f"🆕 MODALITÀ NORMALE: Apertura nuove posizioni con leva {leverage}x...")
                return self.create_new_positions(exchange_long, exchange_short, size_long, size_short, leverage, user_id, bot_id, bot_config)
            
        except Exception as e:
            logger.error(f"Errore gestione posizioni: {e}")
            return False
    
    def _convert_ust_to_ustf0_in_margin(self) -> bool:
        """Converte UST in USTF0 nel margin wallet di Bitfinex se necessario"""
        try:
            # Ottieni la distribuzione dei wallet
            distribution = self._get_bitfinex_wallet_distribution()
            ust_in_margin = distribution.get('margin', {}).get('UST', 0)
            
            if ust_in_margin > 0:
                logger.info(f"Conversione UST->USTF0 nel margin wallet: {ust_in_margin} UST")
                
                # Usa l'API privata per la conversione interna (stesso metodo del test)
                exchange = exchange_manager.exchanges['bitfinex']
                
                params = {
                    "from": "margin",
                    "to": "margin", 
                    "currency": "UST",
                    "currency_to": "USTF0",
                    "amount": str(ust_in_margin)
                }
                
                if hasattr(exchange, 'privatePostAuthWTransfer'):
                    result = exchange.privatePostAuthWTransfer(params)
                    
                    if result and isinstance(result, list) and len(result) > 0:
                        status = result[6] if len(result) > 6 else "UNKNOWN"
                        
                        if status == "SUCCESS":
                            logger.info(f"✅ Conversione UST->USTF0 completata: {ust_in_margin} UST convertiti in USTF0")
                            return True
                        else:
                            error_msg = result[7] if len(result) > 7 else "Errore sconosciuto"
                            logger.error(f"❌ Conversione UST->USTF0 fallita: {status} - {error_msg}")
                            return False
                else:
                    logger.error("❌ Metodo privatePostAuthWTransfer non disponibile")
                    return False
            else:
                logger.info("Nessun UST da convertire nel margin wallet")
                return True
                
        except Exception as e:
            logger.error(f"Errore durante conversione UST->USTF0: {e}")
            return False

    def create_new_positions(self, exchange_long: str, exchange_short: str, 
                           size_long: float, size_short: float, leverage: float, 
                           user_id: str, bot_id: str, bot_config: Dict) -> bool:
        """Crea nuove posizioni sui due exchange"""
        try:
            # Se uno degli exchange è Bitfinex, converti UST in USTF0 nel margin wallet
            if exchange_long == 'bitfinex' or exchange_short == 'bitfinex':
                logger.info("Conversione UST->USTF0 nel margin wallet prima di aprire posizioni...")
                if not self._convert_ust_to_ustf0_in_margin():
                    logger.warning("Conversione UST->USTF0 fallita, ma continuo con l'apertura posizioni")
            
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
            
            logger.info("✅ Strategia di funding arbitrage attivata con successo!")
            
            return True
            
        except Exception as e:
            logger.error(f"Errore creazione nuove posizioni: {e}")
            return False
    
    def increment_existing_positions(self, exchange_long: str, exchange_short: str, 
                                   size_long: float, size_short: float, leverage: float, 
                                   user_id: str, bot_id: str, bot_config: Dict) -> bool:
        """Incrementa posizioni esistenti durante aumento capitale"""
        try:
            # Se uno degli exchange è Bitfinex, converti UST in USTF0 nel margin wallet
            if exchange_long == 'bitfinex' or exchange_short == 'bitfinex':
                logger.info("Conversione UST->USTF0 nel margin wallet prima di incrementare posizioni...")
                if not self._convert_ust_to_ustf0_in_margin():
                    logger.warning("Conversione UST->USTF0 fallita, ma continuo con l'incremento posizioni")
            
            # Recupera posizioni esistenti aperte per questo bot
            existing_positions = position_manager.get_bot_open_positions(bot_id)
            
            if not existing_positions:
                logger.error(f"❌ Nessuna posizione esistente trovata per bot {bot_id} durante incremento")
                return False
            
            logger.info(f"📊 Trovate {len(existing_positions)} posizioni esistenti da incrementare")
            
            # Organizza posizioni per exchange e side
            positions_map = {}
            for pos in existing_positions:
                key = f"{pos['exchange']}_{pos['side']}"
                positions_map[key] = pos
                logger.info(f"Posizione esistente: {pos['exchange']} {pos['side']} - Size: {pos['size']} - Entry: {pos['entry_price']}")
            
            # Verifica che esistano le posizioni attese
            long_key = f"{exchange_long}_long"
            short_key = f"{exchange_short}_short"
            
            if long_key not in positions_map or short_key not in positions_map:
                logger.error(f"❌ Posizioni mancanti per incremento: {long_key} o {short_key}")
                return False
            
            # Apri posizioni incrementali
            order_long = exchange_manager.create_market_order(
                exchange_long, 'buy', size_long, leverage
            )
            
            if not order_long:
                logger.error(f"❌ Errore apertura incremento long su {exchange_long}")
                return False
            
            order_short = exchange_manager.create_market_order(
                exchange_short, 'sell', size_short, leverage
            )
            
            if not order_short:
                logger.error(f"❌ Errore apertura incremento short su {exchange_short}")
                # Prova a chiudere posizione long incrementale
                logger.info("Tentativo chiusura incremento long...")
                exchange_manager.close_position(exchange_long)
                return False
            
            logger.info(f"✅ Incrementi aperti - Long: {order_long['amount']}, Short: {order_short['amount']}")
            
            # Aggiorna posizioni esistenti con nuovi valori
            success_long = self.update_position_with_increment(
                positions_map[long_key], order_long, bot_config
            )
            
            success_short = self.update_position_with_increment(
                positions_map[short_key], order_short, bot_config
            )
            
            if success_long and success_short:
                logger.info("✅ Incremento posizioni completato con successo!")
                return True
            else:
                logger.error("❌ Errore aggiornamento posizioni durante incremento")
                return False
            
        except Exception as e:
            logger.error(f"❌ Errore incremento posizioni esistenti: {e}")
            return False
    
    def update_position_with_increment(self, existing_position: Dict, new_order: Dict, bot_config: Dict) -> bool:
        """Aggiorna una posizione esistente con i dati dell'incremento"""
        try:
            # Dati posizione esistente
            old_size = float(existing_position['size'])
            old_entry_price = float(existing_position['entry_price'])
            old_liquidation_price = float(existing_position.get('liquidation_price', 0))
            
            # Dati nuovo ordine
            increment_size = float(new_order['amount'])
            increment_entry_price = float(new_order['price'])
            
            # Calcola nuovo size totale
            new_total_size = old_size + increment_size
            
            # Calcola nuovo entry price medio ponderato
            old_value = old_size * old_entry_price
            increment_value = increment_size * increment_entry_price
            new_avg_entry_price = (old_value + increment_value) / new_total_size
            
            logger.info(f"📊 Calcolo nuovo entry price:")
            logger.info(f"   Posizione esistente: {old_size} @ {old_entry_price} = {old_value}")
            logger.info(f"   Incremento: {increment_size} @ {increment_entry_price} = {increment_value}")
            logger.info(f"   Nuovo totale: {new_total_size} @ {new_avg_entry_price}")
            
            # Calcola nuovo liquidation price (approssimativo)
            # Per ora manteniamo quello esistente, poi si può migliorare
            new_liquidation_price = old_liquidation_price
            
            # Calcola nuovi safety e rebalance values
            leverage = bot_config.get('leverage', 1)
            new_safety_value = new_avg_entry_price * new_total_size * 0.05  # 5% del valore posizione
            new_rebalance_value = new_avg_entry_price * new_total_size * 0.02  # 2% del valore posizione
            
            # Aggiorna posizione nel database
            success = position_manager.update_existing_position(
                position_id=existing_position['position_id'],
                new_size=new_total_size,
                new_entry_price=new_avg_entry_price,
                new_liquidation_price=new_liquidation_price,
                new_safety_value=new_safety_value,
                new_rebalance_value=new_rebalance_value
            )
            
            if success:
                logger.info(f"✅ Posizione {existing_position['position_id']} aggiornata: {old_size} → {new_total_size}")
                return True
            else:
                logger.error(f"❌ Errore aggiornamento posizione {existing_position['position_id']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Errore calcolo incremento posizione: {e}")
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