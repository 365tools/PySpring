# 认证依赖快速参考

## ✅ 推荐用法

### 基本导入

```python
from typing import Annotated
from fastapi import Depends
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_id,  # 获取用户ID
    get_current_user_email,  # 获取用户邮箱
    get_current_user_roles,  # 获取用户角色列表
    get_token_payload,  # 获取Token完整载荷
    require_role,  # 要求特定角色
    require_any_role,  # 要求任意角色
)
```

---

## 常用模式

### 1. 获取用户ID（最常用）

```python
@router.get("/my-profile")
async def get_my_profile(user_id: Annotated[int, Depends(get_current_user_id)]):
    return {"user_id": user_id}
```

### 2. 获取多个信息

```python
@router.get("/profile")
async def profile(
    user_id: Annotated[int, Depends(get_current_user_id)],
    email: Annotated[str | None, Depends(get_current_user_email)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    return {"id": user_id, "email": email, "roles": roles}
```

### 3. 角色检查

```python
# 单个角色
@router.get("/admin")
async def admin_only(_: Annotated[None, Depends(require_role("admin"))]):
    return {"message": "Admin area"}


# 任意角色
@router.get("/staff")
async def staff_area(_: Annotated[None, Depends(require_any_role(["admin", "moderator"]))]):
    return {"message": "Staff area"}
```

### 4. 组合使用

```python
@router.post("/articles")
async def create_article(
    user_id: Annotated[int, Depends(get_current_user_id)],
    _: Annotated[None, Depends(require_role("author"))],
    title: str,
):
    return {"author_id": user_id, "title": title}
```

---

## vs 其他方式对比

| 方式              | 代码                                                      | 推荐度   |
|-----------------|---------------------------------------------------------|-------|
| ✅ 依赖函数          | `user_id: Annotated[int, Depends(get_current_user_id)]` | ⭐⭐⭐⭐⭐ |
| ⚠️ 工具类          | `AuthUtils.get_current_user_id(request)`                | ⭐⭐⭐   |
| ❌ Request.state | `request.state.user_id`                                 | ⭐⭐    |

---

## 完整示例

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pyspring.security.authentication.web.middleware.dependencies import (
    get_current_user_id,
    get_current_user_roles,
    require_role,
)

router = APIRouter(prefix="/api/users")


@router.get("/me")
async def me(user_id: Annotated[int, Depends(get_current_user_id)]):
    """获取当前用户"""
    return {"user_id": user_id}


@router.get("/admin/dashboard")
async def dashboard(
    user_id: Annotated[int, Depends(get_current_user_id)], _: Annotated[None, Depends(require_role("admin"))]
):
    """管理员仪表板"""
    return {"admin_id": user_id}


@router.put("/me/settings")
async def update_settings(
    user_id: Annotated[int, Depends(get_current_user_id)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    theme: str,
):
    """更新设置"""
    return {"user_id": user_id, "roles": roles, "theme": theme}
```
