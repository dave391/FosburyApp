"""
Price Monitor - Recupero prezzo SOLANA per MVP
Recupera il prezzo SOLUSDT da Binance e lo salva nel database
"""

import requests
from datetime import datetime, timezone
from typing import Dict, List
from database.models import db_manager, bot_manager, position_manager
from config.settings import BOT_STATUS


class PriceMonitor:
    """
    Monitora il prezzo SOLUSDT e lo salva nel database.
    
    Versione semplificata per MVP:
    - Chiama API Binance (con fallback CoinGecko)
    - Salva prezzo in MongoDB collection 'current_prices'
    - Gestione errori base
    """
    
    def __init__(self):
        """Inizializza il price monitor"""
        self.db = db_manager.db
        self.current_price = None  # Memorizza il prezzo corrente per i trigger
        
        # URLs per recupero prezzo (con fallback)
        self.price_sources = [
            {
                "name": "Binance",
                "url": "https://api.binance.com/api/v3/ticker/price",
                "params": {"symbol": "SOLUSDT"},
                "price_field": "price"
            },
            {
                "name": "CoinGecko", 
                "url": "https://api.coingecko.com/api/v3/simple/price",
                "params": {"ids": "solana", "vs_currencies": "usd"},
                "price_field": "solana.usd"
            }
        ]
    
    def update_price(self) -> Dict:
        """
        Aggiorna il prezzo SOLUSDT e salva nel database
        
        Returns:
            dict: Risultato operazione con price e timestamp
        """
        # Recupera prezzo da API esterne
        price_data = self._fetch_price_from_sources()
        
        if not price_data["success"]:
            return price_data
        
        # Prezzo recuperato con successo
        new_price = price_data["price"]
        current_time = datetime.now(timezone.utc)
        
        # Salva nel database
        save_result = self._save_price_to_database(new_price, current_time, price_data["source"])
        
        if save_result["success"]:
            # Memorizza il prezzo corrente per i trigger
            self.current_price = new_price
            
            # Esegui controlli trigger automatici
            self.check_bot_triggers()
            
            return {
                "success": True,
                "price": new_price,
                "timestamp": current_time.isoformat(),
                "source": price_data["source"]
            }
        else:
            return save_result
    
    def _fetch_price_from_sources(self) -> Dict:
        """
        Recupera prezzo da API esterne con sistema di fallback
        
        Returns:
            dict: Risultato con price o error
        """
        
        for source in self.price_sources:
            try:
                # Chiamata API REST
                response = requests.get(
                    source["url"], 
                    params=source["params"],
                    timeout=10
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Estrai prezzo dal campo specifico
                price = self._extract_price_from_response(data, source["price_field"])
                
                if price > 0:
                    return {
                        "success": True,
                        "price": price,
                        "source": source["name"]
                    }
                
            except Exception:
                continue
        
        # Tutti i tentativi falliti
        return {
            "success": False,
            "error": "Impossibile recuperare prezzo da nessuna fonte",
            "price": 0.0
        }
    
    def _extract_price_from_response(self, data: Dict, field_path: str) -> float:
        """
        Estrae prezzo da response JSON usando field path
        
        Args:
            data: Response JSON dell'API
            field_path: Percorso campo prezzo (es. "price" o "solana.usd")
            
        Returns:
            float: Prezzo estratto, 0.0 se errore
        """
        try:
            # Split del path (es. "solana.usd" -> ["solana", "usd"])
            fields = field_path.split(".")
            
            # Naviga nel JSON seguendo il path
            current_data = data
            for field in fields:
                current_data = current_data[field]
            
            # Converte a float
            return float(current_data)
            
        except (KeyError, ValueError, TypeError):
            return 0.0
    
    def _save_price_to_database(self, price: float, timestamp: datetime, source: str) -> Dict:
        """
        Salva prezzo nel database MongoDB
        
        Args:
            price: Prezzo da salvare
            timestamp: Timestamp aggiornamento
            source: Fonte del prezzo (Binance, CoinGecko, etc.)
            
        Returns:
            dict: Risultato operazione
        """
        try:
            # Prepara documento per MongoDB
            price_doc = {
                "symbol": "SOLUSDT",
                "price": price,
                "timestamp": timestamp,
                "source": source,
                "updated_at": timestamp
            }
            
            # UPSERT: aggiorna se esiste, crea se non esiste
            self.db.current_prices.replace_one(
                {"symbol": "SOLUSDT"},  # Filtro
                price_doc,                    # Sostituzione completa
                upsert=True                  # Crea se non esiste
            )
            
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Errore salvataggio MongoDB: {str(e)}"
            }
    
    def check_bot_triggers(self) -> None:
        """Controlla trigger per tutti i bot running"""
        try:
            # Recupera tutti i bot con status 'running'
            running_bots = bot_manager.get_running_bots()
            
            if not running_bots:
                return
            
            # Controlla trigger per ogni bot
            for bot in running_bots:
                try:
                    # Controlla safety trigger
                    self.check_safety_trigger(bot)
                    
                    # Controlla rebalance trigger
                    self.check_rebalance_trigger(bot)
                    
                except Exception as e:
                    # Ignora errori per MVP come richiesto
                    pass
                    
        except Exception as e:
            # Ignora errori per MVP come richiesto
            pass
    
    def check_safety_trigger(self, bot: Dict) -> None:
        """Controlla safety trigger per un bot"""
        try:
            if self.current_price is None:
                return
            
            user_id = bot["user_id"]
            
            # Recupera posizioni aperte per questo bot
            bot_positions = position_manager.get_bot_positions(bot["_id"])
            open_positions = [p for p in bot_positions if p["status"] == "open"]
            
            if not open_positions:
                return
            
            # Controlla se il safety trigger è scattato
            trigger_activated = False
            
            for position in open_positions:
                safety_value = position.get("safety_value")
                side = position.get("side")
                
                if safety_value is None or side is None:
                    continue
                
                # Controlla trigger in base al lato della posizione
                if side == "long" and self.current_price < safety_value:
                    trigger_activated = True
                    break
                elif side == "short" and self.current_price > safety_value:
                    trigger_activated = True
                    break
            
            # Se trigger attivato, cambia stato bot
            if trigger_activated:
                bot_manager.update_bot_status(user_id, BOT_STATUS["STOP_REQUESTED"], "safety", "emergency_close")
                
        except Exception as e:
            # Ignora errori per MVP come richiesto
            pass
    
    def check_rebalance_trigger(self, bot: Dict) -> None:
        """Controlla rebalance trigger per un bot"""
        try:
            if self.current_price is None:
                return
            
            user_id = bot["user_id"]
            
            # Recupera posizioni aperte per questo bot
            bot_positions = position_manager.get_bot_positions(bot["_id"])
            open_positions = [p for p in bot_positions if p["status"] == "open"]
            
            if not open_positions:
                return
            
            # Controlla se il rebalance trigger è scattato
            trigger_activated = False
            
            for position in open_positions:
                rebalance_value = position.get("rebalance_value")
                side = position.get("side")
                
                if rebalance_value is None or side is None:
                    continue
                
                # Controlla trigger in base al lato della posizione
                if side == "long" and self.current_price < rebalance_value:
                    trigger_activated = True
                    break
                elif side == "short" and self.current_price > rebalance_value:
                    trigger_activated = True
                    break
            
            # Se trigger attivato, cambia stato bot
            if trigger_activated:
                bot_manager.update_bot_status(user_id, BOT_STATUS["TRANSFER_REQUESTED"], "rebalance", "rebalance")
                
        except Exception as e:
            # Ignora errori per MVP come richiesto
            pass


# Istanza globale per utilizzo
price_monitor = PriceMonitor()


if __name__ == "__main__":
    # Test del modulo
    result = price_monitor.update_price()
    if result["success"]:
        print(f"Prezzo aggiornato: SOLUSDT = ${result['price']:.4f}")
    else:
        print(f"Errore: {result['error']}")