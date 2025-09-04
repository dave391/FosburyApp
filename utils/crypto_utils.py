"""
Utility per crittografia e sicurezza
"""
import bcrypt
from cryptography.fernet import Fernet
import base64
import hashlib
from config.settings import ENCRYPTION_KEY

class CryptoUtils:
    """Utility per operazioni di crittografia"""
    
    def __init__(self):
        # Genera una chiave Fernet da una stringa fissa
        key = hashlib.sha256(ENCRYPTION_KEY.encode()).digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(key))
    
    def hash_password(self, password: str) -> str:
        """Hash della password con bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verifica password contro hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Crittografa API key"""
        if not api_key:
            return ""
        encrypted = self.fernet.encrypt(api_key.encode())
        return encrypted.decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrittografa API key"""
        if not encrypted_key:
            return ""
        try:
            decrypted = self.fernet.decrypt(encrypted_key.encode())
            return decrypted.decode()
        except Exception as e:
            print(f"Errore decrittografia: {e}")
            return ""

# Istanza globale
crypto_utils = CryptoUtils()