"""
Script per setup e inizializzazione database MongoDB
"""
import logging
from pymongo import MongoClient, ASCENDING
from pymongo.errors import CollectionInvalid, OperationFailure
from config.settings import MONGODB_URI, DATABASE_NAME

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    """Classe per setup database"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Connessione al database"""
        try:
            self.client = MongoClient(MONGODB_URI)
            self.db = self.client[DATABASE_NAME]
            logger.info(f"✅ Connesso al database: {DATABASE_NAME}")
        except Exception as e:
            logger.error(f"❌ Errore connessione MongoDB: {e}")
            raise
    
    def list_existing_collections(self):
        """Lista collections esistenti"""
        try:
            collections = self.db.list_collection_names()
            logger.info(f"📋 Collections esistenti: {collections}")
            return collections
        except Exception as e:
            logger.error(f"❌ Errore lista collections: {e}")
            return []
    
    def drop_unnecessary_collections(self):
        """Elimina collections non necessarie"""
        existing_collections = self.list_existing_collections()
        necessary_collections = ['users', 'bots']
        
        for collection_name in existing_collections:
            if collection_name not in necessary_collections:
                try:
                    self.db.drop_collection(collection_name)
                    logger.info(f"🗑️  Collection '{collection_name}' eliminata")
                except Exception as e:
                    logger.error(f"❌ Errore eliminazione '{collection_name}': {e}")
    
    def create_users_collection(self):
        """Crea collection users con indici"""
        try:
            # Crea collection se non exists
            if 'users' not in self.db.list_collection_names():
                self.db.create_collection('users')
                logger.info("✅ Collection 'users' creata")
            else:
                logger.info("ℹ️  Collection 'users' già esistente")
            
            users_collection = self.db.users
            
            # Crea indici
            # Indice unique su email
            try:
                users_collection.create_index([("email", ASCENDING)], unique=True)
                logger.info("✅ Indice unique su 'email' creato")
            except OperationFailure as e:
                if "already exists" in str(e):
                    logger.info("ℹ️  Indice 'email' già esistente")
                else:
                    logger.error(f"❌ Errore creazione indice email: {e}")
            
            # Indice su created_at per performance
            try:
                users_collection.create_index([("created_at", ASCENDING)])
                logger.info("✅ Indice su 'created_at' creato")
            except OperationFailure as e:
                if "already exists" in str(e):
                    logger.info("ℹ️  Indice 'created_at' già esistente")
                else:
                    logger.error(f"❌ Errore creazione indice created_at: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore creazione collection users: {e}")
            return False
    
    def create_bots_collection(self):
        """Crea collection bots con indici"""
        try:
            # Crea collection se non exists
            if 'bots' not in self.db.list_collection_names():
                self.db.create_collection('bots')
                logger.info("✅ Collection 'bots' creata")
            else:
                logger.info("ℹ️  Collection 'bots' già esistente")
            
            bots_collection = self.db.bots
            
            # Crea indici
            # Indice su user_id (multiple istanze per utente)
            try:
                bots_collection.create_index([("user_id", ASCENDING)])
                logger.info("✅ Indice su 'user_id' creato")
            except OperationFailure as e:
                if "already exists" in str(e):
                    logger.info("ℹ️  Indice 'user_id' già esistente")
                else:
                    logger.error(f"❌ Errore creazione indice user_id: {e}")
            
            # Indice su status per query veloci
            try:
                bots_collection.create_index([("status", ASCENDING)])
                logger.info("✅ Indice su 'status' creato")
            except OperationFailure as e:
                if "already exists" in str(e):
                    logger.info("ℹ️  Indice 'status' già esistente")
                else:
                    logger.error(f"❌ Errore creazione indice status: {e}")
            
            # Indice composto per query specifiche
            try:
                bots_collection.create_index([("status", ASCENDING), ("created_at", ASCENDING)])
                logger.info("✅ Indice composto 'status+created_at' creato")
            except OperationFailure as e:
                if "already exists" in str(e):
                    logger.info("ℹ️  Indice composto già esistente")
                else:
                    logger.error(f"❌ Errore creazione indice composto: {e}")
            
            # Indice su user_email per ricerche
            try:
                bots_collection.create_index([("user_email", ASCENDING)])
                logger.info("✅ Indice su 'user_email' creato")
            except OperationFailure as e:
                if "already exists" in str(e):
                    logger.info("ℹ️  Indice 'user_email' già esistente")
                else:
                    logger.error(f"❌ Errore creazione indice user_email: {e}")
            
            # Indice su started_at per query temporali
            try:
                bots_collection.create_index([("started_at", ASCENDING)])
                logger.info("✅ Indice su 'started_at' creato")
            except OperationFailure as e:
                if "already exists" in str(e):
                    logger.info("ℹ️  Indice 'started_at' già esistente")
                else:
                    logger.error(f"❌ Errore creazione indice started_at: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore creazione collection bots: {e}")
            return False
    
    def validate_collections(self):
        """Valida struttura collections"""
        try:
            # Valida users collection
            users_indexes = list(self.db.users.list_indexes())
            logger.info(f"📋 Indici users: {[idx['name'] for idx in users_indexes]}")
            
            # Valida bots collection
            bots_indexes = list(self.db.bots.list_indexes())
            logger.info(f"📋 Indici bots: {[idx['name'] for idx in bots_indexes]}")
            
            # Test insert/delete per validare funzionalità
            test_user = {
                "email": "test@example.com",
                "password_hash": "test_hash",
                "bitfinex_api_key": "",
                "bitfinex_api_secret": "",
                "bitmex_api_key": "",
                "bitmex_api_secret": ""
            }
            
            # Test users collection
            result = self.db.users.insert_one(test_user)
            user_id = result.inserted_id
            self.db.users.delete_one({"_id": user_id})
            logger.info("✅ Test users collection: OK")
            
            # Test bots collection
            test_bot = {
                "user_id": str(user_id),
                "user_email": "test@example.com",
                "exchange_long": "bitfinex",
                "exchange_short": "bitmex",
                "capital": 10.0,
                "leverage": 2.0,
                "status": "ready",
                "started_at": None,
                "stopped_at": None,
                "stopped_type": None
            }
            
            result = self.db.bots.insert_one(test_bot)
            bot_id = result.inserted_id
            self.db.bots.delete_one({"_id": bot_id})
            logger.info("✅ Test bots collection: OK")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore validazione collections: {e}")
            return False
    
    def get_database_stats(self):
        """Mostra statistiche database"""
        try:
            stats = self.db.command("dbstats")
            logger.info(f"📊 Statistiche database:")
            logger.info(f"   - Collections: {stats.get('collections', 'N/A')}")
            logger.info(f"   - Data Size: {stats.get('dataSize', 'N/A')} bytes")
            logger.info(f"   - Index Size: {stats.get('indexSize', 'N/A')} bytes")
            
            # Conta documenti per collection
            users_count = self.db.users.count_documents({})
            bots_count = self.db.bots.count_documents({})
            
            logger.info(f"📋 Documenti:")
            logger.info(f"   - Users: {users_count}")
            logger.info(f"   - Bots: {bots_count}")
            
        except Exception as e:
            logger.error(f"❌ Errore statistiche database: {e}")
    
    def setup_complete_database(self):
        """Setup completo database"""
        logger.info("🚀 Avvio setup database...")
        
        try:
            # 1. Lista collections esistenti
            logger.info("\n📋 FASE 1: Analisi collections esistenti")
            self.list_existing_collections()
            
            # 2. Elimina collections non necessarie
            logger.info("\n🗑️  FASE 2: Pulizia collections non necessarie")
            self.drop_unnecessary_collections()
            
            # 3. Crea collection users
            logger.info("\n👥 FASE 3: Setup collection users")
            if not self.create_users_collection():
                logger.error("❌ Errore setup users collection")
                return False
            
            # 4. Crea collection bots
            logger.info("\n🤖 FASE 4: Setup collection bots")
            if not self.create_bots_collection():
                logger.error("❌ Errore setup bots collection")
                return False
            
            # 5. Valida setup
            logger.info("\n✅ FASE 5: Validazione setup")
            if not self.validate_collections():
                logger.error("❌ Errore validazione collections")
                return False
            
            # 6. Mostra statistiche
            logger.info("\n📊 FASE 6: Statistiche finali")
            self.get_database_stats()
            
            logger.info("\n🎉 Setup database completato con successo!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore generale setup database: {e}")
            return False
    
    def close(self):
        """Chiude connessione database"""
        if self.client:
            self.client.close()
            logger.info("🔚 Connessione database chiusa")

def main():
    """Funzione principale setup database"""
    setup = DatabaseSetup()
    
    try:
        success = setup.setup_complete_database()
        if success:
            logger.info("✅ Database pronto per l'uso!")
        else:
            logger.error("❌ Setup database fallito!")
    except KeyboardInterrupt:
        logger.info("❌ Setup interrotto dall'utente")
    except Exception as e:
        logger.error(f"❌ Errore critico: {e}")
    finally:
        setup.close()

if __name__ == "__main__":
    main()