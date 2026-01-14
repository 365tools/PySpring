"""
JWT 加密密钥生成工具

用于生成安全的 Fernet 加密密钥
"""
from cryptography.fernet import Fernet


def generate_encryption_key(args):
    """生成 Fernet 加密密钥"""
    key = Fernet.generate_key()
    key_str = key.decode('utf-8')

    print("=" * 60)
    print("🔐 JWT 加密密钥生成成功")
    print("=" * 60)
    print(f"\n密钥: {key_str}\n")
    print("请将此密钥保存到环境变量中：")
    print("-" * 60)
    print(f"# Linux/Mac")
    print(f"export JWT_ENCRYPTION_KEY=\"{key_str}\"")
    print()
    print(f"# Windows PowerShell")
    print(f"$env:JWT_ENCRYPTION_KEY=\"{key_str}\"")
    print()
    print(f"# Windows CMD")
    print(f"set JWT_ENCRYPTION_KEY={key_str}")
    print("-" * 60)
    print("\n⚠️  注意事项：")
    print("1. 此密钥用于 JWT Token 的加密和解密")
    print("2. 生产环境必须妥善保管，不要提交到代码仓库")
    print("3. 密钥泄露会导致所有加密 Token 被破解")
    print("4. 更换密钥会使所有旧 Token 失效")
    print("=" * 60)
