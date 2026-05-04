"""Encryption utilities for signature data at rest"""
from cryptography.fernet import Fernet
from django.conf import settings
import base64


class SignatureEncryption:
    """Encrypt and decrypt signature data at rest"""
    
    def __init__(self):
        """Initialize cipher with encryption key from settings"""
        encryption_key = getattr(settings, 'SIGNATURE_ENCRYPTION_KEY', None)
        
        if not encryption_key:
            # Generate a key for development (DO NOT use in production)
            encryption_key = Fernet.generate_key()
            
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode('utf-8')
            
        self.cipher = Fernet(encryption_key)
    
    def encrypt_signature_data(self, signature_data):
        """
        Encrypt signature base64 data
        
        Args:
            signature_data: Plain text signature data
            
        Returns:
            Encrypted signature data as string
        """
        if not signature_data:
            return ''
            
        encrypted = self.cipher.encrypt(signature_data.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_signature_data(self, encrypted_data):
        """
        Decrypt signature data
        
        Args:
            encrypted_data: Encrypted signature data
            
        Returns:
            Decrypted signature data as string
        """
        if not encrypted_data:
            return ''
            
        try:
            decoded = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception:
            # If decryption fails, might be unencrypted legacy data
            return encrypted_data
