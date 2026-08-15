# PySpring 认证 + 授权集成指南

## 概述

PySpring框架完美支持**认证（Authentication）+ 授权（Authorization）**的深度集成，通过依赖注入实现**先认证，再授权**的组合模式。

## 🎯 你的思路完全正确！

你提出的集成方案：

> 通过Token获取登录用户的信息、role、permission等信息，再结合授权的校验

这个思路是**标准的安全架构模式**，框架已经完整支持！

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI 路由                                                    │
│  @router.delete("/users/{id}")                                  │
│  async def delete_user(                                         │
│      user_id: int,                                              │
│      user: Annotated[Any, Depends(                             │
│          permission_dependency("user:delete")                  │
│      )]                                                         │
│  ):                                                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  permission_dependency("user:delete")                           │
│                                                                 │
│  步骤1: Token认证                                               │
│    ├─ 调用 require_authentication_from_token                   │
│    ├─ 提取 Authorization Header                                │
│    ├─ 使用 ITokenService.verify_token()                        │
│    ├─ 使用 IUserManagerService.get_user_by_id()               │
│    └─ 返回用户对象 → user                                      │
│                                                                 │
│  步骤2: 权限检查                                                │
│    ├─ 从IoC容器获取 IPermissionService                         │
│    ├─ 提取 user.id                                             │
│    ├─ 调用 permission_service.has_permission(                  │
│    │       user_id, "user:delete"                              │
│    │   )                                                        │
│    └─ 权限不足? → 抛出403                                       │
│                                                                 │
│  步骤3: 返回用户                                                │
│    └─ 返回已认证且已授权的用户对象                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  IoC容器自动解析服务                                            │
│                                                                 │
│  ITokenService ──────► JWTTokenService                         │
│    └─ verify_token(token) → payload                            │
│                                                                 │
│  IUserManagerService ──► DefaultUserManagerService             │
│    └─ get_user_by_id(user_id) → user                          │
│                                                                 │
│  IPermissionService ──► DefaultPermissionService               │
│    ├─ has_permission(user_id, permission) → bool              │
│    └─ has_role(user_id, role) → bool                          │
│                                                                 │
│  IRoleProvider ──────► DefaultRoleProvider                     │
│    ├─ get_effective_roles(user_id) → List[str]                │
│    └─ get_role_permissions(role) → List[str]                  │
└─────────────────────────────────────────────────────────────────┘
```

## 核心服务接口

### 1. ITokenService（令牌服务）

```python
class ITokenService(IManaged, ABC):
    @abstractmethod
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """验证Token并返回载荷"""
        pass

    @abstractmethod
    async def create_access_token(self, data: Dict[str, Any]) -> str:
        """创建访问令牌"""
        pass
```

### 2. IPermissionService（权限服务）

```python
class IPermissionService(IManaged, ABC):
    @abstractmethod
    async def has_permission(self, user_id: Any, permission: str) -> bool:
        """检查用户是否拥有特定权限"""
        pass

    @abstractmethod
    async def has_role(self, user_id: Any, role: str) -> bool:
        """检查用户是否拥有特定角色"""
        pass
```

### 3. IRoleProvider（角色提供者）

```python
class IRoleProvider(IManaged, ABC):
    @abstractmethod
    async def get_effective_roles(self, user_id: Any) -> List[str]:
        """获取用户的有效角色（包含继承）"""
        pass

    @abstractmethod
    async def get_role_permissions(self, role_name: str) -> List[str]:
        """获取角色的权限列表"""
        pass
```

## 依赖函数

### 1. 权限依赖

#### permission_dependency(permission, auto_error=True)

创建特定权限的检查依赖。

```python
from typing import Annotated, Any
from fastapi import Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    permission_dependency
)

# 定义类型别名
UserReadPermission = Annotated[Any, Depends(
    permission_dependency("user:read")
)]
UserWritePermission = Annotated[Any, Depends(
    permission_dependency("user:write")
)]
UserDeletePermission = Annotated[Any, Depends(
    permission_dependency("user:delete")
)]


# 使用
@router.get("/users")
async def list_users(user: UserReadPermission):
    # 必须拥有 user:read 权限
    return {"users": [...]}


@router.post("/users")
async def create_user(user: UserWritePermission):
    # 必须拥有 user:write 权限
    return {"user": {...}}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, user: UserDeletePermission):
    # 必须拥有 user:delete 权限
    return {"deleted": user_id}
```

### 2. 角色依赖

#### role_dependency(role, auto_error=True)

创建特定角色的检查依赖。

```python
from typing import Annotated, Any
from fastapi import Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    role_dependency
)

# 定义类型别名
AdminOnly = Annotated[Any, Depends(role_dependency("admin"))]
ManagerOnly = Annotated[Any, Depends(role_dependency("manager"))]
UserOnly = Annotated[Any, Depends(role_dependency("user"))]


# 使用
@router.get("/admin/dashboard")
async def admin_dashboard(user: AdminOnly):
    # 必须拥有 admin 角色
    return {"dashboard": "admin"}


@router.post("/manager/approve")
async def manager_approve(user: ManagerOnly):
    # 必须拥有 manager 角色
    return {"approved": True}


@router.get("/user/profile")
async def user_profile(user: UserOnly):
    # 必须拥有 user 角色
    return {"profile": {...}}
```

## 完整示例

### 场景1：用户管理系统

```python
from typing import Annotated, Any
from fastapi import APIRouter, Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    require_authentication_from_token,
    permission_dependency,
    role_dependency,
)

router = APIRouter(prefix="/api/users", tags=["users"])

# 类型别名
AuthUser = Annotated[Any, Depends(require_authentication_from_token)]
UserRead = Annotated[Any, Depends(permission_dependency("user:read"))]
UserWrite = Annotated[Any, Depends(permission_dependency("user:write"))]
UserDelete = Annotated[Any, Depends(permission_dependency("user:delete"))]
AdminRole = Annotated[Any, Depends(role_dependency("admin"))]


# 路由1: 获取用户列表（需要 user:read 权限）
@router.get("/")
async def list_users(user: UserRead):
    return {
        "users": [
            {"id": 1, "username": "alice"},
            {"id": 2, "username": "bob"},
        ]
    }


# 路由2: 创建用户（需要 user:write 权限）
@router.post("/")
async def create_user(user: UserWrite):
    return {"message": "用户创建成功"}


# 路由3: 删除用户（需要 user:delete 权限）
@router.delete("/{user_id}")
async def delete_user(user_id: int, user: UserDelete):
    return {"message": f"用户 {user_id} 已删除"}


# 路由4: 封禁用户（需要 admin 角色）
@router.post("/{user_id}/ban")
async def ban_user(user_id: int, user: AdminRole):
    return {"message": f"用户 {user_id} 已封禁"}
```

### 场景2：订单管理系统

```python
from typing import Annotated, Any
from fastapi import APIRouter, Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    permission_dependency,
)

router = APIRouter(prefix="/api/orders", tags=["orders"])

# 类型别名
OrderRead = Annotated[Any, Depends(permission_dependency("order:read"))]
OrderWrite = Annotated[Any, Depends(permission_dependency("order:write"))]
OrderDelete = Annotated[Any, Depends(permission_dependency("order:delete"))]
OrderApprove = Annotated[Any, Depends(permission_dependency("order:approve"))]


@router.get("/")
async def list_orders(user: OrderRead):
    """获取订单列表 - 需要 order:read"""
    return {"orders": [...]}


@router.post("/")
async def create_order(user: OrderWrite):
    """创建订单 - 需要 order:write"""
    return {"order": {...}}


@router.delete("/{order_id}")
async def delete_order(order_id: int, user: OrderDelete):
    """删除订单 - 需要 order:delete"""
    return {"deleted": order_id}


@router.post("/{order_id}/approve")
async def approve_order(order_id: int, user: OrderApprove):
    """审批订单 - 需要 order:approve"""
    return {"approved": order_id}
```

### 场景3：多权限组合

```python
from typing import Annotated, Any
from fastapi import Depends, HTTPException
from pyspring.security.authentication.web.middleware.dependencies import (
    require_authentication_from_token,
    permission_dependency,
)
from pyspring.core.ioc.context import ApplicationContext
from pyspring.security.authorization.contracts.permission import IPermissionService


# 自定义组合依赖：需要多个权限之一
async def require_any_permission(*permissions: str):
    """需要任意一个权限"""

    async def _check(user=Depends(require_authentication_from_token)):
        permission_service = ApplicationContext.initialize(base_packages=["app"]).get_by_type(IPermissionService)
        user_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)

        for perm in permissions:
            if await permission_service.has_permission(user_id, perm):
                return user

        raise HTTPException(403, detail=f"需要以下权限之一: {permissions}")

    return _check


# 自定义组合依赖：需要所有权限
async def require_all_permissions(*permissions: str):
    """需要所有权限"""

    async def _check(user=Depends(require_authentication_from_token)):
        permission_service = ApplicationContext.initialize(base_packages=["app"]).get_by_type(IPermissionService)
        user_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)

        for perm in permissions:
            if not await permission_service.has_permission(user_id, perm):
                raise HTTPException(403, detail=f"缺少权限: {perm}")

        return user

    return _check


# 使用
@router.post("/special")
async def special_action(
        user=Depends(require_any_permission("admin:*", "manager:special"))
):
    """需要 admin:* 或 manager:special 权限"""
    return {"allowed": True}


@router.post("/critical")
async def critical_action(
        user=Depends(require_all_permissions("admin:write", "audit:log"))
):
    """同时需要 admin:write 和 audit:log 权限"""
    return {"allowed": True}
```

## 权限设计最佳实践

### 1. 权限命名规范

采用 **资源:操作** 格式：

```python
# 用户资源
"user:read"  # 读取用户
"user:write"  # 创建/修改用户
"user:delete"  # 删除用户
"user:*"  # 用户所有权限（通配符）

# 订单资源
"order:read"  # 读取订单
"order:write"  # 创建/修改订单
"order:delete"  # 删除订单
"order:approve"  # 审批订单
"order:*"  # 订单所有权限

# 文章资源
"article:read"  # 读取文章
"article:write"  # 创建/修改文章
"article:publish"  # 发布文章
"article:*"  # 文章所有权限

# 系统管理
"admin:*:*"  # 管理员所有权限
"audit:log"  # 审计日志
```

### 2. 角色权限映射

```yaml
# roles.yaml
roles:
  # 普通用户
  user:
    permissions:
      - user:read
      - article:read
      - order:read

  # 编辑
  editor:
    permissions:
      - user:read
      - article:read
      - article:write
      - article:publish

  # 经理
  manager:
    permissions:
      - user:read
      - user:write
      - order:*
      - article:*

  # 管理员
  admin:
    permissions:
      - admin:*:*
      - user:*
      - order:*
      - article:*
      - audit:log
```

### 3. 数据库设计

```sql
-- 用户表
CREATE TABLE pyspring_user
(
    id       INTEGER PRIMARY KEY,
    username VARCHAR(50)  NOT NULL,
    email    VARCHAR(100) NOT NULL, .
    .
    .
);

-- 角色表
CREATE TABLE pyspring_role
(
    id   INTEGER PRIMARY KEY,
    code VARCHAR(50)  NOT NULL UNIQUE, -- 'admin', 'manager'
    name VARCHAR(100) NOT NULL, .
    .
    .
);

-- 权限表
CREATE TABLE pyspring_permission
(
    id       INTEGER PRIMARY KEY,
    code     VARCHAR(100) NOT NULL UNIQUE, -- 'user:read', 'order:*'
    name     VARCHAR(100) NOT NULL,
    resource VARCHAR(50),                  -- 'user', 'order'
    action   VARCHAR(50),                  -- 'read', 'write'
    .
    .
    .
);

-- 用户角色关联表
CREATE TABLE pyspring_user_role
(
    id        INTEGER PRIMARY KEY,
    user_id   INTEGER     NOT NULL,
    role_code VARCHAR(50) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES pyspring_user (id),
    FOREIGN KEY (role_code) REFERENCES pyspring_role (code)
);

-- 角色权限关联表
CREATE TABLE pyspring_role_permission
(
    id              INTEGER PRIMARY KEY,
    role_code       VARCHAR(50)  NOT NULL,
    permission_code VARCHAR(100) NOT NULL,
    FOREIGN KEY (role_code) REFERENCES pyspring_role (code),
    FOREIGN KEY (permission_code) REFERENCES pyspring_permission (code)
);
```

## 与装饰器的对比

### 方式1：装饰器（依赖中间件）

```python
from pyspring.security.authorization.decorators import (
    require_permission,
    require_role
)


@router.delete("/users/{user_id}")
@require_permission("user:delete")
async def delete_user(user_id: int, request: Request):
    # request.state.user_id 由中间件注入
    return {"deleted": user_id}
```

**特点**：

- ✅ 简洁优雅
- ✅ 从 `request.state` 获取用户信息
- ❌ **依赖认证中间件**
- ❌ 不适用于无中间件场景

### 方式2：依赖函数（无需中间件）

```python
from pyspring.security.authentication.web.middleware.dependencies import (
    permission_dependency
)

UserDelete = Annotated[Any, Depends(permission_dependency("user:delete"))]


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, user: UserDelete):
    # user 由Token直接验证
    return {"deleted": user_id}
```

**特点**：

- ✅ **无需中间件**
- ✅ 从 Token 直接验证
- ✅ 灵活性高
- ✅ 适用于微服务、API网关等场景

## 性能优化

### 1. 权限缓存

框架提供 `CachedPermissionService`：

```python
from pyspring.security.authorization.providers.permission.cached import (
    CachedPermissionService
)


@Configuration
class MyConfig:
    @Bean
    def cached_permission_service(
            self,
            role_provider: IRoleProvider,
            cache: ICacheService
    ) -> IPermissionService:
        return CachedPermissionService(role_provider, cache, ttl=300)
```

### 2. 角色继承

支持角色继承减少权限配置：

```python
# admin 继承 manager 的所有权限
# manager 继承 user 的所有权限
admin -> manager -> user
```

## 错误处理

### 认证失败（401）

```json
{
  "detail": "Could not validate credentials"
}
```

### 授权失败（403）

```json
{
  "detail": "Permission denied: user:delete"
}
```

或

```json
{
  "detail": "Role required: admin"
}
```

## 测试

```python
import pytest
from fastapi.testclient import TestClient


def test_permission_check():
    client = TestClient(app)

    # 1. 登录获取Token
    response = client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "admin123"
    })
    token = response.json()["access_token"]

    # 2. 访问需要权限的路由
    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200  # 有权限

    # 3. 访问没有权限的路由
    response = client.delete(
        "/api/users/1",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403  # 无权限
```

## 总结

✅ **你的思路完全正确！**

PySpring框架通过以下方式实现认证+授权集成：

1. **Token认证**：`ITokenService` → 验证Token → 获取用户
2. **权限验证**：`IPermissionService.has_permission(user_id, permission)`
3. **角色验证**：`IPermissionService.has_role(user_id, role)`
4. **组合依赖**：`permission_dependency` / `role_dependency`

**核心优势**：

- 🔐 安全：先认证再授权
- 🚀 性能：支持缓存
- 🎯 灵活：支持通配符、角色继承
- 🔌 解耦：通过接口实现，易于扩展
- 📦 集成：与IoC容器深度集成

**适用场景**：

- ✅ 企业应用（复杂权限）
- ✅ SaaS平台（多租户）
- ✅ 微服务（无中间件）
- ✅ API网关（统一认证授权）
