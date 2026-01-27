# Example Template Framework Best Practice Update

## 更新概述

将 Example 模板的认证服务重构为使用框架 JWT 组件，体现 PySpring 框架的最佳实践。

## 设计原则

✅ **框架优先**：推荐使用框架提供的安全组件  
✅ **配置统一**：通过 `config/security.yaml` 集中管理  
✅ **依赖注入**：自动获取框架组件  
✅ **可扩展性**：保留自定义实现的说明

## 修改内容

### 1. AuthService 重构

**Before**（手动实现 JWT）：

```python
import jwt
from jwt import PyJWTError, ExpiredSignatureError

# 硬编码配置
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        # 手动编码 JWT
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        # 手动验证 JWT
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except ExpiredSignatureError:
            return None
        except PyJWTError:
            return None
```

**After**（使用框架组件）：

```python
from pyspring.security.authentication.token.generator.jwt import JWTTokenGenerator


class AuthService:
    """
    使用框架安全组件的最佳实践：
    - JWTTokenGenerator: 自动处理 Token 生成、验证、加密
    - 配置统一管理: 通过 config/security.yaml 和环境变量配置
    - 安全性保障: 框架自动验证密钥强度、过期时间等
    """

    def __init__(
            self,
            user_repository: UserRepository,
            jwt_generator: JWTTokenGenerator  # 🔧 框架 JWT 组件（依赖注入）
    ):
        self.user_repository = user_repository
        self.jwt_generator = jwt_generator

    def create_access_token(self, user_data: dict) -> str:
        """使用框架 JWT 组件生成 Token"""
        payload = {
            "sub": user_data.get("username"),
            "user_id": user_data.get("user_id"),
            "type": "access"
        }
        return self.jwt_generator.encode(payload)

    def verify_token(self, token: str) -> Optional[dict]:
        """使用框架 JWT 组件验证 Token"""
        payload = self.jwt_generator.decode(token)
        if not payload:
            logger.warning("令牌验证失败")
            return None
        return payload
```

### 2. 依赖清理

**requirements.txt.template**:

**Before**:

```
# 认证
pyjwt>=2.8.0  # JWT 令牌
passlib[bcrypt]>=1.7.4  # 密码哈希
```

**After**:

```
# 认证（密码哈希）
# 注意：JWT 功能由 PySpring 框架提供，无需额外安装
# 框架内置 python-jose 库处理 JWT Token
passlib[bcrypt]>=1.7.4  # 密码哈希
```

### 3. 文档更新

**文件顶部注释**:

```python
"""
认证服务

✅ 框架最佳实践：使用 PySpring 安全组件
展示：
1. 使用框架 JWT Token 生成器（推荐）
2. 密码哈希
3. 用户认证

💡 自定义实现：
如果需要完全自定义 JWT 实现，可以移除 JWTTokenGenerator 依赖，
改用 PyJWT 库手动实现（参考框架文档的自定义认证章节）
"""
```

## 优势对比

| 维度           | 手动实现       | 框架组件（推荐）               |
|--------------|------------|------------------------|
| **配置管理**     | 硬编码或分散配置   | 统一在 `security.yaml` 管理 |
| **安全性**      | 需手动验证密钥强度  | 框架自动验证并警告              |
| **Token 加密** | 需手动实现      | 配置即启用                  |
| **依赖管理**     | 需安装 PyJWT  | 框架内置 python-jose       |
| **代码量**      | ~50 行      | ~15 行                  |
| **维护成本**     | 高（需同步安全更新） | 低（框架自动更新）              |
| **扩展性**      | 灵活但需自己实现   | 插件化扩展                  |

## 用户项目更新指南

### 对于已生成的项目（如 py-demo）

**步骤 1**: 更新 `requirements.txt`

```bash
# 移除
pyjwt>=2.8.0

# 保留
passlib[bcrypt]>=1.7.4
```

**步骤 2**: 更新 `app/services/auth_service.py`

```python
# 1. 修改导入
# Before:
import jwt
from jwt import PyJWTError, ExpiredSignatureError

# After:
from pyspring.security.authentication.token.generator.jwt import JWTTokenGenerator


# 2. 修改构造函数
# Before:
def __init__(self, user_repository: UserRepository):
    self.user_repository = user_repository


# After:
def __init__(self, user_repository: UserRepository, jwt_generator: JWTTokenGenerator):
    self.user_repository = user_repository
    self.jwt_generator = jwt_generator


# 3. 修改 create_access_token 方法
# Before:
def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    # ... 手动编码逻辑
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# After:
def create_access_token(self, user_data: dict) -> str:
    payload = {
        "sub": user_data.get("username"),
        "user_id": user_data.get("user_id"),
        "type": "access"
    }
    return self.jwt_generator.encode(payload)


# 4. 修改 verify_token 方法
# Before:
def verify_token(self, token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        logger.warning("令牌已过期")
        return None
    except PyJWTError:
        logger.warning("令牌验证失败")
        return None


# After:
def verify_token(self, token: str) -> Optional[dict]:
    payload = self.jwt_generator.decode(token)
    if not payload:
        logger.warning("令牌验证失败")
        return None
    return payload


# 5. 修改 authenticate 方法调用
# Before:
access_token = self.create_access_token(
    data={"sub": user.username, "id": user.id, "user_id": user.user_id}
)

# After:
access_token = self.create_access_token({
    "username": user.username,
    "user_id": user.user_id
})

# 6. 移除硬编码配置
# 删除这些行：
# SECRET_KEY = "your-secret-key-change-in-production"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

**步骤 3**: 重新安装依赖

```bash
uv pip install -r requirements.txt
```

**步骤 4**: 验证配置
确保 `config/security.yaml` 包含 JWT 配置：

```yaml
authentication:
  jwt:
    # 开发环境使用框架默认密钥（自动提供）
    # 生产环境必须通过环境变量 JWT_SECRET_KEY 覆盖
    secret_key: null  # null = 使用框架默认值
    algorithm: "HS256"
    access_token_expire: 3600  # 1小时
    refresh_token_expire: 2592000  # 30天
```

## 配置示例

### 开发环境（无需配置）

框架自动提供安全的默认密钥，无需任何配置即可使用。

### 生产环境

**方式 1：环境变量（推荐）**

```bash
# 生成强密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 设置环境变量
export JWT_SECRET_KEY="your-generated-key"
```

**方式 2：配置文件（不推荐硬编码密钥）**

```yaml
# config/security.yaml
authentication:
  jwt:
    secret_key: "your-custom-key"  # 仅用于测试环境
    access_token_expire: 7200  # 2小时
```

## 框架组件功能

### JWTTokenGenerator 提供的功能

1. **Token 生成**
    - 自动添加过期时间（`exp`）
    - 自动添加签发时间（`iat`）
    - 自动添加 Token ID（`jti`）

2. **Token 验证**
    - 签名验证
    - 过期时间验证
    - 自动处理异常

3. **Token 加密**（可选）
   ```yaml
   authentication:
     jwt:
       encryption:
         enabled: true  # 启用 Token 加密
         encryption_key: null  # 通过环境变量设置
   ```

4. **安全验证**
    - 密钥强度检查（最小 32 字节）
    - 不安全默认值警告
    - 生产环境配置提示

## 测试验证

### 单元测试

```python
import pytest
from app.services.auth_service import AuthService
from pyspring.security.authentication.token.generator.jwt import JWTTokenGenerator


@pytest.mark.asyncio
async def test_token_generation(auth_service: AuthService):
    """测试 Token 生成"""
    user_data = {"username": "testuser", "user_id": "uuid-123"}

    # 生成 Token
    token = auth_service.create_access_token(user_data)
    assert token is not None

    # 验证 Token
    payload = auth_service.verify_token(token)
    assert payload["sub"] == "testuser"
    assert payload["user_id"] == "uuid-123"
    assert payload["type"] == "access"
```

### 集成测试

```python
async def test_authentication_flow(client):
    """测试完整认证流程"""
    # 1. 登录
    response = await client.post("/api/auth/login", json={
        "login_identifier": "testuser",
        "password": "password123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # 2. 使用 Token 访问受保护资源
    response = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
```

## 常见问题

### Q: 为什么框架使用 python-jose 而不是 PyJWT？

**A**:

- `python-jose` 提供更完整的 JOSE 标准支持
- 支持 JWT、JWS、JWE 等多种 Token 格式
- 框架内部已集成，用户无需关心底层库

### Q: 可以同时使用框架组件和自定义实现吗？

**A**: 可以。框架组件通过依赖注入提供，不注入即可使用自定义实现：

```python
class CustomAuthService:
    def __init__(self, user_repository: UserRepository):
        # 不注入 jwt_generator，使用自己的实现
        self.user_repository = user_repository
```

### Q: 如何自定义 Token Payload？

**A**: 直接在 `encode()` 时传入：

```python
payload = {
    "sub": username,
    "user_id": user_id,
    "roles": ["admin", "user"],  # 自定义字段
    "permissions": ["read", "write"],  # 自定义字段
    "type": "access"
}
token = self.jwt_generator.encode(payload)
```

## 总结

### 核心价值

1. **简化代码**：从 ~50 行减少到 ~15 行
2. **提高安全性**：框架自动验证和警告
3. **统一配置**：集中管理，环境隔离
4. **降低维护成本**：框架自动更新安全补丁

### 推荐实践

✅ **推荐**：使用框架 `JWTTokenGenerator`  
✅ **推荐**：通过 `config/security.yaml` 配置  
✅ **推荐**：生产环境使用环境变量  
❌ **不推荐**：硬编码密钥  
❌ **不推荐**：自己实现 JWT（除非有特殊需求）

---

**更新日期**: 2026-01-26  
**影响文件**:

- `src/pyspring/templates/example/app/services/auth_service.py.template`
- `src/pyspring/templates/example/requirements.txt.template`
