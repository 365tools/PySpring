"""
PySpring CLI Key Generation
"""
import secrets

try:
    from cryptography.fernet import Fernet

    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def generate_jwt_secret() -> str:
    """Generate JWT secret"""
    return secrets.token_urlsafe(32)


def generate_encryption_key() -> str:
    """Generate JWT encryption key"""
    if HAS_CRYPTO:
        return Fernet.generate_key().decode('utf-8')
    return ""
