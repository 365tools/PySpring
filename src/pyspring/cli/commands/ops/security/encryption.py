"""
JWT Encryption Key Generation Tool

Used to generate secure Fernet encryption keys
"""
from cryptography.fernet import Fernet

from pyspring.cli.core.ui import (
    print_title, print_success, print_warning, print_info
)


def generate_encryption_key(args):
    """Generate Fernet encryption key"""
    key = Fernet.generate_key()
    key_str = key.decode('utf-8')

    print_title("JWT Encryption Key Generated Successfully")
    print_success(f"Key: {key_str}")

    print_info("\nPlease save this key to your environment variables:")
    print("-" * 60)
    print(f"# Linux/Mac")
    print(f'export JWT_ENCRYPTION_KEY="{key_str}"')
    print()
    print(f"# Windows PowerShell")
    print(f'$env:JWT_ENCRYPTION_KEY="{key_str}"')
    print()
    print(f"# Windows CMD")
    print(f'set JWT_ENCRYPTION_KEY={key_str}')
    print("-" * 60)

    print_title("Important Notices")
    print_warning("1. This key is used for encryption and decryption of JWT Tokens")
    print_warning("2. Keep this key safe in production, do NOT commit to version control")
    print_warning("3. Key leakage will allow all encrypted tokens to be cracked")
    print_warning("4. Changing the key will invalidate all old tokens")
