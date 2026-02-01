# identifier 登录功能使用指南

## 概述

从 PySpring v1.1.0 开始，框架支持使用 `identifier` 字段进行登录，可以自动匹配以下字段：

- 用户ID (`user_id`)
- 用户名 (`username`)
- 邮箱 (`email`)
- 手机号 (`phone`)

## 核心实现

### 1. LoginRequest 模型

支持三种方式提供登录凭证：

```python
from pyspring.security.authentication.contracts.request import LoginRequest

# 推荐方式：使用 identifier
request = LoginRequest(
    identifier="admin@example.com",  # 可以是用户名、邮箱、手机号、用户ID
    password="admin123"
)

# 兼容方式1：使用 user_id
request = LoginRequest(
    user_id="admin",
    password="admin123"
)

# 兼容方式2：使用 email
request = LoginRequest(
    email="admin@example.com",
    password="admin123"
)
```

### 2. 登录标识符字段配置（v1.1.0+）

通过配置文件自定义可用于登录的字段：

```yaml
# config/security.yaml
authentication:
  identifier_fields:
    - "user_id"    # 框架标准字段
    - "username"   # 自定义字段
    - "email"      # 框架标准字段
    - "phone"      # 自定义字段
    - "employee_id" # 可添加任意字段
```

**配置说明**：

- 框架会按列表顺序尝试匹配字段
- 如果用户模型没有某个字段，会自动跳过
- 可以添加任意自定义字段
- 详细配置指南：[IDENTIFIER_FIELDS_CONFIGURATION_GUIDE.md](IDENTIFIER_FIELDS_CONFIGURATION_GUIDE.md)

### 3. DefaultPasswordLoginProvider

自动支持 `identifier` 字段：

- 优先使用 `identifier`
- 如果没有 `identifier`，回退到 `user_id` 或 `email`（向后兼容）
- 保持所有安全特性（防时序攻击、密码验证）

### 3. DefaultUserProvider

动态检测用户模型字段：

- 始终支持：`user_id`、`email`
- 如果用户模型有 `username` 字段，自动支持
- 如果用户模型有 `phone` 字段，自动支持

## 使用示例

### API 请求示例

#### 使用 identifier（推荐）

```bash
# 使用邮箱登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "admin@example.com",
    "password": "admin123"
  }'

# 使用用户名登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "admin",
    "password": "admin123"
  }'

# 使用手机号登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "13800138000",
    "password": "admin123"
  }'

# 使用用户ID登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "550e8400-e29b-41d4-a716-446655440000",
    "password": "admin123"
  }'
```

#### 兼容旧方式

```bash
# 使用 user_id 字段
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "admin",
    "password": "admin123"
  }'

# 使用 email 字段
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }'
```

### Python 代码示例

```python
from fastapi import APIRouter, Depends
from pyspring.ioc.di.inject import Inject
from pyspring.security.authentication.contracts.flow import ILoginService
from pyspring.security.authentication.contracts.request import LoginRequest

router = APIRouter()

@router.post("/login")
async def login(
    request: LoginRequest,
    login_service: ILoginService = Depends(lambda: Inject(ILoginService))
):
    """
    用户登录
    
    请求示例：
    {
        "identifier": "admin@example.com",  # 推荐方式
        "password": "admin123"
    }
    """
    result = await login_service.login(request)
    return result
```

## 用户模型配置

### 扩展用户模型

如果你想支持 `username` 或 `phone` 字段，需要扩展用户模型：

```python
# app/models/user.py
from sqlalchemy import Column, String
from pyspring.repositories.db.models.common.define import BaseUserTable


class User(BaseUserTable):
    """
    用户模型
    
    继承 BaseUserTable 自动获得：
    - id, user_id, email, password, first_name, last_name
    - uuid, active, deleted, creator, created_time, etc.
    """
    __tablename__ = "users"
    
    # 扩展字段
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    phone = Column(String(20), unique=True, index=True, nullable=True, comment="手机号")
```

框架会自动检测这些字段并支持查询！

### 自定义查询逻辑（可选）

如果你需要更复杂的查询逻辑（例如：添加其他字段、修改查询条件），可以继承 `DefaultUserProvider`：

```python
# app/providers/custom_user_provider.py
from typing import Any, Optional
from pyspring.ioc.annotations import Component
from pyspring.security.authentication.providers.user.database import DefaultUserProvider
from sqlalchemy import select, or_
from app.models.user import User


@Component
class CustomUserProvider(DefaultUserProvider):
    """自定义用户提供者"""

    async def get_user_by_identity(self, identity: str) -> Optional[Any]:
        """
        自定义查询逻辑
        
        可以添加更多字段或修改查询条件
        """
        async with await self.db.session() as session:
            result = await session.execute(
                select(User).where(
                    or_(
                        User.user_id == identity,
                        User.username == identity,
                        User.email == identity,
                        User.phone == identity,
                        # 添加其他字段...
                        User.nickname == identity,  # 示例：昵称
                    )
                )
            )
            return result.scalar_one_or_none()
```

## 特性说明

### 1. 向后兼容

- 旧代码使用 `user_id` 或 `email` 字段的，无需修改
- 新代码推荐使用 `identifier` 字段

### 2. 优先级

查询优先级：`identifier` > `user_id` > `email`

如果同时提供多个字段，按优先级使用

### 3. 安全特性

保持所有安全特性：

- ✅ 防时序攻击（用户不存在时执行 dummy hash）
- ✅ 统一错误消息（不泄露用户是否存在）
- ✅ 密码加密验证（Argon2/BCrypt）

### 4. 动态字段检测

框架会自动检测用户模型中的字段：

- 如果有 `username` 字段，自动支持用户名登录
- 如果有 `phone` 字段，自动支持手机号登录
- 无需额外配置！

## 测试

运行测试验证功能：

```bash
python test_identifier_login.py
```

## 响应示例

成功响应：

```json
{
    "success": true,
    "data": {
        "access_token": "eyJhbGc...",
        "refresh_token": "eyJhbGc...",
        "token_type": "bearer",
        "expires_in": 3600,
        "refresh_token_expire": 2592000,
        "message": "登录成功"
    }
}
```

失败响应：

```json
{
    "success": false,
    "message": "用户名或密码错误"
}
```

## 常见问题

### Q: 是否必须使用 identifier？

A: 不是必须的。`user_id` 和 `email` 字段仍然支持，用于向后兼容。但推荐新项目使用 `identifier` 字段。

### Q: 如何添加其他登录字段（如昵称）？

A: 扩展用户模型添加字段，然后继承 `DefaultUserProvider` 并重写 `get_user_by_identity` 方法。

### Q: 框架如何知道我的用户模型有哪些字段？

A: 使用 Python 的 `hasattr()` 函数动态检测。只要你的模型有该字段，框架就会自动支持。

### Q: 查询性能如何？

A: 使用单条 SQL 的 OR 查询，性能高效。建议在常用字段上添加索引（username, email, phone）。

## 完整示例项目

查看示例项目获取完整的实现：

```bash
# 初始化示例项目
pyspring init myproject

# 查看相关文件
myproject/
├── app/
│   ├── models/
│   │   └── user.py              # 用户模型（扩展 username, phone）
│   ├── services/
│   │   └── custom_login_provider.py  # 自定义登录提供者（可选）
│   └── api/
│       └── auth.py              # 认证端点
```

## 更新日志

- **v1.1.0**: 添加 `identifier` 字段支持
- **v1.1.0**: 动态字段检测（username, phone）
- **v1.1.0**: 向后兼容 `user_id` 和 `email` 字段
