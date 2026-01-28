# PySpring认证依赖方案对比

## 概述

你的问题提出了一个很好的想法：**将从Token获取用户信息的功能集成到框架中，并与令牌提供者深度整合**。

我已经完成了这个集成！以下是详细说明。

---

## ✅ 你的需求

### 原始代码（自定义实现）

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(lambda: Inject(AuthService))
) -> User:
    """从令牌获取用户信息"""
    token = credentials.credentials
    user = await auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user
```

### 你的期望

1. ✅ 添加到框架的默认实现
2. ✅ 集成到令牌提供者
3. ✅ 支持多种令牌提供者，自动匹配
4. ✅ 依托框架令牌提供者的多样性

---

## ✅ 框架实现（已完成）

### 新的框架函数

```python
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_from_token,        # 可选认证（不自动抛出错误）
    require_authentication_from_token,  # 强制认证（自动抛出401）
    get_current_user_with_fallback,     # 智能回退
    token_auth_dependency                # 工厂函数
)
```

### 框架集成点

#### 1. 自动使用 ITokenService

```python
# 框架会自动从IoC容器获取
from pyspring.security.authentication.contracts.token import ITokenService

token_service = ApplicationContext.get_instance().get_by_type(ITokenService)
```

#### 2. 自动使用 IUserManagerService

```python
# 框架会自动从IoC容器获取
from pyspring.security.authentication.contracts.user import IUserManagerService

user_service = ApplicationContext.get_instance().get_by_type(IUserManagerService)
```

#### 3. 支持多种令牌提供者

框架通过 `ITokenService` 接口自动适配：

```python
# JWT提供者
from pyspring.security.authentication.services.token.jwt import JWTTokenService

# Session提供者（如果有）
from pyspring.security.authentication.services.token.session import SessionTokenService

# API Key提供者（如果有）
from pyspring.security.authentication.services.token.apikey import APIKeyTokenService

# 框架自动使用注册的实现，无需修改依赖函数
```

---

## 📊 对比分析

### 方案对比

| 特性        | 自定义实现                | 框架实现（新）                       |
|-----------|----------------------|-------------------------------|
| **集成度**   | ⭐⭐ 需要手动注入AuthService | ⭐⭐⭐⭐⭐ 自动使用ITokenService       |
| **令牌提供者** | ❌ 绑定到AuthService     | ✅ 支持所有ITokenService实现         |
| **用户服务**  | ⭐⭐ 通过AuthService     | ⭐⭐⭐⭐⭐ 自动使用IUserManagerService |
| **错误处理**  | ⭐⭐⭐ 手动处理             | ⭐⭐⭐⭐⭐ 统一错误处理                  |
| **灵活性**   | ⭐⭐⭐                  | ⭐⭐⭐⭐⭐ 多种模式                    |
| **代码复用**  | ⭐⭐                   | ⭐⭐⭐⭐⭐                         |

### 使用对比

#### 旧方式（自定义）

```python
# 需要手动定义
async def get_current_user(
    credentials = Depends(security),
    auth_service = Depends(lambda: Inject(AuthService))
):
    # 手动实现所有逻辑
    token = credentials.credentials
    user = await auth_service.get_current_user(token)
    if not user:
        raise HTTPException(...)
    return user

# 使用
@router.get("/test")
async def test(user: User = Depends(get_current_user)):
    return {"user": user}
```

#### 新方式（框架）

```python
# 直接使用框架提供的依赖
from typing import Annotated
from fastapi import Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    require_authentication_from_token
)

AuthenticatedUser = Annotated[Any, Depends(require_authentication_from_token)]

# 使用
@router.get("/test")
async def test(user: AuthenticatedUser):
    return {"user": user}
```

---

## 🎯 架构设计

### 完整的集成流程

```
┌─────────────────────────────────────────────────────────────┐
│  FastAPI路由                                                │
│  @router.get("/protected")                                  │
│  async def protected(                                       │
│      user: Annotated[Any, Depends(                         │
│          require_authentication_from_token                 │
│      )]                                                     │
│  ):                                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  dependencies.py                                            │
│  require_authentication_from_token()                        │
│    ├─ 提取 Authorization Header                            │
│    ├─ 调用 ApplicationContext.get_by_type(ITokenService)   │
│    ├─ 调用 token_service.verify_token(token)               │
│    ├─ 提取 payload["sub"] (user_id)                        │
│    ├─ 调用 ApplicationContext.get_by_type(                 │
│    │       IUserManagerService)                            │
│    ├─ 调用 user_service.get_user_by_id(user_id)           │
│    └─ 返回用户对象                                         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│  IoC容器自动解析                                           │
│                                                            │
│  ITokenService  ──────►  JWTTokenService                  │
│                          │                                 │
│                          ├─ encode()                       │
│                          ├─ decode()                       │
│                          └─ verify_token()  ◄──────┐      │
│                                                     │      │
│  IUserManagerService ──►  DefaultUserManagerService│      │
│                          │                          │      │
│                          ├─ get_user_by_id()  ◄────┤      │
│                          └─ get_user_by_email()     │      │
│                                                     │      │
│  自动使用IoC容器中注册的实现  ◄────────────────────┘      │
└────────────────────────────────────────────────────────────┘
```

### 令牌提供者扩展性

```python
# 1. JWT令牌提供者（默认）
@Component
class JWTTokenService(ITokenService):
    async def verify_token(self, token: str):
        # JWT验证逻辑
        pass

# 2. Session令牌提供者（可选）
@Component
class SessionTokenService(ITokenService):
    async def verify_token(self, token: str):
        # Session验证逻辑
        pass

# 3. API Key提供者（可选）
@Component
class APIKeyTokenService(ITokenService):
    async def verify_token(self, token: str):
        # API Key验证逻辑
        pass

# 4. 多租户令牌提供者（自定义）
@Component
class MultiTenantTokenService(ITokenService):
    async def verify_token(self, token: str):
        # 多租户验证逻辑
        pass

# 框架的dependencies.py会自动使用注册的实现
# 无需修改任何依赖函数代码！
```

---

## 💡 高级功能

### 1. 智能回退机制

```python
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_with_fallback
)

@router.get("/flexible")
async def flexible(
    user = Depends(get_current_user_with_fallback)
):
    """
    智能回退：
    1. 先尝试从 request.state 获取（中间件）
    2. 失败则从 Token 验证
    """
    pass
```

### 2. 工厂函数自定义

```python
from pyspring.security.authentication.web.middleware.dependencies import (
    token_auth_dependency
)

# 创建自定义认证依赖
StrictAuth = Annotated[Any, Depends(token_auth_dependency(auto_error=True))]
OptionalAuth = Annotated[Any, Depends(token_auth_dependency(auto_error=False))]

@router.get("/test1")
async def test1(user: StrictAuth):
    # 强制认证
    pass

@router.get("/test2")
async def test2(user: OptionalAuth):
    # 可选认证
    pass
```

### 3. 组合依赖

```python
async def get_admin_user(
    user: Annotated[Any, Depends(require_authentication_from_token)]
) -> Any:
    """组合依赖：先认证，再检查角色"""
    if 'admin' not in getattr(user, 'roles', []):
        raise HTTPException(403, detail="需要管理员权限")
    return user

AdminUser = Annotated[Any, Depends(get_admin_user)]

@router.get("/admin")
async def admin_only(user: AdminUser):
    # 只有管理员可访问
    pass
```

---

## 🚀 迁移路径

### Step 1: 保持现有实现（向后兼容）

```python
# 你的现有代码继续工作
async def get_current_user(...):
    # 自定义实现
    pass

@router.get("/old")
async def old_route(user = Depends(get_current_user)):
    pass
```

### Step 2: 渐进式迁移

```python
# 新路由使用框架实现
from pyspring.security.authentication.web.middleware.dependencies import (
    require_authentication_from_token
)

@router.get("/new")
async def new_route(
    user: Annotated[Any, Depends(require_authentication_from_token)]
):
    pass
```

### Step 3: 完全迁移

```python
# 删除自定义实现，全部使用框架
from typing import Annotated
from fastapi import Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    require_authentication_from_token
)

# 定义全局类型别名
AuthenticatedUser = Annotated[Any, Depends(require_authentication_from_token)]

# 所有路由使用统一类型
@router.get("/route1")
async def route1(user: AuthenticatedUser):
    pass

@router.get("/route2")
async def route2(user: AuthenticatedUser):
    pass
```

---

## 📋 总结

### ✅ 你的想法已经实现

| 需求        | 实现状态 | 说明                                    |
|-----------|------|---------------------------------------|
| 集成到框架     | ✅ 完成 | `dependencies.py` 已添加                 |
| 与令牌提供者集成  | ✅ 完成 | 自动使用 `ITokenService`                  |
| 支持多种令牌提供者 | ✅ 完成 | 通过IoC容器自动适配                           |
| 自动匹配      | ✅ 完成 | 依赖注入自动解析                              |
| 提取令牌信息    | ✅ 完成 | `verify_token()` → `get_user_by_id()` |

### 🎯 优势

1. **框架级集成** - 与PySpring认证体系深度整合
2. **自动适配** - 支持所有ITokenService实现
3. **多种模式** - 可选认证、强制认证、智能回退
4. **易于扩展** - 添加新令牌提供者无需修改依赖代码
5. **类型安全** - 使用Annotated提供清晰的类型提示

### 📚 相关文档

- [完整使用指南](./AUTH_TOKEN_DEPENDENCIES_GUIDE.md)
- [示例代码](../examples/example_token_auth_dependencies.py)
- [快速参考](./AUTH_DEPENDENCIES_QUICKREF.md)

---

**你的建议非常合理且已经完全实现！** 🎉
