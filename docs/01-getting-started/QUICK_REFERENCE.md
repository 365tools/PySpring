# PySpring 快速参考

## 安装

```bash
pip install pyspring
```

## 初始化项目

```bash
# 基本初始化
pyspring init

# 在指定目录初始化
pyspring init /path/to/project

# 强制覆盖
pyspring init --force

# 最小配置
pyspring init --minimal
```

## CLI 命令

| 命令                         | 说明           |
|----------------------------|--------------|
| `pyspring init`            | 初始化项目配置      |
| `pyspring init --help`     | 查看帮助         |
| `pyspring init --force`    | 强制覆盖已存在的文件   |
| `pyspring init --minimal`  | 仅创建核心配置      |
| `pyspring init --skip-env` | 跳过 .env 文件生成 |

## 配置文件

初始化后会创建以下文件：

```
your-project/
├── config/
│   ├── container.yaml      # IoC 容器配置
│   ├── logging.yaml        # 日志配置
│   ├── repositories.yaml   # 数据库和缓存配置
│   └── security.yaml       # 认证和授权配置
├── .env                    # 环境变量
├── .env.example            # 环境变量示例
└── .gitignore              # Git 忽略文件
```

## 环境变量

### JWT 配置

```bash
# JWT 签名密钥（必须）
JWT_SECRET_KEY=your-secret-key

# JWT 加密（可选，推荐生产环境启用）
JWT_ENCRYPTION_ENABLED=true
JWT_ENCRYPTION_KEY=your-encryption-key

# Token 过期时间（可选）
ACCESS_TOKEN_EXPIRE=3600        # 1小时
REFRESH_TOKEN_EXPIRE=2592000    # 30天
```

### 数据库配置

```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=your-database

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DB=your-database
```

### Redis 配置

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-password
REDIS_DB=0
```

## 基本使用

### 1. 创建应用

```python
from fastapi import FastAPI
from pyspring.ioc.container import ServiceContainer
from pyspring.system.config.manager import ConfigManager

app = FastAPI()

# 加载配置
config_manager = ConfigManager()
config_manager.load_config("config")

# 初始化容器
container = ServiceContainer()
container.register_all()

@app.get("/")
async def root():
    return {"message": "Hello PySpring!"}
```

### 2. 认证接口

```python
@app.post("/api/auth/login")
async def login(username: str, password: str):
    from pyspring.security.auth.impl.login import LoginService
    
    login_service = container.get(LoginService)
    result = await login_service.login(
        user_id="1",
        username=username,
        roles=["admin"]
    )
    return result
```

### 3. 受保护的接口

```python
from pyspring.security.auth.middleware.auth import AuthMiddleware
from fastapi import Depends

# 添加中间件
app.add_middleware(AuthMiddleware)

@app.get("/api/user/profile")
async def get_profile(
    current_user: dict = Depends(AuthMiddleware.get_current_user)
):
    return {"user": current_user}
```

### 4. 数据库操作

```python
@app.get("/api/data")
async def get_data():
    from pyspring.repositories.db.service import DatabaseService
    
    db_service = container.get(DatabaseService)
    
    async with db_service.get_session() as session:
        # 执行查询
        # result = await session.execute(select(Model))
        pass
```

### 5. 缓存操作

```python
@app.get("/api/cache/{key}")
async def get_cache(key: str):
    from pyspring.repositories.cache.service import CacheService
    
    cache_service = container.get(CacheService)
    value = await cache_service.get(key)
    return {"value": value}

@app.post("/api/cache/{key}")
async def set_cache(key: str, value: str):
    cache_service = container.get(CacheService)
    await cache_service.set(key, value, ttl=3600)
    return {"success": True}
```

## 配置模式

### 开发环境

```yaml
# repositories.yaml
cache:
  type: "memory"
database:
  type: "sqlite"
  sqlite:
    database: "data/dev.db"

# security.yaml
authentication:
  jwt:
    encryption:
      enabled: false
security:
  rate_limit:
    enabled: false
```

### 生产环境

```yaml
# repositories.yaml
cache:
  type: "redis"
database:
  type: "postgresql"

# security.yaml
authentication:
  jwt:
    access_token_expire: 1800  # 30分钟
    encryption:
      enabled: true  # 必须启用
security:
  rate_limit:
    enabled: true
```

## JWT 加密

### 生成加密密钥

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

或使用工具：

```bash
python tools/generate_encryption_key.py
```

### 配置加密

```yaml
# config/security.yaml
authentication:
  jwt:
    encryption:
      enabled: true
      encryption_key: null  # 使用环境变量
      algorithm: "Fernet"
```

```bash
# .env
JWT_ENCRYPTION_ENABLED=true
JWT_ENCRYPTION_KEY=your-fernet-key
```

## 常用命令

### 运行应用

```bash
# 开发模式
uvicorn main:app --reload

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 生成密钥

```bash
# JWT 签名密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# JWT 加密密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 文档链接

- 📖 [完整安装指南](./INSTALLATION_GUIDE.md)
- 🔐 [认证配置指南](./SECURITY_CONFIG_GUIDE.md)
- 🔒 [JWT 加密指南](./JWT_ENCRYPTION_GUIDE.md)
- 💾 [数据库管理指南](../src/pyspring/repositories/db/doc/DB_MANAGER_USAGE_GUIDE.md)
- 💡 [示例代码](../examples/)

## 故障排查

### 问题：模板文件不存在

```bash
pip install --force-reinstall pyspring
```

### 问题：cryptography 未安装

```bash
pip install cryptography
```

### 问题：配置文件已存在

```bash
pyspring init --force
```

### 问题：Token 验证失败

1. 检查 JWT_SECRET_KEY 是否设置
2. 检查 Token 是否过期
3. 检查 encryption 配置是否一致

## 获取帮助

- 📧 邮件: allureyc@gmail.com
- 🐛 Issues: https://github.com/365tools/PySpring/issues
- 💬 讨论: https://github.com/365tools/PySpring/discussions
