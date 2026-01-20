"""
JWT 认证提供者
基于 JWT Token 的认证实现
"""
from typing import Optional

from fastapi import Request

from pyspring.log.instance import logger
from .base import BaseAuthenticationProvider, AuthenticationResult
from ...services.flow.token import DefaultTokenManagerService


class JWTAuthenticationProvider(BaseAuthenticationProvider):
    """JWT Token 认证提供者"""

    def __init__(self, name: str, config: dict, token_manager: DefaultTokenManagerService):
        """
        初始化 JWT 认证提供者
        
        Args:
            name: 提供者名称
            config: 提供者配置
            token_manager: Token 管理服务
        """
        super().__init__(name, config)
        self.token_manager = token_manager

        # 从配置读取 token 来源优先级
        self.token_sources = self.get_config("token_sources", ["header", "cookie", "query"])
        self.token_prefix = self.get_config("token_prefix", "Bearer")

        logger.info(f"✅ JWTAuthProvider 初始化完成 - 来源: {self.token_sources}")

    async def authenticate(self, request: Request) -> AuthenticationResult:
        """
        执行认证逻辑 (实现基类抽象方法)
        
        Args:
            request: FastAPI Request 对象
            
        Returns:
            AuthenticationResult: 认证结果
        """
        token = await self.extract_credentials(request)
        if not token:
            return AuthenticationResult(success=False, error_message="Token not found")

        return await self.validate_credentials(token)

    async def extract_credentials(self, request: Request) -> Optional[str]:
        """
        从请求中提取 JWT Token
        
        按照配置的优先级顺序提取：
        1. header: Authorization: Bearer <token>
        2. cookie: access_token=<token>
        3. query: ?token=<token>
        
        Args:
            request: FastAPI Request 对象
            
        Returns:
            Optional[str]: JWT Token 字符串，未找到返回 None
        """
        for source in self.token_sources:
            token = None

            if source == "header":
                # 从 Authorization Header 提取
                authorization = request.headers.get("Authorization")
                if authorization:
                    parts = authorization.split()
                    if len(parts) == 2 and parts[0] == self.token_prefix:
                        token = parts[1]

            elif source == "cookie":
                # 从 Cookie 提取
                token = request.cookies.get("access_token")

            elif source == "query":
                # 从 URL 参数提取
                token = request.query_params.get("token")

            if token:
                logger.debug(f"🔑 从 {source} 提取到 Token")
                return token

        return None

    async def validate_credentials(self, credentials: str) -> AuthenticationResult:
        """
        验证 JWT Token
        
        Args:
            credentials: JWT Token 字符串
            
        Returns:
            AuthenticationResult: 认证结果
        """
        try:
            # 验证 Token（调用原有的 TokenManagerService）
            payload = await self.token_manager.verify_token(credentials)

            if payload is None:
                return AuthenticationResult(
                    success=False,
                    error_message="Token 无效或已过期",
                    provider_name=self.name
                )

            # 提取用户信息
            user_id = payload.get("sub")
            username = payload.get("email")
            roles = payload.get("roles", [])

            return AuthenticationResult(
                success=True,
                user_id=user_id,
                username=username,
                roles=roles,
                extra_data=payload,
                provider_name=self.name
            )

        except Exception as e:
            logger.error(f"❌ JWT 验证失败: {e}")
            return AuthenticationResult(
                success=False,
                error_message=f"Token 验证失败: {str(e)}",
                provider_name=self.name
            )
