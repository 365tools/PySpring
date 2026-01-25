# PyJWT Exception Fix Report

## 问题描述

**错误信息**：

```json
{
  "message": "module 'jwt' has no attribute 'JWTError'",
  "success": false,
  "data": {
    "error_type": "AttributeError",
    "reason": "module 'jwt' has no attribute 'JWTError'. Did you mean: 'PyJWTError'?",
    "traceback": "File \"D:\\Project\\PycharmProjects\\py-demo\\app\\services\\auth_service.py\", line 91, in verify_token\n    except jwt.JWTError:\n           ^^^^^^^^^^^^\n",
    "path": "/api/users/me",
    "method": "GET"
  }
}
```

**问题根因**：
模板文件使用了 PyJWT 1.x 的异常名称 `jwt.JWTError`，但 PyJWT 2.0+ 版本中此异常已重命名为 `jwt.PyJWTError`。

## 问题分析

### PyJWT 版本兼容性

**PyJWT 1.x（旧版本）**：

```python
import jwt

try:
    payload = jwt.decode(token, secret, algorithms=['HS256'])
except jwt.JWTError:  # ✅ 1.x 支持
    pass
except jwt.ExpiredSignatureError:  # ✅ 1.x 支持
    pass
```

**PyJWT 2.0+（新版本）**：

```python
import jwt
from jwt import PyJWTError, ExpiredSignatureError  # 推荐显式导入

try:
    payload = jwt.decode(token, secret, algorithms=['HS256'])
except jwt.PyJWTError:  # ✅ 2.0+ 正确名称
    pass
except jwt.JWTError:  # ❌ 2.0+ 不存在此异常
    pass
```

**PyJWT 2.10.1 可用异常**（当前版本）：

```python
from jwt import (
    PyJWTError,              # 基础异常（所有 JWT 错误的父类）
    DecodeError,             # 解码错误
    ExpiredSignatureError,   # 令牌过期
    InvalidTokenError,       # 无效令牌
    InvalidSignatureError,   # 签名验证失败
    InvalidAlgorithmError,   # 无效算法
    InvalidAudienceError,    # 无效受众
    InvalidIssuerError,      # 无效颁发者
    # ... 更多具体异常
)
```

### 框架 vs 模板的 JWT 实现

**PySpring 框架**：

- 使用 `python-jose` 库
- 异常：`from jose import JWTError`
- 位置：`src/pyspring/security/authentication/token/generator/jwt.py`
- 用途：框架内部 JWT Token 生成和验证

**Example 模板**：

- 使用 `PyJWT` 库（更常用）
- 依赖：`pyjwt>=2.8.0`
- 位置：`src/pyspring/templates/example/app/services/auth_service.py.template`
- 用途：示例代码，展示如何手动实现 JWT 认证

**设计考量**：

- 模板保持简单，不强制依赖框架 JWT 组件
- 用户可以自由选择使用框架组件或自己实现
- PyJWT 是社区最常用的库（下载量 > python-jose）

## 修复方案

### 修改：`src/pyspring/templates/example/app/services/auth_service.py.template`

#### 1. 添加显式异常导入

**Before**:

```python
from datetime import datetime, timedelta
from typing import Optional

import jwt
import bcrypt
```

**After**:

```python
from datetime import datetime, timedelta
from typing import Optional

import jwt
from jwt import PyJWTError, ExpiredSignatureError  # 🔧 显式导入异常
import bcrypt
```

#### 2. 修复异常处理

**Before** (Line 85-95):

```python
def verify_token(self, token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:  # ✅ 正确
        logger.warning("令牌已过期")
        return None
    except jwt.JWTError:  # ❌ PyJWT 2.0+ 不存在此异常
        logger.warning("令牌验证失败")
        return None
```

**After**:

```python
def verify_token(self, token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:  # ✅ 显式导入后直接使用
        logger.warning("令牌已过期")
        return None
    except PyJWTError:  # ✅ 正确的异常名称
        logger.warning("令牌验证失败")
        return None
```

## 验证测试

### 测试代码

```python
import jwt
from jwt import PyJWTError, ExpiredSignatureError

SECRET_KEY = "test-secret-key"
ALGORITHM = "HS256"

# 测试正常解码
token = jwt.encode({"sub": "user123"}, SECRET_KEY, algorithm=ALGORITHM)
try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print("✅ 正常解码:", payload)
except PyJWTError as e:
    print("❌ 解码失败:", e)

# 测试错误异常名称
try:
    jwt.JWTError  # 尝试访问不存在的异常
except AttributeError as e:
    print("❌ jwt.JWTError 不存在:", e)

# 测试正确异常名称
print("✅ PyJWTError 存在:", PyJWTError)
print("✅ ExpiredSignatureError 存在:", ExpiredSignatureError)
```

### 测试结果

```
✅ 正常解码: {'sub': 'user123'}
❌ jwt.JWTError 不存在: module 'jwt' has no attribute 'JWTError'
✅ PyJWTError 存在: <class 'jwt.exceptions.PyJWTError'>
✅ ExpiredSignatureError 存在: <class 'jwt.exceptions.ExpiredSignatureError'>
```

## 影响范围

### 修改文件

**`src/pyspring/templates/example/app/services/auth_service.py.template`**

- Line 12: 添加 `from jwt import PyJWTError, ExpiredSignatureError`
- Line 88: `except jwt.ExpiredSignatureError:` → `except ExpiredSignatureError:`
- Line 91: `except jwt.JWTError:` → `except PyJWTError:`

### 影响评估

**正向影响**：

- ✅ 修复 PyJWT 2.0+ 版本兼容性问题
- ✅ 已生成的用户项目需要手动更新（或重新生成）
- ✅ 更符合 Python 最佳实践（显式导入异常类）

**需要注意**：

- ⚠️ 如果用户使用 PyJWT 1.x，仍然可以工作（`PyJWTError` 在 1.x 中也存在）
- ⚠️ 已生成的项目需要手动修改 `app/services/auth_service.py`

### 用户项目修复指南

**对于已生成的项目**（如 py-demo），需要手动修改 `app/services/auth_service.py`：

```python
# 1. 添加导入
from jwt import PyJWTError, ExpiredSignatureError


# 2. 修改异常处理
def verify_token(self, token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:  # 修改此行
        logger.warning("令牌已过期")
        return None
    except PyJWTError:  # 修改此行
        logger.warning("令牌验证失败")
        return None
```

## 设计建议

### 未来改进方向

**1. 推荐使用框架 JWT 组件**

模板可以添加注释，推荐用户使用框架的 JWT 组件：

```python
"""
认证服务

展示两种方式：
1. 手动实现 JWT（当前示例）- 适合学习和自定义
2. 使用框架组件（推荐）- 适合生产环境

推荐方式：
from pyspring.security.authentication.token.generator.jwt import JWTTokenGenerator

@Component()
class AuthService:
    def __init__(self, jwt_generator: JWTTokenGenerator):
        self.jwt_generator = jwt_generator
    
    def create_token(self, user_data: dict) -> str:
        return self.jwt_generator.encode(user_data)
    
    def verify_token(self, token: str) -> Optional[dict]:
        return self.jwt_generator.decode(token)
"""
```

**2. 统一 JWT 库选择**

考虑框架和模板都使用 `PyJWT`（而非 python-jose），因为：

- PyJWT 是 PyPI 下载量最高的 JWT 库
- 社区活跃，维护良好
- 文档完善，API 稳定

但这需要重构框架的 JWT 实现，影响较大。

**3. 添加版本兼容性测试**

在 CI/CD 中测试多个 PyJWT 版本：

```yaml
# .github/workflows/test.yml
strategy:
  matrix:
    pyjwt-version: ['2.8.0', '2.9.0', '2.10.0']
```

## 总结

### 问题本质

**库版本不兼容**：

- 模板代码使用了 PyJWT 1.x 的异常名称 `jwt.JWTError`
- 用户安装的是 PyJWT 2.0+，此异常已重命名为 `jwt.PyJWTError`
- 导致运行时 `AttributeError`

### 修复方法

**显式导入并使用正确的异常名称**：

```python
from jwt import PyJWTError, ExpiredSignatureError  # 显式导入

# 使用时不需要 jwt. 前缀
except ExpiredSignatureError:
    ...
except PyJWTError:
    ...
```

### 设计原则

**版本兼容性优先**：

- 使用库的最新稳定版本 API
- 显式导入异常类（而非通过模块访问）
- 添加版本要求：`pyjwt>=2.8.0`

---

**修复日期**: 2026-01-26  
**影响版本**: v1.1.0b27+  
**修复状态**: ✅ 已完成（模板已修复，用户项目需手动更新）
