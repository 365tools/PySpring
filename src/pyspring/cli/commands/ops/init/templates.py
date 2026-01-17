"""
PySpring CLI Init Command Templates
"""

ENV_FILE_CONTENT = """# PySpring Framework Environment Configuration
# Copy this file to .env and modify values accordingly

# ==================== JWT Configuration ====================
# JWT Signing Secret (Required for Token signing)
JWT_SECRET_KEY={jwt_secret}

# JWT Algorithm (Optional, default HS256)
# JWT_ALGORITHM=HS256

# Access Token Expiration (seconds, optional)
# ACCESS_TOKEN_EXPIRE=3600

# Refresh Token Expiration (seconds, optional)
# REFRESH_TOKEN_EXPIRE=2592000

# ==================== JWT Encryption Configuration ====================
# Enable JWT Encryption (Optional, default false)
# JWT_ENCRYPTION_ENABLED=true

# JWT Encryption Key (Required when encryption is enabled)
{jwt_encryption_key_line}

# ==================== Database Configuration ====================
# PostgreSQL Configuration
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=your-password
# POSTGRES_DB=your-database

# MySQL Configuration
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=root
# MYSQL_PASSWORD=your-password
# MYSQL_DB=your-database

# ==================== Redis Configuration ====================
# Redis Host
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_PASSWORD=your-password
# REDIS_DB=0

# ==================== Application Configuration ====================
# Application Environment (development, testing, production)
# APP_ENV=development

# Log Level (DEBUG, INFO, WARNING, ERROR)
# LOG_LEVEL=INFO
"""

POSTGRES_INIT_SCRIPT = """-- PySpring Framework Database Initialization Script (PostgreSQL)
-- Generated at: {date}
-- Based on PySpring ORM model definitions

-- ==================== Table Structure ====================
{table_definitions}

-- ==================== Initial Data ====================
-- Insert default roles
INSERT INTO role (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('admin', 'Administrator', 'System Administrator with all permissions', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user', 'User', 'Standard User Role', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- Insert default permissions
INSERT INTO permission (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('user:read', 'View User', 'View user information', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:write', 'Edit User', 'Create and edit users', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:delete', 'Delete User', 'Delete users', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:read', 'View Role', 'View role information', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:write', 'Edit Role', 'Create and edit roles', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:delete', 'Delete Role', 'Delete roles', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- Assign all permissions to admin role
INSERT INTO role_permission (role_code, permission_code, active, deleted, creator, created_time, modifier, modified_time)
SELECT r.code, p.code, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP
FROM role r, permission p
WHERE r.code = 'admin'
ON CONFLICT DO NOTHING;

-- Complete
SELECT '✅ Database initialization complete' AS status;
"""

SQLITE_INIT_SCRIPT = """-- PySpring Framework Database Initialization Script (SQLite)
-- Generated at: {date}
-- Based on PySpring ORM model definitions

-- ==================== Table Structure ====================
{table_definitions}

-- ==================== Initial Data ====================
-- Insert default roles
INSERT OR IGNORE INTO role (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('admin', 'Administrator', 'System Administrator with all permissions', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user', 'User', 'Standard User Role', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP);

-- Insert default permissions
INSERT OR IGNORE INTO permission (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('user:read', 'View User', 'View user information', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:write', 'Edit User', 'Create and edit users', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:delete', 'Delete User', 'Delete users', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:read', 'View Role', 'View role information', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:write', 'Edit Role', 'Create and edit roles', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:delete', 'Delete Role', 'Delete roles', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP);

-- Assign all permissions to admin role
INSERT OR IGNORE INTO role_permission (role_code, permission_code, active, deleted, creator, created_time, modifier, modified_time)
SELECT r.code, p.code, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP
FROM role r, permission p
WHERE r.code = 'admin';
"""

DB_README_CONTENT = """# Database Scripts

This directory contains database initialization scripts for the PySpring framework.

## File Description

- `init_postgresql.sql`: PostgreSQL database initialization script
- `init_sqlite.sql`: SQLite database initialization script

## Usage

### PostgreSQL

```bash
# Create database
createdb your_database_name

# Execute initialization script
psql -U your_username -d your_database_name -f init_postgresql.sql
```

### SQLite

```bash
# Execute initialization script
sqlite3 your_database.db < init_sqlite.sql
```

## Database Table Description

### Core Tables

- **users**: User table
- **roles**: Role table
- **user_roles**: User-Role association table
- **permissions**: Permission table
- **role_permissions**: Role-Permission association table

### Security Tables

- **refresh_tokens**: Refresh Token table

## Default Data

The scripts will automatically create the following default data:

### Roles
- `admin`: Administrator (has all permissions)
- `user`: Standard User

### Permissions
- `user:read`: View User
- `user:write`: Edit User
- `user:delete`: Delete User
- `role:read`: View Role
- `role:write`: Edit Role
- `role:delete`: Delete Role

## Important Notes

1. Please ensure the database is created before running the script.
2. The script supports idempotent execution and will not overwrite existing data.
3. For production environments, please adjust table structures and indexes according to actual needs.
4. Regular database backups are recommended.
"""

APP_INIT_FILE = '"""PySpring Application"""\n'
