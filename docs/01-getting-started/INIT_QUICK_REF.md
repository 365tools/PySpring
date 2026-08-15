# PySpring Init 快速参考

## 一键创建标准化项目

```bash
pyspring init
```

## 生成的结构

```
your-project/
├── app/                    # 应用代码
│   ├── api/               # API 路由
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   └── schemas/           # Pydantic schemas
├── config/                 # 配置文件
│   ├── container.yaml     # IoC 容器
│   ├── logging.yaml       # 日志配置
│   ├── repositories.yaml  # 数据库配置
│   └── security.yaml      # 安全配置
├── scripts/db/            # 数据库脚本
│   ├── init_postgresql.sql
│   ├── init_sqlite.sql
│   └── README.md
├── tests/                 # 测试
├── logs/                  # 日志
├── data/                  # 数据
├── main.py               # 应用入口
├── pyproject.toml        # 项目配置和依赖
├── .env                  # 环境变量
└── .gitignore            # Git 忽略
```

## 快速开始

```bash
# 1. 创建项目
mkdir my-app && cd my-app
pyspring init

# 2. 安装依赖
pip install -e .
# 或包含开发工具: pip install -e .[dev]

# 3. 初始化数据库
# PostgreSQL:
psql -U user -d dbname -f scripts/db/init_postgresql.sql

# 或 SQLite:
sqlite3 data/app.db < scripts/db/init_sqlite.sql

# 4. 配置环境变量
# 编辑 .env 文件

# 5. 启动应用
python main.py
# 访问 http://localhost:8000/docs
```

## 命令选项

```bash
pyspring init [目录]      # 在指定目录初始化
pyspring init --force     # 强制覆盖
pyspring init --minimal   # 最小配置
pyspring init --skip-env  # 跳过 .env
```

## 数据库表

### 核心表

- **users** - 用户
- **roles** - 角色
- **user_roles** - 用户角色关联
- **permissions** - 权限
- **role_permissions** - 角色权限关联

### 安全表

- **refresh_tokens** - Token 管理

### 默认数据

- 角色: `admin`, `user`
- 权限: `user:read/write/delete`, `role:read/write/delete`

## 配置文件

### .env

```bash
JWT_SECRET_KEY=...
JWT_ENCRYPTION_KEY=...
POSTGRES_HOST=localhost
POSTGRES_DB=mydb
```

### repositories.yaml

```yaml
database:
  type: "postgresql"  # 或 "sqlite"
```

## 应用结构

### main.py

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome"}
```

### 添加路由

```python
# app/api/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/users")

# main.py
from app.api import users

app.include_router(users.router)
```

## 重要提醒

- ⚠️ 不要提交 `.env` 到仓库
- ⚠️ 生产环境更换 JWT 密钥
- ⚠️ 定期备份数据库
- ⚠️ 初始化数据库前先创建数据库

## 文档链接

- [完整指南](PROJECT_INIT_GUIDE.md)
- [数据库配置](REPOSITORIES_CONFIG_GUIDE.md)
- [安全配置](SECURITY_CONFIG_GUIDE.md)
- [JWT 加密](JWT_ENCRYPTION_GUIDE.md)

---

快速、简单、标准化！🚀
