"""
PySpring CLI Key Generation
"""
import secrets

try:
    from cryptography.fernet import Fernet

    has_crypto = True
except ImportError:
    has_crypto = False


def generate_jwt_secret() -> str:
    """Generate JWT secret"""
    return secrets.token_urlsafe(32)


def generate_encryption_key() -> str:
    """Generate JWT encryption key"""
    if has_crypto:
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode('utf-8')
    return ""
