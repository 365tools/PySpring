# 应用配置指南 (APPLICATION_CONFIG_GUIDE.md)

## 概述

PySpring 提供了完整的配置管理系统，支持多种配置源和灵活的配置方式。

## 配置文件结构

```
config/
├── application.yaml     # 应用配置（新增）
├── container.yaml       # IoC 容器配置
├── logging.yaml         # 日志配置
├── repositories.yaml    # 数据库和缓存配置
└── security.yaml        # 安全和认证配置
```

## application.yaml 配置项

### 1. 应用基本信息

```yaml
app:
  name: "PySpring Application"
  version: "1.0.0"
  description: "基于 PySpring 框架构建的应用"
  environment: "development"  # development, staging, production
```

### 2. 服务器配置

```yaml
server:
  host: "0.0.0.0"        # 监听地址
  port: 8000              # 监听端口
  reload: true            # 热重载（仅开发环境）
  log_level: "info"       # 日志级别
  workers: 1              # 工作进程数（生产环境建议=CPU核心数）
  timeout: 30             # 请求超时时间（秒）
  max_request_size: 10485760  # 最大请求体大小（10MB）
```

### 3. CORS 配置

```yaml
cors:
  enabled: true
  allow_origins:
    - "*"  # 生产环境请修改为具体域名
  allow_credentials: true
  allow_methods: [ "*" ]
  allow_headers: [ "*" ]
```

### 4. API 配置

```yaml
api:
  prefix: "/api/v1"
  openapi_enabled: true
  docs_url: "/docs"
  redoc_url: "/redoc"
```

## 使用方式

### 方式 1：在 main.py 中使用（推荐）

```python
from pyspring.system.impl.service import SystemService

if __name__ == "__main__":
    import uvicorn

    # 从配置文件读取服务器配置
    system_service = SystemService()

    uvicorn.run(
        "main:app",
        host=system_service.get_config("server.host", "0.0.0.0"),
        port=int(system_service.get_config("server.port", 8000)),
        reload=system_service.get_config("server.reload", True),
        log_level=system_service.get_config("server.log_level", "info")
    )
```

### 方式 2：通过 IoC 容器

```python
from pyspring.core.ioc import ApplicationContext

# 获取系统服务
system_service = ApplicationContext.service(SystemService)

# 读取配置
app_name = system_service.get_config("app.name")
server_port = system_service.get_config("server.port", 8000)
```

### 方式 3：在 FastAPI 应用中使用

```python
from fastapi import FastAPI, Depends
from pyspring.core.ioc import ApplicationContext


def get_system_service():
    return ApplicationContext.service(SystemService)


@app.get("/config")
async def get_config(system: SystemService = Depends(get_system_service)):
    return {
        "app_name": system.get_config("app.name"),
        "environment": system.get_config("app.environment")
    }
```

## 配置优先级

PySpring 按以下优先级加载配置（优先级从低到高）：

1. **config/*.yaml 文件** - 基础配置
2. **.env 文件** - 环境特定配置
3. **环境变量** - 运行时配置
4. **代码默认值** - 兜底配置

示例：

```bash
# .env 文件
SERVER_PORT=9000
SERVER_HOST=127.0.0.1

# 环境变量会覆盖 yaml 配置
export SERVER_PORT=9000
```

## CORS 配置说明

### 开发环境

```yaml
cors:
  allow_origins: [ "*" ]  # 允许所有源
```

### 生产环境

```yaml
cors:
  allow_origins:
    - "https://example.com"
    - "https://www.example.com"
  allow_credentials: true
```

## 多环境配置

### 方式 1：使用环境变量切换

```bash
# 开发环境
export APP_ENVIRONMENT=development

# 生产环境
export APP_ENVIRONMENT=production
```

### 方式 2：使用不同的配置文件

```
config/
├── application.yaml          # 默认配置
├── application.dev.yaml      # 开发环境
├── application.staging.yaml  # 测试环境
└── application.prod.yaml     # 生产环境
```

在代码中根据环境加载：

```python
import os

env = os.getenv("APP_ENVIRONMENT", "development")
config_file = f"config/application.{env}.yaml"
```

## 配置验证

建议在应用启动时验证必需的配置：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 验证配置
    system = SystemService()

    # 检查必需配置
    required_configs = [
        "server.host",
        "server.port",
        "app.name"
    ]

    for config_key in required_configs:
        value = system.get_config(config_key)
        if value is None:
            raise ValueError(f"Missing required config: {config_key}")

    logger.info("✅ 配置验证通过")

    yield
```

## 最佳实践

1. **敏感信息使用环境变量**
   ```yaml
   # ❌ 不要在 yaml 中写敏感信息
   database:
     password: "secret123"
   
   # ✅ 使用环境变量
   database:
     password: ${DATABASE_PASSWORD}
   ```

2. **生产环境禁用调试功能**
   ```yaml
   production:
     server:
       reload: false
       workers: 4
     development:
       debug: false
   ```

3. **使用类型安全的配置访问**
   ```python
   # ✅ 提供默认值和类型转换
   port = int(system.get_config("server.port", 8000))
   
   # ❌ 直接使用可能为 None
   port = system.get_config("server.port")
   ```

4. **CORS 配置要严格**
   ```yaml
   # 开发环境可以宽松
   development:
     cors:
       allow_origins: ["*"]
   
   # 生产环境必须限制
   production:
     cors:
       allow_origins:
         - "https://example.com"
   ```

## 配置热重载

PySpring 支持配置热重载（需要在应用中实现）：

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ConfigReloadHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".yaml"):
            logger.info(f"配置文件已更新: {event.src_path}")
            # 重新加载配置
            system_service.reload_config()
```

## 常见问题

### Q1: 配置文件找不到？

**A:** 检查配置文件路径，PySpring 会在以下位置查找：

- `config/*.yaml`
- `./config/*.yaml`
- `项目根目录/config/*.yaml`

### Q2: 环境变量不生效？

**A:** 确保环境变量名称正确，使用大写和下划线：

```bash
# YAML 配置
server.port

# 环境变量名
SERVER_PORT
```

### Q3: 如何调试配置加载？

**A:** 启用调试日志：

```yaml
logging:
  level: "DEBUG"
```

## 参考

- [IoC 配置指南](IOC_CONFIG_GUIDE.md)
- [日志配置指南](LOGGING_CONFIG_GUIDE.md)
- [数据库配置指南](REPOSITORIES_CONFIG_GUIDE.md)
- [安全配置指南](SECURITY_CONFIG_GUIDE.md)
