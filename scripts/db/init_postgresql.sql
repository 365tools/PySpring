-- ============================================================================
-- PySpring 框架默认数据库表结构 - PostgreSQL
-- ============================================================================
-- 说明：
-- 1. 这是框架内置的保底脚本，提供基本的用户鉴权授权表结构
-- 2. 用户项目可以在 project/scripts/db/init_postgresql.sql 中自定义扩展
-- 3. MigrationInitializer 会优先使用用户项目的脚本
-- ============================================================================

-- 用户表
CREATE TABLE IF NOT EXISTS users
(
    id
    SERIAL
    PRIMARY
    KEY,
    username
    VARCHAR
(
    50
) UNIQUE NOT NULL,
    email VARCHAR
(
    100
) UNIQUE NOT NULL,
    password_hash VARCHAR
(
    255
) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- 角色表
CREATE TABLE IF NOT EXISTS roles
(
    id
    SERIAL
    PRIMARY
    KEY,
    name
    VARCHAR
(
    50
) UNIQUE NOT NULL,
    description VARCHAR
(
    200
),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- 权限表
CREATE TABLE IF NOT EXISTS permissions
(
    id
    SERIAL
    PRIMARY
    KEY,
    name
    VARCHAR
(
    100
) UNIQUE NOT NULL,
    resource VARCHAR
(
    100
) NOT NULL,
    action VARCHAR
(
    50
) NOT NULL,
    description VARCHAR
(
    200
),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles
(
    user_id
    INTEGER
    NOT
    NULL
    REFERENCES
    users
(
    id
) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles
(
    id
)
  ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY
(
    user_id,
    role_id
)
    );

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions
(
    role_id
    INTEGER
    NOT
    NULL
    REFERENCES
    roles
(
    id
) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions
(
    id
)
  ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY
(
    role_id,
    permission_id
)
    );

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource);
CREATE INDEX IF NOT EXISTS idx_permissions_action ON permissions(action);

-- 插入默认角色
INSERT INTO roles (name, description)
VALUES ('admin', '管理员角色，拥有所有权限'),
       ('user', '普通用户角色，拥有基本权限') ON CONFLICT (name) DO NOTHING;

-- 插入默认权限
INSERT INTO permissions (name, resource, action, description)
VALUES ('users:read', 'users', 'read', '查看用户信息'),
       ('users:write', 'users', 'write', '创建/更新用户'),
       ('users:delete', 'users', 'delete', '删除用户'),
       ('roles:read', 'roles', 'read', '查看角色'),
       ('roles:write', 'roles', 'write', '管理角色') ON CONFLICT (name) DO NOTHING;

-- 为 admin 角色分配所有权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r,
     permissions p
WHERE r.name = 'admin' ON CONFLICT DO NOTHING;

-- 为 user 角色分配基本权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r,
     permissions p
WHERE r.name = 'user'
  AND p.name IN ('users:read') ON CONFLICT DO NOTHING;

-- 更新时间戳触发器
CREATE
OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at
= CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$
LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE
    ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
