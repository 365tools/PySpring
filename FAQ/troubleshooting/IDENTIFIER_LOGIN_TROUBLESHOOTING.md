# Identifier Login 故障排查指南

## 问题描述

使用 identifier 登录时，SQL 查询了框架默认的 `pyspring_user` 表，而不是自定义的用户表（如 `users`、`myapp_users` 等）。

### 错误示例

```json
{
    "message": "500: 登录失败: (sqlite3.OperationalError) no such table: pyspring_user"
}
```

SQL 日志：

```sql
SELECT ... FROM pyspring_user WHERE pyspring_user.email = ? OR pyspring_user.user_id = ?
```

---

## 根本原因

框架使用默认的 `SecurityEntityConfiguration`，其中 `user_orm_model = UserTable`（表名：`pyspring_user`），而不是用户自定义的 `User` 模型。

---

## 解决方案

### 方案 1：创建配置文件（推荐）

在项目中创建 `app/config/security_config.py`：

```python
from pyspring.ioc.annotations import Component
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
from app.models.user import User  # 导入你的自定义 User 模型


@Component()
class CustomSecurityEntityConfiguration(SecurityEntityConfiguration):
    """自定义安全实体配置"""
    
    def __init__(self):
        super().__init__()  # 继承所有默认值
        self.user_orm_model = User  # 使用自定义的 User 模型
```

### 方案 2：检查模板文件

如果你是通过 `pyspring init --example` 创建的项目，检查：

1. **文件是否存在**：
   ```bash
   ls app/config/security_config.py
   ```

2. **如果不存在**，从框架模板复制：
   ```bash
   # 找到 PySpring 安装位置
   python -c "import pyspring; print(pyspring.__file__)"
   
   # 复制模板（路径示例）
   cp .venv/lib/python3.11/site-packages/pyspring/templates/example/app/config/security_config.py.template \
      app/config/security_config.py
   ```

3. **确保扫描**：`app/main.py` 中应该有：
   ```python
   app_context = ApplicationContext.initialize(
       base_packages=['app'],  # 这会扫描 app.config.security_config
       ...
   )
   ```

### 方案 3：验证配置生效

启动应用时查看日志，确认：

```
📦 步骤 2/3: 扫描并注册组件...
✅ 组件已注册: CustomSecurityEntityConfiguration (app.config.security_config)
```

如果看到的是：

```
✅ 组件已注册: SecurityEntityConfiguration (pyspring.security.authentication.config.entity)
```

说明自定义配置**没有生效**！

---

## 快速检查清单

- [ ] `app/config/security_config.py` 文件存在
- [ ] `CustomSecurityEntityConfiguration` 有 `@Component()` 装饰器
- [ ] `user_orm_model = User` 指向正确的自定义模型
- [ ] `app/main.py` 中 `base_packages` 包含 `'app'`
- [ ] 启动日志显示 `CustomSecurityEntityConfiguration` 已注册

---

## 完整示例

### app/models/user.py

```python
from sqlalchemy import Column, String
from pyspring.repositories.db.models.common.define import BaseUserTable


class User(BaseUserTable):
    """自定义用户模型"""
    __tablename__ = "users"  # 实际表名：{prefix}_users
    
    username = Column(String(50), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
```

### app/config/security_config.py

```python
from pyspring.ioc.annotations import Component
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
from app.models.user import User


@Component()
class CustomSecurityEntityConfiguration(SecurityEntityConfiguration):
    def __init__(self):
        super().__init__()
        self.user_orm_model = User  # ✅ 使用自定义表
```

### 预期 SQL（修复后）

```sql
-- 假设 table_prefix = "myapp"
SELECT ... FROM myapp_users WHERE myapp_users.username = ? OR myapp_users.email = ?
```

---

## 框架设计说明

### identifier_fields 配置（config/security.yaml）

```yaml
authentication:
  identifier_fields:
    - "username"  # 自定义字段（需要在 User 模型中定义）
    - "email"     # BaseUserTable 标准字段
    - "user_id"   # BaseUserTable 标准字段
```

### 动态字段匹配逻辑

框架会：

1. 读取 `identifier_fields` 配置
2. 使用 `hasattr(user_orm_model, field_name)` 检查模型是否有该字段
3. 构建 `WHERE field1 = ? OR field2 = ? OR ...` 查询

因此：

- ✅ `username` 字段：如果 `User` 模型有，会匹配
- ✅ `email` 字段：`BaseUserTable` 自带，会匹配
- ✅ `user_id` 字段：`BaseUserTable` 自带，会匹配
- ❌ `phone` 字段：如果未在配置中，不会匹配

---

## 常见错误

### 错误 1：忘记 `@Component()` 装饰器

```python
# ❌ 错误：没有装饰器，扫描器无法识别
class CustomSecurityEntityConfiguration(SecurityEntityConfiguration):
    ...

# ✅ 正确
@Component()
class CustomSecurityEntityConfiguration(SecurityEntityConfiguration):
    ...
```

### 错误 2：import 路径错误

```python
# ❌ 错误：相对导入可能失败
from .user import User

# ✅ 正确：绝对导入
from app.models.user import User
```

### 错误 3：表名前缀未配置

如果你的数据库表是 `myapp_users`，确保 `config/repositories.yaml` 中：

```yaml
database:
  table_prefix: "myapp"
```

---

## 进一步调试

### 1. 查看容器注册信息

在 `app/main.py` 的 `lifespan` 中添加：

```python
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration

entity_config = app_context.get_bean(SecurityEntityConfiguration)
logger.info(f"当前使用的用户模型: {entity_config.user_orm_model}")
logger.info(f"表名: {entity_config.user_orm_model.__tablename__}")
logger.info(f"identifier_fields: {entity_config.identifier_fields}")
```

预期输出：

```
当前使用的用户模型: <class 'app.models.user.User'>
表名: users
identifier_fields: ['username', 'email', 'user_id']
```

### 2. 测试 SQL 生成

```python
from sqlalchemy import select, or_

user_model = entity_config.user_orm_model
identifier = "admin@example.com"

conditions = []
for field_name in ['username', 'email', 'user_id']:
    if hasattr(user_model, field_name):
        field = getattr(user_model, field_name)
        conditions.append(field == identifier)

stmt = select(user_model).where(or_(*conditions))
logger.info(f"生成的 SQL: {stmt}")
```

---

## 总结

**问题**：框架默认使用 `pyspring_user` 表  
**原因**：缺少自定义配置  
**解决**：创建 `app/config/security_config.py` 并重写 `user_orm_model`

✅ **最佳实践**：使用项目初始化脚本 `pyspring init --example` 会自动生成完整配置！
