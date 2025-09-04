"""
Gestore degli exchange con CCXT
"""
import ccxt
import logging
import time
from typing import Dict, Optional, Tuple
from config.settings import EXCHANGE_SYMBOLS, EXCHANGE_MULTIPLIERS, SOLANA_PRECISION
from utils.exchange_utils import ExchangeUtils, get_exchange_config

logger = logging.getLogger(__name__)

class ExchangeManager:
    """Manager per operazioni con gli exchange"""
    
    def __init__(self):
        self.exchanges = {}
    
    def get_exchange_symbol(self, exchange_name: str) -> str:
        """Ottiene il simbolo futures perpetual corretto per l'exchange"""
        return EXCHANGE_SYMBOLS.get(exchange_name.lower(), "SOL/USDT")
    
    def calculate_exchange_size(self, exchange_name: str, sol_amount: float) -> float:
        """Calcola la size appropriata per l'exchange specifico"""
        multiplier = EXCHANGE_MULTIPLIERS.get(exchange_name.lower(), 1)
        
        if exchange_name.lower() == "bitmex":
            # BitMEX: converti SOL in contratti e arrotonda a centinaia
            contracts = int(sol_amount * multiplier)
            contracts = max(contracts, 1000)  # Minimo 1000 contratti
            contracts = round(contracts / 100) * 100  # Arrotonda a centinaia
            logger.info(f"BitMEX size conversion: {sol_amount} SOL → {contracts} contratti")
            return contracts
        else:
            # Bitfinex: usa size normale
            return sol_amount
    
    def initialize_exchange(self, exchange_name: str, api_key: str, api_secret: str) -> bool:
        """Inizializza connessione exchange con gestione ottimizzata"""
        try:
            # Ottieni configurazione specifica per exchange
            config = get_exchange_config(exchange_name)
            
            if exchange_name == "bitfinex":
                exchange_config = {
                    'apiKey': api_key,
                    'secret': api_secret,
                    'sandbox': False,
                    'enableRateLimit': True,
                    'timeout': 30000,  # 30 secondi timeout
                    'options': config.get('options', {})
                }
                
                # Aggiungi nonce dinamico per Bitfinex
                if config.get('requires_nonce'):
                    exchange_config['nonce'] = lambda: int(time.time() * 1000)
                
                exchange = ccxt.bitfinex(exchange_config)
                
            elif exchange_name == "bitmex":
                exchange_config = {
                    'apiKey': api_key,
                    'secret': api_secret,
                    'sandbox': False,
                    'enableRateLimit': True,
                    'timeout': 30000,  # 30 secondi timeout
                    'options': config.get('options', {})
                }
                
                exchange = ccxt.bitmex(exchange_config)
                
            else:
                logger.error(f"Exchange non supportato: {exchange_name}")
                return False
            
            # Test connessione con retry per gestire problemi di nonce
            def test_connection():
                exchange.load_markets()
                return exchange
            
            exchange = ExchangeUtils.retry_with_nonce_fix(test_connection, max_retries=3, wait_seconds=2)
            
            self.exchanges[exchange_name] = exchange
            logger.info(f"Exchange {exchange_name} inizializzato con successo")
            return True
            
        except Exception as e:
            if ExchangeUtils.is_nonce_error(str(e)):
                logger.error(f"Errore nonce {exchange_name}: {e}. Riprova tra qualche secondo.")
            elif ExchangeUtils.is_auth_error(str(e)):
                logger.error(f"Errore autenticazione {exchange_name}: Verifica API keys e permessi.")
            else:
                logger.error(f"Errore inizializzazione {exchange_name}: {e}")
            return False
    
    def get_solana_price(self, exchange_name: str) -> Optional[float]:
        """Ottiene prezzo corrente SOLANA"""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                logger.error(f"Exchange {exchange_name} non inizializzato")
                return None
            
            symbol = self.get_exchange_symbol(exchange_name)
            ticker = exchange.fetch_ticker(symbol)
            price = ticker['last']
            logger.info(f"Prezzo SOLANA su {exchange_name}: {price}")
            return price
            
        except Exception as e:
            logger.error(f"Errore recupero prezzo SOLANA su {exchange_name}: {e}")
            return None
    
    def calculate_solana_size(self, usdt_amount: float, solana_price: float) -> float:
        """Calcola size SOLANA in base a capitale USDT"""
        if not solana_price or solana_price <= 0:
            return 0
        
        # Calcola size esatta
        exact_size = usdt_amount / solana_price
        
        # Arrotonda per difetto con precisione specificata
        rounded_size = int(exact_size / SOLANA_PRECISION) * SOLANA_PRECISION
        
        logger.info(f"Size calcolata: {usdt_amount} USDT / {solana_price} = {exact_size} SOL → {rounded_size} SOL")
        return rounded_size
    
    def get_account_balance(self, exchange_name: str) -> Optional[Dict]:
        """Ottiene saldo account"""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                logger.error(f"Exchange {exchange_name} non inizializzato")
                return None
            
            balance = exchange.fetch_balance()
            return balance
            
        except Exception as e:
            logger.error(f"Errore recupero saldo {exchange_name}: {e}")
            return None
    
    def create_market_order(self, exchange_name: str, side: str, sol_amount: float, 
                           leverage: float = 1.0) -> Optional[Dict]:
        """Crea ordine di mercato"""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                logger.error(f"Exchange {exchange_name} non inizializzato")
                return None
            
            # Ottieni simbolo corretto per l'exchange
            symbol = self.get_exchange_symbol(exchange_name)
            
            # Calcola size appropriata per l'exchange
            exchange_size = self.calculate_exchange_size(exchange_name, sol_amount)
            
            # Gestione leva specifica per exchange
            order_params = {}
            
            if exchange_name.lower() == "bitfinex":
                # Bitfinex: passa leva come parametro 'lev' (int) secondo documentazione CCXT
                # Validazione: deve essere tra 1 e 100 inclusi
                lev_int = max(1, min(100, int(leverage)))
                order_params['lev'] = lev_int
                if lev_int != int(leverage):
                    logger.warning(f"Bitfinex: leva {leverage} aggiustata a {lev_int} (range supportato: 1-100)")
                logger.info(f"Bitfinex: leva {lev_int}x passata come parametro 'lev'")
                
            elif exchange_name.lower() == "bitmex":
                # BitMEX: imposta leva prima dell'ordine
                try:
                    exchange.set_leverage(leverage, symbol)
                    logger.info(f"BitMEX: leva {leverage}x impostata per {symbol}")
                except Exception as lev_error:
                    logger.warning(f"BitMEX: impossibile impostare leva {leverage}x: {lev_error}")
                
                # BitMEX: imposta margine isolato
                try:
                    exchange.set_position_parameters(symbol, margin_mode='isolated')
                    logger.info(f"BitMEX: margine isolato impostato per {symbol}")
                except Exception as margin_error:
                    logger.warning(f"BitMEX: impossibile impostare margine isolato: {margin_error}")
            
            # Crea ordine di mercato
            order = exchange.create_market_order(symbol, side, exchange_size, None, order_params)
            logger.info(f"Ordine creato su {exchange_name}: {side} {exchange_size} {symbol} (SOL: {sol_amount}, leva: {leverage}x)")
            return order
            
        except Exception as e:
            logger.error(f"Errore creazione ordine {exchange_name}: {e}")
            return None
    
    def get_position(self, exchange_name: str) -> Optional[Dict]:
        """Ottiene posizione corrente"""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                logger.error(f"Exchange {exchange_name} non inizializzato")
                return None
            
            symbol = self.get_exchange_symbol(exchange_name)
            positions = exchange.fetch_positions([symbol])
            if positions:
                position = positions[0]
                logger.info(f"Posizione {exchange_name}: {position}")
                return position
            
            return None
            
        except Exception as e:
            logger.error(f"Errore recupero posizione {exchange_name}: {e}")
            return None
    
    def close_position(self, exchange_name: str) -> Dict:
        """Chiude posizione aperta"""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                logger.error(f"Exchange {exchange_name} non inizializzato")
                return {"success": False, "message": "exchange_not_initialized", "error": "Exchange non inizializzato"}
            
            # Gestione speciale per Bitmex
            if exchange_name.lower() == "bitmex":
                return self._close_bitmex_position(exchange)
            
            # Gestione standard per altri exchange
            position = self.get_position(exchange_name)
            if not position:
                logger.info(f"Nessuna posizione da chiudere su {exchange_name}")
                return {"success": True, "message": "no_position", "order": None}
            
            # Gestisci diversi formati di size tra exchange
            position_size = position.get('size') or position.get('notional') or 0
            if position_size == 0:
                logger.info(f"Nessuna posizione da chiudere su {exchange_name}")
                return {"success": True, "message": "no_position", "order": None}
            
            # Usa il simbolo della posizione reale, non quello predefinito
            symbol = position['symbol']
            
            # Determina side opposto per chiudere
            side = 'sell' if position['side'] == 'long' else 'buy'
            
            # Calcola amount in SOL e poi converti per l'exchange
            sol_amount = abs(position_size)
            if exchange_name.lower() == "bitmex":
                # Converti contratti BitMEX in SOL
                sol_amount = sol_amount / EXCHANGE_MULTIPLIERS["bitmex"]
            
            # Crea ordine di chiusura usando il simbolo corretto
            logger.info(f"Chiusura {side} {sol_amount} {symbol} su {exchange_name}")
            order = exchange.create_market_order(symbol, side, sol_amount)
            if order:
                logger.info(f"Posizione chiusa su {exchange_name}")
                return {"success": True, "message": "position_closed", "order": order}
            
            return {"success": False, "message": "order_failed", "order": None}
            
        except Exception as e:
            logger.error(f"Errore chiusura posizione {exchange_name}: {e}")
            return {"success": False, "message": "exception", "error": str(e)}
            
    def _close_bitmex_position(self, exchange) -> Dict:
        """
        Chiude posizioni aperte su Bitmex con gestione speciale
        
        Args:
            exchange: Istanza dell'exchange Bitmex
            
        Returns:
            dict: Risultato della chiusura
        """
        try:
            logger.info("Recupero posizioni aperte su Bitmex...")
            
            # Recupera tutte le posizioni
            all_positions = exchange.fetch_positions()
            logger.info(f"Trovate {len(all_positions)} posizioni totali su Bitmex")
            
            # Filtra solo quelle con contracts/size != 0
            open_positions = []
            for pos in all_positions:
                contracts = pos.get('contracts', 0)
                size = pos.get('contractSize', 0)
                side = pos.get('side')
                symbol = pos.get('symbol')
                
                # Verifica se è una posizione valida
                if (contracts != 0 or size != 0) and side and symbol:
                    open_positions.append(pos)
            
            if not open_positions:
                logger.info("Nessuna posizione aperta trovata su Bitmex")
                return {"success": True, "message": "no_position", "order": None}
            
            # Log delle posizioni trovate
            logger.info(f"Trovate {len(open_positions)} posizioni aperte su Bitmex:")
            for pos in open_positions:
                contracts = pos.get('contracts', 0) or pos.get('contractSize', 0)
                side = pos.get('side', 'unknown')
                symbol = pos.get('symbol', 'unknown')
                entry_price = pos.get('entryPrice', 0)
                logger.info(f"- {side} {contracts} {symbol} @ {entry_price}")
            
            # Chiudi ogni posizione
            success_count = 0
            orders = []
            
            for position in open_positions:
                symbol = position.get('symbol')
                side = position.get('side')
                contracts = position.get('contracts') or position.get('contractSize') or 0
                
                if not symbol or not side or contracts == 0:
                    logger.error(f"Dati posizione incompleti: {position}")
                    continue
                
                # Determina il lato opposto per chiudere
                close_side = 'sell' if side == 'long' else 'buy'
                
                logger.info(f"Chiusura posizione {side} {contracts} {symbol} con {close_side}")
                
                try:
                    # Crea ordine di mercato per chiudere
                    order = exchange.create_market_order(
                        symbol=symbol,
                        side=close_side,
                        amount=abs(contracts)
                    )
                    
                    logger.info(f"Ordine di chiusura creato: {order}")
                    orders.append(order)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Errore chiusura posizione {symbol}: {e}")
            
            # Ritorna risultato
            if success_count > 0:
                return {"success": True, "message": "position_closed", "order": orders}
            else:
                return {"success": False, "message": "close_failed", "error": "Nessuna posizione chiusa con successo"}
            
        except Exception as e:
            logger.error(f"Errore chiusura posizioni Bitmex: {e}")
            return {"success": False, "message": "exception", "error": str(e)}

# Istanza globale
exchange_manager = ExchangeManager()