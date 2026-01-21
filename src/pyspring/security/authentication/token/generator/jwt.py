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
from pyspring.security.authentication.contracts.token_generator import ITokenGenerator
from pyspring.security.authentication.infrastructure.crypto.encryption import JWTEncryptionManager
from pyspring.security.authorization.contracts.schema.config import JWTConfig
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

        # 验证JWT密钥是否存在
        if not secret_key or secret_key == 'null' or secret_key == 'your-secret-key-change-in-production':
            error_msg = (
                "[SECURITY CRITICAL] JWT_SECRET_KEY 未配置或使用了不安全的默认值！\n"
                "生产环境必须通过环境变量设置强密钥。\n"
                "生成强密钥: python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
                "设置方式: export JWT_SECRET_KEY='your-generated-key'"
            )
            logger.critical(error_msg)
            raise ValueError(error_msg)

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

    def generate_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        生成 JWT Access Token
        
        Args:
            data: Token 载荷数据
            expires_delta: 过期时间增量（可选）
            
        Returns:
            str: JWT Token 字符串（可能被加密）
        """
        to_encode = data.copy()

        # 生成唯一Token ID (JTI)
        token_id = str(uuid.uuid4())

        # 设置过期时间
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(seconds=self.jwt_config.access_token_expire)

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(UTC),
            "jti": token_id,  # JWT ID - 唯一标识，用于黑名单
            "type": "access"
        })

        # 编码 JWT
        encoded_jwt = jwt.encode(
            to_encode,
            self.jwt_config.secret_key,
            algorithm=self.jwt_config.algorithm
        )

        # 加密 Token（如果启用）
        encrypted_token = self.jwt_encryption.encrypt(encoded_jwt)

        logger.debug(f"[TokenGen][JWT] 生成 Access Token: {data.get('email', 'unknown')}")
        return encrypted_token

    async def generate_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        生成 JWT Refresh Token
        
        Args:
            data: Token 载荷数据
            expires_delta: 过期时间增量（可选）
            
        Returns:
            str: JWT Refresh Token 字符串
        """
        to_encode = data.copy()

        # 生成唯一Token ID (JTI)
        token_id = str(uuid.uuid4())

        # 设置过期时间
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(seconds=self.jwt_config.access_token_expire)

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(UTC),
            "jti": token_id,  # JWT ID - 唯一标识，用于黑名单
            "type": "refresh"
        })

        # 编码 JWT
        encoded_jwt = jwt.encode(
            to_encode,
            self.jwt_config.secret_key,
            algorithm=self.jwt_config.algorithm
        )

        logger.debug(f"[TokenGen][JWT] 生成 Refresh Token: {data.get('email', 'unknown')}")
        return encoded_jwt

    async def decode_token(self, token: str, verify: bool = True) -> Optional[Dict[str, Any]]:
        """
        解析 JWT Token
        
        Args:
            token: JWT Token 字符串
            verify: 是否验证签名和过期时间
            
        Returns:
            Optional[Dict]: Token 载荷，解析失败返回 None
        """
        try:
            # 尝试解密 Token（如果加密了）
            decrypted_token = self.jwt_encryption.decrypt(token)

            # 解码 JWT
            if verify:
                payload = jwt.decode(
                    decrypted_token,
                    self.jwt_config.secret_key,
                    algorithms=[self.jwt_config.algorithm]
                )
            else:
                payload = jwt.decode(
                    decrypted_token,
                    options={"verify_signature": False}
                )

            return payload

        except JWTError as e:
            logger.error(f"[TokenGen][JWT] Token 解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"[TokenGen][JWT] Token 解析异常: {e}")
            return None

    async def parse_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        解析 Token（实现接口方法）
        
        Args:
            token: Token 字符串
            token_type: Token 类型（access/refresh）
            
        Returns:
            Optional[Dict]: Token 载荷，解析失败返回 None
        """
        return await self.decode_token(token)

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
