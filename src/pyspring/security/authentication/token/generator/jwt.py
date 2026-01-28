"""
JWT Token 生成器实现

使用最新的IOC框架，负责生成和解析JWT Token
"""
import uuid
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, Optional

from jose import JWTError, jwt

from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.log.instance import logger
from pyspring.security.authentication.contracts.config import JWTConfig
from pyspring.security.authentication.contracts.token import ITokenGenerator
from pyspring.security.authentication.infrastructure.crypto.encryption import JWTEncryptionManager
from pyspring.security.core.config.loader import SecurityConfigManager


@Component()
@Singleton
class JWTTokenGenerator(ITokenGenerator):
    """
    JWT Token 生成器
    
    职责：
    - 生成 JWT Access Token
    - 生成 JWT Refresh Token
    - 解析 JWT Token
    - 支持 Token 加密（可选）
    
    配置来源：
    - SecurityConfigManager 统一管理配置
    """

    def __init__(self, jwt_encryption: JWTEncryptionManager, config_manager: SecurityConfigManager):
        """
        初始化 JWT Token 生成器
        
        Args:
            jwt_encryption: JWT 加密管理器（通过IOC注入）
            config_manager: 安全配置管理器（通过IOC注入）
        """
        # 加载JWT配置
        jwt_config_dict = config_manager.get_jwt_config()

        # 验证JWT密钥配置（组件自己验证自己需要的配置）
        self._validate_jwt_secret(jwt_config_dict)

        # 将字典配置转换为 JWTConfig 对象（过滤掉额外字段）
        allowed_fields = {'secret_key', 'algorithm', 'access_token_expire', 'refresh_token_expire'}
        filtered_config = {k: v for k, v in jwt_config_dict.items() if k in allowed_fields}
        self.jwt_config = JWTConfig(**filtered_config)
        self.jwt_encryption = jwt_encryption
        logger.info("[TokenGen][JWT] JWT Token 生成器初始化完成")

    def _validate_jwt_secret(self, jwt_config: Dict[str, Any]):
        """验证JWT密钥配置"""
        secret_key = jwt_config.get('secret_key')

        # 检查密钥是否存在或为无效值
        if not secret_key or secret_key == 'null' or secret_key.strip() == '':
            logger.warning(
                "[SECURITY WARNING] JWT_SECRET_KEY 未显式配置，使用框架默认开发密钥！\n"
                "⚠️  仅适用于开发/测试环境\n"
                "⚠️  生产环境必须通过环境变量 JWT_SECRET_KEY 设置强密钥\n"
                "生成强密钥: python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
                "设置方式: export JWT_SECRET_KEY='your-generated-key'"
            )
            # 使用框架提供的开发环境默认密钥（确保配置已加载此默认值）
            # 如果配置系统正确工作，这里不应该出现空值
            return

        # 检查是否使用不安全的默认值
        insecure_defaults = [
            'your-secret-key-change-in-production',
            'pyspring-dev-secret-key-CHANGE-IN-PRODUCTION-32bytes-minimum'
        ]
        if any(default in secret_key for default in insecure_defaults):
            logger.warning(
                "[SECURITY WARNING] 检测到使用开发环境默认密钥！\n"
                "⚠️  仅适用于开发/测试环境\n"
                "⚠️  生产环境必须通过环境变量 JWT_SECRET_KEY 设置强密钥\n"
                "生成强密钥: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        # 验证密钥强度
        if len(secret_key) < 32:
            logger.warning(
                f"[SECURITY WARNING] JWT密钥长度不足！\n"
                f"当前长度: {len(secret_key)} bytes\n"
                f"推荐长度: >= 32 bytes\n"
                f"存在安全风险，建议使用更长的密钥"
            )
        else:
            logger.info(f"[Security] JWT密钥强度验证通过 (长度: {len(secret_key)} bytes)")

    def encode(self, payload: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        编码JWT Token（符合新接口）
        
        Args:
            payload: Token载荷数据
            expires_delta: 过期时间增量（可选）
            
        Returns:
            str: 编码并可能加密的JWT Token
        """
        to_encode = payload.copy()

        # 生成唯一Token ID (JTI)
        token_id = str(uuid.uuid4())

        # 获取token类型（用于日志）
        token_type = payload.get("type", "access")

        # 设置过期时间
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            # 根据token类型使用不同的过期时间
            if token_type == "refresh":
                expire = datetime.now(UTC) + timedelta(seconds=self.jwt_config.refresh_token_expire)
            else:
                expire = datetime.now(UTC) + timedelta(seconds=self.jwt_config.access_token_expire)

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(UTC),
            "jti": token_id,  # JWT ID - 唯一标识，用于黑名单
        })

        # 编码 JWT
        encoded_jwt = jwt.encode(
            to_encode,
            self.jwt_config.secret_key,
            algorithm=self.jwt_config.algorithm
        )

        # 加密 Token（如果启用）
        encrypted_token = self.jwt_encryption.encrypt(encoded_jwt)

        logger.debug(f"[TokenGen][JWT] 编码 {token_type} Token")
        return encrypted_token

    def decode(self, token: str) -> Optional[Dict[str, Any]]:
        """
        解码JWT Token（符合新接口）
        
        Args:
            token: JWT Token字符串
            
        Returns:
            Optional[Dict]: 解码后的载荷，失败返回None
        """
        try:
            # 尝试解密 Token（如果加密了）
            decrypted_token = self.jwt_encryption.decrypt(token)

            # 解码 JWT
            payload = jwt.decode(
                decrypted_token,
                self.jwt_config.secret_key,
                algorithms=[self.jwt_config.algorithm]
            )

            return payload

        except JWTError as e:
            # 记录token信息便于调试（不记录完整token避免泄露）
            token_preview = token[:20] + '...' if len(token) > 20 else token
            logger.error(f"[TokenGen][JWT] Token 解码失败: {e} | Token长度: {len(token)} | 前20字符: {token_preview}")
            return None
        except Exception as e:
            logger.error(f"[TokenGen][JWT] Token 解码异常: {e}")
            return None

    def get_token_type(self) -> str:
        """返回Token类型标识"""
        return "JWT"

    def get_access_token_expire(self) -> int:
        """
        获取访问令牌过期时间
        
        Returns:
            int: 过期时间（秒）
        """
        return self.jwt_config.access_token_expire

    def get_refresh_token_expire(self) -> int:
        """
        获取刷新令牌过期时间
        
        Returns:
            int: 过期时间（秒）
        """
        return self.jwt_config.refresh_token_expire
