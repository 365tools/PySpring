# 日志系统配置指南

## 概述

PySpring 的日志系统基于 Loguru 构建，现在支持通过 YAML 配置文件进行灵活管理。无需修改代码即可调整日志行为。

## 配置文件位置

日志配置管理器会按以下顺序查找配置文件：

1. `{项目根目录}/config/logging.yaml`
2. `{当前工作目录}/config/logging.yaml`
3. `{当前工作目录}/logging.yaml`

如果找不到配置文件，将使用默认配置。

## 完整配置示例

```yaml
# 日志系统配置
logging:
  # 日志级别: TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
  level: "INFO"
  
  # 控制台日志配置
  console:
    enabled: true
    colorize: true
    format: "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[file_relative]}</cyan>:<cyan>{line}</cyan> | {message}"
    
  # 文件日志配置
  file:
    enabled: false
    path: "logs/app.log"
    rotation: "10 MB"
    retention: "7 days"
    compression: "zip"
    format: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[file_relative]}:{line} | {message}"
    
  # 高级配置
  advanced:
    backtrace: true
    diagnose: true
    enqueue: true
    depth_offset: 1
    
  # 过滤器配置
  filters:
    health_check: true
    metrics: true
    favicon: true
    custom_paths:
      - "/health"
      - "/metrics"
      - "/favicon.ico"
    
  # 日志拦截配置
  intercept:
    stdlib: true
    uvicorn: true
    fastapi: true
    watchfiles: true
    custom_loggers:
      - "sqlalchemy.engine"
      - "asyncio"
```

## 配置项详解

### 1. 基础配置

#### `logging.level`

日志级别，控制输出的最低日志级别。

**可选值**:

- `TRACE`: 最详细的追踪信息
- `DEBUG`: 调试信息
- `INFO`: 一般信息（推荐默认值）
- `SUCCESS`: 成功信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

**建议**:

- 开发环境: `DEBUG`
- 生产环境: `INFO` 或 `WARNING`

---

### 2. 控制台日志 (`console`)

#### `console.enabled`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否启用控制台日志输出

#### `console.colorize`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否启用彩色输出
- **建议**: 开发环境 `true`，生产环境 `false`（日志收集系统可能不支持颜色）

#### `console.format`

- **类型**: `string`
- **说明**: 控制台日志格式化字符串

**可用变量**:

- `{time}`: 时间戳（可自定义格式，如 `{time:YYYY-MM-DD HH:mm:ss.SSS}`）
- `{level}`: 日志级别
- `{message}`: 日志消息
- `{name}`: 记录器名称
- `{function}`: 函数名
- `{line}`: 行号
- `{file}`: 文件路径
- `{extra[file_relative]}`: 相对文件路径（自动计算）

**格式示例**:

```yaml
# 简洁格式
format: "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}"

# 标准格式（推荐）
format: "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[file_relative]}</cyan>:<cyan>{line}</cyan> | {message}"

# 详细格式
format: "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}"
```

---

### 3. 文件日志 (`file`)

#### `file.enabled`

- **类型**: `boolean`
- **默认值**: `false`
- **说明**: 是否启用文件日志
- **建议**: 生产环境建议设置为 `true`

#### `file.path`

- **类型**: `string`
- **默认值**: `"logs/app.log"`
- **说明**: 日志文件路径（相对于项目根目录）

#### `file.rotation`

- **类型**: `string`
- **说明**: 日志轮转策略

**按大小轮转**:

```yaml
rotation: "10 MB"   # 10 兆字节
rotation: "500 MB"  # 500 兆字节
rotation: "1 GB"    # 1 吉字节
```

**按时间轮转**:

```yaml
rotation: "12:00"    # 每天中午12点
rotation: "1 week"   # 每周
rotation: "1 month"  # 每月
```

#### `file.retention`

- **类型**: `string`
- **默认值**: `"7 days"`
- **说明**: 日志保留时间，超过时间的旧日志将被删除

**示例**:

```yaml
retention: "1 day"
retention: "1 week"
retention: "1 month"
retention: "3 months"
```

#### `file.compression`

- **类型**: `string`
- **默认值**: `"zip"`
- **说明**: 压缩格式

**可选值**: `zip`, `gz`, `tar`, `tar.gz`, `tar.bz2`

---

### 4. 高级配置 (`advanced`)

#### `advanced.backtrace`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 异常时是否显示完整的调用栈回溯
- **建议**: 开发环境 `true`，生产环境根据需要设置

#### `advanced.diagnose`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否在日志中显示变量值（用于诊断）
- **⚠️ 注意**: 生产环境建议设置为 `false`，因为可能泄露敏感信息

#### `advanced.enqueue`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否使用异步队列处理日志（提高性能）
- **建议**: 生产环境建议设置为 `true`

#### `advanced.depth_offset`

- **类型**: `integer`
- **默认值**: `1`
- **说明**: 调用深度偏移量，用于准确定位日志调用位置
- **⚠️ 注意**: 通常不需要修改

---

### 5. 过滤器配置 (`filters`)

用于过滤掉不想记录的日志消息。

#### `filters.health_check`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 过滤健康检查相关的日志

#### `filters.metrics`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 过滤指标收集相关的日志

#### `filters.favicon`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 过滤 favicon.ico 请求日志

#### `filters.custom_paths`

- **类型**: `array of strings`
- **默认值**: `["/health", "/metrics", "/favicon.ico"]`
- **说明**: 自定义要过滤的路径列表

**示例**:

```yaml
filters:
  health_check: true
  metrics: true
  favicon: true
  custom_paths:
    - "/health"
    - "/metrics"
    - "/favicon.ico"
    - "/api/internal/ping"  # 添加自定义路径
```

---

### 6. 日志拦截配置 (`intercept`)

用于拦截 Python 标准库和第三方库的日志，统一通过 Loguru 处理。

#### `intercept.stdlib`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否拦截 Python 标准库 logging 模块

#### `intercept.uvicorn`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否拦截 Uvicorn 服务器日志

#### `intercept.fastapi`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否拦截 FastAPI 框架日志

#### `intercept.watchfiles`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否拦截 watchfiles 日志（会自动过滤 "changes detected" 消息）

#### `intercept.custom_loggers`

- **类型**: `array of strings`
- **默认值**: `[]`
- **说明**: 要拦截的自定义日志记录器名称列表

**示例**:

```yaml
intercept:
  stdlib: true
  uvicorn: true
  fastapi: true
  watchfiles: true
  custom_loggers:
    - "sqlalchemy.engine"    # 拦截 SQLAlchemy SQL 日志
    - "httpx"                # 拦截 HTTPX 请求日志
    - "redis"                # 拦截 Redis 日志
    - "asyncio"              # 拦截 asyncio 日志
```

---

## 使用方法

### 基础用法

日志服务会在首次使用时自动加载配置：

```python
from pyspring.log.loguru.logger import logger

# 直接使用
logger.info("应用启动")
logger.debug("调试信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 绑定上下文

```python
# 绑定请求ID
request_logger = logger.bind(request_id="123456")
request_logger.info("处理请求")
```

### 手动初始化（可选）

如果需要强制重新加载配置：

```python
from pyspring.log.loguru.config.formatter import LoguruConfig

# 从 YAML 配置初始化
LoguruConfig.setup_from_yaml(force=True)
```

---

## 环境配置示例

### 开发环境配置

**config/logging.yaml**:

```yaml
logging:
  level: "DEBUG"
  console:
    enabled: true
    colorize: true
    format: "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[file_relative]}</cyan>:<cyan>{line}</cyan> | {message}"
  file:
    enabled: false
  advanced:
    backtrace: true
    diagnose: true
    enqueue: false
  intercept:
    stdlib: true
    uvicorn: true
    fastapi: true
    watchfiles: true
```

### 生产环境配置

**config/logging.yaml**:

```yaml
logging:
  level: "INFO"
  console:
    enabled: true
    colorize: false  # 日志收集器可能不支持颜色
    format: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[file_relative]}:{line} | {message}"
  file:
    enabled: true
    path: "logs/production.log"
    rotation: "500 MB"
    retention: "30 days"
    compression: "gz"
    format: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[file_relative]}:{line} | {message}"
  advanced:
    backtrace: false
    diagnose: false  # 安全考虑
    enqueue: true
  filters:
    health_check: true
    metrics: true
  intercept:
    stdlib: true
    uvicorn: true
    custom_loggers:
      - "sqlalchemy.engine"
```

### 测试环境配置

**config/logging.yaml**:

```yaml
logging:
  level: "DEBUG"
  console:
    enabled: true
    colorize: true
  file:
    enabled: true
    path: "logs/test.log"
    rotation: "50 MB"
    retention: "3 days"
  advanced:
    backtrace: true
    diagnose: true
```

---

## 最佳实践

### 1. 日志级别选择

```python
# TRACE - 极详细的追踪信息（很少使用）
logger.trace("进入函数 process_data")

# DEBUG - 调试信息
logger.debug(f"处理数据: {data}")

# INFO - 一般信息（默认级别）
logger.info("服务启动成功")

# SUCCESS - 成功操作
logger.success("用户注册成功")

# WARNING - 警告
logger.warning("缓存命中率低于 50%")

# ERROR - 错误
logger.error("数据库连接失败")

# CRITICAL - 严重错误
logger.critical("系统内存不足，即将崩溃")
```

### 2. 异常日志

```python
try:
    result = process_data()
except Exception as e:
    # 使用 exception() 自动记录异常堆栈
    logger.exception("处理数据时发生异常")
```

### 3. 结构化日志

```python
# 使用字典绑定结构化信息
logger.bind(user_id=user.id, action="login", ip=request.client.host).info("用户登录")
```

### 4. 性能日志

```python
import time

start = time.time()
result = expensive_operation()
duration = time.time() - start

logger.bind(duration=duration).info(f"操作完成，耗时 {duration:.2f}秒")
```

---

## 故障排查

### 配置文件未加载

如果看到提示 "⚠️ 未找到日志配置文件，使用默认配置"：

1. 检查配置文件路径是否正确
2. 确认文件名为 `logging.yaml` 而不是 `logging.yml`
3. 查看控制台输出的搜索路径

### 日志未输出

1. 检查 `logging.level` 是否设置过高
2. 确认 `console.enabled` 为 `true`
3. 检查是否被过滤器过滤

### 文件日志未生成

1. 确认 `file.enabled` 为 `true`
2. 检查文件路径权限
3. 查看是否有错误日志输出

### 日志格式不正确

1. 检查 `format` 字符串语法
2. 确认使用的变量名正确
3. 注意 `{extra[file_relative]}` 需要方括号

---

## 高级主题

### 动态重载配置

```python
from pyspring.log.loguru.config.manager import LoggingConfigManager

# 重新加载配置
config_manager = LoggingConfigManager()
config_manager.reload()

# 重新初始化日志系统
from pyspring.log.loguru.config.formatter import LoguruConfig

LoguruConfig.setup_from_yaml(force=True)
```

### 多环境配置

使用环境变量切换配置文件：

```python
import os
from pathlib import Path

env = os.getenv("ENV", "development")
config_path = Path(f"config/logging.{env}.yaml")
```

### 自定义日志处理器

如果需要添加自定义处理器（如发送到远程服务器）：

```python
from loguru import logger as _loguru

# 添加自定义处理器
_loguru.add(custom_handler, format="{message}", level="ERROR")
```

---

## 参考资料

- [Loguru 官方文档](https://loguru.readthedocs.io/)
- [YAML 语法参考](https://yaml.org/)
- PySpring 日志源码: `src/pyspring/log/loguru/`
