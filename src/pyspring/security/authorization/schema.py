from typing import List, Union, Callable

from fastapi import Request, HTTPException, status

from pyspring.log.instance import logger


def require_permissions(permissions: Union[str, List[str]], logic: str = "OR") -> Callable:
    """
    创建一个依赖注入函数，用于检查当前用户是否具有指定权限。

    注意: 这通常要求 Access Token 的 payload 中包含 'permissions' 字段。
    如果你目前只有 'roles'，你可能需要先升级 LoginService 以注入 permissions，
    或者在这里实现 roles -> permissions 的实时查询 (会影响性能)。

    Args:
        permissions: 单个权限字符串或权限列表 (e.g. "user:read" 或 ["user:read", "user:write"])
        logic: 逻辑关系，"OR" (满足其一) 或 "AND" (全部满足)。默认为 "OR"。

    Returns:
        FastAPI dependency function
    """

    if isinstance(permissions, str):
        permissions = [permissions]

    async def permission_dependency(request: Request):
        # 1. 获取当前用户持有的权限列表
        # 假设 Token Payload 中有一个 'permissions' 字段
        # 或者在 AuthenticationMiddleware 中已经解析并放入了 request.state.user_permissions

        # 优先读取 state，如果没有则尝试从 payload 读取，还没有则为空
        user_permissions = getattr(request.state, "user_permissions", [])

        if not user_permissions:
            # 兼容逻辑: 尝试从 payload 读取 (如果 Middleware 没做处理)
            payload = getattr(request.state, "token_payload", {})
            user_permissions = payload.get("permissions", [])

        # 2. 执行检查
        if not user_permissions:
            logger.warning(f"❌ 拒绝访问: 用户 {getattr(request.state, 'user_email', 'Unknown')} 没有权限列表")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions (No permissions assigned)"
            )

        has_perm = False
        if logic.upper() == "OR":
            # 只要有一个匹配即可
            # 支持通配符简单的实现: user:* 可以匹配 user:read
            for req in permissions:
                if _check_single_permission(req, user_permissions):
                    has_perm = True
                    break
        elif logic.upper() == "AND":
            # 必须全部匹配
            has_perm = True
            for req in permissions:
                if not _check_single_permission(req, user_permissions):
                    has_perm = False
                    break

        if not has_perm:
            logger.warning(f"⚠️ 权限不足: 需要 {logic} {permissions}, 实际拥有 {user_permissions}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: required {permissions}"
            )

        return True  # 验证通过

    return permission_dependency


def _check_single_permission(required: str, owned_list: List[str]) -> bool:
    """
    检查单个权限是否满足，支持简单的 * 通配符
    Example: 
      owned=['user:*'], required='user:read' -> True
      owned=['user:read'], required='user:read' -> True
    """
    if required in owned_list:
        return True

    # 检查通配符
    for owned in owned_list:
        if owned.endswith('*'):
            prefix = owned.rstrip('*')
            if required.startswith(prefix):
                return True

    return False


# 别名
has_permission = require_permissions
