"""
Encrypted storage manager for API keys and sensitive data
Uses Fernet symmetric encryption with password-based key derivation
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

logger = logging.getLogger(__name__)


class EncryptedStorage:
    """Manages encrypted storage of API keys and sensitive configuration"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize encrypted storage
        
        Args:
            storage_path: Path to encrypted storage file
        """
        if storage_path is None:
            # Use app data directory
            if os.name == 'nt':  # Windows
                app_data = os.getenv('APPDATA', os.path.expanduser('~'))
                storage_dir = Path(app_data) / 'AIUsageDash'
            else:  # Linux/Mac
                storage_dir = Path.home() / '.ai_usage_dash'
            
            storage_dir.mkdir(parents=True, exist_ok=True)
            storage_path = str(storage_dir / 'encrypted_keys.dat')
        
        self.storage_path = Path(storage_path)
        self.salt_path = self.storage_path.parent / 'salt.dat'
        self.cipher: Optional[Fernet] = None
        self.is_initialized = False
        
    def initialize(self, password: str) -> bool:
        """
        Initialize encryption with master password
        
        Args:
            password: Master password for encryption
            
        Returns:
            True if initialization successful
        """
        try:
            # Generate or load salt
            if self.salt_path.exists():
                with open(self.salt_path, 'rb') as f:
                    salt = f.read()
            else:
                salt = os.urandom(16)
                with open(self.salt_path, 'wb') as f:
                    f.write(salt)
            
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            self.cipher = Fernet(key)
            self.is_initialized = True
            
            logger.info("Encrypted storage initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize encrypted storage: {e}")
            return False
    
    def store_api_keys(self, api_keys: Dict[str, str]) -> bool:
        """
        Store API keys in encrypted format
        
        Args:
            api_keys: Dictionary of provider -> API key
            
        Returns:
            True if storage successful
        """
        if not self.is_initialized or self.cipher is None:
            logger.error("Storage not initialized. Call initialize() first.")
            return False
        
        try:
            # Encrypt the data
            data_json = json.dumps(api_keys)
            encrypted_data = self.cipher.encrypt(data_json.encode())
            
            # Write to file
            with open(self.storage_path, 'wb') as f:
                f.write(encrypted_data)
            
            logger.info(f"Stored {len(api_keys)} API keys")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store API keys: {e}")
            return False
    
    def load_api_keys(self) -> Optional[Dict[str, str]]:
        """
        Load and decrypt API keys
        
        Returns:
            Dictionary of provider -> API key, or None if failed
        """
        if not self.is_initialized or self.cipher is None:
            logger.error("Storage not initialized. Call initialize() first.")
            return None
        
        if not self.storage_path.exists():
            logger.info("No existing API keys found")
            return {}
        
        try:
            # Read encrypted data
            with open(self.storage_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt
            decrypted_data = self.cipher.decrypt(encrypted_data)
            api_keys = json.loads(decrypted_data.decode())
            
            logger.info(f"Loaded {len(api_keys)} API keys")
            return api_keys
            
        except Exception as e:
            logger.error(f"Failed to load API keys: {e}")
            return None
    
    def update_api_key(self, provider: str, api_key: str) -> bool:
        """
        Update a single API key
        
        Args:
            provider: Provider name
            api_key: New API key
            
        Returns:
            True if update successful
        """
        api_keys = self.load_api_keys()
        if api_keys is None:
            api_keys = {}
        
        api_keys[provider] = api_key
        return self.store_api_keys(api_keys)
    
    def delete_api_key(self, provider: str) -> bool:
        """
        Delete a single API key
        
        Args:
            provider: Provider name
            
        Returns:
            True if deletion successful
        """
        api_keys = self.load_api_keys()
        if api_keys is None:
            return False
        
        if provider in api_keys:
            del api_keys[provider]
            return self.store_api_keys(api_keys)
        
        return True
    
    def has_api_key(self, provider: str) -> bool:
        """
        Check if API key exists for provider
        
        Args:
            provider: Provider name
            
        Returns:
            True if key exists
        """
        api_keys = self.load_api_keys()
        return api_keys is not None and provider in api_keys
    
    def list_providers(self) -> list:
        """
        List all providers with stored API keys
        
        Returns:
            List of provider names
        """
        api_keys = self.load_api_keys()
        if api_keys is None:
            return []
        return list(api_keys.keys())
    
    def clear_all(self) -> bool:
        """
        Clear all stored API keys
        
        Returns:
            True if successful
        """
        try:
            if self.storage_path.exists():
                self.storage_path.unlink()
            logger.info("Cleared all API keys")
            return True
        except Exception as e:
            logger.error(f"Failed to clear API keys: {e}")
            return False
