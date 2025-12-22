# PySpring 框架安装与初始化指南

## 简介

PySpring 是一个受 Spring Boot 启发的 Python 框架，基于 FastAPI 构建，提供 IoC 容器、自动配置、认证授权等企业级功能。

## 安装

### 1. 通过 pip 安装（推荐）

```bash
pip install pyspring
```

### 2. 从源码安装

```bash
git clone https://github.com/365tools/PySpring.git
cd PySpring
pip install -e .
```

## 快速开始

### 1. 初始化项目

安装 PySpring 后，在您的项目目录中运行：

```bash
# 在当前目录初始化
pyspring init

# 在指定目录初始化
pyspring init /path/to/your/project

# 查看更多选项
pyspring init --help
```

初始化命令会自动创建以下文件：

```
your-project/
├── config/
│   ├── container.yaml      # IoC 容器配置
│   ├── logging.yaml        # 日志配置
│   ├── repositories.yaml   # 数据库和缓存配置
│   └── security.yaml       # 认证和授权配置
├── .env                    # 环境变量（已生成密钥）
├── .env.example            # 环境变量示例
└── .gitignore              # Git 忽略文件
```

### 2. 配置环境变量

初始化后，`.env` 文件已经自动生成了 JWT 密钥。您需要根据实际需求修改其他配置：

```bash
# JWT 配置（已自动生成）
JWT_SECRET_KEY=automatically-generated-secret-key
JWT_ENCRYPTION_KEY=automatically-generated-encryption-key

# 数据库配置（根据需要修改）
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your-user
POSTGRES_PASSWORD=your-password
POSTGRES_DB=your-database

# Redis 配置（根据需要修改）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-password
```

### 3. 编写应用代码

创建 `main.py`：

```python
from fastapi import FastAPI
from pyspring.ioc.container import ServiceContainer
from pyspring.system.config.manager import ConfigManager

# 创建 FastAPI 应用
app = FastAPI()

# 初始化配置管理器
config_manager = ConfigManager()
config_manager.load_config("config")

# 初始化 IoC 容器
container = ServiceContainer()
container.register_all()

@app.get("/")
async def root():
    return {"message": "Hello PySpring!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 4. 运行应用

```bash
python main.py
```

或使用 uvicorn：

```bash
uvicorn main:app --reload
```

## 初始化选项

### 完整初始化（默认）

创建所有配置文件：

```bash
pyspring init
```

### 最小化初始化

仅创建核心安全配置：

```bash
pyspring init --minimal
```

### 强制覆盖

强制覆盖已存在的配置文件：

```bash
pyspring init --force
```

### 跳过环境变量

不生成 `.env` 文件（手动管理环境变量）：

```bash
pyspring init --skip-env
```

## 配置文件说明

### container.yaml - IoC 容器配置

配置服务扫描路径和容器行为：

```yaml
scan:
  packages:
    - src.pyspring.repositories
    - your.custom.package  # 添加您的包
  recursive: true

container:
  lazy_loading: true
  auto_interface_mapping: true
```

### logging.yaml - 日志配置

配置日志级别、格式和输出：

```yaml
logging:
  level: "INFO"
  console:
    enabled: true
    colorize: true
  file:
    enabled: true
    path: "logs/app.log"
```

### repositories.yaml - 数据仓储配置

配置数据库和缓存：

```yaml
cache:
  type: "redis"  # 或 "memory"
  redis:
    host: "localhost"
    port: 6379

database:
  type: "postgresql"  # 或 "sqlite", "mysql"
  postgresql:
    host: "localhost"
    database: "app_db"
```

### security.yaml - 安全配置

配置认证、授权和 JWT：

```yaml
authentication:
  enabled: true
  jwt:
    algorithm: "HS256"
    access_token_expire: 3600
    encryption:
      enabled: true  # 启用 JWT 加密
      algorithm: "Fernet"
```

## 环境配置建议

### 开发环境

```yaml
# logging.yaml
logging:
  level: "DEBUG"
  console:
    colorize: true
  file:
    enabled: false

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
      enabled: false  # 开发环境可禁用加密
security:
  rate_limit:
    enabled: false
```

### 生产环境

```yaml
# logging.yaml
logging:
  level: "INFO"
  console:
    colorize: false
  file:
    enabled: true
    rotation: "500 MB"
    retention: "30 days"

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
      enabled: true  # 生产必须启用
security:
  rate_limit:
    enabled: true
```

## 安全注意事项

1. **保护环境变量**: 永远不要将 `.env` 文件提交到代码仓库
2. **更换密钥**: 生产环境必须使用独立的 JWT 密钥
3. **启用加密**: 生产环境建议启用 JWT 加密
4. **使用 HTTPS**: 生产环境必须使用 HTTPS
5. **限流配置**: 启用 rate_limit 防止暴力破解

## 依赖安装

PySpring 需要以下可选依赖，根据使用的功能安装：

```bash
# JWT 加密（推荐）
pip install cryptography

# PostgreSQL 支持
pip install asyncpg psycopg2-binary

# MySQL 支持
pip install aiomysql pymysql

# Redis 支持
pip install redis aioredis

# 完整安装
pip install pyspring[full]
```

## 故障排查

### 问题: 模板文件不存在

```
错误: 模板文件不存在: security.yaml
```

**解决方案**: 重新安装 PySpring

```bash
pip install --force-reinstall pyspring
```

### 问题: cryptography 未安装

```
警告: cryptography 库未安装，跳过加密密钥生成
```

**解决方案**: 安装 cryptography

```bash
pip install cryptography
```

### 问题: 配置文件已存在

```
警告: 文件已存在，跳过: config/security.yaml
```

**解决方案**: 使用 `--force` 选项强制覆盖

```bash
pyspring init --force
```

## 示例项目

完整的示例项目请参考：

- [基础示例](https://github.com/365tools/PySpring/tree/main/examples/basic)
- [认证示例](https://github.com/365tools/PySpring/tree/main/examples/auth)
- [完整应用](https://github.com/365tools/PySpring/tree/main/examples/full-app)

## 更多文档

- [完整文档](https://pyspring.readthedocs.io/)
- [API 参考](https://pyspring.readthedocs.io/api/)
- [认证配置指南](./SECURITY_CONFIG_GUIDE.md)
- [JWT 加密指南](./JWT_ENCRYPTION_GUIDE.md)
- [数据库管理指南](./DB_MANAGER_USAGE_GUIDE.md)

## 获取帮助

- GitHub Issues: https://github.com/365tools/PySpring/issues
- 讨论区: https://github.com/365tools/PySpring/discussions
- 邮件: allureyc@gmail.com

## 许可证

Apache License 2.0
