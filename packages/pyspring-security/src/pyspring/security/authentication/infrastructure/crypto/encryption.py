"""
JWT 加密工具
提供 JWT Token 的加密和解密功能，防止 Token 被轻易解析
"""
import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.ioc.interfaces.core import IManaged
from pyspring.core.log.instance import logger
from pyspring.security.core.config.loader import SecurityConfigManager


class JWTEncryption:
    """
    JWT 加密工具类
    
    支持两种加密算法：
    1. Fernet (推荐): AES-128-CBC + HMAC-SHA256
       - 简单易用，自动处理 IV 和认证
       - 密钥固定 32 字节（base64 编码）
       
    2. AES-GCM (高级): AES-256-GCM
       - 更强的加密（256位密钥）
       - 需要手动管理 nonce
    
    工作流程：
    - 加密：JWT (签名后) → 加密 → Base64 编码 → 返回密文
    - 解密：接收密文 → Base64 解码 → 解密 → 返回 JWT
    """

    def __init__(self, encryption_key: (str) | None = None, algorithm: str = "Fernet"):
        """
        初始化加密工具
        
        Args:
            encryption_key: 加密密钥（base64编码字符串或原始字节）
            algorithm: 加密算法（Fernet 或 AES-GCM）
        """
        self.algorithm = algorithm
        self.encryption_key = encryption_key
        # 声明实例变量（延迟初始化，类型为可空）
        self.fernet: Fernet | None = None
        self.aes_gcm: AESGCM | None = None

        # 初始化加密器
        if algorithm == "Fernet":
            self._init_fernet()
        elif algorithm == "AES-GCM":
            self._init_aes_gcm()
        else:
            raise ValueError(f"不支持的加密算法: {algorithm}")

    def _init_fernet(self):
        """初始化 Fernet 加密器"""
        if not self.encryption_key:
            raise ValueError("Fernet 加密需要提供 encryption_key")

        try:
            # 如果是字符串，转换为字节
            if isinstance(self.encryption_key, str):
                key_bytes = self.encryption_key.encode('utf-8')
            else:
                key_bytes = self.encryption_key

            # 创建 Fernet 实例
            self.fernet = Fernet(key_bytes)
            logger.info("[Security] Fernet 加密器初始化成功")

        except Exception as e:
            logger.error(f"[Error] Fernet 加密器初始化失败: {e}")
            raise ValueError(f"无效的 Fernet 密钥: {e}")

    def _init_aes_gcm(self):
        """初始化 AES-GCM 加密器"""
        if not self.encryption_key:
            raise ValueError("AES-GCM 加密需要提供 encryption_key")

        try:
            # 如果密钥不是 32 字节，使用 PBKDF2 派生
            if isinstance(self.encryption_key, str):
                key_bytes = self.encryption_key.encode('utf-8')
            else:
                key_bytes = self.encryption_key

            if len(key_bytes) != 32:
                # 使用 PBKDF2 派生 32 字节密钥
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'pyspring_jwt_salt',  # 固定 salt（生产环境应使用配置）
                    iterations=100000,
                )
                key_bytes = kdf.derive(key_bytes)

            self.aes_gcm = AESGCM(key_bytes)
            logger.info("[Security] AES-GCM 加密器初始化成功")

        except Exception as e:
            logger.error(f"[Error] AES-GCM 加密器初始化失败: {e}")
            raise ValueError(f"无效的 AES-GCM 密钥: {e}")

    def encrypt(self, jwt_token: str) -> str:
        """
        加密 JWT Token
        
        Args:
            jwt_token: 原始 JWT Token 字符串
            
        Returns:
            加密后的 Token（base64 编码）
        """
        try:
            if self.algorithm == "Fernet":
                return self._encrypt_fernet(jwt_token)
            elif self.algorithm == "AES-GCM":
                return self._encrypt_aes_gcm(jwt_token)
            raise ValueError(f"不支持的加密算法: {self.algorithm}")
        except Exception as e:
            logger.error(f"[Error] JWT 加密失败: {e}")
            raise

    def decrypt(self, encrypted_token: str) -> str:
        """
        解密 JWT Token
        
        Args:
            encrypted_token: 加密的 Token
            
        Returns:
            原始 JWT Token 字符串
        """
        try:
            if self.algorithm == "Fernet":
                return self._decrypt_fernet(encrypted_token)
            elif self.algorithm == "AES-GCM":
                return self._decrypt_aes_gcm(encrypted_token)
            raise ValueError(f"不支持的加密算法: {self.algorithm}")
        except Exception as e:
            logger.error(f"[Error] JWT 解密失败: {e}")
            raise

    def _encrypt_fernet(self, jwt_token: str) -> str:
        """使用 Fernet 加密"""
        token_bytes = jwt_token.encode('utf-8')
        assert self.fernet is not None, "Fernet 加密器未初始化"
        encrypted_bytes = self.fernet.encrypt(token_bytes)
        # Fernet 输出已经是 base64 编码的，直接返回
        return encrypted_bytes.decode('utf-8')

    def _decrypt_fernet(self, encrypted_token: str) -> str:
        """使用 Fernet 解密"""
        try:
            encrypted_bytes = encrypted_token.encode('utf-8')
            assert self.fernet is not None, "Fernet 加密器未初始化"
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            raise ValueError("Token 解密失败：无效的加密 Token 或密钥不匹配")

    def _encrypt_aes_gcm(self, jwt_token: str) -> str:
        """使用 AES-GCM 加密"""
        # 生成随机 nonce（12 字节）
        nonce = os.urandom(12)

        # 加密
        token_bytes = jwt_token.encode('utf-8')
        assert self.aes_gcm is not None, "AES-GCM 加密器未初始化"
        ciphertext = self.aes_gcm.encrypt(nonce, token_bytes, None)

        # 组合 nonce + ciphertext，然后 base64 编码
        combined = nonce + ciphertext
        return base64.urlsafe_b64encode(combined).decode('utf-8')

    def _decrypt_aes_gcm(self, encrypted_token: str) -> str:
        """使用 AES-GCM 解密"""
        try:
            # Base64 解码
            combined = base64.urlsafe_b64decode(encrypted_token.encode('utf-8'))

            # 分离 nonce 和 ciphertext
            nonce = combined[:12]
            ciphertext = combined[12:]

            # 解密
            assert self.aes_gcm is not None, "AES-GCM 加密器未初始化"
            decrypted_bytes = self.aes_gcm.decrypt(nonce, ciphertext, None)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Token 解密失败：{e}")

    @staticmethod
    def generate_fernet_key() -> str:
        """
        生成新的 Fernet 密钥
        
        Returns:
            Base64 编码的 32 字节密钥
        """
        key = Fernet.generate_key()
        return key.decode('utf-8')

    @staticmethod
    def is_encrypted_token(token: str) -> bool:
        """
        简单判断 Token 是否可能是加密的
        
        JWT Token 格式：header.payload.signature（包含两个点）
        加密 Token：随机字符串（Fernet）或 base64（无点）
        
        Args:
            token: Token 字符串
            
        Returns:
            True 如果看起来像加密 Token
        """
        # JWT 至少有两个点
        jwt_dot_count = token.count('.')

        # 如果没有点或只有一个点，可能是加密的
        return jwt_dot_count < 2


@Component
@Singleton
class JWTEncryptionManager(IManaged):
    """
    JWT 加密管理器（由IOC容器管理单例）
    
    根据配置自动加载加密设置
    """

    _encryption: (JWTEncryption) | None = None
    _enabled: bool = False

    def __init__(self, config_manager: SecurityConfigManager):
        """
        初始化JWT加密管理器
        
        Args:
            config_manager: 安全配置管理器（通过IOC注入）
        """
        self._config_manager = config_manager
        if self._encryption is None:
            self._load_config(config_manager)

    def _load_config(self, config_manager: SecurityConfigManager):
        """从配置文件加载加密设置"""
        encryption_config = config_manager.get("authentication.jwt.encryption", {})

        # 是否启用加密
        self._enabled = encryption_config.get("enabled", False)

        if not self._enabled:
            logger.info("[Unlock] JWT 加密未启用")
            return

        # 获取加密密钥（优先使用环境变量）
        encryption_key = os.getenv("JWT_ENCRYPTION_KEY") or encryption_config.get("encryption_key")

        if not encryption_key:
            logger.warning("[Warning] JWT 加密已启用，但未提供加密密钥，自动生成临时密钥")
            encryption_key = JWTEncryption.generate_fernet_key()
            logger.warning(f"[Warning] 临时密钥：{encryption_key}")
            logger.warning("[Warning] 生产环境请设置环境变量 JWT_ENCRYPTION_KEY")

        # 获取加密算法
        algorithm = encryption_config.get("algorithm", "Fernet")

        try:
            # 创建加密器
            self._encryption = JWTEncryption(encryption_key, algorithm)
            logger.info(f"[Security] JWT 加密已启用 - 算法: {algorithm}")
        except Exception as e:
            logger.error(f"[Error] JWT 加密器初始化失败: {e}")
            self._enabled = False

    def is_enabled(self) -> bool:
        """检查是否启用加密"""
        return self._enabled

    def encrypt(self, jwt_token: str) -> str:
        """
        加密 JWT Token（如果启用）
        
        Args:
            jwt_token: 原始 JWT Token
            
        Returns:
            加密后的 Token（如果启用加密），否则返回原始 Token
        """
        if not self._enabled or not self._encryption:
            return jwt_token

        return self._encryption.encrypt(jwt_token)

    def decrypt(self, token: str) -> str:
        """
        解密 Token（如果需要）
        
        Args:
            token: 可能加密的 Token
            
        Returns:
            原始 JWT Token
        """
        if not self._enabled or not self._encryption:
            return token

        # 判断是否是加密 Token
        if JWTEncryption.is_encrypted_token(token):
            return self._encryption.decrypt(token)

        # 直接返回未加密的 Token
        return token

    def reload(self):
        """重新加载配置"""
        self._encryption = None
        self._enabled = False
        self._load_config(self._config_manager)

# JWTEncryptionManager 现在由 IoC 容器管理，通过容器获取实例
# 示例: container.get(JWTEncryptionManager)
