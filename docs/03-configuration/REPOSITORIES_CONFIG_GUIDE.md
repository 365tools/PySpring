# 数据仓储配置指南

## 概述

PySpring 的数据仓储系统（缓存和数据库）现在支持通过 YAML 配置文件进行统一管理。无需在代码中硬编码连接信息和配置参数。

## 配置文件位置

配置管理器会按以下顺序查找配置文件：

1. `{项目根目录}/config/repositories.yaml`
2. `{当前工作目录}/config/repositories.yaml`
3. `{当前工作目录}/repositories.yaml`

如果找不到配置文件，将使用默认配置。

## 完整配置示例

```yaml
# 缓存配置
cache:
  type: "redis"  # redis 或 memory
  
  redis:
    host: "localhost"
    port: 6379
    db: 0
    password: null
    pool:
      max_connections: 50
      socket_keepalive: true
      socket_connect_timeout: 5
      retry_on_timeout: true
  
  memory:
    max_size: 1000
    ttl: 3600

# 数据库配置
database:
  type: "postgresql"  # postgresql, sqlite, mysql
  
  postgresql:
    host: "localhost"
    port: 5432
    database: "app_db"
    user: "postgres"
    password: null
    pool:
      size: 5
      max_overflow: 10
      recycle: 3600
      timeout: 30
      pre_ping: true
  
  sqlite:
    database: "data/app.db"
    pool:
      size: 5
      max_overflow: 10
      recycle: 3600
```

---

## 缓存配置详解

### 1. 基础配置

#### `cache.type`

- **类型**: `string`
- **可选值**: `redis`, `memory`
- **默认值**: `redis`
- **说明**: 缓存类型选择
- **建议**:
    - 开发环境: `memory`（无需外部依赖）
    - 生产环境: `redis`（支持分布式、持久化）

---

### 2. Redis 配置 (`cache.redis`)

#### 连接配置

##### `redis.host`

- **类型**: `string`
- **默认值**: `"localhost"`
- **环境变量**: `REDIS_HOST`
- **说明**: Redis 服务器地址

##### `redis.port`

- **类型**: `integer`
- **默认值**: `6379`
- **环境变量**: `REDIS_PORT`
- **说明**: Redis 服务器端口

##### `redis.db`

- **类型**: `integer`
- **默认值**: `0`
- **范围**: `0-15`
- **环境变量**: `REDIS_DB`
- **说明**: Redis 数据库编号

##### `redis.password`

- **类型**: `string` or `null`
- **默认值**: `null`
- **环境变量**: `REDIS_PASSWORD`（推荐）
- **说明**: Redis 密码
- **⚠️ 安全提示**: 生产环境建议通过环境变量设置，不要直接写在配置文件中

#### 连接池配置 (`redis.pool`)

##### `pool.max_connections`

- **类型**: `integer`
- **默认值**: `50`
- **说明**: 最大连接数
- **建议**:
    - 小型应用: 20-50
    - 中型应用: 50-100
    - 大型应用: 100-200

##### `pool.socket_keepalive`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否保持 TCP 连接

##### `pool.socket_connect_timeout`

- **类型**: `integer`
- **默认值**: `5`
- **单位**: 秒
- **说明**: 连接超时时间

##### `pool.retry_on_timeout`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 超时是否自动重试

**示例配置**:

```yaml
cache:
  type: "redis"
  redis:
    host: "redis.example.com"
    port: 6379
    db: 0
    # 通过环境变量设置密码
    password: null
    pool:
      max_connections: 100
      socket_keepalive: true
      socket_connect_timeout: 10
      retry_on_timeout: true
```

---

### 3. 内存缓存配置 (`cache.memory`)

#### `memory.max_size`

- **类型**: `integer`
- **默认值**: `1000`
- **说明**: 最大缓存项数，使用 LRU 策略淘汰

#### `memory.ttl`

- **类型**: `integer`
- **默认值**: `3600`
- **单位**: 秒
- **说明**: 默认过期时间

**示例配置**:

```yaml
cache:
  type: "memory"
  memory:
    max_size: 5000
    ttl: 7200
```

---

## 数据库配置详解

### 1. 基础配置

#### `database.type`

- **类型**: `string`
- **可选值**: `postgresql`, `sqlite`, `mysql`
- **默认值**: `postgresql`
- **说明**: 数据库类型选择
- **建议**:
    - 开发环境: `sqlite`（零配置）
    - 生产环境: `postgresql` 或 `mysql`

---

### 2. PostgreSQL 配置 (`database.postgresql`)

#### 连接配置

##### `postgresql.host`

- **类型**: `string`
- **默认值**: `"localhost"`
- **环境变量**: `POSTGRES_HOST`
- **说明**: PostgreSQL 服务器地址

##### `postgresql.port`

- **类型**: `integer`
- **默认值**: `5432`
- **环境变量**: `POSTGRES_PORT`
- **说明**: PostgreSQL 服务器端口

##### `postgresql.database`

- **类型**: `string`
- **默认值**: `"app_db"`
- **环境变量**: `POSTGRES_DB`
- **说明**: 数据库名称

##### `postgresql.user`

- **类型**: `string`
- **默认值**: `"postgres"`
- **环境变量**: `POSTGRES_USER`
- **说明**: 数据库用户名

##### `postgresql.password`

- **类型**: `string` or `null`
- **默认值**: `null`
- **环境变量**: `POSTGRES_PASSWORD`（推荐）
- **说明**: 数据库密码
- **⚠️ 安全提示**: 生产环境必须通过环境变量设置

#### 连接池配置 (`postgresql.pool`)

##### `pool.size`

- **类型**: `integer`
- **默认值**: `5`
- **说明**: 连接池大小
- **建议**:
    - 小型应用: 5-10
    - 中型应用: 10-20
    - 大型应用: 20-50

##### `pool.max_overflow`

- **类型**: `integer`
- **默认值**: `10`
- **说明**: 最大溢出连接数（超过 pool.size 时允许的额外连接）

##### `pool.recycle`

- **类型**: `integer`
- **默认值**: `3600`
- **单位**: 秒
- **说明**: 连接回收时间，定期回收连接避免长时间占用

##### `pool.timeout`

- **类型**: `integer`
- **默认值**: `30`
- **单位**: 秒
- **说明**: 获取连接的超时时间

##### `pool.pre_ping`

- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 连接使用前是否 ping 检查，确保连接可用

**示例配置**:

```yaml
database:
  type: "postgresql"
  postgresql:
    host: "postgres.production.com"
    port: 5432
    database: "production_db"
    user: "app_user"
    # 通过环境变量设置密码
    password: null
    pool:
      size: 20
      max_overflow: 30
      recycle: 1800
      timeout: 60
      pre_ping: true
```

---

### 3. MySQL 配置 (`database.mysql`)

#### 连接配置

##### `mysql.host`

- **类型**: `string`
- **默认值**: `"localhost"`
- **环境变量**: `MYSQL_HOST`

##### `mysql.port`

- **类型**: `integer`
- **默认值**: `3306`
- **环境变量**: `MYSQL_PORT`

##### `mysql.database`

- **类型**: `string`
- **默认值**: `"app_db"`
- **环境变量**: `MYSQL_DB`

##### `mysql.user`

- **类型**: `string`
- **默认值**: `"root"`
- **环境变量**: `MYSQL_USER`

##### `mysql.password`

- **类型**: `string` or `null`
- **默认值**: `null`
- **环境变量**: `MYSQL_PASSWORD`（推荐）

##### `mysql.charset`

- **类型**: `string`
- **默认值**: `"utf8mb4"`
- **说明**: 字符集，建议使用 utf8mb4 支持 emoji 和特殊字符

#### 连接池配置

与 PostgreSQL 连接池配置相同。

**示例配置**:

```yaml
database:
  type: "mysql"
  mysql:
    host: "mysql.example.com"
    port: 3306
    database: "myapp_db"
    user: "myapp_user"
    password: null
    charset: "utf8mb4"
    pool:
      size: 10
      max_overflow: 20
      recycle: 3600
      timeout: 30
      pre_ping: true
```

---

### 4. SQLite 配置 (`database.sqlite`)

#### `sqlite.database`

- **类型**: `string`
- **默认值**: `"data/app.db"`
- **说明**: 数据库文件路径
    - 相对路径：相对于项目根目录
    - 绝对路径：直接使用指定路径
    - 目录不存在时会自动创建

#### 连接池配置

SQLite 也支持连接池配置（仅 `size`, `max_overflow`, `recycle`）。

**示例配置**:

```yaml
database:
  type: "sqlite"
  sqlite:
    database: "data/development.db"
    pool:
      size: 5
      max_overflow: 10
      recycle: 3600
```

---

## 使用方法

### 基础用法

服务会在实例化时自动加载配置：

```python
from pyspring.repositories.cache.redis.impl.service import RedisService
from pyspring.repositories.db.ins.postgres.impl.service import PostgresService

# 自动从 YAML 配置加载
redis = RedisService()
postgres = PostgresService()
```

### 通过管理器获取配置

```python
from pyspring.repositories.config_manager import RepositoriesConfigManager

config_manager = RepositoriesConfigManager()

# 获取缓存配置
cache_config = config_manager.get_cache_config()
print(f"缓存类型: {cache_config['type']}")

# 获取数据库配置
db_config = config_manager.get_database_config()
print(f"数据库类型: {db_config['type']}")

# 使用点号路径获取配置
redis_host = config_manager.get('cache.redis.host')
postgres_pool_size = config_manager.get('database.postgresql.pool.size')
```

---

## 环境配置示例

### 开发环境（快速启动）

**config/repositories.yaml**:

```yaml
cache:
  type: "memory"  # 无需 Redis
  memory:
    max_size: 1000
    ttl: 3600

database:
  type: "sqlite"  # 无需外部数据库
  sqlite:
    database: "data/dev.db"
```

### 测试环境（独立数据）

**config/repositories.yaml**:

```yaml
cache:
  type: "memory"
  memory:
    max_size: 500
    ttl: 1800

database:
  type: "sqlite"
  sqlite:
    database: "data/test.db"
```

### 生产环境（高性能）

**config/repositories.yaml**:

```yaml
cache:
  type: "redis"
  redis:
    host: "redis-cluster.production.com"
    port: 6379
    db: 0
    password: null  # 通过环境变量 REDIS_PASSWORD 设置
    pool:
      max_connections: 200
      socket_keepalive: true
      socket_connect_timeout: 10
      retry_on_timeout: true

database:
  type: "postgresql"
  postgresql:
    host: "postgres-primary.production.com"
    port: 5432
    database: "production_db"
    user: "app_user"
    password: null  # 通过环境变量 POSTGRES_PASSWORD 设置
    pool:
      size: 50
      max_overflow: 100
      recycle: 1800
      timeout: 60
      pre_ping: true
```

**环境变量设置**:

```bash
export REDIS_PASSWORD="your_redis_password"
export POSTGRES_PASSWORD="your_postgres_password"
```

---

## 环境变量支持

所有敏感信息都支持通过环境变量设置，优先级：

**环境变量 > YAML 配置 > 默认值**

### 支持的环境变量

**Redis**:

- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_DB`
- `REDIS_PASSWORD`

**PostgreSQL**:

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

**MySQL**:

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_DB`
- `MYSQL_USER`
- `MYSQL_PASSWORD`

---

## 最佳实践

### 1. 安全性

```yaml
# ❌ 不要这样做（密码明文）
cache:
  redis:
    password: "my_secret_password"

# ✅ 应该这样做（通过环境变量）
cache:
  redis:
    password: null  # 通过 REDIS_PASSWORD 环境变量设置
```

### 2. 连接池大小

根据应用负载和数据库资源调整：

```python
# 经验公式
pool_size = (CPU核心数 * 2) + 有效磁盘数

# 示例：4核CPU，1个SSD
recommended_pool_size = (4 * 2) + 1 = 9
```

### 3. 多环境管理

```bash
# 方式1：不同配置文件
config/repositories.dev.yaml
config/repositories.test.yaml
config/repositories.prod.yaml

# 方式2：环境变量控制
export APP_ENV=production
# 在代码中根据 APP_ENV 加载不同配置
```

### 4. 缓存策略选择

```yaml
# 开发环境：快速启动
cache:
  type: "memory"

# 单机生产：简单可靠
cache:
  type: "redis"
  redis:
    host: "localhost"

# 分布式生产：高可用
cache:
  type: "redis"
  redis:
    host: "redis-cluster.example.com"
    pool:
      max_connections: 200
```

---

## 故障排查

### 配置文件未加载

如果看到 "⚠️ 未找到仓储配置文件，使用默认配置"：

1. 检查配置文件路径
2. 确认文件名为 `repositories.yaml`
3. 查看控制台输出的搜索路径

### Redis 连接失败

1. 检查 Redis 服务是否运行：`redis-cli ping`
2. 确认 host、port 配置正确
3. 检查防火墙和网络配置
4. 验证密码（如果有）

### PostgreSQL 连接失败

1. 检查 PostgreSQL 服务状态
2. 确认数据库、用户、密码正确
3. 检查 `pg_hba.conf` 配置
4. 验证网络连接和防火墙

### SQLite 文件权限错误

1. 检查数据库文件路径是否可写
2. 确认目录存在且有权限
3. 查看磁盘空间是否充足

---

## 性能优化建议

### 1. 连接池优化

```yaml
# 高并发场景
database:
  postgresql:
    pool:
      size: 50
      max_overflow: 100
      timeout: 60
      pre_ping: true

# 低并发场景
database:
  postgresql:
    pool:
      size: 5
      max_overflow: 10
      timeout: 30
      pre_ping: false
```

### 2. 缓存配置优化

```yaml
# 高性能缓存
cache:
  redis:
    pool:
      max_connections: 200
      socket_connect_timeout: 10
      retry_on_timeout: true
```

### 3. 连接回收策略

```yaml
# 短连接场景（API服务）
pool:
  recycle: 1800  # 30分钟

# 长连接场景（后台任务）
pool:
  recycle: 7200  # 2小时
```

---

## 高级主题

### 动态重载配置

```python
from pyspring.repositories.config_manager import RepositoriesConfigManager

config_manager = RepositoriesConfigManager()
config_manager.reload()
```

### 自定义配置路径

修改 `config_manager.py` 中的 `_load_config` 方法添加自定义路径。

### 多数据源支持

```yaml
database:
  type: "postgresql"
  # 主库
  postgresql:
    host: "primary.db.com"
  # 可以在应用层实现读写分离
  postgresql_read:
    host: "replica.db.com"
```

---

## 参考资料

- [Redis 配置文档](https://redis.io/docs/management/config/)
- [PostgreSQL 连接池优化](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [SQLAlchemy 连接池配置](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- PySpring 仓储源码: `src/pyspring/repositories/`
