"""
全局认证拦截中间件

基于认证提供者链（Chain of Responsibility Pattern）
统一处理所有 API 请求的认证逻辑，类似 Spring Boot 的 AOP
"""

from typing import Any, Callable

from fastapi import HTTPException, Request, Response, status
from pyspring.core.ioc.context import ApplicationContext
from pyspring.core.log.instance import logger
from pyspring.security.authentication.contracts.request_auth import (
    RequestAuthenticationResult,
)
from pyspring.security.authentication.contracts.user import IUserProvider
from pyspring.security.authentication.infrastructure.chain import AuthenticationChain
from pyspring.security.authentication.infrastructure.context import AuthContext
from pyspring.security.authorization.contracts.permission import IPermissionService
from pyspring.security.authorization.contracts.rule import IPathPermissionProvider
from pyspring.security.authorization.web.middleware.role import RoleCheckMiddleware
from pyspring.security.core.config.loader import SecurityConfigManager
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    全局认证拦截中间件

    架构特性：
    1. 基于认证提供者链（Chain of Responsibility）
    2. 配置驱动，支持多种认证方式（JWT、API Key、OAuth2等）
    3. 白名单配置化（精确匹配、前缀匹配、正则匹配）
    4. 灵活的认证提供者机制
    5. 统一的认证结果和错误处理

    工作流程：
    1. 检查路径是否在白名单 -> 直接放行
    2. 执行认证提供者链（按优先级）
    3. 验证用户角色权限（可选）
    4. 将用户信息注入到 request.state

    类似 Spring Boot 的拦截器/过滤器
    """

    def __init__(self, app, enable_role_check: (bool) | None = None):
        """
        初始化认证中间件

        Args:
            app: FastAPI应用实例
            enable_role_check: 是否启用角色验证（None 时从配置读取）
        """
        super().__init__(app)
        self.enable_role_check: bool = bool(enable_role_check) if enable_role_check is not None else False
        self.enable_role_check_initial_setting = enable_role_check

        self._config_manager: (SecurityConfigManager) | None = None
        self._auth_chain: (AuthenticationChain) | None = None
        self._role_middleware: (RoleCheckMiddleware) | None = None
        self._initialization_attempted = False

    def _ensure_initialized(self):
        """懒加载初始化依赖"""
        if self._initialization_attempted:
            return

        try:
            container = ApplicationContext.get_instance()

            if self._config_manager is None:
                self._config_manager = container.get_by_type(SecurityConfigManager)

            if self.enable_role_check_initial_setting is None:
                self.enable_role_check = (
                    self._config_manager.is_authorization_enabled()
                    if self._config_manager
                    else False
                    if self._config_manager
                    else False
                )
            else:
                self.enable_role_check = self.enable_role_check_initial_setting

            if self._auth_chain is None:
                self._auth_chain = container.get_by_type(AuthenticationChain)

            if self._role_middleware is None:
                try:
                    permission_service = container.get_by_type(IPermissionService)
                    path_provider = container.get_by_type(IPathPermissionProvider)
                    self._role_middleware = RoleCheckMiddleware(
                        permission_service=permission_service,
                        path_provider=path_provider,
                        enable_role_check=self.enable_role_check,
                    )
                except Exception as e:
                    logger.warning(f"[Warning] 初始化 RoleCheckMiddleware 失败: {e} | 将禁用角色检查")
                    self.enable_role_check = False

            self._initialization_attempted = True
        except Exception as e:
            logger.error(f"[Error] AuthenticationMiddleware 初始化失败: {e}")
            raise e

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        """
        拦截请求进行认证
        """
        self._ensure_initialized()

        try:
            if self._auth_chain and self._auth_chain.is_public_path(request.url.path):
                return await call_next(request)

            auth_result = (
                await self._auth_chain.authenticate(request)
                if self._auth_chain
                else RequestAuthenticationResult(success=False, error_message="Auth chain not initialized")
            )

            user = None
            if auth_result.success and auth_result.user_id:
                try:
                    user_provider = ApplicationContext.get_instance().get_by_type(IUserProvider)
                    user = await user_provider.get_user_by_id(auth_result.user_id)
                except Exception as e:
                    logger.warning(f"[Warning] 加载用户失败: {e}")

            if user:
                request.state.user = user
                AuthContext.set_current_user(user)

                try:
                    from pyspring.security.authorization.contracts.role import (
                        IRoleProvider,
                    )

                    role_provider = ApplicationContext.get_instance().get_by_type(IRoleProvider)
                    user_roles = await role_provider.get_user_roles(user.user_id)

                    user_permissions = set()
                    for role in user_roles:
                        role_perms = await role_provider.get_role_permissions(role)
                        user_permissions.update(role_perms)

                    request.state.user_permissions = list(user_permissions)
                    request.state.user_roles = user_roles
                except Exception as e:
                    logger.warning(f"[Warning] 加载用户权限和角色失败: {e}")
                    request.state.user_permissions = []
                    request.state.user_roles = []
            elif auth_result.error_message:
                logger.warning(f"[Warning] 认证失败: {auth_result.error_message}")
                return self.create_error_response(
                    status.HTTP_401_UNAUTHORIZED, "Authentication Failed", str(auth_result.error_message)
                )
            else:
                logger.warning(f"[Warning] 无效的认证请求: {request.url.path}")
                return self.create_error_response(
                    status.HTTP_401_UNAUTHORIZED,
                    "Authentication Required",
                    "No valid authentication credentials provided",
                )

            if self.enable_role_check and self._role_middleware:
                try:
                    result = await self._role_middleware.auth(request.url.path, request)
                    if isinstance(result, JSONResponse):
                        return result
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"[Error] Role check failed: {e}")
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission check failed")

            response = await call_next(request)
            return response

        except Exception as exc:
            logger.error(f"[Error] 认证中间件内部错误: {exc}", exc_info=True)
            return self.create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR, "Authentication Service Error", str(exc)
            )

    @staticmethod
    def create_error_response(status_code: int, message: str, detail: (str) | None = None) -> JSONResponse:
        """
        创建统一的认证错误响应

        Args:
            status_code: HTTP状态码
            message: 错误消息
            detail: 详细信息（可选）

        Returns:
            JSON响应
        """
        response_data = {"code": status_code, "message": message, "data": None}

        if detail:
            response_data["detail"] = detail

        return JSONResponse(status_code=status_code, content=response_data)
