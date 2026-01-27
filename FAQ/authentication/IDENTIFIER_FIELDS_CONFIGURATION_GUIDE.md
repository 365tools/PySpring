# identifier_fields 配置指南

## 概述

从 PySpring v1.1.0 开始，登录标识符字段支持通过配置文件自定义，无需硬编码字段名。

## 配置方式

### 1. 通过配置文件（推荐）

在 `config/security.yaml` 中配置：

```yaml
authentication:
  # 登录标识符字段配置
  identifier_fields:
    - "user_id"    # 框架标准字段（用户UUID）
    - "username"   # 常用字段（用户名）
    - "email"      # 框架标准字段（邮箱）
    - "phone"      # 常用字段（手机号）
```

### 2. 通过代码配置

```python
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
from pyspring.ioc.annotations import Component

@Component()
class CustomSecurityEntityConfiguration(SecurityEntityConfiguration):
    def __init__(self):
        super().__init__(
            identifier_fields=['user_id', 'username', 'email', 'phone', 'nickname']
        )
```

## 配置说明

### 字段列表规则

1. **框架会按列表顺序尝试匹配** - 如果找到匹配的用户，立即返回
2. **自动跳过不存在的字段** - 如果用户模型没有某个字段，框架会自动忽略
3. **至少保留框架标准字段** - 建议至少包含 `user_id` 和 `email`
4. **支持任意自定义字段** - 可以添加任何你需要的字段

### 默认值

如果未配置，框架使用以下默认值：

```python
identifier_fields = ['user_id', 'username', 'email', 'phone']
```

## 使用示例

### 示例1：基础配置

```yaml
# config/security.yaml
authentication:
  identifier_fields:
    - "user_id"
    - "email"
```

用户可以通过 user_id 或 email 登录。

### 示例2：扩展字段

```yaml
# config/security.yaml
authentication:
  identifier_fields:
    - "user_id"
    - "username"
    - "email"
    - "phone"
    - "employee_id"  # 员工工号
    - "nickname"     # 昵称
```

用户可以通过任何配置的字段登录。

### 示例3：仅使用邮箱

```yaml
# config/security.yaml
authentication:
  identifier_fields:
    - "email"
```

仅支持邮箱登录（不推荐，建议至少保留 user_id）。

## 工作原理

### 1. 配置加载

```python
# SecurityEntityConfiguration.__init__
config = ConfigManager()
identifier_fields = config.get(
    'security.authentication.identifier_fields',
    ['user_id', 'username', 'email', 'phone']  # 默认值
)
self.identifier_fields = identifier_fields
```

### 2. 动态字段检测

```python
# DefaultUserProvider.get_user_by_identity
conditions = []
for field_name in self.component.identifier_fields:
    # 检查用户模型是否有该字段
    if hasattr(self.component.user_orm_model, field_name):
        field = getattr(self.component.user_orm_model, field_name)
        conditions.append(field == identity)
```

### 3. 查询执行

```python
# 使用 OR 条件查询
from sqlalchemy import or_
stmt = select(User).where(or_(*conditions))
```

生成的 SQL：

```sql
SELECT * FROM users 
WHERE user_id = ? OR username = ? OR email = ? OR phone = ?
```

## 用户模型示例

### 基础用户模型

```python
# app/models/user.py
from sqlalchemy import Column, String
from pyspring.repositories.db.models.common.define import BaseUserTable

class User(BaseUserTable):
    __tablename__ = "users"
    
    # 扩展字段
    username = Column(String(50), unique=True, index=True)
    phone = Column(String(20), unique=True, index=True)
```

框架会自动检测到 `username` 和 `phone` 字段。

### 扩展用户模型

```python
# app/models/user.py
class User(BaseUserTable):
    __tablename__ = "users"
    
    # 标准扩展字段
    username = Column(String(50), unique=True, index=True)
    phone = Column(String(20), unique=True, index=True)
    
    # 自定义字段
    nickname = Column(String(50), unique=True, index=True)
    employee_id = Column(String(20), unique=True, index=True)
```

然后在配置中添加：

```yaml
authentication:
  identifier_fields:
    - "user_id"
    - "username"
    - "email"
    - "phone"
    - "nickname"      # 新增
    - "employee_id"   # 新增
```

## 最佳实践

### ✅ 推荐做法

1. **保留框架标准字段**
   ```yaml
   identifier_fields:
     - "user_id"   # 必须保留
     - "email"     # 必须保留
     - "username"  # 推荐添加
   ```

2. **按常用程度排序**
   ```yaml
   identifier_fields:
     - "username"   # 最常用，放第一位
     - "email"
     - "phone"
     - "user_id"
   ```

3. **添加索引**
   ```python
   username = Column(String(50), unique=True, index=True)  # ✅ 添加索引
   ```

4. **使用唯一约束**
   ```python
   username = Column(String(50), unique=True)  # ✅ 唯一约束
   ```

### ❌ 不推荐做法

1. **删除框架标准字段**
   ```yaml
   identifier_fields:
     - "username"   # ❌ 缺少 user_id 和 email
   ```

2. **添加非唯一字段**
   ```python
   # ❌ first_name 不是唯一字段，不应用于登录
   identifier_fields:
     - "first_name"
   ```

3. **没有索引**
   ```python
   username = Column(String(50))  # ❌ 缺少索引，查询慢
   ```

## 性能优化

### 1. 添加索引

所有用于登录的字段都应该添加索引：

```python
class User(BaseUserTable):
    username = Column(String(50), unique=True, index=True)  # ✅
    phone = Column(String(20), unique=True, index=True)     # ✅
    email = Column(String(100), unique=True, index=True)    # ✅
```

### 2. 使用复合索引（可选）

如果经常同时查询多个字段，可以添加复合索引：

```python
from sqlalchemy import Index

class User(BaseUserTable):
    username = Column(String(50))
    email = Column(String(100))
    
    __table_args__ = (
        Index('idx_username_email', 'username', 'email'),
    )
```

### 3. 控制字段数量

不要添加太多字段，建议 3-5 个：

```yaml
# ✅ 合理
identifier_fields:
  - "user_id"
  - "username"
  - "email"
  - "phone"

# ❌ 过多
identifier_fields:
  - "user_id"
  - "username"
  - "email"
  - "phone"
  - "nickname"
  - "employee_id"
  - "passport_number"
  - "driver_license"
```

## 安全考虑

### 1. 避免敏感字段

不要使用敏感字段作为登录标识符：

```yaml
# ❌ 不要使用
identifier_fields:
  - "ssn"              # 社会保障号
  - "credit_card"      # 信用卡号
  - "password"         # 密码（当然不会）
```

### 2. 使用唯一字段

只使用唯一字段作为登录标识符：

```yaml
# ✅ 正确
identifier_fields:
  - "user_id"    # 唯一
  - "username"   # 唯一
  - "email"      # 唯一

# ❌ 错误
identifier_fields:
  - "first_name"  # 不唯一
  - "age"         # 不唯一
```

### 3. 防止信息泄露

使用统一的错误消息，不要泄露用户是否存在：

```python
# ✅ 框架已实现
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="用户名或密码错误"  # 统一消息
)
```

## 故障排查

### 问题1：配置不生效

**现象**：修改了 `identifier_fields` 但登录失败

**原因**：配置文件路径错误或格式错误

**解决**：

1. 检查配置文件路径：`config/security.yaml`
2. 检查 YAML 格式是否正确
3. 重启应用加载新配置

### 问题2：字段未被识别

**现象**：添加了字段但无法登录

**原因**：用户模型没有该字段

**解决**：

1. 检查用户模型是否定义了该字段
2. 确保字段名拼写正确（区分大小写）
3. 确保数据库迁移已执行

### 问题3：查询性能差

**现象**：登录很慢

**原因**：字段没有索引

**解决**：

```python
# 添加索引
username = Column(String(50), unique=True, index=True)
```

## 完整示例

### 1. 配置文件

```yaml
# config/security.yaml
authentication:
  identifier_fields:
    - "username"
    - "email"
    - "phone"
    - "employee_id"
```

### 2. 用户模型

```python
# app/models/user.py
from sqlalchemy import Column, String
from pyspring.repositories.db.models.common.define import BaseUserTable

class User(BaseUserTable):
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    employee_id = Column(String(20), unique=True, index=True, nullable=True)
```

### 3. 登录请求

```python
# 使用用户名
request = LoginRequest(identifier="admin", password="admin123")

# 使用邮箱
request = LoginRequest(identifier="admin@example.com", password="admin123")

# 使用手机号
request = LoginRequest(identifier="13800138000", password="admin123")

# 使用员工工号
request = LoginRequest(identifier="EMP001", password="admin123")
```

所有这些方式都会被框架自动识别和处理！

## 总结

✅ **灵活配置** - 通过 YAML 文件配置，无需改代码
✅ **动态检测** - 自动检测用户模型字段
✅ **性能优化** - 使用索引和 OR 查询
✅ **安全保障** - 统一错误消息，防时序攻击
✅ **易于扩展** - 添加新字段只需修改配置

这是一个**最佳实践**的实现方案！
