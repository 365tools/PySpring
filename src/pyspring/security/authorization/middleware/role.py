from typing import Optional, List

from fastapi import Request, status
from fastapi.responses import JSONResponse

from pyspring.log.instance import logger
from pyspring.web.core.response import Response, HttpResponse


class RoleCheckMiddleware:
    """
    角色
    """

    def __init__(self, enable_role_check: bool = True):
        self.enable_role_check = enable_role_check
        self.ROLE_BASED_PATHS: dict = {
            "/api/user/": ["admin", "super_admin"],  # 前缀匹配
            "/api/config/": ["admin", "super_admin"],
        }

    async def auth(self, path: str, request: Request) -> JSONResponse | bool:
        """
        认证
        """
        required_roles = self.requires_role(path)
        if required_roles:
            user_roles = getattr(request.state, "user_roles", [])
            has_permission = any(role in required_roles for role in user_roles)

            if not has_permission:
                logger.warning(f"⚠️ 权限不足: {request.state.user_email} 尝试访问 {path} (需要角。 {required_roles}, 拥有角色: {user_roles})")
                return Response.error(
                    HttpResponse(
                        code=status.HTTP_403_FORBIDDEN,
                        message="权限不足",
                        data=f"此操作需要以下角色之一: {', '.join(required_roles)}"
                    ))
            logger.debug(f"✅ 角色验证通过: {path} (角色: {user_roles})")
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
