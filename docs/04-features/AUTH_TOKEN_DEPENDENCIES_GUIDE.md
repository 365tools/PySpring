# PySpring 认证依赖注入完整指南

## 概述

PySpring提供了三种获取认证用户的方式，适用于不同场景：

| 方式                 | 数据源                  | 适用场景                | 自动抛出401 |
|--------------------|----------------------|---------------------|---------|
| **从request.state** | 中间件注入                | 使用AuthMiddleware的应用 | ❌       |
| **从Token验证**       | Authorization header | 无中间件或自定义认证          | ✅/❌ 可选  |
| **智能回退**           | 两者都尝试                | 混合场景                | ❌       |

---

## 一、从request.state获取（中间件模式）

### 适用场景

✅ 应用已配置AuthMiddleware  
✅ 所有请求都通过统一的认证中间件  
✅ 需要在request.state中注入用户信息

### 使用方式

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_id,
    get_current_user_email,
    get_current_user_roles
)

router = APIRouter()

@router.get("/profile")
async def get_profile(
    user_id: Annotated[int, Depends(get_current_user_id)],
    email: Annotated[str | None, Depends(get_current_user_email)],
    roles: Annotated[list[str], Depends(get_current_user_roles)]
):
    """从中间件注入的request.state获取用户信息"""
    return {
        "user_id": user_id,
        "email": email,
        "roles": roles
    }
```

### 配置要求

```python
from fastapi import FastAPI
from pyspring.security.authentication.web.middleware import AuthMiddleware

app = FastAPI()

# 必须配置认证中间件
app.add_middleware(AuthMiddleware)
```

---

## 二、从Token直接验证获取（Token验证模式）

### 适用场景

✅ 无需使用AuthMiddleware  
✅ 每个路由独立验证Token  
✅ 需要灵活控制认证行为  
✅ **框架级实现，自动集成ITokenService和IUserManagerService**

### 2.1 可选认证（不自动抛出错误）

```python
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_from_token
)

router = APIRouter()

@router.get("/optional-auth")
async def optional_auth(
    user: Annotated[Optional[Any], Depends(get_current_user_from_token)]
):
    """可选认证 - 未认证不会抛出错误"""
    if user:
        return {"authenticated": True, "user": user}
    else:
        return {"authenticated": False, "message": "游客访问"}
```

### 2.2 强制认证（自动抛出401）

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    require_authentication_from_token
)

router = APIRouter()

@router.get("/protected")
async def protected_route(
    user: Annotated[Any, Depends(require_authentication_from_token)]
):
    """强制认证 - 未认证自动抛出401错误"""
    # user一定不为None
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email
    }
```

### 2.3 检查用户状态

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pyspring.security.authentication.web.middleware.dependencies import (
    require_authentication_from_token
)

router = APIRouter()

@router.get("/active-users-only")
async def active_users_only(
    user: Annotated[Any, Depends(require_authentication_from_token)]
):
    """只允许激活用户访问"""
    # require_authentication_from_token已经检查了user.active
    # 如果用户被禁用会自动抛出403错误
    return {"message": "Welcome active user!", "user": user}
```

### 框架集成说明

这些函数会自动使用IoC容器中配置的服务：

```python
# 自动使用的服务
from pyspring.security.authentication.contracts.token import ITokenService
from pyspring.security.authentication.contracts.user import IUserManagerService

# 框架会自动：
# 1. 从IoC容器获取ITokenService
# 2. 调用token_service.verify_token(token)验证Token
# 3. 从payload提取user_id
# 4. 从IoC容器获取IUserManagerService  
# 5. 调用user_service.get_user_by_id(user_id)获取用户
# 6. 返回用户对象
```

### 配置要求

```python
# 只需要配置Token服务和用户服务，无需中间件
from pyspring.security.authentication.services.token.jwt import JWTTokenService
from pyspring.security.authentication.services.user.manager import DefaultUserManagerService

# 服务会自动被IoC容器管理
# dependencies.py会自动发现并使用这些服务
```

---

## 三、智能回退模式

### 适用场景

✅ 同时支持中间件认证和Token认证  
✅ 部分路由使用中间件，部分不使用  
✅ 需要最大灵活性

```python
from typing import Annotated, Optional
from fastapi import APIRouter, Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_with_fallback
)

router = APIRouter()

@router.get("/flexible")
async def flexible_auth(
    user: Annotated[Optional[Any], Depends(get_current_user_with_fallback)]
):
    """
    智能认证 - 自动尝试两种方式：
    1. 优先从request.state获取（中间件）
    2. 失败则从Token验证
    """
    if user:
        return {"authenticated": True, "user": user}
    return {"authenticated": False}
```

---

## 四、使用工厂函数自定义

### 4.1 创建类型别名

```python
from typing import Annotated, Any
from fastapi import Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    token_auth_dependency
)

# 强制认证的用户类型
CurrentUser = Annotated[Any, Depends(token_auth_dependency(auto_error=True))]

# 可选认证的用户类型
OptionalUser = Annotated[Any, Depends(token_auth_dependency(auto_error=False))]

# 在路由中使用
@router.get("/test1")
async def test1(user: CurrentUser):
    """必须认证"""
    return {"user": user}

@router.get("/test2")
async def test2(user: OptionalUser):
    """可选认证"""
    if user:
        return {"user": user}
    return {"guest": True}
```

---

## 五、完整示例项目

### 示例1：纯Token验证模式（无中间件）

```python
"""
纯Token验证模式示例
适用于微服务、API网关等场景
"""
from typing import Annotated, Any
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_from_token,
    require_authentication_from_token
)

app = FastAPI()
router = APIRouter(prefix="/api")

# 注意：这里不使用AuthMiddleware

@router.get("/public")
async def public_endpoint():
    """公开端点 - 无需认证"""
    return {"message": "公开内容"}


@router.get("/optional-auth")
async def optional_auth(
    user: Annotated[Any | None, Depends(get_current_user_from_token)]
):
    """可选认证 - 根据是否认证返回不同内容"""
    if user:
        return {
            "message": f"欢迎回来, {user.username}!",
            "premium_content": "..."
        }
    return {
        "message": "游客访问",
        "limited_content": "..."
    }


@router.get("/protected")
async def protected_endpoint(
    user: Annotated[Any, Depends(require_authentication_from_token)]
):
    """受保护端点 - 强制认证"""
    return {
        "user_id": user.id,
        "username": user.username,
        "data": "敏感数据"
    }


@router.get("/admin")
async def admin_endpoint(
    user: Annotated[Any, Depends(require_authentication_from_token)]
):
    """管理员端点 - 需要认证+角色检查"""
    # 手动检查角色
    if not hasattr(user, 'roles') or 'admin' not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return {"message": "管理员面板"}


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 测试方式

```bash
# 1. 公开端点
curl http://localhost:8000/api/public

# 2. 可选认证（无Token）
curl http://localhost:8000/api/optional-auth

# 3. 可选认证（有Token）
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/optional-auth

# 4. 受保护端点（会返回401）
curl http://localhost:8000/api/protected

# 5. 受保护端点（有Token）
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/protected
```

---

### 示例2：混合模式（中间件+Token验证）

```python
"""
混合模式示例
部分路由使用中间件，部分使用Token验证
"""
from typing import Annotated, Any
from fastapi import FastAPI, APIRouter, Depends
from pyspring.security.authentication.web.middleware import AuthMiddleware
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_id,  # 从中间件
    require_authentication_from_token,  # 从Token
    get_current_user_with_fallback  # 智能回退
)

app = FastAPI()

# 仅对特定路由应用中间件
middleware_router = APIRouter(prefix="/api/v1", tags=["v1-with-middleware"])
token_router = APIRouter(prefix="/api/v2", tags=["v2-token-only"])
flexible_router = APIRouter(prefix="/api/v3", tags=["v3-flexible"])

# V1 API - 使用中间件
@middleware_router.get("/profile")
async def v1_profile(
    user_id: Annotated[int, Depends(get_current_user_id)]
):
    """V1: 从中间件获取用户ID"""
    return {"version": "v1", "user_id": user_id}


# V2 API - 直接Token验证
@token_router.get("/profile")
async def v2_profile(
    user: Annotated[Any, Depends(require_authentication_from_token)]
):
    """V2: 直接从Token验证"""
    return {"version": "v2", "user": user}


# V3 API - 智能回退
@flexible_router.get("/profile")
async def v3_profile(
    user: Annotated[Any | None, Depends(get_current_user_with_fallback)]
):
    """V3: 智能回退 - 优先中间件，失败则Token"""
    if user:
        return {"version": "v3", "user": user}
    return {"version": "v3", "authenticated": False}


# 只对v1路由应用中间件
app.add_middleware(AuthMiddleware, exclude_paths=["/api/v2", "/api/v3"])

app.include_router(middleware_router)
app.include_router(token_router)
app.include_router(flexible_router)
```

---

## 六、对比总结

### 6.1 功能对比

| 依赖函数                                | 数据源           | 返回值        | 失败行为   | 使用场景  |
|-------------------------------------|---------------|------------|--------|-------|
| `get_current_user_id`               | request.state | int        | 抛出401  | 中间件模式 |
| `get_current_user_from_token`       | Token         | User\|None | 返回None | 可选认证  |
| `require_authentication_from_token` | Token         | User       | 抛出401  | 强制认证  |
| `get_current_user_with_fallback`    | 两者            | User\|None | 返回None | 混合模式  |

### 6.2 技术特性对比

| 特性    | 中间件模式       | Token验证模式   |
|-------|-------------|-------------|
| 需要中间件 | ✅ 是         | ❌ 否         |
| 框架集成  | ⭐⭐⭐         | ⭐⭐⭐⭐⭐       |
| 性能    | ⭐⭐⭐⭐⭐ (已验证) | ⭐⭐⭐⭐ (每次验证) |
| 灵活性   | ⭐⭐⭐         | ⭐⭐⭐⭐⭐       |
| 适用场景  | 单体应用        | 微服务/API     |

### 6.3 使用建议

**推荐使用Token验证模式的场景：**

- ✅ 微服务架构
- ✅ API网关
- ✅ 无状态RESTful API
- ✅ 需要灵活的认证策略
- ✅ 不同路由需要不同认证方式

**推荐使用中间件模式的场景：**

- ✅ 传统Web应用
- ✅ 所有请求都需要认证
- ✅ 统一的认证处理
- ✅ 性能敏感场景（避免重复验证）

---

## 七、最佳实践

### 7.1 定义类型别名

```python
# dependencies.py
from typing import Annotated, Any, Optional
from fastapi import Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    require_authentication_from_token,
    get_current_user_from_token
)

# 强制认证用户
AuthenticatedUser = Annotated[Any, Depends(require_authentication_from_token)]

# 可选认证用户
OptionalAuthenticatedUser = Annotated[Optional[Any], Depends(get_current_user_from_token)]

# 在路由中使用
@router.get("/test")
async def test(user: AuthenticatedUser):
    return {"user": user}
```

### 7.2 组合依赖

```python
from typing import Annotated
from fastapi import Depends, HTTPException, status

async def get_admin_user(
    user: Annotated[Any, Depends(require_authentication_from_token)]
) -> Any:
    """要求用户必须是管理员"""
    if not hasattr(user, 'roles') or 'admin' not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user

# 使用
AdminUser = Annotated[Any, Depends(get_admin_user)]

@router.get("/admin/dashboard")
async def dashboard(user: AdminUser):
    return {"admin": user}
```

### 7.3 错误处理

```python
from fastapi import HTTPException, status

@router.get("/custom-error")
async def custom_error(
    user: Annotated[Any | None, Depends(get_current_user_from_token)]
):
    """自定义错误处理"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if hasattr(user, 'subscription') and user.subscription != 'premium':
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="此功能需要Premium订阅"
        )
    
    return {"premium_feature": "..."}
```

---

## 八、迁移指南

### 从自定义实现迁移到框架实现

#### 旧代码（自定义）

```python
from fastapi import Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(
    credentials = Depends(security),
    auth_service = Depends(lambda: Inject(AuthService))
):
    token = credentials.credentials
    user = await auth_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401)
    return user
```

#### 新代码（框架）

```python
from typing import Annotated
from fastapi import Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    require_authentication_from_token
)

# 直接使用框架提供的依赖
AuthenticatedUser = Annotated[Any, Depends(require_authentication_from_token)]

@router.get("/test")
async def test(user: AuthenticatedUser):
    return {"user": user}
```

**优势：**

- ✅ 无需手动管理AuthService
- ✅ 自动集成ITokenService和IUserManagerService
- ✅ 自动处理异常和错误
- ✅ 支持多种Token提供者

---

## 九、常见问题

### Q1: 如何选择使用哪种模式？

**A**:

- 如果你的应用使用了AuthMiddleware → 使用`get_current_user_id`等中间件模式
- 如果你不想用中间件或需要更灵活的控制 → 使用`require_authentication_from_token`
- 如果两种场景都有 → 使用`get_current_user_with_fallback`

### Q2: Token验证模式会影响性能吗？

**A**: 会有轻微影响，因为每个请求都会验证Token。但优势是：

- 无状态，易于水平扩展
- 不依赖中间件
- 更灵活的认证策略

如果性能敏感，建议：

- 使用中间件模式（只验证一次）
- 或使用Redis缓存Token验证结果

### Q3: 可以同时使用两种模式吗？

**A**: 可以！使用`get_current_user_with_fallback`会自动尝试两种方式。

### Q4: 如何扩展支持自定义Token提供者？

**A**: 只需实现`ITokenService`接口并注册到IoC容器，框架会自动使用：

```python
from pyspring.ioc.annotations import Component
from pyspring.security.authentication.contracts.token import ITokenService

@Component()
class MyCustomTokenService(ITokenService):
    async def verify_token(self, token: str):
        # 自定义验证逻辑
        pass
    
# 框架会自动使用你的实现
```

---

## 十、参考文档

- [认证中间件文档](./AUTH_MIDDLEWARE_GUIDE.md)
- [Token服务文档](./TOKEN_SERVICE_GUIDE.md)
- [用户管理服务文档](./USER_SERVICE_GUIDE.md)
