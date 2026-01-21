"""
from pyspring.ioc.manager import AppContainerManager
from pyspring.security.authentication.services.flow.manager import DefaultUserManagerService
from pyspring.security.authentication.core.chain import AuthenticationChain

全局认证拦截中间件（重构版）

基于认证提供者链（Chain of Responsibility Pattern）
统一处理所有API请求的认证逻辑，类似Spring Boot的AOP
"""
from typing import Callable, Optional

from fastapi import Request, Response, status
from pyspring.ioc.manager import AppContainerManager
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from pyspring.log.instance import logger
from pyspring.security.authentication.core.chain import AuthenticationChain
from pyspring.security.authentication.core.context import AuthContext
from pyspring.security.authorization.contracts.permission import IPermissionService
from pyspring.security.authorization.contracts.rule import IPathPermissionProvider
from pyspring.security.authorization.web.middleware.role import RoleCheckMiddleware
from pyspring.security.core.config.loader import SecurityConfigManager


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    全局认证拦截中间件（重构版）
    
    【新架构特性】
    1. 基于认证提供者链（Chain of Responsibility）
    2. 配置驱动，支持多种认证方式（JWT、API Key、OAuth2等）
    3. 白名单配置化（精确匹配、前缀匹配、正则匹配）
    4. 可扩展的认证提供者机制
    5. 统一的认证结果和错误处理
    
    【工作流程】
    1. 检查路径是否在白名单 -> 放行
    2. 执行认证提供者链（按优先级）
    3. 验证用户角色权限（可选）
    4. 将用户信息注入到 request.state
    
    类似Spring Boot的拦截器/过滤器
    """

    def __init__(self, app, enable_role_check: Optional[bool] = None):
        """
        初始化认证中间件
        
        Args:
            app: FastAPI应用实例
            enable_role_check: 是否启用角色验证（None则从配置读取）
        """
        super().__init__(app)
        self.enable_role_check_initial_setting = enable_role_check

        # Lazy loading placeholders
        self._config_manager = None
        self._auth_chain = None
        self._role_middleware = None
        self._initialization_attempted = False

    def _ensure_initialized(self):
        """懒加载初始化依赖"""
        if self._initialization_attempted:
            return

        try:
            container = AppContainerManager()

            # 1. Config
            if self._config_manager is None:
                self._config_manager = container.get(SecurityConfigManager)

            # 2. Determine role check setting
            if self.enable_role_check_initial_setting is None:
                self.enable_role_check = self._config_manager.is_authorization_enabled()
            else:
                self.enable_role_check = self.enable_role_check_initial_setting

            # 3. Auth Chain
            if self._auth_chain is None:
                self._auth_chain = container.get(AuthenticationChain)

            # 4. Role Middleware
            if self._role_middleware is None:
                try:
                    permission_service = container.get(IPermissionService)
                    path_provider = container.get(IPathPermissionProvider)
                    self._role_middleware = RoleCheckMiddleware(
                        permission_service=permission_service,
                        path_provider=path_provider,
                        enable_role_check=self.enable_role_check
                    )
                except Exception as e:
                    logger.warning(f"⚠️ 初始化 RoleCheckMiddleware 失败: {e} | 将禁用角色检查")
                    self.enable_role_check = False

            self._initialization_attempted = True
        except Exception as e:
            # Don't crash on init failure during dispatch, log and retry next time or fail request gracefully
            logger.error(f"❌ AuthenticationMiddleware lazy init failed: {e}")
            raise e

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        拦截请求进行认证
        """
        self._ensure_initialized()

        try:
            # 1. 白名单检查 (委托给 AuthChain)
            if await self._auth_chain.should_skip(request):
                # logger.debug(f"⏩ 跳过认证: {request.url.path}")
                return await call_next(request)

            # 2. 执行认证
            # 认证链会尝试所有 Provider，成功则返回 user，失败则抛出异常或返回 None
            user, auth_error = await self._auth_chain.authenticate(request)

            if user:
                # 认证成功 -> 注入 request.state
                request.state.user = user

                # 构造 AuthContext (如果需要)
                request.state.auth_context = AuthContext(
                    user=user,
                    permissions=[],  # TODO: 加载权限
                    roles=[]  # TODO: 加载角色
                )
            elif auth_error:
                # 认证失败 (有 Provider 匹配但认证不通过) -> 返回 401
                logger.warning(f"🚫 认证失败: {auth_error}")
                return self.create_error_response(
                    status.HTTP_401_UNAUTHORIZED,
                    "Authentication Failed",
                    str(auth_error)
                )
            else:
                # 无 Provider 匹配 -> 视为匿名用户或拒绝访问
                # 这里策略可配置：是否允许匿名？
                # 默认: 如果不是白名单，且没认证成功，则拒绝
                logger.warning(f"🚫 无效的认证请求: {request.url.path}")
                return self.create_error_response(
                    status.HTTP_401_UNAUTHORIZED,
                    "Authentication Required",
                    "No valid authentication credentials provided"
                )

            # 3. 角色/权限检查 (委托给 RoleCheckMiddleware)
            if self.enable_role_check and self._role_middleware:
                # RoleCheckMiddleware 本身就是个 middleware-like 或者有处理方法
                # 这里假设它有个 check 方法，或者我们手动复用它的逻辑
                # 但由于 RoleCheckMiddleware 是 BaseHTTPMiddleware，直接调用比较麻烦
                # 我们这里调用它的业务逻辑 check_permission
                try:
                    await self._role_middleware.check_permission(request)
                except Exception as e:
                    # Role middleware throws HTTPException on failure
                    if hasattr(e, 'status_code'):
                        return self.create_error_response(e.status_code, e.detail)
                    raise e

            response = await call_next(request)
            return response

        except Exception as exc:
            logger.error(f"💥 认证中间件内部错误: {exc}", exc_info=True)
            return self.create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Authentication Service Error",
                str(exc)
            )

    @staticmethod
    def create_error_response(status_code: int, message: str, detail: Optional[str] = None) -> JSONResponse:
        """
        创建统一的错误响应
        
        Args:
            status_code: HTTP状态码
            message: 错误消息
            detail: 详细信息（可选）
            
        Returns:
            JSON响应
        """
        response_data = {
            "code": status_code,
            "message": message,
            "data": None
        }

        if detail:
            response_data["detail"] = detail

        return JSONResponse(
            status_code=status_code,
            content=response_data
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        拦截所有请求并进行认证（重构版）
        
        【新架构流程】
        1. 执行认证提供者链（自动处理白名单）
        2. 验证用户角色权限（可选）
        3. 将用户信息注入到 request.state
        
        Args:
            request: 请求对象
            call_next: 下一个中间件/路由处理器
            
        Returns:
            响应对象
        """
        path = request.url.path

        # 1. 执行认证链（包含白名单检查）
        auth_result = await self.auth_chain.authenticate(request)

        # 认证失败
        if not auth_result.success:
            # 如果是白名单路径（provider_name == "whitelist"），也算认证成功
            if auth_result.provider_name == "whitelist":
                logger.debug(f"✅ 白名单路径放行: {path}")
                return await call_next(request)

            logger.warning(f"⚠️ 认证失败: {request.method} {path} - {auth_result.error_message}")
            return self.create_error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="认证失败",
                detail=auth_result.error_message
            )

        # 2. 白名单路径直接放行
        if auth_result.provider_name == "whitelist":
            logger.debug(f"✅ 白名单路径放行: {path}")
            return await call_next(request)

        # 3. 将用户信息注入到请求状态中（供后续使用）
        if auth_result.user_id:
            request.state.user_id = auth_result.user_id
        if auth_result.username:
            request.state.user_email = auth_result.username

        # 总是初始化 user_roles，避免后续中间件报错
        request.state.user_roles = auth_result.roles if auth_result.roles else []

        if auth_result.extra_data:
            request.state.token_payload = auth_result.extra_data
            # [Permission-Upgrade] 注入 user_permissions 到 state
            request.state.user_permissions = auth_result.extra_data.get("permissions", [])
        else:
            request.state.user_permissions = []

        # 3.5 【新增】设置认证上下文（类似 Spring Security 的 SecurityContextHolder）
        # 从 token 获取完整用户信息并设置到上下文
        try:
            # 如果有额外数据(通常包含Token payload)，可以在这里做进一步处理
            # 目前 AuthContext 主要依赖 request.state，此处留空待扩展
            if auth_result.extra_data:
                pass
        except Exception as e:
            logger.debug(f"⚠️ 设置认证上下文失败: {e}")

        # 4. 角色权限验证（如果启用）
        if self.enable_role_check and self.role_middleware:
            try:
                # 检查角色权限（如果返回 JSONResponse 说明权限不足，需拦截）
                check_result = await self.role_middleware.auth(path, request)
                if isinstance(check_result, JSONResponse):
                    return check_result
            except Exception as e:
                logger.error(f"❌ 角色验证系统异常: {e}")
                return self.create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="权限不足",
                    detail="您没有访问此资源的权限"
                )

        # 6. 所有验证通过，继续处理请求
        logger.debug(f"✅ 认证通过: {request.method} {path} (用户: {auth_result.username}, 提供者: {auth_result.provider_name})")

        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"🚨 请求处理失败: {e}")
            return self.create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="服务器内部错误",
                detail=str(e)
            )
        finally:
            # 7. 【新增】请求结束后清理上下文（防止内存泄漏）
            AuthContext.clear()
