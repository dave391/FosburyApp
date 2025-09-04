"""
Utility per gestione exchange e problemi comuni
"""
import time
import logging

logger = logging.getLogger(__name__)

class ExchangeUtils:
    """Utility per problemi comuni degli exchange"""
    
    @staticmethod
    def get_bitfinex_nonce():
        """Genera nonce per Bitfinex (timestamp in millisecondi)"""
        return int(time.time() * 1000)
    
    @staticmethod
    def wait_for_nonce_reset(seconds: int = 5):
        """Aspetta per reset del nonce"""
        logger.info(f"Attendendo {seconds} secondi per reset nonce...")
        time.sleep(seconds)
    
    @staticmethod
    def is_nonce_error(error_message: str) -> bool:
        """Verifica se l'errore è relativo al nonce"""
        error_lower = str(error_message).lower()
        nonce_keywords = ['nonce', 'timestamp', 'too small', 'invalid timestamp']
        return any(keyword in error_lower for keyword in nonce_keywords)
    
    @staticmethod
    def is_auth_error(error_message: str) -> bool:
        """Verifica se l'errore è di autenticazione"""
        error_lower = str(error_message).lower()
        auth_keywords = ['invalid key', 'authentication', 'unauthorized', 'forbidden', 'invalid api']
        return any(keyword in error_lower for keyword in auth_keywords)
    
    @staticmethod
    def retry_with_nonce_fix(func, max_retries: int = 3, wait_seconds: int = 2):
        """Riprova una funzione gestendo errori di nonce"""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if ExchangeUtils.is_nonce_error(str(e)) and attempt < max_retries - 1:
                    logger.warning(f"Errore nonce (tentativo {attempt + 1}/{max_retries}): {e}")
                    ExchangeUtils.wait_for_nonce_reset(wait_seconds)
                    continue
                else:
                    raise e
        
        raise Exception(f"Falliti tutti i {max_retries} tentativi")

# Configurazioni specifiche per exchange
EXCHANGE_CONFIGS = {
    'bitfinex': {
        'options': {
            'defaultType': 'swap',
            'adjustForTimeDifference': True,
            'recvWindow': 10000
        },
        'requires_nonce': True,
        'nonce_function': ExchangeUtils.get_bitfinex_nonce
    },
    'bitmex': {
        'options': {
            'defaultType': 'swap',
            'test': False
        },
        'requires_nonce': False,
        'nonce_function': None
    }
}

def get_exchange_config(exchange_name: str) -> dict:
    """Ottiene configurazione per exchange specifico"""
    return EXCHANGE_CONFIGS.get(exchange_name.lower(), {})