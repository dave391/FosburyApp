"""
Modelli e operazioni database MongoDB
"""
from pymongo import MongoClient
from datetime import datetime
from typing import Optional, Dict, List
from bson import ObjectId
import logging
from config.settings import MONGODB_URI, DATABASE_NAME, BOT_STATUS
from utils.crypto_utils import crypto_utils

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manager per operazioni database"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Connessione al database"""
        try:
            # Sostituisci <db_password> con la password reale quando necessario
            self.client = MongoClient(MONGODB_URI)
            self.db = self.client[DATABASE_NAME]
            logger.info("Connesso a MongoDB")
        except Exception as e:
            logger.error(f"Errore connessione MongoDB: {e}")
            raise
    
    def close(self):
        """Chiude connessione database"""
        if self.client:
            self.client.close()

class UserManager:
    """Manager per operazioni sugli utenti"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager.db
        self.users = self.db.users
    
    def create_user(self, email: str, password: str) -> bool:
        """Crea nuovo utente"""
        try:
            # Verifica se utente esiste già
            if self.users.find_one({"email": email}):
                return False
            
            # Hash password
            password_hash = crypto_utils.hash_password(password)
            
            user_data = {
                "email": email,
                "password_hash": password_hash,
                "bitfinex_api_key": "",
                "bitfinex_api_secret": "",
                "bitmex_api_key": "",
                "bitmex_api_secret": "",
                "bitfinex_wallet": "",
                "bitmex_wallet": "",
                "created_at": datetime.utcnow()
            }
            
            result = self.users.insert_one(user_data)
            logger.info(f"Utente creato: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Errore creazione utente: {e}")
            return False
    
    def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """Autentica utente e restituisce user_id"""
        try:
            user = self.users.find_one({"email": email})
            if not user:
                return None
            
            if crypto_utils.verify_password(password, user["password_hash"]):
                logger.info(f"Login effettuato: {email}")
                return str(user["_id"])
            
            return None
            
        except Exception as e:
            logger.error(f"Errore autenticazione: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Recupera utente per email"""
        try:
            user = self.users.find_one({"email": email})
            if user:
                return {
                    "user_id": str(user["_id"]),
                    "email": user["email"],
                    "created_at": user.get("created_at")
                }
            return None
        except Exception as e:
            logger.error(f"Errore recupero utente per email: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Recupera utente per user_id"""
        try:
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if user:
                return {
                    "user_id": str(user["_id"]),
                    "email": user["email"],
                    "created_at": user.get("created_at")
                }
            return None
        except Exception as e:
            logger.error(f"Errore recupero utente per ID: {e}")
            return None
    
    def update_api_keys(self, user_id: str, exchange: str, api_key: str, api_secret: str) -> bool:
        """Aggiorna API keys per exchange"""
        try:
            encrypted_key = crypto_utils.encrypt_api_key(api_key)
            encrypted_secret = crypto_utils.encrypt_api_key(api_secret)
            
            update_data = {
                f"{exchange}_api_key": encrypted_key,
                f"{exchange}_api_secret": encrypted_secret
            }
            
            result = self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            logger.info(f"API keys aggiornate per {exchange}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Errore aggiornamento API keys: {e}")
            return False
    
    def get_user_api_keys(self, user_id: str) -> Dict[str, str]:
        """Recupera API keys utente decriptate"""
        try:
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {}
            
            return {
                "bitfinex_api_key": crypto_utils.decrypt_api_key(user.get("bitfinex_api_key", "")),
                "bitfinex_api_secret": crypto_utils.decrypt_api_key(user.get("bitfinex_api_secret", "")),
                "bitmex_api_key": crypto_utils.decrypt_api_key(user.get("bitmex_api_key", "")),
                "bitmex_api_secret": crypto_utils.decrypt_api_key(user.get("bitmex_api_secret", ""))
            }
            
        except Exception as e:
            logger.error(f"Errore recupero API keys: {e}")
            return {}
    
    def update_wallet(self, user_id: str, exchange: str, wallet_address: str) -> bool:
        """Aggiorna wallet address per exchange"""
        try:
            encrypted_wallet = crypto_utils.encrypt_api_key(wallet_address)
            
            update_data = {
                f"{exchange}_wallet": encrypted_wallet
            }
            
            result = self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            logger.info(f"Wallet aggiornato per {exchange}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Errore aggiornamento wallet: {e}")
            return False
    
    def get_user_wallets(self, user_id: str) -> Dict[str, str]:
        """Recupera wallet addresses utente decriptati"""
        try:
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {}
            
            return {
                "bitfinex_wallet": crypto_utils.decrypt_api_key(user.get("bitfinex_wallet", "")),
                "bitmex_wallet": crypto_utils.decrypt_api_key(user.get("bitmex_wallet", ""))
            }
            
        except Exception as e:
            logger.error(f"Errore recupero wallets: {e}")
            return {}

class BotManager:
    """Manager per operazioni sui bot"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager.db
        self.bots = self.db.bots
    
    def create_bot_config(self, user_id: str, exchange_long: str, exchange_short: str, 
                         capital: float, leverage: float, rebalance_threshold: float, 
                         safety_threshold: float, stop_loss_percentage: float) -> bool:
        """Crea nuova istanza bot (sempre una nuova entry)"""
        try:
            # Verifica che l'utente esista
            user = self.db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                logger.error(f"Utente {user_id} non trovato")
                return False
            
            # Ferma tutti i bot attivi dell'utente (se presenti)
            active_bots = self.bots.find({
                "user_id": user_id,
                "status": {"$in": [BOT_STATUS["READY"], BOT_STATUS["RUNNING"]]}
            })
            
            for bot in active_bots:
                self.bots.update_one(
                    {"_id": bot["_id"]},
                    {
                        "$set": {
                            "status": BOT_STATUS["STOPPED"],
                            "stopped_at": datetime.utcnow(),
                            "stopped_type": "new_instance"
                        }
                    }
                )
                logger.info(f"Bot precedente {bot['_id']} fermato per nuova istanza")
            
            # Crea SEMPRE una nuova istanza bot
            bot_data = {
                "user_id": user_id,
                "user_email": user.get("email", ""),
                "exchange_long": exchange_long,
                "exchange_short": exchange_short,
                "capital": capital,
                "leverage": leverage,
                "rebalance_threshold": rebalance_threshold,
                "safety_threshold": safety_threshold,
                "stop_loss_percentage": stop_loss_percentage,
                "status": BOT_STATUS["READY"],
                "created_at": datetime.utcnow(),
                "started_at": None,
                "stopped_at": None,
                "stopped_type": None,
                "started_type": None,
                "transfer_reason": None,
                "transfer_amount": None
            }
            
            result = self.bots.insert_one(bot_data)
            logger.info(f"Nuova istanza bot creata per utente: {user_id}, bot_id: {result.inserted_id}")
            return result.inserted_id is not None
            
        except Exception as e:
            logger.error(f"Errore creazione istanza bot: {e}")
            return False
    
    def get_user_bot(self, user_id: str) -> Optional[Dict]:
        """Recupera l'istanza bot più recente dell'utente"""
        try:
            # Ordina per created_at descrescente per ottenere il più recente
            return self.bots.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
        except Exception as e:
            logger.error(f"Errore recupero bot: {e}")
            return None
    
    def update_bot_status(self, user_id: str, status: str, stopped_type: str = None, started_type: str = None, transfer_reason: str = None, transfer_amount: float = None) -> bool:
        """Aggiorna status dell'istanza bot più recente dell'utente"""
        try:
            # Trova l'istanza bot più recente
            latest_bot = self.get_user_bot(user_id)
            if not latest_bot:
                logger.warning(f"Nessun bot trovato per utente: {user_id}")
                return False
            
            # Prepara update data
            update_data = {"status": status}
            
            if status == BOT_STATUS["RUNNING"]:
                # Bot avviato - imposta started_at
                update_data["started_at"] = datetime.utcnow()
                update_data["stopped_at"] = None
                update_data["stopped_type"] = None
                if transfer_reason:
                    update_data["transfer_reason"] = transfer_reason
                
            elif status == BOT_STATUS["STOPPED"]:
                # Bot fermato - imposta stopped_at e tipo
                update_data["stopped_at"] = datetime.utcnow()
                update_data["stopped_type"] = stopped_type or "manual"
                
            elif status == BOT_STATUS["STOP_REQUESTED"]:
                # Richiesta di stop - non modificare timestamp, solo stato
                # Non modifichiamo stopped_at perché non è ancora effettivamente fermato
                update_data["stopped_type"] = stopped_type or "manual"
                
            elif status == BOT_STATUS["READY"]:
                # Bot pronto - mantieni started_at se presente, resetta stopped
                update_data["stopped_at"] = None
                update_data["stopped_type"] = None
                if started_type:
                    update_data["started_type"] = started_type
                    
            elif status == BOT_STATUS["TRANSFERING"]:
                # Bot in trasferimento - imposta started_type e mantiene transfer_reason
                if started_type:
                    update_data["started_type"] = started_type
                # Non resettiamo transfer_reason qui, viene mantenuto dal precedente stato
                    
            elif status == BOT_STATUS["TRANSFER_REQUESTED"]:
                # Bot richiede trasferimento - imposta stopped_type come motivo e transfer_reason
                if stopped_type:
                    update_data["stopped_type"] = stopped_type
                if transfer_reason:
                    update_data["transfer_reason"] = transfer_reason
                    
            elif status == BOT_STATUS["EXTERNAL_TRANSFER_PENDING"]:
                # Bot in attesa di trasferimento esterno - salva l'importo da trasferire
                if transfer_amount is not None:
                    update_data["transfer_amount"] = transfer_amount
                if transfer_reason:
                    update_data["transfer_reason"] = transfer_reason
            
            # Aggiorna l'istanza specifica tramite _id
            result = self.bots.update_one(
                {"_id": latest_bot["_id"]},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Status bot {latest_bot['_id']} aggiornato a {status} per utente: {user_id}")
                return True
            else:
                logger.warning(f"Errore aggiornamento bot {latest_bot['_id']} per utente: {user_id}")
                return False
            
        except Exception as e:
            logger.error(f"Errore aggiornamento status bot: {e}")
            return False
    
    def get_ready_bots(self) -> List[Dict]:
        """Recupera tutti i bot con status 'ready' o 'transfering'"""
        try:
            return list(self.bots.find({"status": {"$in": [BOT_STATUS["READY"], BOT_STATUS["TRANSFERING"]]}}))
        except Exception as e:
            logger.error(f"Errore recupero bot ready/transfering: {e}")
            return []
    
    def get_stop_requested_bots(self) -> List[Dict]:
        """Recupera tutti i bot con status 'stop_requested'"""
        try:
            return list(self.bots.find({"status": BOT_STATUS["STOP_REQUESTED"]}))
        except Exception as e:
            logger.error(f"Errore recupero bot stop_requested: {e}")
            return []
    
    def get_running_bots(self) -> List[Dict]:
        """Recupera tutti i bot con status 'running'"""
        try:
            return list(self.bots.find({"status": BOT_STATUS["RUNNING"]}))
        except Exception as e:
            logger.error(f"Errore recupero bot running: {e}")
            return []
    
    def get_transfer_requested_bots(self) -> List[Dict]:
        """Recupera tutti i bot con status 'transfer_requested'"""
        try:
            return list(self.bots.find({"status": BOT_STATUS["TRANSFER_REQUESTED"]}))
        except Exception as e:
            logger.error(f"Errore recupero bot transfer_requested: {e}")
            return []
    
    def get_external_transfer_pending_bots(self) -> List[Dict]:
        """Recupera tutti i bot con status 'external_transfer_pending'"""
        try:
            return list(self.bots.find({"status": BOT_STATUS["EXTERNAL_TRANSFER_PENDING"]}))
        except Exception as e:
            logger.error(f"Errore recupero bot external_transfer_pending: {e}")
            return []
    
    def get_user_bot_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Recupera cronologia bot dell'utente"""
        try:
            return list(self.bots.find(
                {"user_id": user_id},
                sort=[("created_at", -1)],
                limit=limit
            ))
        except Exception as e:
            logger.error(f"Errore recupero cronologia bot: {e}")
            return []
    
    def add_missing_fields_to_bots(self):
        """
        Aggiunge i campi mancanti (rebalance_threshold, safety_threshold, stop_loss_percentage) ai bot esistenti
        
        Returns:
            int: Numero di bot aggiornati
        """
        try:
            # Aggiorna tutti i bot che non hanno i campi rebalance_threshold, safety_threshold e stop_loss_percentage
            result = self.bots.update_many(
                {"$or": [
                    {"rebalance_threshold": {"$exists": False}},
                    {"safety_threshold": {"$exists": False}},
                    {"stop_loss_percentage": {"$exists": False}}
                ]},
                {"$set": {
                    "rebalance_threshold": None,
                    "safety_threshold": None,
                    "stop_loss_percentage": None
                }}
            )
            
            logger.info(f"Campi mancanti aggiunti a {result.modified_count} bot")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Errore aggiunta campi mancanti ai bot: {e}")
            return 0

class PositionManager:
    """Manager per gestione posizioni trading"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.positions = db_manager.db.positions
        logger.info("PositionManager inizializzato")
    
    def save_position(self, position_data):
        """
        Salva una posizione nel database
        
        Args:
            position_data (dict): Dati della posizione
            
        Returns:
            bool: True se salvata con successo
        """
        try:
            # Validazione dati essenziali
            required_fields = ['position_id', 'user_id', 'bot_id', 'exchange', 'symbol', 'side', 'size']
            for field in required_fields:
                if field not in position_data:
                    logger.error(f"Campo richiesto mancante: {field}")
                    return False
            
            # Log liquidation price se presente
            if position_data.get('liquidation_price'):
                logger.info(f"Salvando posizione con liquidation price: {position_data['liquidation_price']}")
            else:
                logger.warning("Liquidation price non disponibile per la posizione")
            
            result = self.positions.insert_one(position_data)
            
            if result.inserted_id:
                logger.info(f"Posizione salvata: {position_data['position_id']} su {position_data['exchange']}")
                return True
            else:
                logger.error("Errore inserimento posizione")
                return False
                
        except Exception as e:
            logger.error(f"Errore salvataggio posizione: {e}")
            return False
    
    def get_user_open_positions(self, user_id):
        """
        Recupera tutte le posizioni aperte per un utente
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            list: Lista delle posizioni aperte
        """
        try:
            positions = list(self.positions.find({
                "user_id": user_id,
                "status": "open"
            }))
            
            logger.info(f"Trovate {len(positions)} posizioni aperte per utente {user_id}")
            return positions
            
        except Exception as e:
            logger.error(f"Errore recupero posizioni aperte: {e}")
            return []
    
    def get_bot_positions(self, bot_id):
        """
        Recupera tutte le posizioni di un bot specifico
        
        Args:
            bot_id: ID del bot
            
        Returns:
            list: Lista delle posizioni del bot
        """
        try:
            positions = list(self.positions.find({
                "bot_id": bot_id
            }))
            
            logger.info(f"Trovate {len(positions)} posizioni per bot {bot_id}")
            return positions
            
        except Exception as e:
            logger.error(f"Errore recupero posizioni bot: {e}")
            return []
    
    def update_position_status(self, position_id, status, close_data=None):
        """
        Aggiorna lo status di una posizione
        
        Args:
            position_id: ID della posizione
            status: Nuovo status ("open", "closed", "error")
            close_data: Dati di chiusura opzionali
            
        Returns:
            bool: True se aggiornata con successo
        """
        try:
            update_data = {
                "status": status
            }
            
            # Se stiamo chiudendo, aggiungi dati di chiusura
            if status == "closed" and close_data:
                update_data.update({
                    "closed_at": datetime.utcnow(),
                    "close_price": close_data.get("close_price"),
                    "realized_pnl": close_data.get("realized_pnl")
                })
            
            result = self.positions.update_one(
                {"position_id": position_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Posizione {position_id} aggiornata a status: {status}")
                return True
            else:
                logger.warning(f"Nessuna posizione trovata con ID: {position_id}")
                return False
                
        except Exception as e:
            logger.error(f"Errore aggiornamento posizione: {e}")
            return False
    
    def close_all_user_positions(self, user_id, close_reason="manual"):
        """
        Chiude tutte le posizioni aperte di un utente
        
        Args:
            user_id: ID dell'utente
            close_reason: Motivo della chiusura
            
        Returns:
            int: Numero di posizioni chiuse
        """
        try:
            update_data = {
                "status": "closed",
                "closed_at": datetime.utcnow(),
                "close_reason": close_reason
            }
            
            result = self.positions.update_many(
                {"user_id": user_id, "status": "open"},
                {"$set": update_data}
            )
            
            logger.info(f"Chiuse {result.modified_count} posizioni per utente {user_id}")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Errore chiusura posizioni utente: {e}")
            return 0
    
    def add_missing_fields_to_positions(self):
        """
        Aggiunge i campi mancanti (rebalance_value, safety_value) alle posizioni esistenti
        
        Returns:
            int: Numero di posizioni aggiornate
        """
        try:
            # Aggiorna tutte le posizioni che non hanno i campi rebalance_value e safety_value
            result = self.positions.update_many(
                {"$or": [
                    {"rebalance_value": {"$exists": False}},
                    {"safety_value": {"$exists": False}}
                ]},
                {"$set": {
                    "rebalance_value": None,
                    "safety_value": None
                }}
            )
            
            logger.info(f"Campi mancanti aggiunti a {result.modified_count} posizioni")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Errore aggiunta campi mancanti: {e}")
            return 0
    
    def update_position_threshold_values(self, position_id: str, liquidation_price: float = None, 
                                       safety_value: float = None, rebalance_value: float = None) -> bool:
        """
        Aggiorna i valori threshold di una posizione
        
        Args:
            position_id: ID della posizione
            liquidation_price: Nuovo liquidation price (opzionale)
            safety_value: Nuovo safety value (opzionale)
            rebalance_value: Nuovo rebalance value (opzionale)
            
        Returns:
            bool: True se aggiornamento riuscito
        """
        try:
            update_data = {"threshold_updated_at": datetime.utcnow()}
            
            if liquidation_price is not None:
                update_data["liquidation_price"] = liquidation_price
            if safety_value is not None:
                update_data["safety_value"] = safety_value
            if rebalance_value is not None:
                update_data["rebalance_value"] = rebalance_value
            
            result = self.positions.update_one(
                {"position_id": position_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Threshold aggiornati per posizione {position_id}")
                return True
            else:
                logger.warning(f"Nessuna posizione trovata con ID: {position_id}")
                return False
                
        except Exception as e:
            logger.error(f"Errore aggiornamento threshold posizione: {e}")
            return False

# Istanze globali
db_manager = DatabaseManager()
user_manager = UserManager(db_manager)
bot_manager = BotManager(db_manager)
position_manager = PositionManager(db_manager)