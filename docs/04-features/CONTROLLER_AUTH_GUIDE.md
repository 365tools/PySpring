# Controller 层使用认证与鉴权指南

本指南展示如何在 FastAPI 的 Controller（路由处理器）中使用 PySpring 的认证与鉴权功能。

---

## 目录

1. [前置准备](#前置准备)
2. [获取当前用户信息](#获取当前用户信息)
3. [使用权限装饰器](#使用权限装饰器)
4. [使用角色装饰器](#使用角色装饰器)
5. [依赖注入方式](#依赖注入方式)
6. [完整示例](#完整示例)
7. [最佳实践](#最佳实践)

---

## 前置准备

### 1. 注册认证中间件

在 `main.py` 中注册认证中间件：

```python
from fastapi import FastAPI
from pyspring.security.authentication.web.middleware.auth import AuthenticationMiddleware

app = FastAPI()

# 注册认证中间件（全局）
app.add_middleware(
    AuthenticationMiddleware,
    enable_role_check=True  # 启用角色检查
)
```

### 2. 配置白名单路径

在 `config/security.yaml` 中配置无需认证的路径：

```yaml
authentication:
  whitelist:
    exact_paths:
      - "/api/auth/login"
      - "/api/auth/register"
      - "/docs"
      - "/health"
    prefix_paths:
      - "/api/public"
```

---

## 获取当前用户信息

### 方式 1: 通过 Request.state 获取

```python
from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/user")

@router.get("/profile")
async def get_profile(request: Request):
    """获取当前用户资料"""
    return {
        "user_id": request.state.user_id,          # 用户 ID
        "email": request.state.user_email,         # 用户邮箱
        "roles": request.state.user_roles,         # 用户角色列表
        "permissions": request.state.user_permissions  # 用户权限列表
    }
```

### 方式 2: 通过 AuthContext 获取

```python
from fastapi import APIRouter
from pyspring.security.authentication.infrastructure.context import AuthContext

router = APIRouter(prefix="/api/user")

@router.get("/info")
async def get_user_info():
    """获取当前认证用户信息"""
    user_context = AuthContext.get_current_user()
    
    if not user_context or not user_context.user:
        return {"error": "User not authenticated"}
    
    user = user_context.user
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "roles": user_context.roles
    }
```

---

## 使用权限装饰器

PySpring 提供了 4 个权限装饰器：

### 1. `@require_permission` - 基础权限检查

```python
from fastapi import APIRouter, Request
from pyspring.security.authorization import require_permission

router = APIRouter(prefix="/api/users")

@router.get("")
@require_permission("user:read")
async def list_users(request: Request):
    """需要 user:read 权限才能访问"""
    return {"users": [...]}

@router.post("")
@require_permission("user:create")
async def create_user(request: Request, username: str):
    """需要 user:create 权限才能访问"""
    return {"message": "User created"}

@router.delete("/{user_id}")
@require_permission("user:delete")
async def delete_user(request: Request, user_id: int):
    """需要 user:delete 权限才能访问"""
    return {"message": f"User {user_id} deleted"}
```

### 2. `@require_any_permission` - 任意权限（OR）

```python
from pyspring.security.authorization import require_any_permission

@router.get("/admin-or-manager")
@require_any_permission("admin:*", "manager:*")
async def privileged_action(request: Request):
    """拥有 admin:* 或 manager:* 任一权限即可访问"""
    return {"message": "You have elevated privileges"}
```

### 3. `@require_all_permissions` - 所有权限（AND）

```python
from pyspring.security.authorization import require_all_permissions

@router.post("/sensitive-operation")
@require_all_permissions("user:read", "user:write", "user:delete")
async def sensitive_operation(request: Request):
    """必须同时拥有 user:read, user:write, user:delete 三个权限"""
    return {"message": "Operation completed"}
```

### 4. 权限列表 + require_all 参数

```python
from pyspring.security.authorization import require_permission

# 方式 A: 任意权限（默认 require_all=False）
@router.get("/option-a")
@require_permission(["admin:*", "manager:*"], require_all=False)
async def any_permission_example(request: Request):
    """拥有 admin:* 或 manager:* 任一权限即可"""
    return {"access": "granted"}

# 方式 B: 所有权限（require_all=True）
@router.post("/option-b")
@require_permission(["user:read", "user:write"], require_all=True)
async def all_permissions_example(request: Request):
    """必须同时拥有 user:read 和 user:write"""
    return {"access": "granted"}
```

### 权限通配符支持

```python
@router.delete("/admin-only")
@require_permission("admin:*")
async def admin_only_action(request: Request):
    """需要所有以 'admin:' 开头的权限（通配符）"""
    return {"message": "Admin action completed"}
```

---

## 使用角色装饰器

### 1. `@require_role` - 基础角色检查

```python
from fastapi import APIRouter, Request
from pyspring.security.authorization import require_role

router = APIRouter(prefix="/api/admin")

@router.get("/dashboard")
@require_role("admin")
async def admin_dashboard(request: Request):
    """只有 admin 角色可以访问"""
    return {"dashboard": "admin data"}

@router.post("/settings")
@require_role(["admin", "super_admin"], require_all=False)
async def modify_settings(request: Request):
    """拥有 admin 或 super_admin 角色即可访问"""
    return {"message": "Settings updated"}
```

### 2. 多角色组合

```python
from pyspring.security.authorization import require_role

# 任意角色（OR）
@router.get("/managers")
@require_role(["admin", "manager", "team_lead"], require_all=False)
async def manager_action(request: Request):
    """拥有 admin、manager 或 team_lead 任一角色即可"""
    return {"access": "granted"}

# 所有角色（AND）- 较少使用
@router.get("/super-restricted")
@require_role(["admin", "auditor"], require_all=True)
async def super_restricted(request: Request):
    """必须同时拥有 admin 和 auditor 角色（罕见场景）"""
    return {"access": "granted"}
```

---

## 依赖注入方式

### 1. 手动获取 IPermissionService

```python
from fastapi import APIRouter, Request
from pyspring.ioc.context import ApplicationContext
from pyspring.security.authorization.contracts.permission import IPermissionService

router = APIRouter(prefix="/api/custom")


@router.get("/check-permission")
async def custom_permission_check(request: Request):
    """手动进行权限检查"""
    # 获取权限服务
    permission_service = ApplicationContext.get_instance().get_by_type(IPermissionService)

    # 获取当前用户 ID
    user_id = request.state.user_id

    # 手动检查权限
    has_read = await permission_service.has_permission(user_id, "user:read")
    has_write = await permission_service.has_permission(user_id, "user:write")

    return {
        "user_id": user_id,
        "can_read": has_read,
        "can_write": has_write
    }
```

### 2. 动态权限检查

```python
@router.post("/dynamic-action/{resource_id}")
async def dynamic_action(request: Request, resource_id: int):
    """根据业务逻辑动态检查权限"""
    user_id = request.state.user_id
    permission_service = ApplicationContext.get_instance().get_by_type(IPermissionService)

    # 业务逻辑：根据 resource_id 判断需要的权限
    if resource_id > 1000:
        required_permission = "admin:manage"
    else:
        required_permission = "user:modify"

    # 动态检查
    if not await permission_service.has_permission(user_id, required_permission):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail=f"Permission denied: {required_permission}")

    return {"message": f"Action on resource {resource_id} completed"}
```

---

## 完整示例

### 示例 1: 用户管理 API

```python
from fastapi import APIRouter, Request, HTTPException
from pyspring.security.authorization import (
    require_permission,
    require_any_permission,
    require_all_permissions
)

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("")
@require_permission("user:read")
async def list_users(request: Request):
    """查询用户列表 - 需要 user:read 权限"""
    return {
        "users": [
            {"id": 1, "username": "alice"},
            {"id": 2, "username": "bob"}
        ]
    }


@router.get("/{user_id}")
@require_permission("user:read")
async def get_user(request: Request, user_id: int):
    """查询单个用户 - 需要 user:read 权限"""
    return {"id": user_id, "username": f"user_{user_id}"}


@router.post("")
@require_all_permissions("user:read", "user:create")
async def create_user(request: Request, username: str, email: str):
    """创建用户 - 需要 user:read 和 user:create 权限"""
    return {
        "message": "User created",
        "user": {"username": username, "email": email}
    }


@router.put("/{user_id}")
@require_permission("user:update")
async def update_user(request: Request, user_id: int, username: str):
    """更新用户 - 需要 user:update 权限"""
    return {
        "message": "User updated",
        "user": {"id": user_id, "username": username}
    }


@router.delete("/{user_id}")
@require_permission("user:delete")
async def delete_user(request: Request, user_id: int):
    """删除用户 - 需要 user:delete 权限"""
    return {"message": f"User {user_id} deleted"}


@router.post("/{user_id}/grant-admin")
@require_any_permission("admin:*", "super_admin:*")
async def grant_admin(request: Request, user_id: int):
    """授予管理员权限 - 需要 admin:* 或 super_admin:* 权限"""
    return {"message": f"Admin privileges granted to user {user_id}"}
```

### 示例 2: 管理后台 API

```python
from fastapi import APIRouter, Request
from pyspring.security.authorization import require_role, require_permission

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/dashboard")
@require_role("admin")
async def get_dashboard(request: Request):
    """管理后台首页 - 需要 admin 角色"""
    return {
        "total_users": 1000,
        "active_users": 850,
        "total_orders": 5000
    }


@router.get("/logs")
@require_role(["admin", "auditor"], require_all=False)
async def view_logs(request: Request):
    """查看系统日志 - 需要 admin 或 auditor 角色"""
    return {"logs": ["Log entry 1", "Log entry 2"]}


@router.post("/settings")
@require_permission("admin:settings:write")
async def update_settings(request: Request, key: str, value: str):
    """修改系统设置 - 需要 admin:settings:write 权限"""
    return {"message": f"Setting {key} updated to {value}"}


@router.delete("/cache")
@require_role("admin")
async def clear_cache(request: Request):
    """清空缓存 - 需要 admin 角色"""
    return {"message": "Cache cleared"}
```

### 示例 3: 混合认证与授权

```python
from fastapi import APIRouter, Request, HTTPException
from pyspring.security.authorization import require_permission
from pyspring.security.authentication.infrastructure.context import AuthContext

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.get("")
@require_permission("order:read")
async def list_orders(request: Request):
    """查询订单列表"""
    user_id = request.state.user_id
    return {
        "orders": [
            {"id": 1, "user_id": user_id, "total": 100.0},
            {"id": 2, "user_id": user_id, "total": 200.0}
        ]
    }


@router.get("/{order_id}")
async def get_order(request: Request, order_id: int):
    """查询订单详情 - 业务逻辑权限检查"""
    user_id = request.state.user_id

    # 模拟从数据库查询订单
    order = {"id": order_id, "user_id": 123, "total": 100.0}

    # 业务规则：只能查看自己的订单，或者有 admin 权限
    from pyspring.ioc.context import ApplicationContext
    from pyspring.security.authorization.contracts.permission import IPermissionService

    permission_service = ApplicationContext.get_instance().get_by_type(IPermissionService)
    is_admin = await permission_service.has_permission(user_id, "admin:*")

    if order["user_id"] != user_id and not is_admin:
        raise HTTPException(status_code=403, detail="You can only view your own orders")

    return order


@router.delete("/{order_id}")
@require_permission("order:delete")
async def cancel_order(request: Request, order_id: int):
    """取消订单"""
    user = AuthContext.get_current_user()
    return {
        "message": f"Order {order_id} cancelled by {user.user.email if user and user.user else 'unknown'}"
    }
```

---

## 最佳实践

### 1. 装饰器顺序

装饰器从下往上执行，路由装饰器应该放在最上面：

```python
@router.get("/example")           # ✅ 路由装饰器在最上面
@require_permission("user:read")  # ✅ 权限装饰器在下面
async def example(request: Request):
    return {"data": "..."}
```

### 2. Request 对象必须存在

权限装饰器需要从 `Request` 对象中提取 `user_id`，必须确保：

```python
# ✅ 正确：有 Request 参数
@router.get("/example")
@require_permission("user:read")
async def example(request: Request):
    return {"data": "..."}

# ❌ 错误：缺少 Request 参数
@router.get("/example")
@require_permission("user:read")
async def example():  # 缺少 request 参数
    return {"data": "..."}
```

### 3. 权限命名规范

建议使用 `资源:操作` 格式：

```python
# 推荐
"user:read"      # 读取用户
"user:write"     # 写入用户
"user:delete"    # 删除用户
"admin:*"        # 管理员所有权限
"order:create"   # 创建订单
"report:export"  # 导出报表

# 不推荐
"readUser"       # 驼峰命名不够清晰
"user_read"      # 下划线不如冒号清晰
```

### 4. 异常处理

装饰器会自动抛出 HTTP 异常：

- **401 Unauthorized**: 用户未认证（没有 `user_id`）
- **403 Forbidden**: 权限不足
- **500 Internal Server Error**: 权限服务不可用

```python
# 框架自动处理，无需手动捕获
@router.get("/example")
@require_permission("admin:delete")
async def example(request: Request):
    # 如果权限不足，会自动返回 403
    # 如果未认证，会自动返回 401
    return {"data": "..."}
```

### 5. 组合使用多个装饰器

可以同时使用多个权限/角色装饰器：

```python
from pyspring.security.authorization import require_permission, require_role

@router.post("/super-admin-action")
@require_role("super_admin")                # 必须是 super_admin 角色
@require_permission("system:critical")      # 同时需要 system:critical 权限
async def super_admin_action(request: Request):
    """超级管理员的关键操作"""
    return {"message": "Critical action completed"}
```

### 6. 性能考虑

权限检查会进行数据库查询，建议：

- 使用 Redis 缓存用户权限（框架已内置）
- 避免在循环中重复检查相同权限
- 对于高频接口，考虑缓存权限检查结果

```python
# ✅ 好的做法：一次检查，多次使用
@router.get("/batch-operation")
@require_permission("user:read")
async def batch_operation(request: Request):
    # 权限已检查，可以安全执行批量操作
    user_ids = [1, 2, 3, 4, 5]
    results = [process_user(uid) for uid in user_ids]
    return {"results": results}


# ❌ 不好的做法：循环中重复检查
async def bad_batch_operation(request: Request):
    user_ids = [1, 2, 3, 4, 5]
    permission_service = ApplicationContext.get_instance().get_by_type(IPermissionService)

    results = []
    for uid in user_ids:
        # 每次循环都检查权限，性能差
        if await permission_service.has_permission(request.state.user_id, "user:read"):
            results.append(process_user(uid))
    return {"results": results}
```

### 7. 白名单配置

公开接口应配置在白名单中，而不是在每个路由上跳过检查：

```yaml
# config/security.yaml
authentication:
  whitelist:
    exact_paths:
      - "/api/auth/login"      # ✅ 登录接口
      - "/api/auth/register"   # ✅ 注册接口
      - "/docs"                # ✅ API 文档
      - "/health"              # ✅ 健康检查
    prefix_paths:
      - "/api/public"          # ✅ 所有 /api/public/* 路径
```

---

## 错误码参考

| HTTP 状态码                      | 场景                          | 说明               |
|-------------------------------|-----------------------------|------------------|
| **401 Unauthorized**          | `request.state.user_id` 不存在 | 用户未认证，需要登录       |
| **403 Forbidden**             | 权限检查失败                      | 用户已认证但权限不足       |
| **500 Internal Server Error** | 无法获取权限服务                    | IoC 容器未初始化或服务未注册 |

---

## 总结

PySpring 提供了三种在 Controller 层使用认证鉴权的方式：

1. **装饰器方式**（推荐）:
    - `@require_permission` - 权限检查
    - `@require_role` - 角色检查
    - `@require_any_permission` - 任意权限
    - `@require_all_permissions` - 所有权限

2. **Request.state 方式**:
    - 直接访问 `request.state.user_id`, `request.state.user_roles`, `request.state.user_permissions`

3. **依赖注入方式**:
    - 手动获取 `IPermissionService` 进行灵活的权限检查

**推荐优先级**: 装饰器 > Request.state > 依赖注入

装饰器方式代码最简洁、最符合 Spring Boot 风格，适合大多数场景。
