# DBManagerService 使用指南

## 概述

`DBManagerService` 是一个数据库管理服务，它仿照 `CacheManagerService` 的设计模式实现，提供了自动选择数据库后端的功能。

## 功能特性

- **自动选择数据库**: 优先使用 PostgreSQL，如果不可用则自动切换到 SQLite
- **统一接口**: 提供统一的数据库操作接口（IDBService）
- **单例模式**: 确保数据库服务实例的唯一性
- **健康检查**: 支持数据库连接状态检查

## 架构设计

### 1. 接口层

- `IDBService`: 数据库服务基础接口
- `IPostgresService`: PostgreSQL 服务接口
- `ISqliteService`: SQLite 服务接口

### 2. 实现层

- `PostgresService`: PostgreSQL 数据库服务实现
- `SqliteService`: SQLite 数据库服务实现
- `DBManagerService`: 数据库管理服务

### 3. 目录结构

```
src/ref/
├── core/
│   └── repositories/
│       └── db/
│           ├── service.py              # IDBService 接口
│           ├── postgres/
│           │   ├── interfaces/
│           │   │   └── service.py      # IPostgresService
│           │   └── impl/
│           │       └── service.py      # PostgresService
│           └── sqlite/
│               ├── interfaces/
│               │   └── service.py      # ISqliteService
│               └── impl/
│                   └── service.py      # SqliteService
└── repositories/
    └── db/
        └── manager.py                   # DBManagerService
```

## 使用方法

### 基础使用

```python
from src.ref.core.repositories.db.manager import DBManagerService

# 创建管理器实例
db_manager = DBManagerService()

# 获取可用的数据库服务
db_service = await db_manager.service()

# 执行查询
result = await db_service.fetch_one("SELECT * FROM users WHERE id = :id", {"id": 1})
```

### 数据库操作

#### 1. 查询单条记录

```python
user = await db_service.fetch_one(
    "SELECT * FROM users WHERE email = :email",
    {"email": "user@example.com"}
)
```

#### 2. 查询多条记录

```python
users = await db_service.fetch_all(
    "SELECT * FROM users WHERE status = :status",
    {"status": "active"}
)
```

#### 3. 插入数据

```python
new_user = await db_service.insert(
    "users",
    {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30
    }
)
```

#### 4. 更新数据

```python
success = await db_service.update(
    "users",
    {"name": "Jane Doe", "age": 31},
    {"id": 1}
)
```

#### 5. 删除数据

```python
success = await db_service.delete(
    "users",
    {"id": 1}
)
```

#### 6. 执行自定义SQL

```python
result = await db_service.execute(
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)"
)
```

### 健康检查

```python
# 检查数据库连接
is_available = await db_manager.ping()
if is_available:
    print("数据库连接正常")
else:
    print("数据库连接失败")
```

### 辅助方法

```python
# 生成表名
table_name = DBManagerService.table_name("user", "data")
# 输出: "user_data"

# 使用关键字参数
table_name = DBManagerService.table_name(prefix="app", suffix="logs")
# 输出: "prefix_suffix"
```

## 配置

### PostgreSQL 配置

在系统配置中添加 PostgreSQL 相关配置：

```python
# 环境变量
POSTGRES_HOST = localhost
POSTGRES_PORT = 5432
POSTGRES_DATABASE = mydb
POSTGRES_USER = postgres
POSTGRES_PASSWORD = password
```

### SQLite 配置

```python
# 环境变量
SQLITE_DATABASE = data / app.db
```

## 对比 CacheManagerService

### 相似之处

1. **自动切换机制**:
    - CacheManagerService: Redis → Memory
    - DBManagerService: PostgreSQL → SQLite

2. **单例模式**: 都使用 `ins` 类变量缓存服务实例

3. **统一接口**: 都提供统一的服务接口

4. **健康检查**: 都实现了 `ping()` 方法

### 差异之处

1. **服务类型**:
    - CacheManagerService: 缓存服务
    - DBManagerService: 数据库服务

2. **辅助方法**:
    - CacheManagerService: `key()` 方法用于生成缓存键
    - DBManagerService: `table_name()` 方法用于生成表名

3. **数据操作**:
    - CacheManagerService: get/save/update/delete/clear
    - DBManagerService: fetch_one/fetch_all/insert/update/delete/execute

## 最佳实践

1. **使用依赖注入**: 在需要的地方注入 DBManagerService

```python
class UserService:
    def __init__(self, db_manager: DBManagerService):
        self.db_manager = db_manager

    async def get_user(self, user_id: int):
        db = await self.db_manager.service()
        return await db.fetch_one(
            "SELECT * FROM users WHERE id = :id",
            {"id": user_id}
        )
```

2. **异常处理**: 始终处理数据库操作可能抛出的异常

```python
try:
    result = await db_service.fetch_one(query, params)
except Exception as e:
    logger.error(f"数据库查询失败: {e}")
    # 处理异常
```

3. **参数化查询**: 使用参数化查询防止SQL注入

```python
# ✅ 正确
await db_service.fetch_one(
    "SELECT * FROM users WHERE id = :id",
    {"id": user_id}
)

# ❌ 错误
await db_service.fetch_one(
    f"SELECT * FROM users WHERE id = {user_id}"
)
```

## 运行测试

```bash
python test_db_manager.py
```

## 依赖

- SQLAlchemy (异步支持)
- asyncpg (PostgreSQL 驱动)
- aiosqlite (SQLite 驱动)

安装依赖:

```bash
pip install sqlalchemy[asyncio] asyncpg aiosqlite
```

## 未来扩展

1. 支持更多数据库类型（MySQL、MongoDB等）
2. 添加连接池管理
3. 实现事务支持
4. 添加查询构建器
5. 支持数据库迁移
