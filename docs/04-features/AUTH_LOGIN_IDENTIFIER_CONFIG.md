# 登录凭据字段配置指南

## 概述

PySpring框架支持**灵活的登录凭据配置**，可以通过YAML文件自定义用户登录时使用的标识字段。

## 配置方式

### 1. YAML配置文件

创建或编辑 `config/security.yaml`：

```yaml
authentication:
  # 登录标识符字段配置
  # 用户可以使用这些字段中的任意一个进行登录
  identifier_fields:
    - email          # 邮箱
    - username       # 用户名
    - phone          # 手机号
    - user_id        # 用户ID
```

### 2. 默认配置

如果未指定 `identifier_fields`，框架使用以下默认值：

```python
identifier_fields = ['username', 'email', 'user_id']
```

## 工作原理

### 登录请求格式

```json
{
  "identifier": "user@example.com",  // 可以是任何配置的字段值
  "password": "your_password"
}
```

### 匹配逻辑

框架会按照配置的顺序尝试匹配：

```sql
SELECT * FROM pyspring_user 
WHERE email = 'user@example.com' 
   OR username = 'user@example.com'
   OR phone = 'user@example.com'
   OR user_id = 'user@example.com'
LIMIT 1
```

## 使用示例

### 示例1：仅支持邮箱登录

```yaml
authentication:
  identifier_fields:
    - email
```

登录请求：

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"user@example.com","password":"password123"}'
```

### 示例2：支持多种方式

```yaml
authentication:
  identifier_fields:
    - email
    - username
    - phone
```

登录请求（任意一种）：

```bash
# 使用邮箱
{"identifier": "user@example.com", "password": "password123"}

# 使用用户名
{"identifier": "john_doe", "password": "password123"}

# 使用手机号
{"identifier": "13800138000", "password": "password123"}
```

### 示例3：企业应用（员工工号）

```yaml
authentication:
  identifier_fields:
    - employee_id    # 员工工号
    - email          # 企业邮箱
```

登录请求：

```bash
# 使用员工工号
{"identifier": "EMP20230001", "password": "password123"}

# 使用企业邮箱
{"identifier": "john.doe@company.com", "password": "password123"}
```

## 数据库字段要求

确保配置的字段在 `pyspring_user` 表中存在：

```sql
CREATE TABLE pyspring_user (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE,      -- 用户ID
    username VARCHAR(50) UNIQUE,     -- 用户名
    email VARCHAR(100) UNIQUE,       -- 邮箱
    phone VARCHAR(20) UNIQUE,        -- 手机号（可选）
    employee_id VARCHAR(20) UNIQUE,  -- 员工工号（可选）
    password VARCHAR(255) NOT NULL,
    ...
);
```

⚠️ **重要**：配置的字段必须：

1. 在数据库表中存在
2. 有唯一性约束（UNIQUE）
3. 可以为NULL（如果是可选字段）

## 代码实现

### LoginRequest模型

```python
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    """登录请求"""
    identifier: str = Field(..., description="登录标识符（用户名/邮箱/手机号等）")
    password: str = Field(..., min_length=6, description="用户密码")
```

### 后端处理

框架会自动根据配置动态匹配：

```python
# src/pyspring/security/authentication/providers/user/database.py

async def get_user_by_identifier(self, identifier: str) -> Optional[UserInfo]:
    """
    根据标识符获取用户（支持多字段匹配）
    """
    # 从配置获取标识字段列表
    identifier_fields = self.component.identifier_fields
    
    # 动态构建查询条件
    conditions = []
    for field_name in identifier_fields:
        if hasattr(UserTable, field_name):
            conditions.append(
                getattr(UserTable, field_name) == identifier
            )
    
    # 执行查询
    stmt = select(UserTable).where(or_(*conditions))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    return user
```

## 安全建议

### 1. 字段唯一性

确保所有配置的字段都有唯一性约束：

```sql
-- 好的做法
CREATE UNIQUE INDEX idx_user_email ON pyspring_user(email);
CREATE UNIQUE INDEX idx_user_phone ON pyspring_user(phone);

-- 避免重复值导致的安全问题
```

### 2. 敏感字段保护

不建议使用以下字段作为登录标识：

```yaml
# ❌ 不推荐
authentication:
  identifier_fields:
    - id              # 数据库主键，容易被枚举
    - password_hash   # 密码哈希，永远不应该暴露
```

### 3. 错误消息统一

登录失败时使用统一的错误消息，不要泄露字段信息：

```python
# ✅ 推荐
raise HTTPException(401, detail="Invalid credentials")

# ❌ 不推荐
raise HTTPException(401, detail="Email not found")  # 泄露了字段信息
```

## 最佳实践

### 1. 常见配置场景

**社交应用**：

```yaml
identifier_fields:
  - username
  - email
  - phone
```

**企业应用**：

```yaml
identifier_fields:
  - employee_id
  - email
```

**电商应用**：

```yaml
identifier_fields:
  - phone
  - email
```

**多租户SaaS**：

```yaml
identifier_fields:
  - email          # 格式: user@tenant.domain.com
  - tenant_user_id # 格式: tenant_id:user_id
```

### 2. 性能优化

为配置的字段添加索引：

```sql
-- 提升查询性能
CREATE INDEX idx_user_email ON pyspring_user(email);
CREATE INDEX idx_user_username ON pyspring_user(username);
CREATE INDEX idx_user_phone ON pyspring_user(phone);
```

### 3. 字段顺序

配置字段的顺序影响匹配优先级，建议：

```yaml
identifier_fields:
  - email       # 最常用的放前面
  - username
  - phone       # 较少使用的放后面
```

## 常见问题

### Q1: 用户如何知道可以用哪些字段登录？

A: 在登录页面提供提示：

```html
<input 
  type="text" 
  name="identifier" 
  placeholder="邮箱/用户名/手机号"
>
```

### Q2: 如何区分identifier是邮箱还是手机号？

A: 框架会自动匹配所有配置的字段，无需区分。如果需要验证格式，可以在前端添加：

```javascript
function validateIdentifier(identifier) {
  if (identifier.includes('@')) {
    // 邮箱格式验证
  } else if (/^\d+$/.test(identifier)) {
    // 手机号格式验证
  } else {
    // 用户名格式验证
  }
}
```

### Q3: 配置字段在数据库中不存在会怎样？

A: 框架会自动跳过不存在的字段，并记录警告日志：

```python
if not hasattr(UserTable, field_name):
    logger.warning(f"Field '{field_name}' not found in UserTable")
    continue
```

### Q4: 如何支持国际化（多语言）？

A: identifier字段本身是中性的，错误消息可以国际化：

```python
# i18n/zh_CN.json
{
  "auth.invalid_credentials": "用户名或密码错误"
}

# i18n/en_US.json
{
  "auth.invalid_credentials": "Invalid credentials"
}
```

## 总结

✅ **优势**：

- 灵活性：支持多种登录方式
- 可配置：通过YAML轻松调整
- 安全性：统一错误消息，防止信息泄露
- 扩展性：轻松添加新字段

✅ **关键要点**：

- identifier字段统一所有登录方式
- 配置的字段必须在数据库中存在且唯一
- 框架自动按顺序匹配所有配置的字段
- 错误消息不泄露具体字段信息
