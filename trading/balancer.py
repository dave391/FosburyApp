#!/usr/bin/env python3
"""
Balancer - Modulo per monitorare e mantenere la leva finanziaria dei bot attivi

Questo modulo monitora continuamente tutti i bot attivi nel sistema e mantiene
automaticamente la leva finanziaria entro i parametri desiderati, aggiustando
il margine quando necessario.

Funzionalità:
- Recupera tutti i bot attivi dal database
- Per ogni bot, analizza tutte le posizioni aperte
- Calcola la leva effettiva di ogni posizione
- Confronta la leva effettiva con quella target del bot
- Se la deviazione supera 0,1X, attiva il ribilanciamento
- Calcola esattamente quanto margine aggiungere o rimuovere
"""

import logging
import time
import hmac
import hashlib
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from database.models import bot_manager, position_manager, user_manager
from trading.exchange_manager import exchange_manager
from config.settings import BOT_STATUS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Balancer:
    """Classe che gestisce il monitoraggio e il ribilanciamento della leva finanziaria
    per i bot con stato "running"
    """
    
    def __init__(self):
        """Inizializza il balancer"""
        pass
    
    def run(self):
        """Esegue il monitoraggio per cercare bot con stato "running" e ribilancia la leva"""
        try:
            # Cerca bot con stato "running"
            running_bots = self.get_running_bots()
            
            # Cerca anche bot con stato "transfering" che hanno transfer_reason "rebalance"
            transfering_bots = self.get_transfering_rebalance_bots()
            
            all_bots = running_bots + transfering_bots
            
            if all_bots:
                logger.info(f"Trovati {len(all_bots)} bot da processare ({len(running_bots)} running, {len(transfering_bots)} transfering-rebalance)")
                # Processa ogni bot
                for bot in all_bots:
                    self.process_bot(bot)
            else:
                logger.info("Nessun bot da processare trovato")
            
        except Exception as e:
            logger.error(f"Errore nel ciclo di monitoraggio: {e}")
    
    def get_running_bots(self) -> List[Dict]:
        """Recupera tutti i bot con status 'running'"""
        try:
            return bot_manager.get_running_bots()
        except Exception as e:
            logger.error(f"Errore recupero bot running: {e}")
            return []
    
    def get_transfering_rebalance_bots(self) -> List[Dict]:
        """Recupera tutti i bot con status 'transfering' e transfer_reason 'rebalance'"""
        try:
            # Usa get_ready_bots che include anche bot transfering, poi filtra
            ready_bots = bot_manager.get_ready_bots()
            transfering_rebalance_bots = [
                bot for bot in ready_bots 
                if bot.get('status') == BOT_STATUS['TRANSFERING'] 
                and bot.get('transfer_reason') == 'rebalance'
            ]
            return transfering_rebalance_bots
        except Exception as e:
            logger.error(f"Errore recupero bot transfering-rebalance: {e}")
            return []
    
    def process_bot(self, bot: Dict):
        """Processa un bot con stato "running"
        
        Args:
            bot: Dati del bot da processare
        """
        try:
            user_id = bot["user_id"]
            bot_id = bot["_id"]
            target_leverage = bot.get("leverage")
            
            # Verifica che la leva target sia configurata
            if target_leverage is None:
                logger.warning(f"Leva target non configurata per bot {bot_id}")
                return
            
            logger.info(f"Processando bot {bot_id} con leva target {target_leverage}X")
            
            # Recupera posizioni aperte per questo bot
            bot_positions = position_manager.get_bot_positions(bot_id)
            open_positions = [p for p in bot_positions if p["status"] == "open"]
            
            if not open_positions:
                logger.info(f"Nessuna posizione aperta per bot {bot_id}")
                return
            
            logger.info(f"Trovate {len(open_positions)} posizioni aperte per bot {bot_id}")
            
            # Recupera API keys dell'utente
            api_keys = user_manager.get_user_api_keys(user_id)
            if not api_keys:
                logger.error(f"API keys non trovate per utente {user_id}")
                return
            
            # Inizializza gli exchange necessari
            exchanges_to_init = set(pos["exchange"] for pos in open_positions)
            initialized_exchanges = set()
            
            for exchange_name in exchanges_to_init:
                api_key = api_keys.get(f"{exchange_name}_api_key")
                api_secret = api_keys.get(f"{exchange_name}_api_secret")
                
                if not api_key or not api_secret:
                    logger.warning(f"API keys mancanti per {exchange_name}")
                    continue
                
                success = exchange_manager.initialize_exchange(
                    exchange_name,
                    api_key,
                    api_secret
                )
                
                if success:
                    initialized_exchanges.add(exchange_name)
                    logger.info(f"Exchange {exchange_name} inizializzato con successo")
                else:
                    logger.error(f"Impossibile inizializzare {exchange_name}")
            
            # Analizza e ribilancia le posizioni
            for position in open_positions:
                try:
                    exchange_name = position["exchange"]
                    
                    # Verifica che l'exchange sia stato inizializzato
                    if exchange_name not in initialized_exchanges:
                        logger.warning(f"Exchange {exchange_name} non inizializzato, salto posizione")
                        continue
                    
                    # Analizza la posizione e calcola la leva effettiva
                    self.analyze_and_balance_position(position, target_leverage, api_keys)
                    
                except Exception as e:
                    logger.error(f"Errore nel processare posizione {position.get('position_id')}: {e}")
            
        except Exception as e:
            logger.error(f"Errore nel processare bot {bot.get('_id')}: {e}")
    
    def analyze_and_balance_position(self, position: Dict, target_leverage: float, api_keys: Dict):
        """Analizza una posizione, calcola la leva effettiva e ribilancia se necessario
        
        Args:
            position: Dati della posizione
            target_leverage: Leva target del bot
            api_keys: API keys dell'utente
        """
        try:
            exchange_name = position["exchange"]
            position_id = position["position_id"]
            symbol = position["symbol"]
            side = position["side"]
            
            logger.info(f"Analisi posizione {position_id} su {exchange_name} ({symbol})")
            
            # Recupera la posizione aggiornata dall'exchange
            exchange_position = None
            if exchange_name.lower() == "bitfinex":
                exchange_position = self.get_bitfinex_position(exchange_manager)
            elif exchange_name.lower() == "bitmex":
                exchange_position = self.get_bitmex_position(exchange_manager)
            
            if not exchange_position:
                logger.warning(f"Impossibile recuperare posizione da {exchange_name}")
                return
            
            # Calcola la leva effettiva
            effective_leverage = None
            if exchange_name.lower() == "bitfinex":
                # Per Bitfinex, ottieni la leva direttamente dalla posizione
                effective_leverage = exchange_position.get('leverage', 0)
                if effective_leverage == 0:
                    # Fallback al calcolo manuale solo se non disponibile direttamente
                    effective_leverage = self.calculate_effective_leverage(exchange_position, exchange_name)
                    logger.warning("Leva Bitfinex calcolata manualmente come fallback")
                else:
                    logger.info("Leva Bitfinex ottenuta direttamente dalla posizione")
            else:
                effective_leverage = self.calculate_effective_leverage(exchange_position, exchange_name)
            
            if effective_leverage is None:
                logger.warning(f"Impossibile calcolare leva effettiva per posizione {position_id}")
                return
            
            logger.info(f"Leva effettiva: {effective_leverage:.2f}X, Leva target: {target_leverage:.2f}X")
            
            # Verifica se è necessario ribilanciare
            leverage_diff = abs(effective_leverage - target_leverage)
            
            if leverage_diff > 0.1:  # Deviazione superiore a 0.1X
                logger.info(f"Deviazione leva: {leverage_diff:.2f}X - Ribilanciamento necessario")
                
                # Calcola quanto margine aggiungere o rimuovere
                margin_diff = self.calculate_margin_adjustment(exchange_position, target_leverage, exchange_name, api_keys, symbol)
                
                if margin_diff is None:
                    logger.warning(f"Impossibile calcolare aggiustamento margine per posizione {position_id}")
                    return
                
                # Esegui il ribilanciamento
                if exchange_name.lower() == "bitfinex":
                    success = self.adjust_bitfinex_margin(exchange_position, margin_diff, api_keys, symbol)
                elif exchange_name.lower() == "bitmex":
                    success = self.adjust_bitmex_margin(exchange_position, margin_diff, api_keys, symbol)
                else:
                    logger.warning(f"Exchange {exchange_name} non supportato per ribilanciamento")
                    return
                
                if success:
                    logger.info(f"Ribilanciamento completato con successo per posizione {position_id}")
                else:
                    logger.warning(f"Ribilanciamento fallito per posizione {position_id}")
            else:
                logger.info(f"Leva già entro i parametri desiderati (diff: {leverage_diff:.2f}X)")
            
        except Exception as e:
            logger.error(f"Errore nell'analisi e ribilanciamento della posizione: {e}")
    
    def get_bitfinex_position(self, exchange_manager) -> Optional[Dict]:
        """Recupera la posizione aperta su Bitfinex
        
        Args:
            exchange_manager: Manager degli exchange inizializzato
            
        Returns:
            Dict con i dati della posizione o None se non trovata
        """
        try:
            exchange = exchange_manager.exchanges.get('bitfinex')
            if not exchange:
                logger.error("Exchange Bitfinex non inizializzato")
                return None
            
            # Recupera tutte le posizioni
            positions = exchange.fetch_positions()
            
            # Trova la prima posizione aperta (assumiamo ce ne sia solo una)
            for position in positions:
                contracts = position.get('contracts', 0)
                size = position.get('size', 0)
                notional = position.get('notional', 0)
                
                # Controlla se la posizione è aperta
                if contracts != 0 or size != 0 or notional != 0:
                    logger.info(f"Posizione trovata: {position.get('symbol')} - Size: {contracts or size} - Notional: {notional}")
                    return position
            
            logger.warning("Nessuna posizione aperta trovata su Bitfinex")
            return None
            
        except Exception as e:
            logger.error(f"Errore recupero posizione Bitfinex: {e}")
            return None
    
    def get_bitmex_position(self, exchange_manager) -> Optional[Dict]:
        """Recupera la posizione aperta su BitMEX
        
        Args:
            exchange_manager: Manager degli exchange
            
        Returns:
            Dati della posizione o None se non trovata
        """
        try:
            exchange = exchange_manager.exchanges.get('bitmex')
            if not exchange:
                logger.error("Exchange BitMEX non inizializzato")
                return None
            
            # Recupera tutte le posizioni
            positions = exchange.fetch_positions()
            
            # Trova posizione aperta (currentQty != 0)
            for position in positions:
                current_qty = position.get('contracts', 0)
                if current_qty != 0:
                    logger.info(f"Posizione trovata: {position.get('symbol')} - Size: {current_qty}")
                    return position
            
            logger.warning("Nessuna posizione aperta trovata su BitMEX")
            return None
            
        except Exception as e:
            logger.error(f"Errore recupero posizione BitMEX: {e}")
            return None
    
    def calculate_effective_leverage(self, position: Dict, exchange_name: str) -> Optional[float]:
        """Calcola la leva effettiva di una posizione
        
        Args:
            position: Dati della posizione
            exchange_name: Nome dell'exchange
            
        Returns:
            Leva effettiva o None se errore
        """
        try:
            # Estrai i dati necessari dalla posizione
            if exchange_name.lower() == "bitfinex":
                # Per Bitfinex, ottieni la leva direttamente dalla posizione
                # invece di calcolarla come notional/margin
                leverage = position.get('leverage', 0)
                
                if leverage == 0:
                    # Fallback al calcolo manuale solo se non disponibile direttamente
                    notional = position.get('notional', 0)  # Valore della posizione
                    margin = position.get('collateral') or position.get('margin') or position.get('initialMargin', 0)
                    
                    if notional == 0 or margin == 0:
                        logger.error(f"Dati insufficienti per calcolare leva: notional={notional}, margin={margin}")
                        return None
                    
                    # Calcola leva: valore posizione / margine
                    leverage = abs(notional / margin)
                    logger.warning("Leva calcolata manualmente come fallback")
                
            elif exchange_name.lower() == "bitmex":
                # Per BitMEX
                notional = float(position.get('notional', 0))  # Valore della posizione in USDT
                margin = position.get('initialMargin') or position.get('collateral') or position.get('maintenanceMargin', 0)
                
                # Controlla anche il campo 'info' che potrebbe contenere dati raw
                info = position.get('info', {})
                if margin == 0 and info:
                    margin = info.get('posMargin') or info.get('posInit') or info.get('initMargin', 0)
                
                # Assicurati che margin sia un numero
                try:
                    margin = float(margin)
                except (TypeError, ValueError):
                    logger.error(f"Impossibile convertire margin a float: {margin}")
                    return None
                
                # Converti da Satoshis a USDT se necessario
                if margin > 1000000:  # Probabilmente in Satoshis
                    margin = margin / 1_000_000  # Converti da Satoshis a USDT
                
                if notional == 0 or margin == 0:
                    logger.error(f"Dati insufficienti per calcolare leva: notional={notional}, margin={margin}")
                    return None
                
                # Calcola leva: valore posizione / margine
                leverage = abs(notional / margin)
                
            else:
                logger.error(f"Exchange {exchange_name} non supportato per calcolo leva")
                return None
            
            logger.info(f"Leva effettiva calcolata: {leverage:.2f}X")
            return leverage
            
        except Exception as e:
            logger.error(f"Errore calcolo leva effettiva: {e}")
            return None
    
    def calculate_margin_adjustment(self, position: Dict, target_leverage: float, exchange_name: str, api_keys: Dict, symbol_from_db: str = None) -> Optional[float]:
        """Calcola quanto margine aggiungere o rimuovere per raggiungere la leva target
        
        Args:
            position: Dati della posizione
            target_leverage: Leva target
            exchange_name: Nome dell'exchange
            
        Returns:
            Differenza di margine (positiva = aggiungere, negativa = rimuovere) o None se errore
        """
        try:
            # Estrai i dati necessari dalla posizione
            if exchange_name.lower() == "bitfinex":
                # Per Bitfinex
                size = position.get('notional', 0)  # Valore della posizione
                entry_price = position.get('entryPrice', 0)  # Prezzo di entrata
                current_margin = position.get('collateral') or position.get('margin') or position.get('initialMargin', 0)
                unrealized_pnl = position.get('unrealizedPnl', 0)  # PnL non realizzato
                
                if size == 0 or entry_price == 0 or current_margin == 0:
                    logger.error(f"Dati insufficienti per calcolare aggiustamento: size={size}, entry_price={entry_price}, margin={current_margin}")
                    return None
                
                # Valore nominale della posizione (senza PnL)
                nominal_value = abs(size * entry_price)
                
                # Calcola margine base per leva target
                base_margin = nominal_value / target_leverage
                
                # Sottrai il PnL non realizzato (se positivo riduce il collaterale necessario)
                target_margin = base_margin - unrealized_pnl
                
                # Il margine non può essere negativo o troppo basso
                target_margin = max(target_margin, 0.05)  # Minimo 0.05 USDT per evitare errore "collateral: insufficient"
                
                logger.info(f"Size posizione (notional): {size}")
                logger.info(f"Prezzo entrata: {entry_price:.4f} USDT")
                logger.info(f"PnL non realizzato: {unrealized_pnl:.4f} USDT")
                logger.info(f"Valore nominale posizione: {nominal_value:.2f} USDT")
                logger.info(f"Margine base per {target_leverage}X: {base_margin:.2f} USDT")
                
                # Calcola differenza
                margin_diff = target_margin - current_margin
                
            elif exchange_name.lower() == "bitmex":
                # Per BitMEX
                notional = float(position.get('notional', 0))  # Valore della posizione in USDT
                current_margin = position.get('initialMargin') or position.get('collateral') or position.get('maintenanceMargin', 0)
                
                # Controlla anche il campo 'info' che potrebbe contenere dati raw
                info = position.get('info', {})
                if current_margin == 0 and info:
                    current_margin = info.get('posMargin') or info.get('posInit') or info.get('initMargin', 0)
                
                # Assicurati che current_margin sia un numero
                try:
                    current_margin = float(current_margin)
                except (TypeError, ValueError):
                    logger.error(f"Impossibile convertire current_margin a float: {current_margin}")
                    return None
                
                # Converti da Satoshis a USDT se necessario
                if current_margin > 1000000:  # Probabilmente in Satoshis
                    current_margin = current_margin / 1_000_000  # Converti da Satoshis a USDT
                
                if notional == 0 or current_margin == 0:
                    logger.error(f"Dati insufficienti per calcolare aggiustamento: notional={notional}, margin={current_margin}")
                    return None
                
                # Calcola margine target per leva target
                target_margin = notional / target_leverage
                
                # Calcola differenza
                margin_diff = target_margin - current_margin
                
                # Controlla margine massimo rimovibile per BitMEX quando si riduce il margine
                # Questo previene l'errore "insufficient isolated margin" usando i limiti reali di BitMEX
                if margin_diff < 0:  # Solo quando si riduce il margine
                    # Usa il simbolo dalla posizione del database, non dalla posizione exchange
                    symbol_to_use = symbol_from_db or position.get('symbol', '')
                    max_removable = self.get_bitmex_max_removable_margin(symbol_to_use, api_keys)
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
                logger.error(f"Exchange {exchange_name} non supportato per calcolo aggiustamento margine")
                return None
            
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
            return None
    
    def adjust_bitfinex_margin(self, position: Dict, margin_diff: float, api_keys: Dict, symbol: str) -> bool:
        """Aggiusta il margine della posizione su Bitfinex
        
        Args:
            position: Dati della posizione
            margin_diff: Differenza di margine (positiva = aggiungere, negativa = rimuovere)
            api_keys: API keys dell'utente
            symbol: Simbolo della posizione
            
        Returns:
            True se successo, False altrimenti
        """
        try:
            # Se la differenza è zero, non fare nulla
            if margin_diff == 0:
                logger.info("Nessun aggiustamento necessario")
                return True
            
            # Ottieni le API keys
            api_key = api_keys.get('bitfinex_api_key')
            api_secret = api_keys.get('bitfinex_api_secret')
            
            if not api_key or not api_secret:
                logger.error("API keys Bitfinex non configurate")
                return False
            
            # Ottieni il margine attuale
            current_margin = position.get('collateral') or position.get('margin') or position.get('initialMargin', 0)
            
            # Calcola il nuovo collaterale
            new_collateral = current_margin + margin_diff
            
            # Verifica che il nuovo collaterale sia positivo
            if new_collateral <= 0:
                logger.error(f"Il nuovo collaterale ({new_collateral:.2f}) deve essere positivo")
                return False
            
            # Converti il simbolo nel formato richiesto dall'API (es. "SOL/USDT" -> "tSOLF0:USTF0")
            api_symbol = self.convert_to_bitfinex_symbol(symbol)
            
            # Imposta il collaterale
            success = self.set_bitfinex_collateral(api_key, api_secret, api_symbol, new_collateral)
            
            if success:
                logger.info(f"Collaterale aggiustato con successo: {current_margin:.2f} -> {new_collateral:.2f} USDT")
                
                # Aspetta un momento per permettere all'exchange di aggiornare
                time.sleep(2)
                
                # Recupera la posizione aggiornata per verificare la leva effettiva
                from trading.exchange_manager import ExchangeManager
                exchange_manager = ExchangeManager()
                exchange_manager.initialize_exchange('bitfinex', api_key, api_secret)
                updated_position = self.get_bitfinex_position(exchange_manager)
                
                if updated_position:
                    # Usa la leva direttamente dalla posizione aggiornata
                    current_leverage = updated_position.get('leverage', 0)
                    if current_leverage > 0:
                        logger.info(f"Leva effettiva dopo aggiustamento: {current_leverage:.4f}X")
                        
                        # Verifica se la leva è vicina al target (tolleranza di 0.5X)
                        target_leverage = 3.0  # Leva target fissa a 3X
                        if abs(current_leverage - target_leverage) < 0.5:
                            logger.info(f"Leva aggiustata con successo (target: {target_leverage:.1f}X, attuale: {current_leverage:.4f}X)")
                        else:
                            logger.warning(f"Leva attuale ({current_leverage:.4f}X) non è vicina al target di {target_leverage:.1f}X")
                    else:
                        logger.warning("Impossibile recuperare leva dalla posizione aggiornata")
                
                return True
            else:
                logger.error("Errore nell'aggiustamento del collaterale")
                return False
            
        except Exception as e:
            logger.error(f"Errore aggiustamento margine Bitfinex: {e}")
            return False
    
    def set_bitfinex_collateral(self, api_key: str, api_secret: str, symbol: str, collateral_amount: float) -> bool:
        """Imposta il collaterale di una posizione derivata usando l'API nativa di Bitfinex
        
        Args:
            api_key: API key di Bitfinex
            api_secret: API secret di Bitfinex
            symbol: Simbolo della posizione (es. "tSOLF0:USTF0")
            collateral_amount: Quantità di collaterale da impostare
            
        Returns:
            True se successo, False altrimenti
        """
        try:
            # Endpoint per impostare il collaterale
            url = "https://api.bitfinex.com/v2/auth/w/deriv/collateral/set"
            
            # Payload per la richiesta
            payload = {
                "symbol": symbol,
                "collateral": collateral_amount
            }
            
            # Genera nonce (timestamp in millisecondi)
            nonce = str(int(time.time() * 1000))
            
            # Crea il body della richiesta
            body = json.dumps(payload)
            
            # Crea la stringa per la firma
            message = f"/api/v2/auth/w/deriv/collateral/set{nonce}{body}"
            
            # Genera la firma HMAC-SHA384
            signature = hmac.new(
                api_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha384
            ).hexdigest()
            
            # Headers per l'autenticazione
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "bfx-nonce": nonce,
                "bfx-apikey": api_key,
                "bfx-signature": signature
            }
            
            logger.info(f"Impostazione collaterale {collateral_amount:.2f} per posizione {symbol}")
            
            # Esegui la richiesta
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Risposta API: {result}")
                
                # Verifica se l'operazione è riuscita
                # La risposta [[1]] indica successo secondo la documentazione Bitfinex
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], list) and len(result[0]) > 0 and result[0][0] == 1:
                        logger.info("Collaterale impostato con successo")
                        return True
                    elif result[0] == 1:
                        logger.info("Collaterale impostato con successo")
                        return True
                
                logger.error(f"Operazione fallita: {result}")
                return False
            else:
                logger.error(f"Errore HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Errore impostazione collaterale: {e}")
            return False
    
    def convert_to_bitfinex_symbol(self, symbol: str) -> str:
        """Converte il simbolo nel formato richiesto dall'API di Bitfinex per i derivati
        
        Args:
            symbol: Simbolo nel formato della posizione (es. "SOL/USDT:USDT")
            
        Returns:
            Simbolo nel formato API Bitfinex (es. "tSOLF0:USTF0")
        """
        # Mappa dei simboli comuni per derivati
        symbol_map = {
            "SOL/USDT:USDT": "tSOLF0:USTF0",
            "SOL/USDT": "tSOLF0:USTF0",
            "BTC/USDT:USDT": "tBTCF0:USTF0",
            "BTC/USDT": "tBTCF0:USTF0",
            "ETH/USDT:USDT": "tETHF0:USTF0",
            "ETH/USDT": "tETHF0:USTF0"
        }
        
        converted = symbol_map.get(symbol, symbol)
        logger.info(f"Conversione simbolo: {symbol} -> {converted}")
        return converted
    
    def adjust_bitmex_margin(self, position: Dict, margin_diff: float, api_keys: Dict, symbol: str) -> bool:
        """Aggiusta il margine della posizione su BitMEX
        
        Args:
            position: Dati della posizione
            margin_diff: Differenza di margine (positiva = aggiungere, negativa = rimuovere)
            api_keys: API keys dell'utente
            symbol: Simbolo della posizione
            
        Returns:
            True se successo, False altrimenti
        """
        try:
            # Se la differenza è zero, non fare nulla
            if margin_diff == 0:
                logger.info("Nessun aggiustamento necessario")
                return True
            
            # Ottieni le API keys
            api_key = api_keys.get('bitmex_api_key')
            api_secret = api_keys.get('bitmex_api_secret')
            
            if not api_key or not api_secret:
                logger.error("API keys BitMEX non configurate")
                return False
            
            # Per BitMEX, il margine deve essere espresso in Satoshi della valuta di settlement
            # Per USDT: 1 USDT = 1,000,000 Satoshi USDT
            amount_satoshis = int(margin_diff * 1_000_000)
            
            # Converti il simbolo al formato BitMEX
            bitmex_symbol = symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
            logger.info(f"Simbolo convertito: {symbol} -> {bitmex_symbol}")
            
            logger.info(f"Trasferimento margine: {margin_diff:.2f} USDT = {amount_satoshis} Satoshi USDT")
            
            # Chiama l'API BitMEX per trasferire margine
            exchange = exchange_manager.exchanges.get('bitmex')
            if not exchange:
                logger.error("Exchange BitMEX non inizializzato")
                return False
            
            result = exchange.private_post_position_transfermargin({
                'symbol': bitmex_symbol,
                'amount': amount_satoshis
            })
            
            if result:
                logger.info(f"Margine trasferito con successo: {result}")
                return True
            else:
                logger.error("Errore nel trasferimento margine")
                return False
            
        except Exception as e:
            logger.error(f"Errore aggiustamento margine BitMEX: {e}")
            return False

    def get_bitmex_max_removable_margin(self, symbol: str, api_keys: dict) -> Optional[float]:
        """Ottiene il margine massimo rimovibile da BitMEX tramite API /position"""
        try:
            # Usa l'exchange già inizializzato tramite CCXT
            exchange = exchange_manager.exchanges.get('bitmex')
            if not exchange:
                logger.error("Exchange BitMEX non inizializzato")
                return None
            
            # Il simbolo su BitMEX è già nel formato corretto
            bitmex_symbol = symbol  # Usa il simbolo così com'è
            logger.info(f"Simbolo per posCross: {symbol}")
            
            # Ottieni tutte le posizioni tramite CCXT
            positions = exchange.fetch_positions()
            logger.info(f"Trovate {len(positions)} posizioni totali su BitMEX")
            
            # Cerca la posizione specifica
            for position in positions:
                if position.get('symbol') == bitmex_symbol:
                    # Cerca il campo posCross nei dati raw
                    info = position.get('info', {})
                    pos_cross_raw = info.get('posCross', 0)
                    
                    # Converti pos_cross in numero se è una stringa
                    try:
                        pos_cross = int(pos_cross_raw) if pos_cross_raw else 0
                    except (ValueError, TypeError):
                        pos_cross = 0
                    
                    logger.info(f"posCross BitMEX per {bitmex_symbol}: {pos_cross} Satoshi = {pos_cross / 1_000_000:.6f} USDT")
                    
                    # Controlla se la posizione è attiva (contracts diverso da 0)
                    if position.get('contracts', 0) != 0 and pos_cross > 0:
                        # Converte da Satoshi USDT a USDT (dividi per 1.000.000)
                        max_removable = pos_cross / 1_000_000
                        logger.info(f"posCross BitMEX per {bitmex_symbol}: {pos_cross} Satoshi = {max_removable:.6f} USDT")
                        return max_removable
            
            logger.warning(f"Nessuna posizione attiva trovata per {bitmex_symbol} su BitMEX")
            return None
                
        except Exception as e:
            logger.error(f"Errore chiamata API BitMEX /position: {e}")
            return None


def main():
    """Funzione principale"""
    try:
        logger.info("=== Avvio Balancer ===")
        balancer = Balancer()
        balancer.run()
        logger.info("=== Fine Balancer ===")
        return True
    except Exception as e:
        logger.error(f"Errore generale: {e}")
        return False


if __name__ == "__main__":
    main()