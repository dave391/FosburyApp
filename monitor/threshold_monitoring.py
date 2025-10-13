"""Threshold Monitoring - Modulo per monitorare bot attivi e gestire incrementi capitale

Questo script monitora tutti i bot attivi (tranne STOPPED) e:
- Controlla richieste di incremento capitale (increase = True) per bot RUNNING
- Aggiorna valori threshold per bot RUNNING:
  - liquidation_price dalle API degli exchange
  - safety_value calcolato come percentuale dal liquidation_price
  - rebalance_value calcolato come percentuale dal liquidation_price

Uso:
    python -m trading.threshold_monitoring
"""

import sys
import os
from typing import Dict, List, Optional
from datetime import datetime

# Importa moduli necessari
from database.models import bot_manager, position_manager, user_manager
from trading.exchange_manager import exchange_manager
from config.settings import BOT_STATUS

class ThresholdMonitor:
    """Classe che gestisce il monitoraggio dei bot attivi e gli incrementi di capitale
    
    Funzionalità:
    - Monitora tutti i bot attivi (tranne STOPPED)
    - Gestisce richieste di incremento capitale (RUNNING -> READY)
    - Aggiorna valori threshold per bot RUNNING
    """
    
    def __init__(self):
        """Inizializza il threshold monitor"""
        pass
    
    def run(self):
        """Esegue il monitoraggio per tutti i bot attivi (tranne STOPPED)"""
        try:
            # Cerca tutti i bot attivi (tranne STOPPED)
            active_bots = self.get_active_bots()
            
            if active_bots:
                # Processa ogni bot
                for bot in active_bots:
                    self.process_bot(bot)
            
        except Exception as e:
            print(f"Errore nel ciclo di monitoraggio: {e}")
    
    def get_active_bots(self) -> List[Dict]:
        """Recupera tutti i bot attivi (tutti tranne STOPPED)"""
        try:
            return list(bot_manager.bots.find({"status": {"$ne": BOT_STATUS["STOPPED"]}}))
        except Exception as e:
            print(f"Errore recupero bot attivi: {e}")
            return []
    
    def process_bot(self, bot: Dict):
        """Processa un bot attivo
        
        Args:
            bot: Dati del bot da processare
        """
        try:
            user_id = bot["user_id"]
            bot_id = bot["_id"]
            bot_status = bot.get("status")
            
            # CONTROLLO INCREMENTO CAPITALE
            # Se bot è RUNNING e ha increase = True, cambia stato a READY
            if (bot_status == BOT_STATUS["RUNNING"] and 
                bot.get("increase") is True):
                print(f"Bot {bot_id}: rilevato incremento capitale, cambio stato da RUNNING a READY")
                bot_manager.update_bot_status(user_id, BOT_STATUS["READY"])
                return
            
            # MONITORAGGIO THRESHOLD (solo per bot RUNNING)
            if bot_status != BOT_STATUS["RUNNING"]:
                return
                
            safety_threshold = bot.get("safety_threshold")
            rebalance_threshold = bot.get("rebalance_threshold")
            
            # Verifica che i threshold siano configurati
            if safety_threshold is None or rebalance_threshold is None:
                print(f"Threshold non configurati per bot {bot_id}")
                return
            
            # Recupera posizioni aperte per questo bot
            bot_positions = position_manager.get_bot_positions(bot_id)
            open_positions = [p for p in bot_positions if p["status"] == "open"]
            
            if not open_positions:
                return
            
            # Recupera API keys dell'utente
            api_keys = user_manager.get_user_api_keys(user_id)
            if not api_keys:
                print(f"API keys non trovate per utente {user_id}")
                return
            
            # Inizializza gli exchange necessari
            exchanges_to_init = set(pos["exchange"] for pos in open_positions)
            initialized_exchanges = set()
            
            for exchange_name in exchanges_to_init:
                api_key = api_keys.get(f"{exchange_name}_api_key")
                api_secret = api_keys.get(f"{exchange_name}_api_secret")
                
                if not api_key or not api_secret:
                    continue
                
                success = exchange_manager.initialize_exchange(
                    exchange_name,
                    api_key,
                    api_secret
                )
                
                if success:
                    initialized_exchanges.add(exchange_name)
            
            # Aggiorna le posizioni
            for position in open_positions:
                try:
                    self.update_position_thresholds(
                        position, 
                        safety_threshold, 
                        rebalance_threshold,
                        initialized_exchanges
                    )
                except Exception as e:
                    print(f"Errore aggiornamento posizione: {e}")
            
        except Exception as e:
            print(f"Errore nel processare bot {bot.get('_id')}: {e}")
    
    def update_position_thresholds(self, position: Dict, safety_threshold: float, 
                                 rebalance_threshold: float, initialized_exchanges: set) -> Dict:
        """Aggiorna i valori threshold di una singola posizione
        
        Args:
            position: Dati della posizione
            safety_threshold: Soglia safety in percentuale
            rebalance_threshold: Soglia rebalance in percentuale
            initialized_exchanges: Set degli exchange inizializzati
            
        Returns:
            dict: Risultato dell'aggiornamento
        """
        try:
            exchange_name = position["exchange"]
            symbol = position["symbol"]
            side = position["side"]
            position_id = position["position_id"]
            current_liquidation_price = position.get("liquidation_price")
            
            # Recupera liquidation price aggiornato se l'exchange è inizializzato
            new_liquidation_price = None
            if exchange_name in initialized_exchanges:
                new_liquidation_price = self.fetch_liquidation_price(exchange_name, symbol, side)
            
            # Se non riusciamo a recuperare il nuovo liquidation price, mantieni quello precedente
            liquidation_price = new_liquidation_price if new_liquidation_price else current_liquidation_price
            
            if not liquidation_price:
                return {"success": False, "error": "Liquidation price non disponibile"}
            
            # Estrai entry_price dalla posizione
            entry_price = position.get("entry_price")
            
            # Calcola safety_value e rebalance_value
            safety_value = self.calculate_threshold_value(liquidation_price, safety_threshold, side, entry_price)
            rebalance_value = self.calculate_threshold_value(liquidation_price, rebalance_threshold, side, entry_price)
            
            # Aggiorna la posizione nel database
            success = self.update_position_threshold_values(
                position_id,
                liquidation_price=liquidation_price,
                safety_value=safety_value,
                rebalance_value=rebalance_value
            )
            
            if success:
                return {"success": True}
            else:
                return {"success": False, "error": "Errore aggiornamento database"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def fetch_liquidation_price(self, exchange_name: str, symbol: str, side: str) -> Optional[float]:
        """Recupera liquidation price dalle API dell'exchange
        
        Args:
            exchange_name: Nome dell'exchange
            symbol: Simbolo trading
            side: "long" o "short"
            
        Returns:
            float: Liquidation price o None se non disponibile
        """
        try:
            # Verifica che l'exchange sia inizializzato
            if exchange_name not in exchange_manager.exchanges:
                return None
            
            exchange = exchange_manager.exchanges[exchange_name]
            
            # Per BitMEX usa logica specifica con fetch_positions()
            if exchange_name.lower() == 'bitmex':
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
                            print(f"Liquidation price recuperato da {exchange_name}: {liquidation_price}")
                            return float(liquidation_price)
            else:
                # Altri exchange: usa exchange_manager.get_position() (metodo testato)
                position = exchange_manager.get_position(exchange_name)
                if position and position.get('liquidationPrice'):
                    liquidation_price = float(position['liquidationPrice'])
                    print(f"Liquidation price recuperato da {exchange_name}: {liquidation_price}")
                    return liquidation_price
            
            return None
            
        except Exception as e:
            print(f"Errore recupero liquidation price da {exchange_name}: {e}")
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
                print("Entry price non disponibile, uso vecchia logica di calcolo")
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
            
            print(f"Calcolo threshold {side}: entry={entry_price}, liq={liquidation_price}, diff={price_difference:.4f}, threshold={threshold_value:.4f}")
            return round(threshold_value, 6)  # Arrotonda a 6 decimali
            
        except Exception as e:
            print(f"Errore calcolo threshold value: {e}")
            return 0.0
    
    def update_position_threshold_values(self, position_id: str, liquidation_price: float, 
                                       safety_value: float, rebalance_value: float) -> bool:
        """Aggiorna i valori threshold di una posizione nel database
        
        Args:
            position_id: ID della posizione
            liquidation_price: Nuovo liquidation price
            safety_value: Nuovo safety value
            rebalance_value: Nuovo rebalance value
            
        Returns:
            bool: True se aggiornamento riuscito
        """
        try:
            return position_manager.update_position_threshold_values(
                position_id=position_id,
                liquidation_price=liquidation_price,
                safety_value=safety_value,
                rebalance_value=rebalance_value
            )
            
        except Exception as e:
            print(f"Errore aggiornamento database: {e}")
            return False


def main():
    """Funzione principale"""
    monitor = ThresholdMonitor()
    monitor.run()


if __name__ == "__main__":
    main()