#!/usr/bin/env python3
"""
Closer - Modulo per chiudere posizioni di trading

Questo script monitora i bot con stato "stop_requested" e chiude le posizioni aperte.
Funziona in modo simile all'opener.py ma per la chiusura delle posizioni.

Uso:
    python -m trading.closer
"""

import logging
import sys
import os
import time
from typing import Dict, List, Optional
from datetime import datetime

# Crea directory logs se non esiste
os.makedirs("logs", exist_ok=True)

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/closer_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)

logger = logging.getLogger(__name__)

# Importa moduli necessari
from database.models import bot_manager, position_manager, user_manager
from trading.exchange_manager import exchange_manager
from config.settings import BOT_STATUS

class Closer:
    """
    Classe che gestisce la chiusura delle posizioni per i bot con stato "stop_requested"
    """
    
    def __init__(self):
        """Inizializza il closer"""
        logger.info("Closer inizializzato")
    
    def run(self):
        """
        Esegue il closer per cercare bot con stato "stop_requested"
        """
        logger.info("Avvio closer")
        
        try:
            # Cerca bot con stato "stop_requested"
            stop_requested_bots = bot_manager.get_stop_requested_bots()
            
            if stop_requested_bots:
                logger.info(f"Trovati {len(stop_requested_bots)} bot con richiesta di stop")
                
                # Processa ogni bot
                for bot in stop_requested_bots:
                    self.process_bot(bot)
                
                logger.info(f"Elaborazione completata: {len(stop_requested_bots)} bot processati")
            else:
                logger.info("Nessun bot con richiesta di stop trovato")
                
        except Exception as e:
            logger.error(f"Errore nel ciclo: {e}")
    
    def process_bot(self, bot: Dict):
        """
        Processa un bot con stato "stop_requested"
        
        Args:
            bot: Dati del bot da processare
        """
        try:
            user_id = bot["user_id"]
            bot_id = bot["_id"]
            
            logger.info(f"Processando bot {bot_id} dell'utente {user_id}")
            
            # Recupera posizioni aperte per questo bot
            open_positions = position_manager.get_bot_positions(bot_id)
            open_positions = [p for p in open_positions if p["status"] == "open"]
            
            if not open_positions:
                logger.info(f"Nessuna posizione aperta trovata per bot {bot_id}")
                # Mantieni la distinzione anche quando non ci sono posizioni
                stopped_type = bot.get("stopped_type", "manual")
                if stopped_type == "safety":
                    bot_manager.update_bot_status(user_id, BOT_STATUS["TRANSFER_REQUESTED"], "no_positions")
                else:
                    bot_manager.update_bot_status(user_id, BOT_STATUS["STOPPED"], "no_positions")
                return
            
            logger.info(f"Trovate {len(open_positions)} posizioni da chiudere per bot {bot_id}")
            
            # Recupera API keys dell'utente
            api_keys = user_manager.get_user_api_keys(user_id)
            if not api_keys:
                logger.error(f"API keys non trovate per utente {user_id}")
                # Mantieni la distinzione anche per API keys mancanti
                stopped_type = bot.get("stopped_type", "manual")
                if stopped_type == "safety":
                    bot_manager.update_bot_status(user_id, BOT_STATUS["TRANSFER_REQUESTED"], "api_keys_missing")
                else:
                    bot_manager.update_bot_status(user_id, BOT_STATUS["STOPPED"], "api_keys_missing")
                return
            
            # Inizializza gli exchange necessari
            exchanges_to_init = set(pos["exchange"] for pos in open_positions)
            for exchange_name in exchanges_to_init:
                api_key = api_keys.get(f"{exchange_name}_api_key")
                api_secret = api_keys.get(f"{exchange_name}_api_secret")
                
                if not api_key or not api_secret:
                    logger.error(f"API keys mancanti per {exchange_name}")
                    continue
                
                success = exchange_manager.initialize_exchange(
                    exchange_name,
                    api_key,
                    api_secret
                )
                
                if not success:
                    logger.error(f"Impossibile inizializzare {exchange_name}")
                    continue
                
                logger.info(f"Exchange {exchange_name} inizializzato con successo")
            
            # Chiudi le posizioni
            errors = []
            closed_count = 0
            
            for position in open_positions:
                try:
                    # Passa la posizione completa a close_position
                    result = self.close_position(position)
                    if result["success"]:
                        closed_count += 1
                        logger.info(f"Posizione {position['position_id']} chiusa con successo")
                    else:
                        errors.append(f"{position['exchange']} {position['side']}: {result['error']}")
                        logger.error(f"Errore chiusura posizione {position['position_id']}: {result['error']}")
                except Exception as e:
                    errors.append(f"{position['exchange']} {position['side']}: {str(e)}")
                    logger.error(f"Errore chiusura posizione: {e}")
            
            # Aggiorna stato del bot in base al tipo di stop
            stopped_type = bot.get("stopped_type", "manual")
            
            if errors:
                logger.error(f"Errori nella chiusura di {len(errors)} posizioni su {len(open_positions)}")
                if closed_count > 0:
                    bot_manager.update_bot_status(user_id, BOT_STATUS["STOPPED"], "partial_close")
                else:
                    bot_manager.update_bot_status(user_id, BOT_STATUS["STOPPED"], "close_error")
            else:
                logger.info(f"Tutte le {closed_count} posizioni chiuse con successo")
                
                # Distingui tra stop manuale e safety trigger
                if stopped_type == "safety":
                    # Safety trigger: imposta stato per transfer requested
                    logger.info(f"Safety trigger attivato - impostazione stato TRANSFER_REQUESTED")
                    bot_manager.update_bot_status(user_id, BOT_STATUS["TRANSFER_REQUESTED"], "emergency_close")
                else:
                    # Stop manuale o altri motivi: imposta stato STOPPED
                    logger.info(f"Stop {stopped_type} - impostazione stato STOPPED")
                    bot_manager.update_bot_status(user_id, BOT_STATUS["STOPPED"], "success")
            
        except Exception as e:
            logger.error(f"Errore nel processare bot {bot.get('_id')}: {e}")
            # Mantieni la distinzione anche in caso di errore
            stopped_type = bot.get("stopped_type", "manual")
            if stopped_type == "safety":
                bot_manager.update_bot_status(user_id, BOT_STATUS["TRANSFER_REQUESTED"], "emergency_close")
            else:
                bot_manager.update_bot_status(user_id, BOT_STATUS["STOPPED"], "error")
    
    def close_position(self, position: Dict) -> Dict:
        """
        Chiude una singola posizione
        
        Args:
            position: Dati della posizione da chiudere
            
        Returns:
            dict: Risultato della chiusura
        """
        try:
            exchange_name = position["exchange"]
            symbol = position["symbol"]
            side = position["side"]
            position_id = position["position_id"]
            
            logger.info(f"Chiusura posizione {side} su {exchange_name}: {symbol}")
            
            # Verifica che l'exchange sia inizializzato
            if exchange_name not in exchange_manager.exchanges:
                logger.error(f"Exchange {exchange_name} non inizializzato")
                return {"success": False, "error": f"Exchange {exchange_name} non inizializzato"}
            
            # Chiudi la posizione passando l'intero oggetto position
            result = exchange_manager.close_position(exchange_name)
            
            if isinstance(result, dict) and result.get("success"):
                if result["message"] == "no_position":
                    # Posizione non trovata sull'exchange (già chiusa?)
                    logger.warning(f"Posizione {position_id} non trovata su {exchange_name}, aggiorno DB")
                    # Importante: aggiorna sempre lo stato nel DB anche se non trovata sull'exchange
                    position_manager.update_position_status(position_id, "closed", {
                        "close_price": None,
                        "realized_pnl": None
                    })
                    return {"success": True}
                elif result["message"] == "position_closed":
                    # Posizione chiusa con successo
                    order = result.get("order", {})
                    
                    # Inizializza close_data con valori di default
                    close_data = {
                        "close_price": None,
                        "realized_pnl": None
                    }
                    
                    # Gestisci diversi tipi di dato restituiti dagli exchange
                    if isinstance(order, list):
                        # BitMEX restituisce una lista di ordini
                        if order and len(order) > 0:
                            first_order = order[0]
                            close_data = {
                                "close_price": first_order.get("average") or first_order.get("price"),
                                "realized_pnl": first_order.get("pnl") or first_order.get("profit")
                            }
                    elif isinstance(order, dict):
                        # Altri exchange restituiscono un dizionario
                        close_data = {
                            "close_price": order.get("average") or order.get("price"),
                            "realized_pnl": order.get("pnl") or order.get("profit")
                        }
                    
                    # Aggiorna sempre lo stato nel DB
                    position_manager.update_position_status(position_id, "closed", close_data)
                    return {"success": True}
                else:
                    # Aggiorna comunque lo stato nel DB per sicurezza
                    position_manager.update_position_status(position_id, "closed", {})
                    return {"success": True}  # Caso generico di successo
            else:
                error_msg = result.get("error") if isinstance(result, dict) else "Errore sconosciuto"
                return {"success": False, "error": error_msg}
            
        except Exception as e:
            logger.error(f"Errore chiusura posizione: {e}")
            return {"success": False, "error": str(e)}


def main():
    """Funzione principale"""
    logger.info("Avvio closer")
    closer = Closer()
    closer.run()
    logger.info("Closer terminato")


if __name__ == "__main__":
    main()