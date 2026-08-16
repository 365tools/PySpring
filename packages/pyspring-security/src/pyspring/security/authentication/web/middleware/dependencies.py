"""
认证依赖函数

提供FastAPI路由中使用的认证相关依赖注入函数。
支持两种模式：
1. 从中间件注入的request.state获取（适用于已通过认证中间件的场景）
2. 从Authorization header直接验证Token获取（适用于无中间件或自定义验证场景）

这些函数与PySpring的令牌提供者(ITokenService)和用户管理服务(IUserManagerService)集成。
"""
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pyspring.core.ioc.context import ApplicationContext
from pyspring.core.log.instance import logger
from pyspring.security.authorization.contracts.permission import IPermissionService


def get_current_user_id(request: Request) -> int:
    """
    获取当前用户ID的依赖函数
    
    Usage:
        @router.get("/profile")
        async def get_profile(
            user_id: Annotated[int, Depends(get_current_user_id)]
        ):
            return {"user_id": user_id}
    
    Args:
        request: FastAPI自动注入的Request对象
        
    Returns:
        用户ID
        
    Raises:
        HTTPException: 如果未找到用户ID
    """
    from .utils import AuthUtils
    return AuthUtils.get_current_user_id(request)


def get_current_user_email(request: Request) -> (str) | None:
    """
    获取当前用户邮箱的依赖函数
    
    Usage:
        @router.get("/email")
        async def get_email(
            email: Annotated[(str) | None, Depends(get_current_user_email)]
        ):
            return {"email": email}
    
    Args:
        request: FastAPI自动注入的Request对象
        
    Returns:
        用户邮箱，如果不存在返回None
    """
    from .utils import AuthUtils
    return AuthUtils.get_current_user_email(request)


def get_current_user_roles(request: Request) -> list[str]:
    """
    获取当前用户角色列表的依赖函数
    
    Usage:
        @router.get("/roles")
        async def get_roles(
            roles: Annotated[list[str], Depends(get_current_user_roles)]
        ):
            return {"roles": roles}
    
    Args:
        request: FastAPI自动注入的Request对象
        
    Returns:
        角色列表
    """
    from .utils import AuthUtils
    return AuthUtils.get_current_user_roles(request)


def get_token_payload(request: Request) -> dict[str, Any]:
    """
    获取Token完整载荷的依赖函数
    
    Usage:
        @router.get("/token-info")
        async def token_info(
            payload: Annotated[dict, Depends(get_token_payload)]
        ):
            return {"payload": payload}
    
    Args:
        request: FastAPI自动注入的Request对象
        
    Returns:
        Token载荷字典
    """
    from .utils import AuthUtils
    return AuthUtils.get_token_payload(request)


def require_role(role: str):
    """
    要求特定角色的依赖工厂函数
    
    Usage:
        @router.get("/admin")
        async def admin_only(
            _: Annotated[None, Depends(require_role("admin"))]
        ):
            return {"message": "Admin area"}
    
    Args:
        role: 需要的角色名称
        
    Returns:
        依赖函数
    """

    def _require_role(request: Request) -> None:
        from .utils import AuthUtils
        AuthUtils.require_role(request, role)

    return _require_role


def require_any_role(roles: list[str]):
    """
    要求任意角色的依赖工厂函数
    
    Usage:
        @router.get("/staff")
        async def staff_area(
            _: Annotated[None, Depends(require_any_role(["admin", "moderator"]))]
        ):
            return {"message": "Staff area"}
    
    Args:
        roles: 需要的角色列表
        
    Returns:
        依赖函数
    """

    def _require_any_role(request: Request) -> None:
        from .utils import AuthUtils
        AuthUtils.require_any_role(request, roles)

    return _require_any_role


# ============================================================================
# 基于Token验证的依赖函数（框架级集成）
# ============================================================================

# HTTP Bearer 安全方案
_security = HTTPBearer(auto_error=False)


async def get_current_user_from_token(
        credentials: (HTTPAuthorizationCredentials) | None = Depends(_security),
) -> (Any) | None:
    """
    从Authorization header的Token中获取当前用户（框架级实现）
    
    此函数与PySpring的认证框架深度集成：
    - 自动使用配置的ITokenService进行令牌验证
    - 自动使用配置的IUserManagerService获取用户信息
    - 支持多种令牌提供者（JWT、Session等）
    
    Usage:
        from typing import Annotated
        from fastapi import Depends
        
        @router.get("/protected")
        async def protected_route(
            user: Annotated[Any, Depends(get_current_user_from_token)]
        ):
            if not user:
                raise HTTPException(status_code=401, detail="未认证")
            return {"user": user}
    
    注意：
    - 此函数不会自动抛出401错误，返回None表示未认证
    - 如需强制认证，请使用 require_authentication_from_token
    
    Args:
        credentials: FastAPI自动注入的HTTP Bearer凭据
        
    Returns:
        用户对象，如果未认证或认证失败则返回None
    """
    if not credentials:
        return None

    try:
        # 延迟导入避免循环依赖
        from pyspring.core.ioc.context import ApplicationContext

        from ...contracts.token import ITokenService
        from ...contracts.user import IUserManagerService

        # 获取Token服务
        token_service = ApplicationContext.get_instance().get_by_type(ITokenService)
        if not token_service:
            # 如果未配置TokenService，返回None而不是抛出异常
            return None

        # 验证Token
        token = credentials.credentials
        payload = await token_service.verify_token(token)

        if not payload:
            return None

        # 从payload中提取user_id
        user_id = payload.get("sub")
        if not user_id:
            return None

        # 获取用户管理服务
        user_service = ApplicationContext.get_instance().get_by_type(IUserManagerService)
        if not user_service:
            return None

        # 获取用户信息
        user_info = await user_service.get_user_by_id(user_id)

        # 返回用户对象（UserInfo或其他用户模型）
        return user_info.user if hasattr(user_info, 'user') else user_info

    except Exception:
        # 任何异常都返回None，由调用方决定如何处理
        return None


async def require_authentication_from_token(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> Any:
    """
    从Token获取当前用户（强制认证，框架级实现）
    
    与get_current_user_from_token的区别：
    - 此函数会在认证失败时自动抛出401异常
    - 保证返回的一定是有效用户对象
    
    Usage:
        from typing import Annotated
        from fastapi import Depends
        
        @router.get("/protected")
        async def protected_route(
            user: Annotated[Any, Depends(require_authentication_from_token)]
        ):
            # user一定不为None
            return {"user_id": user.id}
    
    Args:
        credentials: FastAPI自动注入的HTTP Bearer凭据
        
    Returns:
        用户对象
        
    Raises:
        HTTPException: 如果未提供Token或验证失败
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_current_user_from_token(credentials)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否被禁用
    if hasattr(user, 'active') and not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    return user


def get_current_user_with_fallback(
        request: Request,
        credentials: (HTTPAuthorizationCredentials) | None = None,
) -> (Any) | None:
    """
    智能获取当前用户（带回退机制）
    
    尝试顺序：
    1. 优先从request.state获取（中间件已验证）
    2. 如果失败，从Authorization header验证Token
    
    这是最灵活的方式，同时支持中间件认证和直接Token验证。
    
    Usage:
        from typing import Annotated
        from fastapi import Depends
        
        @router.get("/flexible")
        async def flexible_route(
            user: Annotated[Any, Depends(get_current_user_with_fallback)]
        ):
            if user:
                return {"authenticated": True, "user": user}
            return {"authenticated": False}
    
    Args:
        request: FastAPI请求对象
        credentials: HTTP Bearer凭据（可选）
        
    Returns:
        用户对象，未认证返回None
    """
    # 方式1: 从request.state获取（中间件已验证）
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        # TODO: 可以选择返回完整的用户对象或只返回ID
        # 这里简化处理，返回一个包含user_id的字典
        return {
            "id": user_id,
            "email": getattr(request.state, "user_email", None),
            "roles": getattr(request.state, "user_roles", [])
        }

    # 方式2: 从Token验证
    if credentials:
        return get_current_user_from_token(credentials)

    return None


# ============================================================================
# 便捷工厂函数
# ============================================================================

def token_auth_dependency(auto_error: bool = True):
    """
    创建自定义的Token认证依赖
    
    Args:
        auto_error: 是否在认证失败时自动抛出错误
        
    Returns:
        依赖函数
        
    Usage:
        # 强制认证
        CurrentUser = Annotated[Any, Depends(token_auth_dependency(auto_error=True))]
        
        # 可选认证  
        OptionalUser = Annotated[Any, Depends(token_auth_dependency(auto_error=False))]
        
        @router.get("/test")
        async def test(user: CurrentUser):
            return {"user": user}
    """
    # 注：这里不使用 HTTPBearer 实例，认证凭据直接通过 credentials 参数传入
    async def _get_user(
            credentials: (HTTPAuthorizationCredentials) | None = None
    ) -> (Any) | None:
        if auto_error:
            assert credentials is not None, "auto_error 模式下必须提供认证凭据"
            return await require_authentication_from_token(credentials)
        else:
            return await get_current_user_from_token(credentials)

    return _get_user


# ============================================================================
# 🔐 授权依赖函数（Authorization Dependencies）
# ============================================================================
#
# 功能：基于Token认证 + 权限/角色授权的组合依赖
# 集成：IPermissionService（权限服务）
# 模式：先认证（Token），再授权（Permission/Role）
#
# 使用场景：
# 1. 需要特定权限的路由（如 user:read, order:delete）
# 2. 需要特定角色的路由（如 admin, manager）
# 3. 同时需要认证和授权的组合场景
#
# 与 @require_permission/@require_role 装饰器的区别：
# - 装饰器：从 request.state 获取user_id（依赖中间件）
# - 依赖函数：从 Token 直接验证（无需中间件）
# ============================================================================

def permission_dependency(permission: str, auto_error: bool = True):
    """
    工厂函数：创建权限检查依赖
    
    工作流程：
    1. 先通过Token认证获取用户（require_authentication_from_token）
    2. 从IoC容器获取IPermissionService
    3. 检查用户是否拥有指定权限
    4. 权限不足时根据auto_error决定是否抛出403
    
    Args:
        permission: 权限字符串（如 'user:read', 'order:delete'）
        auto_error: 权限不足时是否自动抛出403（默认True）
    
    Returns:
        FastAPI依赖函数
    
    使用示例：
        ```python
        from typing import Annotated
        from fastapi import Depends
        
        # 定义类型别名
        UserReadPermission = Annotated[
            Any, 
            Depends(permission_dependency("user:read"))
        ]
        OrderDeletePermission = Annotated[
            Any, 
            Depends(permission_dependency("order:delete"))
        ]
        
        # 使用类型别名
        @router.get("/users")
        async def list_users(user: UserReadPermission):
            return {"users": [...]}
        
        @router.delete("/orders/{order_id}")
        async def delete_order(
            order_id: int,
            user: OrderDeletePermission
        ):
            return {"deleted": order_id}
        ```
    """

    async def _permission_check(
            user=Depends(require_authentication_from_token)
    ) -> (Any) | None:
        try:
            # 获取权限服务
            permission_service = ApplicationContext.get_instance().get_by_type(IPermissionService)

            # 提取user_id
            user_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)
            if not user_id:
                logger.error("[permission_dependency] 用户对象缺少ID字段")
                if auto_error:
                    raise HTTPException(500, detail="Invalid user object")
                return None

            # 检查权限
            has_perm = await permission_service.has_permission(user_id, permission)

            if not has_perm:
                logger.warning(
                    f"[permission_dependency] 权限不足: "
                    f"user_id={user_id}, permission={permission}"
                )
                if auto_error:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {permission}"
                    )
                return None

            logger.debug(
                f"[permission_dependency] 权限验证通过: "
                f"user_id={user_id}, permission={permission}"
            )
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[permission_dependency] 权限检查异常: {e}")
            if auto_error:
                raise HTTPException(500, detail="Permission check failed")
            return None

    return _permission_check


def role_dependency(role: str, auto_error: bool = True):
    """
    工厂函数：创建角色检查依赖
    
    工作流程：
    1. 先通过Token认证获取用户（require_authentication_from_token）
    2. 从IoC容器获取IPermissionService
    3. 检查用户是否拥有指定角色
    4. 角色不足时根据auto_error决定是否抛出403
    
    Args:
        role: 角色字符串（如 'admin', 'manager'）
        auto_error: 角色不足时是否自动抛出403（默认True）
    
    Returns:
        FastAPI依赖函数
    
    使用示例：
        ```python
        from typing import Annotated
        from fastapi import Depends
        
        # 定义类型别名
        AdminOnly = Annotated[Any, Depends(role_dependency("admin"))]
        ManagerOnly = Annotated[Any, Depends(role_dependency("manager"))]
        
        # 使用类型别名
        @router.get("/admin/dashboard")
        async def admin_dashboard(user: AdminOnly):
            return {"dashboard": "admin"}
        
        @router.post("/manager/approve")
        async def manager_approve(user: ManagerOnly):
            return {"approved": True}
        ```
    """

    async def _role_check(
            user=Depends(require_authentication_from_token)
    ) -> (Any) | None:
        try:
            # 获取权限服务
            permission_service = ApplicationContext.get_instance().get_by_type(IPermissionService)

            # 提取user_id
            user_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)
            if not user_id:
                logger.error("[role_dependency] 用户对象缺少ID字段")
                if auto_error:
                    raise HTTPException(500, detail="Invalid user object")
                return None

            # 检查角色
            has_role = await permission_service.has_role(user_id, role)

            if not has_role:
                logger.warning(
                    f"[role_dependency] 角色不足: "
                    f"user_id={user_id}, role={role}"
                )
                if auto_error:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Role required: {role}"
                    )
                return None

            logger.debug(
                f"[role_dependency] 角色验证通过: "
                f"user_id={user_id}, role={role}"
            )
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[role_dependency] 角色检查异常: {e}")
            if auto_error:
                raise HTTPException(500, detail="Role check failed")
            return None

    return _role_check
