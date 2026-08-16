"""
PySpring CLI Key Generation
"""
import secrets
from importlib.util import find_spec

# 特性检测：仅检查 cryptography 模块是否可用，避免为检测而导入 Fernet
has_crypto = find_spec("cryptography") is not None


def generate_jwt_secret() -> str:
    """Generate JWT secret"""
    return secrets.token_urlsafe(32)


def generate_encryption_key() -> str:
    """Generate JWT encryption key"""
    if has_crypto:
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode('utf-8')
    return ""
