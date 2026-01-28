"""
JWT 请求认证提供者
基于 JWT Token 的请求认证实现

验证请求中的 JWT Token，提取用户身份信息
"""
from typing import Optional

from fastapi import Request

from pyspring.log.instance import logger
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
from pyspring.security.authentication.contracts.request_auth import (
    IRequestAuthenticationProvider,
    RequestAuthenticationResult
)
from pyspring.security.authentication.contracts.token import ITokenService


class JWTRequestAuthenticationProvider(IRequestAuthenticationProvider):
    """
    JWT 请求认证提供者
    
    【设计说明】
    - 继承接口：IRequestAuthenticationProvider
    - 职责：从 HTTP 请求中提取并验证 JWT Token
    - Token 来源：Header、Cookie、Query Parameter（可配置优先级）
    - 验证逻辑：委托给 TokenManagerService
    """

    def __init__(self, name: str, config: dict, token_manager: ITokenService,
                 security_config: SecurityEntityConfiguration):
        """
        初始化 JWT 认证提供者
        
        Args:
            name: 提供者名称
            config: 提供者配置
            token_manager: Token 管理服务
            security_config: 安全配置（用于获取identifier_fields）
        """
        super().__init__(name, config)
        self.token_manager = token_manager
        self.security_config = security_config

        # 从配置读取 token 来源优先级
        self.token_sources = self.get_config("token_sources", ["header", "cookie", "query"])
        self.token_prefix = self.get_config("token_prefix", "Bearer")

        logger.info(f"[Success] JWTAuthProvider 初始化完成 - 来源: {self.token_sources}")

    async def authenticate(self, request: Request) -> RequestAuthenticationResult:
        """
        执行请求认证逻辑 (实现接口方法)
        
        【认证流程】
        1. 提取 Token：从 Header/Cookie/Query 提取
        2. 验证 Token：委托给 TokenManagerService
        3. 返回结果：包含用户身份信息
        
        Args:
            request: FastAPI Request 对象
            
        Returns:
            RequestAuthenticationResult: 认证结果
        """
        token = await self.extract_credentials(request)
        if not token:
            return RequestAuthenticationResult(success=False, error_message="Token not found")

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
                logger.debug(f"[Auth] 从 {source} 提取到 Token")
                return token

        return None

    async def validate_credentials(self, credentials: str) -> RequestAuthenticationResult:
        """
        验证 JWT Token
        
        Args:
            credentials: JWT Token 字符串
            
        Returns:
            RequestAuthenticationResult: 认证结果
        """
        try:
            # 验证 Token（委托给 TokenManagerService）
            payload = await self.token_manager.verify_token(credentials)

            if payload is None:
                return RequestAuthenticationResult(
                    success=False,
                    error_message="Token 无效或已过期",
                    provider_name=self.name
                )

            # 提取用户信息
            user_id = payload.get("sub")
            roles = payload.get("roles", [])

            # 动态提取 user_info（包含所有 identifier_fields）
            user_info = {}
            display_name = None

            # 优先使用配置的展示字段
            if self.security_config.display_identifier_field:
                display_name = payload.get(self.security_config.display_identifier_field)

            # 遍历所有identifier_fields
            for field_name in self.security_config.identifier_fields:
                field_value = payload.get(field_name)
                if field_value is not None:
                    user_info[field_name] = field_value
                    # 如果未配置展示字段，使用第一个非空identifier
                    if display_name is None:
                        display_name = field_value

            # 如果没有任何identifier，降级使用user_id
            if not display_name:
                display_name = user_id

            return RequestAuthenticationResult(
                success=True,
                user_id=user_id,
                display_name=display_name,  # 展示用名称
                roles=roles,
                user_info=user_info,  # 动态用户信息
                extra_data=payload,
                provider_name=self.name
            )

        except Exception as e:
            logger.error(f"[Error] JWT 验证失败: {e}")
            return RequestAuthenticationResult(
                success=False,
                error_message=f"Token 验证失败: {str(e)}",
                provider_name=self.name
            )
