"""
权限装饰器

提供细粒度的权限和角色检查装饰器
"""
from functools import wraps
from typing import Callable, Union, List

from fastapi import HTTPException, Request

from pyspring.ioc.context import ApplicationContext
from pyspring.log.instance import logger
from pyspring.security.authorization.contracts.permission import IPermissionService


def require_permission(permission: Union[str, List[str]], require_all: bool = False):
    """
    权限检查装饰器
    
    使用示例：
        @require_permission("order:delete")
        async def delete_order(order_id: int): ...
        
        @require_permission(["admin:*", "manager:*"], require_all=False)
        async def admin_action(): ...
    
    Args:
        permission: 权限字符串或权限列表
        require_all: 是否需要拥有所有权限（默认False，只需一个）
        
    Raises:
        HTTPException: 权限不足时抛出403
    """
    # 统一为列表
    permissions = [permission] if isinstance(permission, str) else permission
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. 提取Request对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # 从kwargs中查找
                request = kwargs.get('request')
            
            if not request:
                logger.error("[require_permission] 未找到Request对象，无法验证权限")
                raise HTTPException(
                    status_code=500,
                    detail="Internal error: missing request context"
                )
            
            # 2. 提取user_id
            user_id = getattr(request.state, 'user_id', None)
            if not user_id:
                logger.warning("[require_permission] 用户未认证")
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            # 3. 获取权限服务
            try:
                permission_service = ApplicationContext.get_instance().get_by_type(IPermissionService)
            except Exception as e:
                logger.error(f"[require_permission] 无法获取权限服务: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Permission service unavailable"
                )
            
            # 4. 检查权限
            try:
                if require_all:
                    # 需要所有权限
                    for perm in permissions:
                        if not await permission_service.has_permission(user_id, perm):
                            logger.warning(f"[require_permission] 权限不足: user={user_id}, required={perm}")
                            raise HTTPException(
                                status_code=403,
                                detail=f"Permission denied: {perm}"
                            )
                else:
                    # 只需一个权限
                    has_any = False
                    for perm in permissions:
                        if await permission_service.has_permission(user_id, perm):
                            has_any = True
                            break
                    
                    if not has_any:
                        logger.warning(f"[require_permission] 权限不足: user={user_id}, required_any={permissions}")
                        raise HTTPException(
                            status_code=403,
                            detail=f"Permission denied: requires any of {permissions}"
                        )
                
                logger.debug(f"[require_permission] 权限检查通过: user={user_id}")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"[require_permission] 权限检查异常: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Permission check failed"
                )
            
            # 5. 权限通过，执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role: Union[str, List[str]], require_all: bool = False):
    """
    角色检查装饰器
    
    使用示例：
        @require_role("admin")
        async def admin_only(): ...
        
        @require_role(["admin", "manager"], require_all=False)
        async def admin_or_manager(): ...
    
    Args:
        role: 角色字符串或角色列表
        require_all: 是否需要拥有所有角色（默认False，只需一个）
        
    Raises:
        HTTPException: 角色不足时抛出403
    """
    # 统一为列表
    roles = [role] if isinstance(role, str) else role
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. 提取Request对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if not request:
                logger.error("[require_role] 未找到Request对象")
                raise HTTPException(
                    status_code=500,
                    detail="Internal error: missing request context"
                )
            
            # 2. 提取user_id
            user_id = getattr(request.state, 'user_id', None)
            if not user_id:
                logger.warning("[require_role] 用户未认证")
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            # 3. 获取权限服务
            try:
                permission_service = ApplicationContext.get_instance().get_by_type(IPermissionService)
            except Exception as e:
                logger.error(f"[require_role] 无法获取权限服务: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Permission service unavailable"
                )
            
            # 4. 检查角色
            try:
                if require_all:
                    # 需要所有角色
                    for r in roles:
                        if not await permission_service.has_role(user_id, r):
                            logger.warning(f"[require_role] 角色不足: user={user_id}, required={r}")
                            raise HTTPException(
                                status_code=403,
                                detail=f"Role required: {r}"
                            )
                else:
                    # 只需一个角色
                    has_any = False
                    for r in roles:
                        if await permission_service.has_role(user_id, r):
                            has_any = True
                            break
                    
                    if not has_any:
                        logger.warning(f"[require_role] 角色不足: user={user_id}, required_any={roles}")
                        raise HTTPException(
                            status_code=403,
                            detail=f"Role required: any of {roles}"
                        )
                
                logger.debug(f"[require_role] 角色检查通过: user={user_id}")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"[require_role] 角色检查异常: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Role check failed"
                )
            
            # 5. 角色通过，执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(*permissions: str):
    """
    要求任意一个权限的简化装饰器
    
    使用示例：
        @require_any_permission("admin:*", "manager:*")
        async def privileged_action(): ...
    """
    return require_permission(list(permissions), require_all=False)


def require_all_permissions(*permissions: str):
    """
    要求所有权限的简化装饰器
    
    使用示例：
        @require_all_permissions("user:read", "user:write")
        async def full_user_access(): ...
    """
    return require_permission(list(permissions), require_all=True)
