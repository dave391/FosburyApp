"""
Configurazioni per l'applicazione di trading
"""
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
DB_PASSWORD = os.getenv('DB_PASSWORD', 'JUIgRKrwJPyoRfq6')
MONGODB_URI = f"mongodb+srv://fosburyalpha:{DB_PASSWORD}@fundingarbitrage.w8nnll9.mongodb.net/"
DATABASE_NAME = "FundingArbitrage"

# Encryption Configuration
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'TradingAppSecureKey2024ForFund!')

# Environment Configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# Trading Configuration
MIN_CAPITAL = 10
MAX_LEVERAGE = 20
MIN_LEVERAGE = 0
SOLANA_PRECISION = 0.1  # Arrotondamento size SOLANA

# Rebalance and Safety Configuration
MIN_REBALANCE_THRESHOLD = 5
MAX_REBALANCE_THRESHOLD = 50
DEFAULT_REBALANCE_THRESHOLD = 20

MIN_SAFETY_THRESHOLD = 1
MAX_SAFETY_THRESHOLD = 15
DEFAULT_SAFETY_THRESHOLD = 5

# Bot Status
BOT_STATUS = {
    "READY": "ready",
    "RUNNING": "running", 
    "STOPPED": "stopped",
    "STOP_REQUESTED": "stop_requested",
    "TRANSFER_REQUESTED": "transfer_requested",
    "TRANSFERING": "transfering",
    "READY_TO_RESTART": "ready_to_restart"
}

# Exchange Configuration
SUPPORTED_EXCHANGES = ["bitfinex", "bitmex"]

# Simboli futures perpetual per exchange
EXCHANGE_SYMBOLS = {
    "bitfinex": "tSOLF0:USTF0",  # Futures perpetual SOLANA su Bitfinex
    "bitmex": "SOLUSDT"          # Futures perpetual SOLANA su Bitmex
}

# Moltiplicatori per calcolo size
EXCHANGE_MULTIPLIERS = {
    "bitfinex": 1,      # Size normale in SOL
    "bitmex": 10000     # Contratti BitMEX (10000 = 1 SOL)
}