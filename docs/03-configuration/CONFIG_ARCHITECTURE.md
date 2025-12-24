# PySpring 配置文件职责划分

## 配置文件总览

| 配置文件                  | 主要职责        | 核心配置项                                           |
|-----------------------|-------------|-------------------------------------------------|
| **application.yaml**  | 应用和服务器基础配置  | app, server, api, monitoring, development       |
| **container.yaml**    | IoC 容器和依赖注入 | scan, container                                 |
| **logging.yaml**      | 日志系统配置      | logging (level, console, file, filters)         |
| **repositories.yaml** | 数据存储配置      | database, redis, cache                          |
| **security.yaml**     | 安全和认证配置     | authentication, authorization, cors, rate_limit |

## 详细配置项分配

### application.yaml

```yaml
✅ app (应用信息)
✅ server (host, port, reload, log_level, workers)
✅ api (prefix, docs_url, openapi配置)
✅ monitoring (health_check, metrics)
✅ development (debug, auto_reload)
❌ cors (移除，归入 security.yaml)
```

### security.yaml

```yaml
✅ authentication (JWT, 认证提供者, 白名单)
✅ authorization (角色权限, 路径映射)
✅ security.rate_limit (限流配置)
✅ security.cors (跨域配置) ← 唯一位置
```

### logging.yaml

```yaml
✅ logging.level (日志级别)
✅ logging.console (控制台输出)
✅ logging.file (文件日志)
✅ logging.filters.health_check (过滤健康检查日志) ← 与 application.yaml 不冲突
```

### repositories.yaml

```yaml
✅ database (PostgreSQL/SQLite配置)
✅ redis (Redis配置)
✅ cache (缓存策略)
```

### container.yaml

```yaml
✅ scan (服务扫描路径)
✅ container (懒加载, 接口映射)
```

## 配置项去重结果

### ✅ 已解决的重复配置

1. **CORS 配置** - 统一在 `security.yaml`
    - ❌ 从 `application.yaml` 移除
    - ✅ 保留在 `security.yaml`

2. **健康检查配置** - 不冲突
    - `application.yaml`: `monitoring.health_check: true` (启用端点)
    - `logging.yaml`: `filters.health_check: true` (过滤日志)
    - 含义不同，都保留

3. **host/port 配置** - 按职责分离
    - `application.yaml`: `server.host`, `server.port` (应用服务器)
    - `repositories.yaml`: `redis.host`, `redis.port` (Redis服务器)
    - `repositories.yaml`: `database.host`, `database.port` (数据库服务器)
    - 不同服务，不冲突

## 配置优先级

1. **环境变量** (最高优先级)
2. **命令行参数**
3. **配置文件** (yaml)
4. **代码默认值** (最低优先级)

## 配置加载示例

### 读取服务器配置

```python
from pyspring.system.impl.service import SystemService

system = SystemService()
host = system.get_config("server.host", "0.0.0.0")
port = system.get_config("server.port", 8000)
```

### 读取 CORS 配置

```python
cors_enabled = system.get_config("security.cors.enabled", True)
allow_origins = system.get_config("security.cors.allow_origins", ["*"])
```

### 读取数据库配置

```python
db_host = system.get_config("database.postgres.host", "localhost")
db_port = system.get_config("database.postgres.port", 5432)
```

## 最佳实践

### ✅ 推荐做法

1. **按职责划分配置**
    - 应用基础 → application.yaml
    - 安全认证 → security.yaml
    - 数据存储 → repositories.yaml

2. **环境特定配置使用环境变量**
   ```bash
   export SERVER_PORT=9000
   export JWT_SECRET_KEY=your-secret-key
   ```

3. **敏感信息不写配置文件**
   ```yaml
   # ❌ 不要这样
   jwt:
     secret_key: "my-secret-123"
   
   # ✅ 使用环境变量
   jwt:
     secret_key: null  # 从 JWT_SECRET_KEY 环境变量读取
   ```

### ❌ 避免做法

1. **不要在多个文件中配置同一项**
2. **不要混淆不同职责的配置**
3. **不要在配置文件中存储敏感信息**

## 配置检查清单

创建新项目时检查：

- [ ] application.yaml 中没有 CORS 配置
- [ ] security.yaml 是 CORS 的唯一配置位置
- [ ] 各配置文件职责清晰，无重复
- [ ] 敏感信息使用环境变量
- [ ] 生产环境配置已审查

## 配置文件示例位置

- 模板文件：`src/pyspring/templates/config/*.yaml`
- 示例文件：`config/*.yaml`
- 文档说明：`docs/*_CONFIG_GUIDE.md`
