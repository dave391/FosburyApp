"""
Modulo Position Closer - Chiude posizioni aperte per un utente
"""
import logging
from typing import Dict, List
from database.models import position_manager, bot_manager, user_manager
from trading.exchange_manager import exchange_manager

# Setup logging
logger = logging.getLogger(__name__)

class PositionCloser:
    """Gestisce la chiusura delle posizioni trading"""
    
    def __init__(self):
        logger.info("PositionCloser inizializzato")
    
    def close_user_positions(self, user_id: str, reason: str = "manual") -> Dict:
        """
        Chiude tutte le posizioni aperte per un utente
        
        Args:
            user_id: ID dell'utente
            reason: Motivo della chiusura ("manual", "error", etc.)
            
        Returns:
            dict: Risultato dell'operazione
        """
        try:
            logger.info(f"🔒 Avvio chiusura posizioni per utente: {user_id}")
            
            # 1. Recupera posizioni aperte dal database
            open_positions = position_manager.get_user_open_positions(user_id)
            
            if not open_positions:
                logger.info("Nessuna posizione aperta trovata")
                # Aggiorna comunque bot status
                bot_manager.update_bot_status(user_id, "stopped", stopped_type=reason)
                return {
                    "success": True,
                    "message": "Nessuna posizione da chiudere",
                    "positions_closed": 0
                }
            
            logger.info(f"Trovate {len(open_positions)} posizioni da chiudere")
            
            # 2. Inizializza exchange con API keys utente
            api_keys = user_manager.get_user_api_keys(user_id)
            if not api_keys:
                return {
                    "success": False,
                    "error": "API keys utente non trovate",
                    "message": "Impossibile chiudere posizioni: API keys mancanti"
                }
            
            # Inizializza SEMPRE gli exchange necessari (anche se già inizializzati)
            # Questo garantisce che vengano usate le API keys dell'utente corrente
            exchanges_to_init = list(set(pos['exchange'] for pos in open_positions))
            
            # Forza reinizializzazione di tutti gli exchange necessari
            for exchange_name in exchanges_to_init:
                logger.info(f"Inizializzazione {exchange_name} per utente {user_id}...")
                
                # Ottieni API keys specifiche per questo exchange
                api_key = api_keys.get(f'{exchange_name}_api_key')
                api_secret = api_keys.get(f'{exchange_name}_api_secret')
                
                if not api_key or not api_secret:
                    logger.error(f"API keys mancanti per {exchange_name}")
                    return {
                        "success": False,
                        "error": f"API keys mancanti per {exchange_name}",
                        "message": f"Configura le API keys per {exchange_name}"
                    }
                
                # Inizializza l'exchange con le API keys dell'utente
                success = exchange_manager.initialize_exchange(
                    exchange_name,
                    api_key,
                    api_secret
                )
                
                if not success:
                    logger.error(f"Impossibile inizializzare {exchange_name} per utente {user_id}")
                    return {
                        "success": False,
                        "error": f"Impossibile inizializzare {exchange_name}",
                        "message": f"Errore inizializzazione exchange {exchange_name}"
                    }
                
                logger.info(f"✅ Exchange {exchange_name} inizializzato per chiusura")
            
            # 3. Chiudi ogni posizione
            errors = []
            closed_count = 0
            
            for position in open_positions:
                try:
                    logger.info(f"Chiusura posizione {position['side']} su {position['exchange']}")
                    
                    # Chiudi posizione sull'exchange
                    close_result = self.close_position_on_exchange(position)
                    
                    if close_result['success']:
                        # Aggiorna status nel database
                        close_data = {
                            "close_price": close_result.get('close_price'),
                            "realized_pnl": close_result.get('realized_pnl')
                        }
                        position_manager.update_position_status(
                            position['position_id'], 
                            "closed", 
                            close_data
                        )
                        closed_count += 1
                        logger.info(f"✅ Posizione {position['position_id']} chiusa con successo")
                    else:
                        # Se skip_db_update, non contare come errore ma aggiorna comunque DB
                        if close_result.get('skip_db_update'):
                            logger.warning(f"⚠️ Posizione {position['position_id']} non trovata su exchange - aggiorno DB come chiusa")
                            # Passa close_data vuoto per impostare il timestamp
                            position_manager.update_position_status(position['position_id'], "closed", {})
                            closed_count += 1
                        else:
                            errors.append(f"{position['exchange']} {position['side']}: {close_result['error']}")
                            logger.error(f"❌ Errore chiusura {position['position_id']}: {close_result['error']}")
                        
                except Exception as e:
                    error_msg = f"{position['exchange']} {position['side']}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"❌ Errore chiusura posizione: {error_msg}")
            
            # 4. Se ci sono errori, ferma tutto
            if errors:
                logger.error(f"❌ Errori nella chiusura di {len(errors)} posizioni")
                return {
                    "success": False,
                    "errors": errors,
                    "message": f"Errori nella chiusura posizioni. {closed_count}/{len(open_positions)} chiuse con successo.",
                    "positions_closed": closed_count,
                    "total_positions": len(open_positions)
                }
            
            # 5. Se tutto ok, aggiorna bot status
            bot_manager.update_bot_status(user_id, "stopped", stopped_type=reason)
            
            logger.info(f"✅ Chiuse tutte le {closed_count} posizioni con successo")
            return {
                "success": True,
                "message": f"Tutte le {closed_count} posizioni chiuse con successo",
                "positions_closed": closed_count,
                "total_positions": len(open_positions)
            }
            
        except Exception as e:
            logger.error(f"❌ Errore generale nella chiusura posizioni: {e}")
            return {
                "success": False,
                "error": f"Errore generale: {str(e)}",
                "message": "Errore nella chiusura delle posizioni"
            }
    
    def close_position_on_exchange(self, position: Dict) -> Dict:
        """
        Chiude una singola posizione sull'exchange
        
        Args:
            position: Dati della posizione dal database
            
        Returns:
            dict: Risultato della chiusura
        """
        try:
            exchange_name = position['exchange']
            symbol = position['symbol']
            side = position['side']
            
            logger.info(f"Chiusura posizione {side} su {exchange_name}: {symbol}")
            
            # Verifica che l'exchange sia inizializzato
            if exchange_name not in exchange_manager.exchanges:
                logger.error(f"Exchange {exchange_name} non inizializzato per la chiusura")
                return {
                    "success": False,
                    "error": f"Exchange {exchange_name} non inizializzato"
                }
                
            # Verifica che l'exchange sia connesso
            try:
                # Test rapido per verificare la connessione
                exchange_manager.exchanges[exchange_name].fetch_balance()
                logger.info(f"Connessione a {exchange_name} verificata")
            except Exception as conn_error:
                logger.error(f"Errore connessione a {exchange_name}: {conn_error}")
                return {
                    "success": False,
                    "error": f"Errore connessione a {exchange_name}: {str(conn_error)}"
                }
            
            # Usa il metodo esistente di exchange_manager
            result = exchange_manager.close_position(exchange_name)
            
            # Gestisci i diversi tipi di risultato
            if isinstance(result, dict):
                if result["success"]:
                    if result["message"] == "no_position":
                        # Nessuna posizione da chiudere - non aggiornare DB
                        logger.warning(f"⚠️ Nessuna posizione da chiudere su {exchange_name} - posizione già chiusa?")
                        return {
                            "success": False,
                            "error": "Posizione non trovata sull'exchange (già chiusa?)",
                            "skip_db_update": True
                        }
                    elif result["message"] == "position_closed":
                        # Posizione effettivamente chiusa - aggiorna DB
                        order = result.get("order", {})
                        close_price = order.get('average') or order.get('price') if order else None
                        realized_pnl = order.get('pnl') or order.get('profit') if order else None
                        
                        return {
                            "success": True,
                            "close_price": close_price,
                            "realized_pnl": realized_pnl,
                            "order_data": order
                        }
                else:
                    # Errore nella chiusura
                    return {
                        "success": False,
                        "error": result.get("error", "Errore sconosciuto nella chiusura")
                    }
            else:
                # Formato vecchio - per retrocompatibilità
                if result:
                    return {
                        "success": True,
                        "close_price": None,
                        "realized_pnl": None,
                        "order_data": result
                    }
                else:
                    return {
                        "success": False,
                        "error": "Nessun ordine di chiusura restituito dall'exchange"
                    }
                
        except Exception as e:
            logger.error(f"Errore chiusura posizione su {exchange_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_positions_summary(self, user_id: str) -> Dict:
        """
        Ottiene un riassunto delle posizioni dell'utente
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            dict: Riassunto delle posizioni
        """
        try:
            open_positions = position_manager.get_user_open_positions(user_id)
            
            summary = {
                "total_positions": len(open_positions),
                "exchanges": list(set(pos['exchange'] for pos in open_positions)),
                "symbols": list(set(pos['symbol'] for pos in open_positions)),
                "total_long": len([p for p in open_positions if p['side'] == 'long']),
                "total_short": len([p for p in open_positions if p['side'] == 'short']),
                "positions": open_positions
            }
            
            return {
                "success": True,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Errore recupero riassunto posizioni: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Istanza globale
position_closer = PositionCloser()