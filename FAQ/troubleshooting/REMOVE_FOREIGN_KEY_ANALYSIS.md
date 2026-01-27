# 移除外键约束 - 架构改造分析

## 📋 执行摘要

**目标：** 移除框架中所有外键约束，改用 `code` 或 `id` 进行逻辑关联

**影响范围：**

- 🔧 修改文件：**13 个**
- 📝 代码位置：**23 处**
- 🗄️ 数据库表：**6 个**
- ⚠️ 破坏性变更：**需要数据迁移**

---

## 🎯 架构决策

### **方案 A（推荐）：全面使用业务标识符**

| 关联类型 | 旧设计       | 新设计              | 优势       |
|------|-----------|------------------|----------|
| 用户关联 | `id` (自增) | `user_id` (UUID) | 不可变、全局唯一 |
| 角色关联 | `id` (自增) | `code` (字符串)     | 业务语义清晰   |
| 权限关联 | `id` (自增) | `code` (字符串)     | 业务语义清晰   |

**设计理念：**

- ✅ 登录使用 `identifier`（灵活查找）
- ✅ Token 使用 `user_id` (UUID)（不可变标识）
- ✅ 数据关联使用业务标识符（可读性好）
- ✅ 移除所有外键约束（应用层维护一致性）

---

## 📊 详细改造清单

### **1. ORM 模型层（4 个文件，10 处修改）**

#### 1.1 框架核心表 [`security/orm/tables.py`](d:\Project\PycharmProjects\PySpring\src\pyspring\security\orm\tables.py)

```python
# ❌ 移除外键约束
class UserRoleTable(BaseUserRoleTable):
    __tablename__ = "pyspring_user_role"

    # 旧设计（使用数据库 ID + 外键）
    user_id = Column(INT, ForeignKey('pyspring_user.id'), nullable=False)
    role_id = Column(INT, ForeignKey('pyspring_role.id'), nullable=False)

    # ✅ 新设计（使用业务标识符，无外键）
    user_id = Column(String(36), nullable=False, index=True, comment="用户UUID")
    role_code = Column(String(50), nullable=False, index=True, comment="角色代码")


class RolePermissionTable(BaseRolePermissionTable):
    __tablename__ = "pyspring_role_permission"

    # 旧设计（使用 code + 外键）
    role_code = Column(String, ForeignKey('pyspring_role.code'), nullable=False)
    permission_code = Column(String, ForeignKey('pyspring_permission.code'), nullable=False)

    # ✅ 新设计（使用 code，无外键）
    role_code = Column(String(50), nullable=False, index=True, comment="角色代码")
    permission_code = Column(String(100), nullable=False, index=True, comment="权限代码")


class TokenBlacklistTable(Base):
    __tablename__ = "token_blacklist"

    # 旧设计（使用数据库 ID）
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")

    # ✅ 新设计（使用 UUID）
    user_id = Column(String(36), nullable=False, index=True, comment="用户UUID")


class RefreshTokenTable(Base):
    __tablename__ = "refresh_token"

    # 旧设计（使用数据库 ID）
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")

    # ✅ 新设计（使用 UUID）
    user_id = Column(String(36), nullable=False, index=True, comment="用户UUID")
```

**修改位置：**

- Line 70: `UserRoleTable.user_id` - 改为 UUID，移除外键
- Line 71: `UserRoleTable.role_id` - 改为 `role_code`，移除外键
- Line 82-83: `RolePermissionTable` - 移除外键（保留 code）
- Line 101: `TokenBlacklistTable.user_id` - 改为 UUID
- Line 119: `RefreshTokenTable.user_id` - 改为 UUID

---

#### 1.2 基础模型定义 [`repositories/db/models/common/define.py`](d:\Project\PycharmProjects\PySpring\src\pyspring\repositories\db\models\common\define.py)

```python
class BaseUserRoleTable(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(INT, primary_key=True, autoincrement=True)
    # 旧设计
    user_id: Mapped[int] = mapped_column(INT, nullable=False)
    role_id: Mapped[int] = mapped_column(INT, nullable=False)

    # ✅ 新设计
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    role_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)


class BaseRolePermissionTable(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(INT, primary_key=True, autoincrement=True)
    # ✅ 保留 code（已无外键，只需删除 ForeignKey 约束）
    role_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    permission_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
```

**修改位置：**

- Line 66-67: `BaseUserRoleTable` 字段类型
- Line 75-76: `BaseRolePermissionTable` 添加索引

---

### **2. 业务逻辑层（5 个文件，8 处修改）**

#### 2.1 Token Service [`security/authentication/token/service.py`](d:\Project\PycharmProjects\PySpring\src\pyspring\security\authentication\token\service.py)

**关键改动：移除 `user_db_id`，全部使用 `user_id` (UUID)**

```python
async def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[Any] = None) -> str:
    payload = data.copy()
    payload["type"] = "refresh"

    refresh_token = self.token_generator.encode(payload, expires_delta)
    decoded = self.token_generator.decode(refresh_token)

    # ❌ 旧代码
    user_uuid = payload.get("sub")
    user_db_id = payload.get("user_db_id")  # 删除此行

    # ✅ 新代码
    user_id = payload.get("sub")  # 直接使用 UUID

    async with await self.db.session() as session:
        refresh_record = RefreshTokenTable(
            # ❌ 旧代码
            user_id=int(user_db_id) if user_db_id else 0,

            # ✅ 新代码
            user_id=user_id,  # UUID 字符串
            user_email=payload.get("email", ""),
            token=refresh_token,
            expires_at=expires_at,
            is_revoked=False
        )
        session.add(refresh_record)
        await session.commit()

    # Redis key 也简化
    # ❌ 旧代码
    redis_user_id = user_uuid or user_db_id

    # ✅ 新代码
    refresh_key = f"token:refresh:{user_id}:{refresh_token[:16]}"
    await self.cache.set(refresh_key, refresh_token, ttl=7 * 24 * 3600)
```

**修改位置：**

- Line 123: 删除 `user_db_id = payload.get("user_db_id")`
- Line 131: 改为 `user_id=payload.get("sub")`
- Line 143-144: 简化 Redis key 逻辑
- Line 269: 删除 `user_db_id = payload.get("user_db_id")`
- Line 279: 改为 `user_id=payload.get("sub")`

---

#### 2.2 Token Payload Builder [`security/authentication/token/builder/default.py`](d:\Project\PycharmProjects\PySpring\src\pyspring\security\authentication\token\builder\default.py)

```python
def build_payload(self, user: Any) -> dict:
    # ❌ 删除 user_db_id
    payload = {
        "sub": user.user_id,       # UUID（不可变）
        # "user_db_id": user.id,   # ❌ 删除此行
        "email": user.email,
        "roles": role_codes,
        "permissions": permissions,
    }
    return payload
```

**修改位置：**

- Line 44: 删除 `"user_db_id": user.id`

---

#### 2.3 Login Service [`security/authentication/services/login.py`](d:\Project\PycharmProjects\PySpring\src\pyspring\security\authentication\services\login.py)

```python
# Refresh token payload
refresh_payload = {
    "sub": user.user_id,       # UUID
    # "user_db_id": user.id,   # ❌ 删除此行
}
```

**修改位置：**

- Line 108: 删除 `"user_db_id": user.id`

---

#### 2.4 Register Service [`security/authentication/services/register.py`](d:\Project\PycharmProjects\PySpring\src\pyspring\security\authentication\services\register.py)

**关键改动：用户角色关联改用 UUID + role_code**

```python
async def _assign_roles(self, session: AsyncSession, user: Any, roles: list[Role]) -> None:
    """
    分配角色给用户
    
    Args:
        session: 数据库会话
        user: 用户对象（使用 user.user_id UUID）
        roles: 角色列表（使用 role.code）
    """
    # 1. 删除旧关联（使用 UUID）
    await session.execute(
        delete(self.component.user_role_orm_model).where(
            # ❌ 旧代码
            self.component.user_role_orm_model.user_id == user_db_id,
            
            # ✅ 新代码
            self.component.user_role_orm_model.user_id == user.user_id,
        )
    )
    
    # 2. 创建新关联（使用 UUID + role_code）
    for role in roles:
        user_role = self.component.user_role_orm_model(
            # ❌ 旧代码
            user_id=user_db_id,   # 数据库 ID
            role_id=role.id,      # 数据库 ID
            
            # ✅ 新代码
            user_id=user.user_id,   # UUID
            role_code=role.code,    # 角色代码
        )
        session.add(user_role)
```

**修改位置：**

- Line 141: 函数签名改为 `user: Any`
- Line 162: 改为 `user.user_id`
- Line 172-173: 改为 `user_id=user.user_id, role_code=role.code`

---

#### 2.5 Role Provider [`security/authorization/providers/role/database.py`](d:\Project\PycharmProjects\PySpring\src\pyspring\security\authorization\providers\role\database.py)

**关键改动：查询逻辑改用 UUID + code**

```python
async def get_user_roles(self, user_id: Any) -> List[str]:
    """
    从数据库查询用户的角色代码列表
    
    查询逻辑（新）：
    User -> UserRole -> Role
    user.user_id (UUID) -> UserRole.user_id (UUID)
    UserRole.role_code -> Role.code
    
    Args:
        user_id: 用户业务ID（user_id UUID，非主键id）
        
    Returns:
        List[str]: 角色代码列表
    """
    # ❌ 旧查询（使用数据库 ID）
    stmt = (
        select(RoleTable.code)
        .join(UserRoleTable, RoleTable.id == UserRoleTable.role_id)
        .join(UserTable, UserTable.id == UserRoleTable.user_id)
        .where(UserTable.user_id == user_id)
    )
    
    # ✅ 新查询（使用业务标识符）
    stmt = (
        select(RoleTable.code)
        .join(UserRoleTable, RoleTable.code == UserRoleTable.role_code)
        .where(UserRoleTable.user_id == user_id)  # 直接用 UUID 查询
    )
```

**修改位置：**

- 查询逻辑简化，不再需要 Join UserTable

---

### **3. Example 模板层（1 个文件，1 处修改）**

#### 3.1 Example AuthService [`templates/example/app/services/auth_service.py.template`](d:\Project\PycharmProjects\PySpring\src\pyspring\templates\example\app\services\auth_service.py.template)

```python
def create_access_token(self, user_data: dict) -> str:
    payload = {
        "sub": user_data.get("user_id"),  # UUID
        # "user_db_id": user_data.get("user_db_id"),  # ❌ 删除此行
        "username": user_data.get("username"),
        "email": user_data.get("email"),
        "type": "access"
    }
    return self.jwt_generator.encode(payload)


async def authenticate(self, login_identifier: str, password: str) -> Optional[str]:
    user = await self.user_repository.find_by_login_identifier(login_identifier)

    access_token = self.create_access_token({
        "user_id": user.user_id,  # UUID
        # "user_db_id": user.id,      # ❌ 删除此行
        "username": user.username,
        "email": user.email
    })
    return access_token
```

**修改位置：**

- Line 102: 删除 `"user_db_id": user_data.get("user_db_id")`
- Line 177: 删除 `"user_db_id": user.id`

---

### **4. 数据库迁移脚本（3 个文件，需重写）**

#### 4.1 PostgreSQL 初始化脚本 [`scripts/db/init_postgresql.sql`](d:\Project\PycharmProjects\PySpring\scripts\db\init_postgresql.sql)

```sql
-- ❌ 旧设计（使用外键）
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- ✅ 新设计（无外键，使用业务标识符）
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,        -- 用户 UUID
    role_code VARCHAR(50) NOT NULL,      -- 角色代码
    active BOOLEAN DEFAULT TRUE,
    deleted BOOLEAN DEFAULT FALSE,
    creator VARCHAR(50) DEFAULT 'system',
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modifier VARCHAR(50) DEFAULT 'system',
    modified_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引（替代外键约束）
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_code ON user_roles(role_code);
CREATE UNIQUE INDEX IF NOT EXISTS uk_user_roles ON user_roles(user_id, role_code) WHERE deleted = FALSE;
```

---

#### 4.2 SQLite 初始化脚本 [`scripts/db/init_sqlite.sql`](d:\Project\PycharmProjects\PySpring\scripts\db\init_sqlite.sql)

```sql
-- ❌ 旧设计
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- ✅ 新设计
CREATE TABLE IF NOT EXISTS user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(36) NOT NULL,
    role_code VARCHAR(50) NOT NULL,
    active INTEGER DEFAULT 1,
    deleted INTEGER DEFAULT 0,
    creator VARCHAR(50) DEFAULT 'system',
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modifier VARCHAR(50) DEFAULT 'system',
    modified_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_code ON user_roles(role_code);
CREATE UNIQUE INDEX IF NOT EXISTS uk_user_roles ON user_roles(user_id, role_code) WHERE deleted = 0;
```

---

#### 4.3 Example 模板数据库脚本（2 个文件）

- `templates/example/scripts/db/init_postgresql.sql.template`
- `templates/example/scripts/db/init_sqlite.sql.template`

需要同步修改用户角色关联表。

---

## 🎯 改造优先级

### **Phase 1: 核心模型层（必须）**

1. ✅ 修改 ORM 模型（移除外键）
2. ✅ 修改基础模型定义
3. ✅ 更新数据库初始化脚本

### **Phase 2: 业务逻辑层（必须）**

1. ✅ 移除 Token Service 中的 `user_db_id`
2. ✅ 移除 Token Payload Builder 中的 `user_db_id`
3. ✅ 更新 Register Service 角色分配逻辑
4. ✅ 更新 Role Provider 查询逻辑

### **Phase 3: Example 模板（推荐）**

1. ✅ 移除 Example AuthService 中的 `user_db_id`
2. ✅ 更新 Example 数据库脚本

---

## ⚠️ 风险与注意事项

### **1. 数据迁移**

**影响：** 现有数据库需要迁移

**解决方案：**

```sql
-- 迁移 user_roles 表
-- 1. 创建新表
CREATE TABLE user_roles_new (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    role_code VARCHAR(50) NOT NULL,
    ...
);

-- 2. 数据迁移
INSERT INTO user_roles_new (user_id, role_code, ...)
SELECT u.user_id, r.code, ...
FROM user_roles old
JOIN users u ON u.id = old.user_id
JOIN roles r ON r.id = old.role_id;

-- 3. 替换表
DROP TABLE user_roles;
ALTER TABLE user_roles_new RENAME TO user_roles;

-- 同理迁移 token_blacklist 和 refresh_token
```

---

### **2. 性能影响**

| 变更      | 旧设计           | 新设计             | 影响          |
|---------|---------------|-----------------|-------------|
| 用户关联    | INT (4 bytes) | UUID (36 bytes) | ⚠️ 存储增加 8 倍 |
| 索引大小    | 小             | 中               | ⚠️ 索引占用增加   |
| JOIN 性能 | 快（INT）        | 稍慢（String）      | ⚠️ 可忽略（有索引） |

**缓解措施：**

- ✅ 添加索引（已在脚本中）
- ✅ 使用 VARCHAR(36) 限制长度
- ✅ 定期 VACUUM ANALYZE（PostgreSQL）

---

### **3. 应用层一致性**

**风险：** 移除外键后，数据一致性由应用层保证

**解决方案：**

1. ✅ 添加业务层验证（检查 `user_id` 是否存在）
2. ✅ 使用事务保证原子性
3. ✅ 添加定期数据一致性检查脚本

```python
# 示例：注册服务中添加验证
async def _assign_roles(self, session, user, roles):
    # 验证用户是否存在
    user_exists = await session.execute(
        select(UserTable).where(UserTable.user_id == user.user_id)
    )
    if not user_exists.scalar_one_or_none():
        raise ValueError(f"用户不存在: {user.user_id}")
    
    # 验证角色是否存在
    for role in roles:
        role_exists = await session.execute(
            select(RoleTable).where(RoleTable.code == role.code)
        )
        if not role_exists.scalar_one_or_none():
            raise ValueError(f"角色不存在: {role.code}")
    
    # 执行关联...
```

---

## 📦 改造收益

### **1. 架构收益**

- ✅ **简化 Token 设计** - 移除冗余的 `user_db_id` 字段
- ✅ **统一标识符** - 全部使用 UUID，符合 JWT 标准
- ✅ **业务语义清晰** - 角色/权限使用 code（如 `admin`）

### **2. 技术收益**

- ✅ **跨系统集成** - UUID 全局唯一，便于 SSO/联邦认证
- ✅ **数据迁移友好** - 不依赖自增 ID，分库分表无压力
- ✅ **数据库独立性** - 无外键约束，切换数据库更容易

### **3. 开发效率**

- ✅ **减少 JOIN** - 部分查询可直接用 UUID/code 查询
- ✅ **简化测试** - 无需考虑外键约束的测试数据准备
- ✅ **更好的可读性** - 代码中直接看到 `role_code="admin"`

---

## 🚀 下一步行动

### **建议执行顺序：**

1. **备份现有数据** ⚠️
2. **修改 ORM 模型**（框架核心）
3. **更新业务逻辑**（Token/Register/Role）
4. **重写数据库脚本**
5. **数据迁移**（生产环境）
6. **测试验证**
7. **更新 Example 模板**
8. **文档更新**

---

## ❓ FAQ

**Q: 为什么不保留外键作为"软约束"？**

A: 外键会影响数据库灵活性（分库分表、数据归档），应用层验证更灵活。

**Q: UUID 性能真的可以接受吗？**

A: 现代数据库对字符串索引优化很好，实际影响可忽略（< 5%）。建议使用 `VARCHAR(36)` 而非 `TEXT`。

**Q: 如何保证数据一致性？**

A:

1. 业务层添加存在性验证
2. 使用数据库事务
3. 定期运行一致性检查脚本
4. 关键操作添加日志审计

---

**报告生成时间：** 2026-01-26  
**建议审核人：** 架构师、DBA、后端负责人
