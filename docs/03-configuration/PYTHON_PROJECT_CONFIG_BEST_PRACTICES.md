# Python 项目配置管理最佳实践

## 📁 推荐的项目结构

### 标准 Python 项目布局（类似 Spring Boot 的 resources）

```
your-project/
├── config/                      # ✅ 配置文件目录（等同于 Spring Boot 的 resources）
│   ├── application.yaml         # 应用主配置
│   ├── logging.yaml            # 日志配置
│   ├── database.yaml           # 数据库配置
│   ├── security.yaml           # 安全配置
│   └── custom.yaml             # 自定义配置
│
├── .env                         # ✅ 环境变量（不提交到 Git）
├── .env.example                # ✅ 环境变量模板（提交到 Git）
├── .env.development            # 开发环境变量
├── .env.production             # 生产环境变量
│
├── src/                        # 源代码目录
│   └── your_app/
│       ├── __init__.py
│       ├── main.py             # 应用入口
│       ├── config/             # 配置类（代码）
│       │   ├── __init__.py
│       │   └── settings.py     # Pydantic 配置模型
│       ├── services/
│       ├── repositories/
│       └── controllers/
│
├── tests/                      # 测试目录
├── logs/                       # 日志输出（不提交到 Git）
├── data/                       # 数据文件
├── requirements.txt            # 依赖列表
├── pyproject.toml             # 项目配置（推荐）
└── README.md
```

### 或者使用 src-layout（更现代的方式）

```
your-project/
├── src/
│   ├── config/                 # ✅ 配置文件也可以放这里
│   │   ├── application.yaml
│   │   ├── logging.yaml
│   │   └── ...
│   └── your_app/
│       └── ...
├── config/                     # ✅ 或者放在项目根目录（推荐）
│   └── ...
├── .env
└── ...
```

---

## 🎯 PySpring 配置文件查找顺序

PySpring 的配置加载器会按以下顺序查找配置文件：

### 1. 项目根目录优先

```
{项目根目录}/config/logging.yaml
{项目根目录}/config/application.yaml
{项目根目录}/config/database.yaml
```

### 2. 当前工作目录

```
{当前目录}/config/logging.yaml
{当前目录}/logging.yaml
```

### 3. 框架默认配置

```
{pyspring安装路径}/templates/config/logging.yaml
```

---

## ✅ 推荐做法：使用 `config/` 目录

### 1. 创建配置目录结构

```bash
# 在项目根目录执行
mkdir config
cd config

# 从框架复制模板配置
# 方式 1: 手动复制
copy path/to/pyspring/templates/config/*.yaml .

# 方式 2: 使用 PySpring CLI（如果有）
pyspring init config
```

### 2. 配置文件示例

#### `config/application.yaml` - 应用配置

```yaml
app:
  name: "MyApp"
  version: "1.0.0"
  environment: ${ENVIRONMENT:development}

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  reload: true  # 开发环境

database:
  type: "postgresql"
  host: ${DB_HOST:localhost}
  port: ${DB_PORT:5432}
  name: ${DB_NAME:myapp}
  username: ${DB_USER:postgres}
  password: ${DB_PASSWORD}  # 从环境变量读取
  pool_size: 10
  echo: false

cache:
  type: "redis"
  host: ${REDIS_HOST:localhost}
  port: ${REDIS_PORT:6379}
  db: 0
  ttl: 3600
```

#### `config/logging.yaml` - 日志配置

```yaml
logging:
  level: ${LOG_LEVEL:INFO}
  
  console:
    enabled: true
    colorize: true
    format: "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}"
  
  file:
    enabled: ${LOG_FILE_ENABLED:false}
    path: "logs/app.log"
    rotation: "10 MB"
    retention: "7 days"
```

#### `.env` - 环境变量（敏感信息）

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp_dev
DB_USER=postgres
DB_PASSWORD=your_secret_password

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT 密钥
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256

# 环境
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

#### `.env.example` - 环境变量模板（提交到 Git）

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_USER=postgres
DB_PASSWORD=your_password_here

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT 密钥（生产环境必须修改）
JWT_SECRET_KEY=change-this-in-production
JWT_ALGORITHM=HS256

# 环境
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## 🔧 在代码中使用配置

### 方式 1：通过 ApplicationContext（推荐）

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pyspring.core.ioc import ApplicationContext


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化 ApplicationContext，自动加载 config/ 下的配置
    ctx = ApplicationContext.initialize(
        base_packages=['your_app']  # 扫描你的包
    )

    await ctx.container.initialize_lifecycle_services()

    yield

    await ctx.container.shutdown_lifecycle_services()


app = FastAPI(lifespan=lifespan)
```

### 方式 2：使用 Pydantic Settings（推荐用于类型安全）

#### 创建 `src/your_app/config/settings.py`：

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseSettings(BaseSettings):
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    name: str = "myapp"
    username: str = "postgres"
    password: str = Field(default="", env="DB_PASSWORD")
    pool_size: int = 10
    
    model_config = SettingsConfigDict(
        env_prefix="DB_",  # 环境变量前缀
        env_file=".env",
        env_file_encoding="utf-8"
    )

class RedisSettings(BaseSettings):
    """Redis 配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    ttl: int = 3600
    
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env"
    )

class AppSettings(BaseSettings):
    """应用主配置"""
    name: str = "MyApp"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    
    # 嵌套配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

# 全局配置实例（单例）
settings = AppSettings()
```

#### 在服务中使用：

```python
from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from your_app.config.settings import settings


@Component
@Singleton
class DatabaseService:
    def __init__(self):
        # 直接使用配置
        self.host = settings.database.host
        self.port = settings.database.port
        self.database = settings.database.name

    async def connect(self):
        connection_string = f"postgresql://{settings.database.username}:{settings.database.password}@{self.host}:{self.port}/{self.database}"
        # 连接数据库...
```

### 方式 3：使用 PySpring 的 ConfigLoader

```python
from pyspring.core.configuration.loader import ConfigLoader

class MyService:
    def __init__(self):
        loader = ConfigLoader()
        
        # 加载 YAML 配置
        app_config = loader.load_yaml(loader.project_root / "config" / "application.yaml")
        
        self.db_host = app_config.get("database", {}).get("host", "localhost")
        self.db_port = app_config.get("database", {}).get("port", 5432)
```

### 方式 4：使用 @Configuration 和 @Bean（类似 Spring Boot）

```python
from pyspring.core.ioc.annotations.configuration import Configuration, Bean
from pyspring.core.ioc.annotations.scope import Singleton
from your_app.config.settings import settings


@Configuration
class AppConfiguration:
    """应用配置类"""

    @Bean()
    @Singleton
    def database_config(self) -> dict:
        """数据库配置 Bean"""
        return {
            "host": settings.database.host,
            "port": settings.database.port,
            "database": settings.database.name,
            "username": settings.database.username,
            "password": settings.database.password,
            "pool_size": settings.database.pool_size
        }

    @Bean()
    @Singleton
    def redis_config(self) -> dict:
        """Redis 配置 Bean"""
        return {
            "host": settings.redis.host,
            "port": settings.redis.port,
            "db": settings.redis.db
        }


# 服务中注入使用
@Component
@Singleton
class UserService:
    def __init__(self, database_config: dict):
        # 自动注入配置
        self.db_config = database_config
```

---

## 📋 .gitignore 配置

在项目根目录的 `.gitignore` 中添加：

```gitignore
# 环境变量（包含敏感信息）
.env
.env.local
.env.*.local

# 不要忽略示例文件
!.env.example

# 日志文件
logs/
*.log

# 数据库文件
*.db
*.sqlite
*.sqlite3

# IDE 配置
.vscode/
.idea/
*.swp
*.swo

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/

# 测试
.pytest_cache/
.coverage
htmlcov/

# 虚拟环境
venv/
env/
ENV/
.venv
```

---

## 🌍 多环境配置管理

### 方式 1：使用不同的 .env 文件

```bash
# 开发环境
cp .env.example .env.development
# 编辑 .env.development

# 生产环境
cp .env.example .env.production
# 编辑 .env.production

# 启动时指定环境
export ENV=production  # Linux/Mac
set ENV=production     # Windows

# 或者在代码中加载
from dotenv import load_dotenv
import os

env = os.getenv("ENV", "development")
load_dotenv(f".env.{env}")
```

### 方式 2：使用多个 YAML 配置文件

```
config/
├── application.yaml          # 基础配置
├── application-dev.yaml      # 开发环境覆盖
├── application-prod.yaml     # 生产环境覆盖
└── application-test.yaml     # 测试环境覆盖
```

```python
import os
import yaml
from pathlib import Path

def load_config():
    config_dir = Path("config")
    
    # 加载基础配置
    with open(config_dir / "application.yaml") as f:
        config = yaml.safe_load(f)
    
    # 根据环境加载覆盖配置
    env = os.getenv("ENV", "development")
    env_config_file = config_dir / f"application-{env}.yaml"
    
    if env_config_file.exists():
        with open(env_config_file) as f:
            env_config = yaml.safe_load(f)
            # 深度合并配置
            config.update(env_config)
    
    return config
```

---

## 🎯 完整示例：FastAPI + PySpring 项目

### 项目结构

```
my-fastapi-app/
├── config/
│   ├── application.yaml
│   ├── logging.yaml
│   ├── database.yaml
│   └── security.yaml
├── .env
├── .env.example
├── src/
│   └── magic/
│       ├── __init__.py
│       ├── main.py
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py
│       ├── services/
│       ├── repositories/
│       └── api/
├── requirements.txt
└── README.md
```

### `src/magic/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pyspring.core.ioc import ApplicationContext
from pyspring.log.instance import logger

# 全局上下文
app_context: ApplicationContext = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global app_context

    logger.info("🚀 应用启动中...")

    # 1. 初始化 ApplicationContext
    # 自动从 config/ 目录加载所有配置文件
    app_context = ApplicationContext.initialize(
        base_packages=['magic']  # 扫描你的包
    )

    # 2. 初始化生命周期服务
    await app_context.container.initialize_lifecycle_services()

    logger.info("✅ 应用启动完成")

    yield  # 应用运行

    # 关闭
    logger.info("👋 应用关闭中...")
    await app_context.container.shutdown_lifecycle_services()
    logger.info("✅ 应用已关闭")


app = FastAPI(
    title="My FastAPI App",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### `src/magic/config/settings.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """应用配置"""
    app_name: str = "My FastAPI App"
    app_version: str = "1.0.0"
    environment: str = "development"
    
    # 数据库
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "myapp"
    db_user: str = "postgres"
    db_password: str = ""
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

settings = Settings()
```

---

## 📚 总结对比

| 特性          | Spring Boot (Java)                | PySpring (Python)          |
|-------------|-----------------------------------|----------------------------|
| **配置目录**    | `src/main/resources`              | `config/` 或 `src/config/`  |
| **配置文件**    | `application.properties` / `.yml` | `application.yaml`         |
| **环境变量**    | `application-{profile}.yml`       | `.env` + `.env.{env}`      |
| **敏感信息**    | 环境变量 / Vault                      | `.env` (不提交 Git)           |
| **配置类**     | `@ConfigurationProperties`        | `Pydantic BaseSettings`    |
| **Bean 配置** | `@Configuration` + `@Bean`        | `@Configuration` + `@Bean` |
| **自动注入**    | `@Autowired`                      | 构造函数参数注入                   |

---

## ✅ 最佳实践清单

- ✅ 使用 `config/` 目录存放配置文件（项目根目录）
- ✅ 使用 `.env` 文件存储敏感信息
- ✅ 提供 `.env.example` 模板给团队成员
- ✅ 在 `.gitignore` 中排除 `.env` 文件
- ✅ 使用 Pydantic Settings 实现类型安全的配置
- ✅ 支持环境变量覆盖配置文件
- ✅ 使用 YAML 格式（比 JSON 更友好）
- ✅ 配置文件支持环境变量插值 `${VAR:default}`
- ✅ 分离开发和生产环境配置
- ✅ 定期更新 `.env.example` 与实际 `.env` 保持同步

---

## 🔗 相关文档

- [日志配置指南](./LOGGING_CONFIG_GUIDE.md)
- [应用配置指南](./APPLICATION_CONFIG_GUIDE.md)
- [IOC 容器配置](../02-core-concepts/IOC_CONFIG_GUIDE.md)
