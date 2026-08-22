# PySpring 认证+授权快速参考

## 导入

```python
from typing import Annotated, Any
from fastapi import Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    # Token认证
    require_authentication_from_token,  # 强制认证
    get_current_user_from_token,  # 可选认证
    # 权限/角色依赖
    permission_dependency,  # 权限检查
    role_dependency,  # 角色检查
)
```

## 认证依赖

| 函数                                  | 用途        | 失败行为   |
|-------------------------------------|-----------|--------|
| `require_authentication_from_token` | 强制Token认证 | 抛出401  |
| `get_current_user_from_token`       | 可选Token认证 | 返回None |

### 示例

```python
# 强制认证
AuthUser = Annotated[Any, Depends(require_authentication_from_token)]


@router.get("/profile")
async def get_profile(user: AuthUser):
    return {"user": user}


# 可选认证
OptionalUser = Annotated[Any, Depends(get_current_user_from_token)]


@router.get("/optional")
async def optional_route(user: OptionalUser):
    if user:
        return {"user": user}
    else:
        return {"guest": True}
```

## 权限依赖

### permission_dependency(permission, auto_error=True)

```python
# 定义权限类型
UserRead = Annotated[Any, Depends(permission_dependency("user:read"))]
UserWrite = Annotated[Any, Depends(permission_dependency("user:write"))]
UserDelete = Annotated[Any, Depends(permission_dependency("user:delete"))]


# 使用
@router.get("/users")
async def list_users(user: UserRead):
    # 需要 user:read 权限
    return {"users": [...]}


@router.post("/users")
async def create_user(user: UserWrite):
    # 需要 user:write 权限
    return {"user": {...}}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, user: UserDelete):
    # 需要 user:delete 权限
    return {"deleted": user_id}
```

## 角色依赖

### role_dependency(role, auto_error=True)

```python
# 定义角色类型
AdminOnly = Annotated[Any, Depends(role_dependency("admin"))]
ManagerOnly = Annotated[Any, Depends(role_dependency("manager"))]
UserOnly = Annotated[Any, Depends(role_dependency("user"))]


# 使用
@router.get("/admin/dashboard")
async def admin_dashboard(user: AdminOnly):
    # 需要 admin 角色
    return {"dashboard": "admin"}


@router.post("/manager/approve")
async def manager_approve(user: ManagerOnly):
    # 需要 manager 角色
    return {"approved": True}
```

## 权限命名规范

```
资源:操作

user:read       # 读取用户
user:write      # 创建/修改用户
user:delete     # 删除用户
user:*          # 用户所有权限

order:read      # 读取订单
order:write     # 创建/修改订单
order:approve   # 审批订单
order:*         # 订单所有权限

admin:*:*       # 管理员所有权限
```

## 常用权限组合

```python
# 1. 用户管理
UserRead = Annotated[Any, Depends(permission_dependency("user:read"))]
UserWrite = Annotated[Any, Depends(permission_dependency("user:write"))]
UserDelete = Annotated[Any, Depends(permission_dependency("user:delete"))]

# 2. 订单管理
OrderRead = Annotated[Any, Depends(permission_dependency("order:read"))]
OrderWrite = Annotated[Any, Depends(permission_dependency("order:write"))]
OrderDelete = Annotated[Any, Depends(permission_dependency("order:delete"))]
OrderApprove = Annotated[Any, Depends(permission_dependency("order:approve"))]

# 3. 文章管理
ArticleRead = Annotated[Any, Depends(permission_dependency("article:read"))]
ArticleWrite = Annotated[Any, Depends(permission_dependency("article:write"))]
ArticlePublish = Annotated[Any, Depends(permission_dependency("article:publish"))]
ArticleDelete = Annotated[Any, Depends(permission_dependency("article:delete"))]

# 4. 角色
AdminOnly = Annotated[Any, Depends(role_dependency("admin"))]
ManagerOnly = Annotated[Any, Depends(role_dependency("manager"))]
EditorOnly = Annotated[Any, Depends(role_dependency("editor"))]
UserOnly = Annotated[Any, Depends(role_dependency("user"))]
```

## 工作流程

```
请求 → Token认证 → 权限/角色检查 → 业务逻辑

1. 提取 Authorization Header
2. 使用 ITokenService.verify_token(token)
3. 使用 IUserManagerService.get_user_by_id(user_id)
4. 使用 IPermissionService.has_permission(user_id, permission)
   或 IPermissionService.has_role(user_id, role)
5. 权限通过 → 执行业务逻辑
   权限不足 → 抛出 403
```

## 错误码

| 状态码 | 含义             | 场景         |
|-----|----------------|------------|
| 401 | Unauthorized   | Token无效/过期 |
| 403 | Forbidden      | 权限/角色不足    |
| 500 | Internal Error | 服务异常       |

## 与装饰器对比

| 特性    | 依赖函数      | 装饰器           |
|-------|-----------|---------------|
| 认证方式  | Token直接验证 | request.state |
| 中间件依赖 | ❌ 不需要     | ✅ 需要          |
| 使用场景  | 微服务、API网关 | 单体应用          |
| 灵活性   | ⭐⭐⭐⭐⭐     | ⭐⭐⭐           |

### 装饰器方式

```python
from pyspring.security.authorization.decorators import require_permission


@router.delete("/users/{user_id}")
@require_permission("user:delete")
async def delete_user(user_id: int, request: Request):
    # 从 request.state.user_id 获取
    return {"deleted": user_id}
```

### 依赖函数方式

```python
from pyspring.security.authentication.web.middleware.dependencies import permission_dependency

UserDelete = Annotated[Any, Depends(permission_dependency("user:delete"))]


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, user: UserDelete):
    # 直接从 Token 验证
    return {"deleted": user_id}
```

## 最佳实践

1. **集中定义类型别名**
   ```python
   # permissions.py
   from typing import Annotated, Any
   from fastapi import Depends
   from pyspring.security.authentication.web.middleware.dependencies import permission_dependency, role_dependency

   # 权限
   UserRead = Annotated[Any, Depends(permission_dependency("user:read"))]
   UserWrite = Annotated[Any, Depends(permission_dependency("user:write"))]
   # ... 更多权限

   # 角色
   AdminOnly = Annotated[Any, Depends(role_dependency("admin"))]
   ManagerOnly = Annotated[Any, Depends(role_dependency("manager"))]
   ```

2. **在路由中使用**
   ```python
   from .permissions import UserRead, UserWrite, UserDelete, AdminOnly


   @router.get("/users")
   async def list_users(user: UserRead):
       pass


   @router.post("/users")
   async def create_user(user: UserWrite):
       pass


   @router.delete("/users/{id}")
   async def delete_user(id: int, user: UserDelete):
       pass


   @router.post("/users/{id}/ban")
   async def ban_user(id: int, user: AdminOnly):
       pass
   ```

3. **权限配置文件化**
   ```yaml
   # permissions.yaml
   resources:
     user:
       - read
       - write
       - delete
     
     order:
       - read
       - write
       - approve
       - delete
   
   roles:
     admin:
       permissions:
         - admin:*:*
         - user:*
         - order:*
     
     manager:
       permissions:
         - user:read
         - user:write
         - order:*
     
     user:
       permissions:
         - user:read
         - order:read
   ```

## 常见问题

**Q: 如何获取user_id？**

A: `user_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)`

**Q: 如何支持多权限之一？**

A: 使用自定义组合依赖（见完整文档）

**Q: 如何缓存权限检查？**

A: 使用 `CachedPermissionService`（见完整文档）

**Q: 权限通配符如何工作？**

A: `user:*` 匹配 `user:read`, `user:write`, `user:delete`

## 相关文档

- [完整集成指南](./AUTH_AUTHORIZATION_INTEGRATION_GUIDE.md)
- [Token认证指南](./AUTH_TOKEN_DEPENDENCIES_GUIDE.md)

> 💡 可通过 `pyspring init my-app --example` 生成包含认证/授权完整示例的应用。
