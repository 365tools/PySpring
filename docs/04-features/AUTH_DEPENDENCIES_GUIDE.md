# 认证依赖注入使用指南

## 概述

PySpring提供了两种方式在FastAPI路由中获取认证信息：

1. **AuthUtils工具类** - 在路由函数内部使用
2. **依赖函数** - 通过FastAPI的Depends注入（推荐）

---

## 方案对比

### ❌ 不推荐：直接使用AuthUtils

```python
from fastapi import APIRouter, Request
from pyspring.security.authentication.web.middleware.utils import AuthUtils

router = APIRouter()

@router.get("/profile")
async def get_profile(request: Request):
    # 需要手动调用AuthUtils
    user_id = AuthUtils.get_current_user_id(request)
    email = AuthUtils.get_current_user_email(request)
    
    return {
        "user_id": user_id,
        "email": email
    }
```

**缺点**：

- 每次都需要传递`request`参数
- 代码重复，不够简洁
- 难以复用和测试

---

### ✅ 推荐：使用依赖函数

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
    return {
        "user_id": user_id,
        "email": email,
        "roles": roles
    }
```

**优点**：

- ✅ 符合FastAPI最佳实践
- ✅ 代码简洁，依赖清晰
- ✅ 易于测试和Mock
- ✅ 自动错误处理

---

## 详细用法示例

### 1. 获取用户ID

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from pyspring.security.authentication.web.middleware.dependencies import get_current_user_id

router = APIRouter()

@router.get("/my-data")
async def get_my_data(
    user_id: Annotated[int, Depends(get_current_user_id)]
):
    """只需要用户ID"""
    return {"user_id": user_id, "data": "..."}
```

---

### 2. 获取多个认证信息

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
async def get_full_profile(
    user_id: Annotated[int, Depends(get_current_user_id)],
    email: Annotated[str | None, Depends(get_current_user_email)],
    roles: Annotated[list[str], Depends(get_current_user_roles)]
):
    """获取完整用户信息"""
    return {
        "user_id": user_id,
        "email": email,
        "roles": roles
    }
```

---

### 3. 角色权限检查

#### 方式1：要求单个角色

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_id,
    require_role
)

router = APIRouter()

@router.get("/admin/dashboard")
async def admin_dashboard(
    user_id: Annotated[int, Depends(get_current_user_id)],
    _: Annotated[None, Depends(require_role("admin"))]  # 要求admin角色
):
    """仅管理员可访问"""
    return {"message": "Admin Dashboard"}
```

#### 方式2：要求任意角色

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_id,
    require_any_role
)

router = APIRouter()

@router.get("/staff/panel")
async def staff_panel(
    user_id: Annotated[int, Depends(get_current_user_id)],
    _: Annotated[None, Depends(require_any_role(["admin", "moderator", "staff"]))]
):
    """管理员、版主、员工可访问"""
    return {"message": "Staff Panel"}
```

---

### 4. 组合使用

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_id,
    get_current_user_roles,
    require_role
)

router = APIRouter()

@router.post("/articles")
async def create_article(
    user_id: Annotated[int, Depends(get_current_user_id)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    _: Annotated[None, Depends(require_role("author"))],  # 必须是作者
    title: str,
    content: str
):
    """创建文章 - 需要author角色"""
    return {
        "author_id": user_id,
        "author_roles": roles,
        "title": title,
        "content": content
    }
```

---

### 5. 获取Token载荷

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from pyspring.security.authentication.web.middleware.dependencies import get_token_payload

router = APIRouter()

@router.get("/token-info")
async def get_token_info(
    payload: Annotated[dict, Depends(get_token_payload)]
):
    """查看Token完整载荷"""
    return {
        "sub": payload.get("sub"),
        "exp": payload.get("exp"),
        "iat": payload.get("iat"),
        "custom_claims": payload
    }
```

---

## 完整示例

```python
"""
用户管理API示例
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_id,
    get_current_user_email,
    get_current_user_roles,
    require_role,
    require_any_role
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me")
async def get_current_user(
    user_id: Annotated[int, Depends(get_current_user_id)],
    email: Annotated[str | None, Depends(get_current_user_email)],
    roles: Annotated[list[str], Depends(get_current_user_roles)]
):
    """获取当前用户信息"""
    return {
        "id": user_id,
        "email": email,
        "roles": roles
    }


@router.get("/me/profile")
async def get_my_profile(
    user_id: Annotated[int, Depends(get_current_user_id)]
):
    """获取我的详细资料"""
    # 从数据库查询用户详细信息
    return {
        "user_id": user_id,
        "profile": "..."
    }


@router.put("/me/email")
async def update_my_email(
    user_id: Annotated[int, Depends(get_current_user_id)],
    new_email: str
):
    """更新我的邮箱"""
    # 更新邮箱逻辑
    return {
        "user_id": user_id,
        "new_email": new_email,
        "message": "邮箱更新成功"
    }


@router.get("/admin/all")
async def list_all_users(
    _: Annotated[None, Depends(require_role("admin"))],  # 只有admin可访问
    skip: int = 0,
    limit: int = 10
):
    """列出所有用户（仅管理员）"""
    return {
        "users": [],
        "skip": skip,
        "limit": limit
    }


@router.delete("/{target_user_id}")
async def delete_user(
    target_user_id: int,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    _: Annotated[None, Depends(require_any_role(["admin", "moderator"]))]
):
    """删除用户（管理员或版主）"""
    if target_user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    # 删除逻辑
    return {"message": f"用户 {target_user_id} 已删除"}


@router.post("/staff/promote/{target_user_id}")
async def promote_user(
    target_user_id: int,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    current_roles: Annotated[list[str], Depends(get_current_user_roles)],
    _: Annotated[None, Depends(require_role("admin"))]
):
    """提升用户权限（仅管理员）"""
    return {
        "promoted_by": current_user_id,
        "promoter_roles": current_roles,
        "target_user": target_user_id,
        "message": "权限提升成功"
    }
```

---

## 混合使用场景

有时你可能需要在同一个路由中同时使用依赖注入和直接调用：

```python
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from pyspring.security.authentication.web.middleware.dependencies import get_current_user_id
from pyspring.security.authentication.web.middleware.utils import AuthUtils

router = APIRouter()

@router.get("/complex")
async def complex_operation(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)]  # 依赖注入获取ID
):
    """复杂操作 - 混合使用"""
    
    # 通过依赖已经获取了user_id
    print(f"User ID from Depends: {user_id}")
    
    # 如果需要在路由内部动态检查角色
    if AuthUtils.has_role(request, "premium"):
        # premium用户的特殊逻辑
        pass
    
    # 获取完整的token载荷
    payload = AuthUtils.get_token_payload(request)
    
    return {
        "user_id": user_id,
        "has_premium": AuthUtils.has_role(request, "premium"),
        "payload_keys": list(payload.keys())
    }
```

---

## 测试建议

使用依赖函数使测试更容易：

```python
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from typing import Annotated

# 创建测试用的override依赖
def override_get_current_user_id():
    return 123  # 测试用户ID

app = FastAPI()

# 在测试中override依赖
from pyspring.security.authentication.web.middleware.dependencies import get_current_user_id

app.dependency_overrides[get_current_user_id] = override_get_current_user_id

@app.get("/test")
async def test_route(user_id: Annotated[int, Depends(get_current_user_id)]):
    return {"user_id": user_id}

def test_authenticated_route():
    client = TestClient(app)
    response = client.get("/test")
    assert response.json() == {"user_id": 123}
```

---

## 总结

### 推荐做法

✅ **使用依赖函数**：

```python
user_id: Annotated[int, Depends(get_current_user_id)]
```

### 不推荐做法

❌ **直接在路由中调用AuthUtils**：

```python
async def route(request: Request):
    user_id = AuthUtils.get_current_user_id(request)
```

❌ **尝试这样使用（不符合FastAPI约定）**：

```python
user_id: Annotated[int, Depends(AuthUtils.get_current_user_id)]  # Request参数会自动注入，但不优雅
```

### 最佳实践

1. 优先使用 `dependencies.py` 中的依赖函数
2. 在路由签名中明确声明需要的认证信息
3. 使用类型注解和`Annotated`提高代码可读性
4. 权限检查使用 `require_role` 和 `require_any_role`
5. 复杂逻辑可以混合使用依赖注入和AuthUtils工具类
