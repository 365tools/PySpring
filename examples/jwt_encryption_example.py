"""
JWT 加密功能使用示例

演示如何使用 JWT 加密功能
"""
from cryptography.fernet import Fernet
from pyspring.ioc.manager import AppContainerManager
from pyspring.security.authentication.crypto.encryption import JWTEncryption, JWTEncryptionManager


def example_1_basic_encryption():
    """示例 1: 基本的 Fernet 加密/解密"""
    print("\n" + "=" * 60)
    print("示例 1: 基本的 Fernet 加密/解密")
    print("=" * 60)

    # 生成密钥
    key = Fernet.generate_key()
    print(f"生成密钥: {key.decode()}")

    # 创建加密器
    encryption = JWTEncryption(key, algorithm="Fernet")

    # 模拟 JWT Token
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwicm9sZXMiOlsiYWRtaW4iXX0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    print(f"\n原始 JWT Token:")
    print(f"  {jwt_token}")
    print(f"  长度: {len(jwt_token)} 字符")

    # 加密
    encrypted_token = encryption.encrypt(jwt_token)
    print(f"\n加密后的 Token:")
    print(f"  {encrypted_token}")
    print(f"  长度: {len(encrypted_token)} 字符")

    # 解密
    decrypted_token = encryption.decrypt(encrypted_token)
    print(f"\n解密后的 Token:")
    print(f"  {decrypted_token}")

    # 验证
    assert jwt_token == decrypted_token, "加密/解密失败！"
    print(f"\n✅ 加密/解密验证成功！")


def example_2_aes_gcm_encryption():
    """示例 2: AES-GCM 加密"""
    print("\n" + "=" * 60)
    print("示例 2: AES-GCM 加密")
    print("=" * 60)

    # 使用自定义密钥（会被派生为 32 字节）
    custom_key = "my-super-secret-password"
    print(f"自定义密钥: {custom_key}")

    # 创建 AES-GCM 加密器
    encryption = JWTEncryption(custom_key, algorithm="AES-GCM")

    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    print(f"\n原始 JWT Token:")
    print(f"  {jwt_token[:50]}...")

    # 加密
    encrypted_token = encryption.encrypt(jwt_token)
    print(f"\n加密后的 Token:")
    print(f"  {encrypted_token[:50]}...")

    # 解密
    decrypted_token = encryption.decrypt(encrypted_token)
    print(f"\n解密后的 Token:")
    print(f"  {decrypted_token[:50]}...")

    assert jwt_token == decrypted_token, "加密/解密失败！"
    print(f"\n✅ AES-GCM 加密/解密验证成功！")


def example_3_token_detection():
    """示例 3: Token 类型检测"""
    print("\n" + "=" * 60)
    print("示例 3: Token 类型检测")
    print("=" * 60)

    # 标准 JWT Token（三段式，包含两个点）
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    print(f"\nJWT Token: {jwt_token[:50]}...")
    print(f"  是否加密: {JWTEncryption.is_encrypted_token(jwt_token)}")

    # 加密后的 Token（随机字符串）
    encrypted_token = "gAAAAABmX8Y5k3J2h7LmP9qN0oR5tU3vB6cA1dE4fI7jK8lM2nO3pQ"
    print(f"\n加密 Token: {encrypted_token}")
    print(f"  是否加密: {JWTEncryption.is_encrypted_token(encrypted_token)}")


def example_4_encryption_manager():
    """示例 4: 使用加密管理器（单例）"""
    print("\n" + "=" * 60)
    print("示例 4: 使用加密管理器")
    print("=" * 60)
    # 通过 IoC 容器获取加密管理器单例
    try:
        container = AppContainerManager()
        manager = container.get(JWTEncryptionManager)
    except Exception as e:
        print(f"⚠️ 无法获取容器或管理器: {e}")
        # 用于演示的回退
        print("💡 使用默认配置创建临时管理器用于演示")
        from pyspring.core.conf import config
        manager = JWTEncryptionManager(config)

    print(f"\n加密是否启用: {manager.is_enabled()}")

    if not manager.is_enabled():
        print("ℹ️  JWT 加密未启用（在 config/security.yaml 中配置）")
        return

    # 测试加密
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    encrypted = manager.encrypt(jwt_token)
    print(f"\n原始 Token: {jwt_token[:50]}...")
    print(f"加密 Token: {encrypted[:50]}...")

    decrypted = manager.decrypt(encrypted)
    print(f"解密 Token: {decrypted[:50]}...")

    assert jwt_token == decrypted, "加密/解密失败！"
    print(f"\n✅ 加密管理器验证成功！")


def example_5_performance_test():
    """示例 5: 性能测试"""
    print("\n" + "=" * 60)
    print("示例 5: 性能测试")
    print("=" * 60)

    import time

    # 生成密钥
    key = Fernet.generate_key()
    encryption = JWTEncryption(key, algorithm="Fernet")

    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwicm9sZXMiOlsiYWRtaW4iXX0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    # 测试加密性能
    iterations = 1000

    start = time.time()
    for _ in range(iterations):
        encrypted = encryption.encrypt(jwt_token)
    encrypt_time = time.time() - start

    print(f"\n加密性能测试 ({iterations} 次):")
    print(f"  总时间: {encrypt_time:.3f} 秒")
    print(f"  平均每次: {encrypt_time / iterations * 1000:.3f} 毫秒")

    # 测试解密性能
    encrypted_token = encryption.encrypt(jwt_token)

    start = time.time()
    for _ in range(iterations):
        decrypted = encryption.decrypt(encrypted_token)
    decrypt_time = time.time() - start

    print(f"\n解密性能测试 ({iterations} 次):")
    print(f"  总时间: {decrypt_time:.3f} 秒")
    print(f"  平均每次: {decrypt_time / iterations * 1000:.3f} 毫秒")

    total_time = encrypt_time + decrypt_time
    print(f"\n总性能 ({iterations} 次加密+解密):")
    print(f"  总时间: {total_time:.3f} 秒")
    print(f"  平均每次: {total_time / iterations * 1000:.3f} 毫秒")


def example_6_key_generation():
    """示例 6: 密钥生成"""
    print("\n" + "=" * 60)
    print("示例 6: 密钥生成")
    print("=" * 60)

    # 生成 5 个不同的密钥
    print("\n生成 Fernet 密钥（每次都不同）:")
    for i in range(5):
        key = JWTEncryption.generate_fernet_key()
        print(f"  密钥 {i + 1}: {key}")

    print("\n💡 使用方式:")
    print("  1. 选择一个密钥")
    print("  2. 设置环境变量: export JWT_ENCRYPTION_KEY=\"<密钥>\"")
    print("  3. 在 config/security.yaml 中启用加密")


def main():
    """运行所有示例"""
    print("=" * 60)
    print("JWT 加密功能使用示例")
    print("=" * 60)

    try:
        example_1_basic_encryption()
        example_2_aes_gcm_encryption()
        example_3_token_detection()
        example_4_encryption_manager()
        example_5_performance_test()
        example_6_key_generation()

        print("\n" + "=" * 60)
        print("✅ 所有示例运行成功！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
