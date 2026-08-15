# PySpring 项目初始化指南

本指南介绍如何使用 `pyspring init` 命令快速创建标准化的 PySpring 项目。

## 快速开始

### 基本用法

在空目录中运行：

```bash
pyspring init
```

这将在当前目录创建完整的项目结构。

### 指定目录

```bash
pyspring init /path/to/your/project
```

### 命令选项

```bash
# 查看帮助
pyspring init --help

# 强制覆盖已存在的文件
pyspring init --force

# 只创建最小配置（仅 security.yaml）
pyspring init --minimal

# 跳过 .env 文件生成
pyspring init --skip-env
```

## 生成的项目结构

```
your-project/
├── app/                    # 应用代码
│   ├── api/               # API 路由
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   └── schemas/           # Pydantic schemas
├── config/                 # 配置文件
│   ├── container.yaml     # IoC 容器配置
│   ├── logging.yaml       # 日志配置
│   ├── repositories.yaml  # 数据库与缓存配置
│   └── security.yaml      # 认证与授权配置
├── scripts/               # 脚本文件
│   └── db/               # 数据库初始化脚本
│       ├── init_postgresql.sql
│       ├── init_sqlite.sql
│       └── README.md
├── tests/                 # 测试文件
├── logs/                  # 日志文件
├── data/                  # 数据文件
├── main.py               # 应用入口
├── pyproject.toml        # 项目配置和依赖管理
├── .env                  # 环境变量
├── .env.example          # 环境变量示例
└── .gitignore            # Git 忽略文件
```

## 初始化步骤

### 1. 创建项目

```bash
mkdir my-pyspring-app
cd my-pyspring-app
pyspring init
```

### 2. 安装依赖

使用 pip 安装项目：

```bash
# 安装基础依赖
pip install -e .

# 或安装包含开发工具的依赖
pip install -e .[dev]
```

### 3. 配置环境变量

编辑 `.env` 文件，配置数据库连接、JWT密钥等：

```bash
# JWT 配置
JWT_SECRET_KEY=your-generated-secret-key
JWT_ENCRYPTION_KEY=your-generated-encryption-key

# 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=your-database
```

### 4. 初始化数据库

#### PostgreSQL

```bash
# 创建数据库
createdb your_database_name

# 执行初始化脚本
psql -U postgres -d your_database_name -f scripts/db/init_postgresql.sql
```

#### SQLite

```bash
# 创建数据目录
mkdir -p data

# 执行初始化脚本
sqlite3 data/app.db < scripts/db/init_sqlite.sql
```

### 5. 配置数据库连接

编辑 `config/repositories.yaml`，选择并配置您的数据库：

```yaml
database:
  # 使用 PostgreSQL
  type: "postgresql"
  postgresql:
    host: "${POSTGRES_HOST:localhost}"
    port: ${POSTGRES_PORT:5432}
    user: "${POSTGRES_USER:postgres}"
    password: "${POSTGRES_PASSWORD}"
    database: "${POSTGRES_DB:pyspring}"
```

或使用 SQLite：

```yaml
database:
  # 使用 SQLite
  type: "sqlite"
  sqlite:
    database: "data/app.db"
```

### 6. 启动应用

```bash
python main.py
```

应用将在 `http://localhost:8000` 启动。

访问：

- API 文档: `http://localhost:8000/docs`
- ReDoc 文档: `http://localhost:8000/redoc`
- 健康检查: `http://localhost:8000/health`

## 配置文件说明

### container.yaml - IoC 容器配置

定义服务的依赖注入配置。

### logging.yaml - 日志配置

配置日志级别、格式、输出路径等。

### repositories.yaml - 数据库与缓存配置

配置数据库连接（PostgreSQL/MySQL/SQLite）和 Redis 缓存。

### security.yaml - 认证与授权配置

配置 JWT、密码加密等安全相关设置。

详细说明请参考各配置文件中的注释。

## 数据库初始化脚本

### 表结构

初始化脚本会创建以下表：

**核心表：**

- `users` - 用户表
- `roles` - 角色表
- `user_roles` - 用户角色关联表
- `permissions` - 权限表
- `role_permissions` - 角色权限关联表

**安全相关表：**

- `refresh_tokens` - Refresh Token 表

### 默认数据

脚本会自动创建：

**角色：**

- `admin` - 管理员（拥有所有权限）
- `user` - 普通用户

**权限：**

- `user:read` - 查看用户
- `user:write` - 编辑用户
- `user:delete` - 删除用户
- `role:read` - 查看角色
- `role:write` - 编辑角色
- `role:delete` - 删除角色

## 最佳实践

### 1. 环境变量管理

- ✅ 将 `.env` 添加到 `.gitignore`（已自动配置）
- ✅ 使用 `.env.example` 作为模板
- ✅ 不同环境使用不同的 `.env` 文件
- ✅ 生产环境使用环境变量而非 `.env` 文件

### 2. JWT 密钥安全

- ✅ 使用生成的随机密钥
- ✅ 不同环境使用不同的密钥
- ✅ 定期轮换密钥
- ✅ 生产环境启用 JWT 加密

### 3. 数据库配置

- ✅ 开发环境可使用 SQLite
- ✅ 生产环境使用 PostgreSQL/MySQL
- ✅ 配置数据库连接池
- ✅ 定期备份数据库

### 4. 日志管理

- ✅ 开发环境使用 DEBUG 级别
- ✅ 生产环境使用 INFO 级别
- ✅ 配置日志轮转和清理
- ✅ 敏感信息不要记录到日志

## 开发工作流

### 1. 创建 API 路由

在 `app/api/` 目录创建路由文件：

```python
# app/api/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
async def list_users():
    return {"users": []}
```

在 `main.py` 中注册路由：

```python
from app.api import users

app.include_router(users.router)
```

### 2. 创建数据模型

在 `app/models/` 目录创建 SQLAlchemy 模型。

### 3. 创建业务逻辑

在 `app/services/` 目录创建服务类。

### 4. 创建 Pydantic Schema

在 `app/schemas/` 目录创建请求/响应模型。

### 5. 编写测试

在 `tests/` 目录编写测试用例。

## 常见问题

### Q: 如何更换数据库？

A: 修改 `config/repositories.yaml` 中的 `database.type`，然后配置相应的数据库连接信息。

### Q: 如何启用 JWT 加密？

A: 在 `.env` 中设置：

```bash
JWT_ENCRYPTION_ENABLED=true
JWT_ENCRYPTION_KEY=your-encryption-key
```

详见 [JWT 加密指南](JWT_ENCRYPTION_GUIDE.md)。

### Q: 如何添加新的用户角色？

A: 在数据库中插入新角色，然后分配相应权限：

```sql
INSERT INTO roles (code, name, description) VALUES
    ('editor', '编辑', '内容编辑角色');
    
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.code = 'editor' AND p.code IN ('user:read', 'user:write');
```

### Q: 如何自定义项目结构？

A: `pyspring init` 创建的是标准结构，您可以根据需要调整。只需确保配置文件路径正确。

## 相关文档

- [快速参考](QUICK_REFERENCE.md)
- [安全配置指南](SECURITY_CONFIG_GUIDE.md)
- [JWT 加密指南](JWT_ENCRYPTION_GUIDE.md)
- [数据库配置指南](REPOSITORIES_CONFIG_GUIDE.md)
- [日志配置指南](LOGGING_CONFIG_GUIDE.md)
- [IoC 容器指南](IOC_CONFIG_GUIDE.md)

## 获取帮助

- 查看文档: [docs/](.)
- 提交问题: GitHub Issues
- 参与讨论: GitHub Discussions

---

祝您使用 PySpring 开发愉快！🚀
