# SQL INSERT 语句修复指南

## 问题原因

你的INSERT语句只提供了部分字段：

```sql
INSERT
OR IGNORE INTO role (code, name, description, status) VALUES ...
```

但表结构中有这些必填字段（NOT NULL）：

- `active`
- `deleted`
- `creator`
- `created_time`
- `modifier`
- `modified_time`

虽然SQLAlchemy模型中定义了Python级别的默认值，但直接执行SQL时无法使用这些默认值。

## 解决方案1：在INSERT中补全所有必填字段

```sql
-- 插入默认角色
INSERT
OR IGNORE INTO role (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('admin', '管理员', '系统管理员，拥有所有权限', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user', '普通用户', '普通用户角色', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP);

-- 插入默认权限
INSERT
OR IGNORE INTO permission (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('user:read', '查看用户', '查看用户信息', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:write', '编辑用户', '创建和编辑用户', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:delete', '删除用户', '删除用户', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:read', '查看角色', '查看角色信息', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:write', '编辑角色', '创建和编辑角色', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:delete', '删除角色', '删除角色', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP);

-- 为管理员角色分配所有权限（注意：role_permission表的role_code和permission_code类型应该是VARCHAR而不是INTEGER）
INSERT
OR IGNORE INTO role_permission (role_code, permission_code, active, deleted, creator, created_time, modifier, modified_time)
SELECT r.code,
       p.code,
       1,
       0,
       'system',
       CURRENT_TIMESTAMP,
       'system',
       CURRENT_TIMESTAMP
FROM role r,
     permission p
WHERE r.code = 'admin';
```

## 解决方案2：修改表结构，添加DEFAULT子句（推荐）

修改 [define.py](d:\Project\PycharmProjects\PySpring\src\pyspring\repositories\db\models\common\define.py)，使用`server_default`：

```python
from datetime import datetime, UTC
from sqlalchemy import Column, String, Boolean, INT, TIMESTAMP, text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""

    version = Column(INT, nullable=True)
    active = Column(Boolean, nullable=False, default=True, server_default=text("1"))
    deleted = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    creator = Column(String, nullable=False, default="system", server_default=text("'system'"))
    created_time = Column(
        TIMESTAMP, nullable=False, default=lambda: datetime.now(UTC), server_default=text("CURRENT_TIMESTAMP")
    )
    modifier = Column(String, nullable=False, default="system", server_default=text("'system'"))
    modified_time = Column(
        TIMESTAMP,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )
```

这样重新生成SQL脚本时，CREATE TABLE会包含DEFAULT子句，INSERT时可以省略这些字段。

## 额外发现的问题

在 `role_permission` 表中：

```sql
CREATE TABLE IF NOT EXISTS role_permission
(
    role_code
    INTEGER
    NOT
    NULL, -- ❌ 类型错误，应该是VARCHAR
    permission_code
    INTEGER
    NOT
    NULL, -- ❌ 类型错误，应该是VARCHAR
    FOREIGN
    KEY
(
    role_code
) REFERENCES role
(
    code
),
    FOREIGN KEY
(
    permission_code
) REFERENCES permission
(
    code
)
    )
```

`role.code` 和 `permission.code` 都是VARCHAR类型，但外键字段定义成了INTEGER，这会导致外键约束失败。

需要检查对应的ORM模型定义是否正确。
