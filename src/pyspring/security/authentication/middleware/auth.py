"""
from pyspring.ioc.manager import AppContainerManager
from pyspring.security.authentication.services.user.manager import UserManagerService
from pyspring.security.authentication.core.chain import AuthenticationChain

全局认证拦截中间件（重构版）

基于认证提供者链（Chain of Responsibility Pattern）
统一处理所有API请求的认证逻辑，类似Spring Boot的AOP
"""
from typing import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from pyspring.ioc.manager import AppContainerManager
from pyspring.log.instance import logger
from pyspring.security.authorization.middleware.role import RoleCheckMiddleware
from pyspring.security.core.config.loader import SecurityConfigManager
from ..core.chain import AuthenticationChain
from ..core.context import AuthContext
from ..services.user.manager import UserManagerService


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

    def __init__(self, app, enable_role_check: bool = None):
        """
        初始化认证中间件
        
        Args:
            app: FastAPI应用实例
            enable_role_check: 是否启用角色验证（None则从配置读取）
        """
        super().__init__(app)

        # 获取配置管理器（通过 IoC 容器）
        container = AppContainerManager()
        self.config_manager = container.get(SecurityConfigManager)

        if enable_role_check is None:
            self.enable_role_check = self.config_manager.is_authorization_enabled()
        else:
            self.enable_role_check = enable_role_check

        # 获取认证链（通过 IoC 容器）
        self.auth_chain = container.get(AuthenticationChain)

        logger.info(f"🔒 全局认证中间件已启动 (基于认证链)")
        logger.info(f"   - 角色验证: {'启用' if self.enable_role_check else '禁用'}")
        # 注意: 认证提供者此时尚未初始化，将在应用启动时由 AuthenticationInitializer 加载

    @staticmethod
    def create_error_response(status_code: int, message: str, detail: str = None) -> JSONResponse:
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

            container = AppContainerManager()
            user_manager = container.get(UserManagerService)

            # 从 token 获取用户信息
            token = auth_result.extra_data.get('token') if auth_result.extra_data else None
            if token:
                user_info = await user_manager.get_current_user(token)
                if user_info:
                    AuthContext.set_current_user(user_info)
                    AuthContext.set_current_token(token)
                    logger.debug(f"🔐 上下文已设置: {user_info.user.email}")
        except Exception as e:
            logger.debug(f"⚠️ 设置认证上下文失败: {e}")

        # 4. 角色权限验证（如果启用）
        if self.enable_role_check:
            role_middleware = RoleCheckMiddleware()
            try:
                # 检查角色权限（如果返回 JSONResponse 说明权限不足，需拦截）
                check_result = await role_middleware.auth(path, request)
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
