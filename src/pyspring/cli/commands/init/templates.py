"""
PySpring CLI Init Command Templates
"""

ENV_FILE_CONTENT = """# PySpring 框架环境变量配置
# 复制此文件为 .env 并修改相应的值

# ==================== JWT 配置 ====================
# JWT 签名密钥（必须设置，用于 Token 签名）
JWT_SECRET_KEY={jwt_secret}

# JWT 算法（可选，默认 HS256）
# JWT_ALGORITHM=HS256

# Access Token 过期时间（秒，可选）
# ACCESS_TOKEN_EXPIRE=3600

# Refresh Token 过期时间（秒，可选）
# REFRESH_TOKEN_EXPIRE=2592000

# ==================== JWT 加密配置 ====================
# 是否启用 JWT 加密（可选，默认 false）
# JWT_ENCRYPTION_ENABLED=true

# JWT 加密密钥（启用加密时必须设置）
{jwt_encryption_key_line}

# ==================== 数据库配置 ====================
# PostgreSQL 配置
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=your-password
# POSTGRES_DB=your-database

# MySQL 配置
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=root
# MYSQL_PASSWORD=your-password
# MYSQL_DB=your-database

# ==================== Redis 配置 ====================
# Redis 主机
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_PASSWORD=your-password
# REDIS_DB=0

# ==================== 应用配置 ====================
# 应用环境（development, testing, production）
# APP_ENV=development

# 日志级别（DEBUG, INFO, WARNING, ERROR）
# LOG_LEVEL=INFO
"""

POSTGRES_INIT_SCRIPT = """-- PySpring 框架数据库初始化脚本 (PostgreSQL)
-- 自动生成于: {date}
-- 基于 PySpring ORM 模型定义

-- ==================== 表结构 ====================
{table_definitions}

-- ==================== 初始化数据 ====================
-- 插入默认角色
INSERT INTO role (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('admin', '管理员', '系统管理员，拥有所有权限', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user', '普通用户', '普通用户角色', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- 插入默认权限
INSERT INTO permission (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('user:read', '查看用户', '查看用户信息', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:write', '编辑用户', '创建和编辑用户', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:delete', '删除用户', '删除用户', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:read', '查看角色', '查看角色信息', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:write', '编辑角色', '创建和编辑角色', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:delete', '删除角色', '删除角色', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- 为管理员角色分配所有权限
INSERT INTO role_permission (role_code, permission_code, active, deleted, creator, created_time, modifier, modified_time)
SELECT r.code, p.code, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP
FROM role r, permission p
WHERE r.code = 'admin'
ON CONFLICT DO NOTHING;

-- 完成
SELECT '✅ 数据库初始化完成' AS status;
"""

SQLITE_INIT_SCRIPT = """-- PySpring 框架数据库初始化脚本 (SQLite)
-- 自动生成于: {date}
-- 基于 PySpring ORM 模型定义

-- ==================== 表结构 ====================
{table_definitions}

-- ==================== 初始化数据 ====================
-- 插入默认角色
INSERT OR IGNORE INTO role (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('admin', '管理员', '系统管理员，拥有所有权限', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user', '普通用户', '普通用户角色', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP);

-- 插入默认权限
INSERT OR IGNORE INTO permission (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('user:read', '查看用户', '查看用户信息', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:write', '编辑用户', '创建和编辑用户', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:delete', '删除用户', '删除用户', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:read', '查看角色', '查看角色信息', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:write', '编辑角色', '创建和编辑角色', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:delete', '删除角色', '删除角色', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP);

-- 为管理员角色分配所有权限
INSERT OR IGNORE INTO role_permission (role_code, permission_code, active, deleted, creator, created_time, modifier, modified_time)
SELECT r.code, p.code, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP
FROM role r, permission p
WHERE r.code = 'admin';
"""

DB_README_CONTENT = """# 数据库脚本

本目录包含 PySpring 框架的数据库初始化脚本。

## 文件说明

- `init_postgresql.sql`: PostgreSQL 数据库初始化脚本
- `init_sqlite.sql`: SQLite 数据库初始化脚本

## 使用方法

### PostgreSQL

```bash
# 创建数据库
createdb your_database_name

# 执行初始化脚本
psql -U your_username -d your_database_name -f init_postgresql.sql
```

### SQLite

```bash
# 执行初始化脚本
sqlite3 your_database.db < init_sqlite.sql
```

## 数据库表说明

### 核心表

- **users**: 用户表
- **roles**: 角色表
- **user_roles**: 用户角色关联表
- **permissions**: 权限表
- **role_permissions**: 角色权限关联表

### 安全相关表

- **refresh_tokens**: Refresh Token 表

## 默认数据

脚本会自动创建以下默认数据：

### 角色
- `admin`: 管理员（拥有所有权限）
- `user`: 普通用户

### 权限
- `user:read`: 查看用户
- `user:write`: 编辑用户
- `user:delete`: 删除用户
- `role:read`: 查看角色
- `role:write`: 编辑角色
- `role:delete`: 删除角色

## 注意事项

1. 执行脚本前请确保数据库已创建
2. 脚本支持重复执行，不会覆盖已有数据
3. 生产环境请根据实际需求调整表结构和索引
4. 建议定期备份数据库
"""

APP_INIT_FILE = '"""PySpring Application"""\n'
