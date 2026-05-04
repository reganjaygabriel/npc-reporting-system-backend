"""Cryptographic utilities for signature verification"""
import hashlib
import hmac
from datetime import datetime
from django.conf import settings


class SignatureVerifier:
    """Cryptographic signature verification using HMAC-SHA256"""
    
    @staticmethod
    def generate_signature_hash(signature_data, signatory_name, timestamp):
        """
        Generate HMAC-SHA256 hash for signature verification
        
        Args:
            signature_data: Base64 encoded signature data
            signatory_name: Name of the signatory
            timestamp: ISO format timestamp
            
        Returns:
            Hexadecimal hash string
        """
        secret_key = getattr(settings, 'SIGNATURE_SECRET_KEY', 'default-secret-change-in-production')
        message = f"{signature_data}|{signatory_name}|{timestamp}"
        
        return hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_signature(signature_obj):
        """
        Verify signature integrity by comparing hashes
        
        Args:
            signature_obj: ESignature model instance
            
        Returns:
            Boolean indicating if signature is valid
        """
        if not signature_obj.verification_hash:
            return False
            
        computed_hash = SignatureVerifier.generate_signature_hash(
            signature_obj.signature_data or '',
            signature_obj.signatory_name,
            signature_obj.created_at.isoformat()
        )
        
        return hmac.compare_digest(computed_hash, signature_obj.verification_hash)
    
    @staticmethod
    def generate_report_signature_hash(report_date, report_type, signatory_name, signature_id, timestamp):
        """
        Generate hash for report signature verification
        
        Args:
            report_date: Date of the report
            report_type: Type of report (PSR, etc.)
            signatory_name: Name of signatory
            signature_id: ID of the signature used
            timestamp: ISO format timestamp
            
        Returns:
            Hexadecimal hash string
        """
        secret_key = getattr(settings, 'SIGNATURE_SECRET_KEY', 'default-secret-change-in-production')
        message = f"{report_date}|{report_type}|{signatory_name}|{signature_id}|{timestamp}"
        
        return hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
