from typing import Optional, List, Dict

from fastapi import Request, status
from fastapi.responses import JSONResponse

from pyspring.log.instance import logger
from pyspring.security.authentication.infrastructure.context import AuthContext
from pyspring.security.authorization.contracts.permission import IPermissionService
from pyspring.security.authorization.contracts.rule import IPathPermissionProvider
from pyspring.web.core.response import Response, HttpResponse


class RoleCheckMiddleware:
    """
    角色验证中间件 (Refactored)
    """

    def __init__(self,
                 permission_service: IPermissionService,
                 path_provider: IPathPermissionProvider,
                 enable_role_check: bool = True):
        self.permission_service = permission_service
        self.path_provider = path_provider
        self.enable_role_check = enable_role_check

        # Load rules from provider
        self.ROLE_BASED_PATHS: Dict[str, List[str]] = self.path_provider.get_path_rules()
        logger.debug(f"[Debug] [RoleCheck] 已加载路径规则: {len(self.ROLE_BASED_PATHS)}条")

    async def auth(self, path: str, request: Request) -> JSONResponse | bool:
        """
        认证
        """
        required_roles = self.requires_role(path)
        if required_roles:
            # Try to get user from AuthContext
            user_ctx = AuthContext.get_current_user()

            has_permission = False

            if user_ctx and user_ctx.user:
                # Async check using service (Prefer ID)
                for role_code in required_roles:
                    if await self.permission_service.has_role(user_ctx.user.id, role_code):
                        has_permission = True
                        break
            else:
                # 使用 request state
                user_roles = getattr(request.state, "user_roles", [])
                has_permission = any(role in required_roles for role in user_roles)

            if not has_permission:
                logger.warning(f"[Warning] 权限不足: {getattr(request.state, 'user_email', 'Unknown')} 尝试访问 {path}")
                return Response.error(
                    HttpResponse(
                        code=status.HTTP_403_FORBIDDEN,
                        message="权限不足",
                        data=f"此操作需要以下角色之一: {', '.join(required_roles)}"
                    ))
            logger.debug(f"[Success] 角色验证通过: {path}")
            return True
        return False

    def requires_role(self, path: str) -> Optional[List[str]]:
        """
        检查路径是否需要特定角。

        Args:
            path: 请求路径

        Returns:
            需要的角色列表，如果不需要返回None
        """
        if not self.enable_role_check:
            return None

        # 精确匹配
        if path in self.ROLE_BASED_PATHS:
            return self.ROLE_BASED_PATHS[path]

        # 前缀匹配
        for pattern, roles in self.ROLE_BASED_PATHS.items():
            if pattern.endswith("/") and path.startswith(pattern):
                return roles

        return None
