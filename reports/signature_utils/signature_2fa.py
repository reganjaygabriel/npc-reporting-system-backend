"""Two-factor authentication for signature operations"""
import pyotp
import secrets
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings


class Signature2FA:
    """Two-factor authentication for signature operations"""
    
    @staticmethod
    def generate_otp():
        """
        Generate time-based OTP
        
        Returns:
            Tuple of (otp_code, secret)
        """
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret, interval=300)  # 5 minute validity
        otp_code = totp.now()
        
        return otp_code, secret
    
    @staticmethod
    def generate_simple_otp():
        """
        Generate simple 6-digit OTP (fallback if pyotp not available)
        
        Returns:
            Tuple of (otp_code, secret)
        """
        otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        secret = secrets.token_urlsafe(32)
        
        return otp_code, secret
    
    @staticmethod
    def send_otp_email(user, otp_code, signatory_name):
        """
        Send OTP via email
        
        Args:
            user: User object
            otp_code: OTP code to send
            signatory_name: Name of signatory for context
        """
        try:
            subject = 'E-Signature Verification Code - NPC Reporting System'
            message = f"""
Hello {user.username},

You are attempting to apply an e-signature for: {signatory_name}

Your verification code is: {otp_code}

This code is valid for 5 minutes.

If you did not request this, please contact your administrator immediately.

Best regards,
NPC Reporting System
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@npc-reporting.com',
                [user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Failed to send OTP email: {e}")
            return False
    
    @staticmethod
    def verify_otp(secret, user_input):
        """
        Verify OTP code
        
        Args:
            secret: Secret key used to generate OTP
            user_input: User's input code
            
        Returns:
            Boolean indicating if OTP is valid
        """
        try:
            totp = pyotp.TOTP(secret, interval=300)
            return totp.verify(user_input, valid_window=1)
        except Exception:
            # Fallback to simple comparison for simple OTP
            return False
    
    @staticmethod
    def verify_simple_otp(stored_code, user_input, created_at, validity_minutes=5):
        """
        Verify simple OTP code with time check
        
        Args:
            stored_code: The stored OTP code
            user_input: User's input code
            created_at: When the OTP was created
            validity_minutes: How long the OTP is valid
            
        Returns:
            Boolean indicating if OTP is valid
        """
        # Check if OTP has expired
        if timezone.now() > created_at + timedelta(minutes=validity_minutes):
            return False
            
        # Compare codes
        return secrets.compare_digest(stored_code, user_input)
