# 数据库自动初始化功能

PySpring 提供了强大的数据库自动初始化功能，可以在应用启动时自动创建数据库表结构。

## 功能特性

✅ **自动检测**: 自动查找项目中的 SQL 初始化脚本  
✅ **增量模式**: 只创建不存在的表，保护现有数据  
✅ **全覆盖模式**: 重建所有表（开发环境）  
✅ **灵活配置**: 通过 YAML 文件轻松配置  
✅ **扩展性强**: 基于启动初始化器模式，易于扩展

## 快速开始

### 1. 配置文件

在 `config/repositories.yaml` 中配置：

```yaml
database:
  type: "postgresql"
  
  # 数据库初始化配置
  initialization:
    enabled: true              # 是否启用自动初始化
    mode: "incremental"        # 初始化模式: incremental 或 full
    script_path: null          # SQL 脚本路径（null 则自动检测）
    auto_detect: true          # 是否自动检测脚本路径
  
  postgresql:
    host: "localhost"
    port: 5432
    database: "app_db"
    user: "postgres"
    password: null
```

### 2. SQL 脚本

将数据库初始化脚本放在以下位置（按优先级）：

1. `scripts/db/init_postgresql.sql`
2. `scripts/db/init_sqlite.sql`
3. `scripts/init_*.sql`
4. `db/init_*.sql`

**示例脚本** (scripts/db/init_postgresql.sql):

```sql
-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建角色表
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL
);

-- 初始化数据
INSERT INTO roles (code, name) VALUES
    ('admin', '管理员'),
    ('user', '普通用户')
ON CONFLICT (code) DO NOTHING;
```

### 3. 应用启动代码

在 `main.py` 中集成：

```python
from fastapi import FastAPI
from pyspring.log.loguru.ins import logger
from pyspring.interfaces.IStartupInitializer import StartupInitializerManager
from pyspring.repositories.db.initializer import DatabaseInitializer
from pyspring.repositories.db.manager import DBManagerService
from pyspring.repositories.config_manager import RepositoriesConfigManager

app = FastAPI(title="PySpring Application")

db_manager: DBManagerService = None

@app.on_event("startup")
async def startup_event():
    global db_manager
    
    logger.info("🚀 应用启动中...")
    
    # 1. 初始化数据库管理器
    db_manager = DBManagerService()
    db_service = await db_manager.service()
    
    # 2. 创建启动初始化器管理器
    initializer_manager = StartupInitializerManager()
    
    # 3. 注册数据库初始化器
    config_manager = RepositoriesConfigManager()
    init_config = config_manager.get_database_initialization_config()
    
    if init_config['enabled']:
        db_initializer = DatabaseInitializer(
            db_service=db_service,
            enabled=init_config['enabled'],
            mode=init_config['mode'],
            script_path=init_config['script_path'],
            auto_detect=init_config['auto_detect']
        )
        initializer_manager.register(db_initializer)
    
    # 4. 执行所有初始化器
    await initializer_manager.execute_all(stop_on_failure=True)
    
    logger.info("✅ 应用启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    if db_manager:
        await db_manager.close()
```

## 配置说明

### initialization.enabled

**类型**: `bool`  
**默认值**: `false`  
**说明**: 是否启用数据库自动初始化

**推荐配置**:

- 开发环境: `true` - 快速搭建环境
- 测试环境: `true` - 自动创建测试数据库
- 生产环境: `false` - 使用专业迁移工具（如 Alembic）

### initialization.mode

**类型**: `"incremental" | "full"`  
**默认值**: `"incremental"`  
**说明**: 初始化模式

**incremental（增量模式）**:

- 只创建不存在的表
- 保护现有数据
- 安全，适合生产环境

**full（全覆盖模式）**:

- DROP 并重建所有表
- **会丢失所有数据！**
- 仅用于开发环境

```yaml
# 开发环境 - 全覆盖模式
initialization:
  enabled: true
  mode: "full"

# 生产环境 - 增量模式
initialization:
  enabled: false
  mode: "incremental"
```

### initialization.script_path

**类型**: `string | null`  
**默认值**: `null`  
**说明**: SQL 脚本文件路径（相对于项目根目录）

```yaml
# 指定脚本路径
script_path: "scripts/db/init_postgresql.sql"

# 自动检测（推荐）
script_path: null
```

### initialization.auto_detect

**类型**: `bool`  
**默认值**: `true`  
**说明**: 是否自动检测脚本路径

当设置为 `true` 时，会按以下顺序查找：

1. `scripts/db/init_{database_type}.sql`
2. `scripts/init_{database_type}.sql`
3. `db/init_{database_type}.sql`

## 高级用法

### 自定义初始化器

创建自己的启动初始化器：

```python
from pyspring.interfaces.IStartupInitializer import IStartupInitializer
from pyspring.log.loguru.ins import logger

class CacheWarmupInitializer(IStartupInitializer):
    """缓存预热初始化器"""
    
    def __init__(self, cache_service, enabled: bool = True):
        super().__init__(enabled)
        self.cache_service = cache_service
    
    def get_name(self) -> str:
        return "CacheWarmupInitializer"
    
    async def initialize(self) -> bool:
        logger.info("🔥 开始缓存预热...")
        
        # 预加载热数据
        await self.cache_service.set("config:version", "1.0.0")
        await self.cache_service.set("config:env", "production")
        
        logger.info("✅ 缓存预热完成")
        return True
```

在应用启动时注册：

```python
@app.on_event("startup")
async def startup_event():
    initializer_manager = StartupInitializerManager()
    
    # 注册多个初始化器
    initializer_manager.register(DatabaseInitializer(...))
    initializer_manager.register(CacheWarmupInitializer(...))
    initializer_manager.register(ConfigValidatorInitializer(...))
    
    # 按顺序执行
    await initializer_manager.execute_all(stop_on_failure=True)
```

### 条件初始化

根据环境变量控制初始化：

```python
import os

@app.on_event("startup")
async def startup_event():
    env = os.getenv("APP_ENV", "development")
    
    initializer_manager = StartupInitializerManager()
    
    # 数据库初始化
    db_initializer = DatabaseInitializer(
        db_service=db_service,
        enabled=(env == "development"),  # 仅开发环境启用
        mode="full" if env == "development" else "incremental"
    )
    initializer_manager.register(db_initializer)
    
    await initializer_manager.execute_all()
```

## 完整示例

### pyspring init 生成的项目

使用 `pyspring init` 创建项目时，会自动生成：

```
my-project/
├── config/
│   └── repositories.yaml      # 已配置数据库初始化
├── scripts/
│   └── db/
│       ├── init_postgresql.sql  # PostgreSQL 脚本
│       ├── init_sqlite.sql      # SQLite 脚本
│       └── README.md
├── main.py                     # 已集成启动初始化器
└── pyproject.toml
```

直接运行即可：

```bash
cd my-project
pip install -e .
python main.py
```

启动日志：

```
🚀 应用启动中...
📦 数据库服务已初始化: PostgresService(postgresql://localhost/app_db)
📋 数据库自动初始化已启用
🚀 开始执行初始化器: DatabaseInitializer
🗄️  开始数据库初始化 (模式: incremental)
🔍 自动检测到 SQL 脚本: scripts/db/init_postgresql.sql
📄 读取 SQL 脚本: scripts/db/init_postgresql.sql (1234 字符)
📝 准备执行 15 条 SQL 语句
✓ 执行 SQL (1/15)
✓ 执行 SQL (2/15)
...
✅ 成功执行 15/15 条 SQL 语句
✅ 数据库初始化完成
✅ 初始化器 [DatabaseInitializer] 执行成功
📊 初始化器执行完成: 成功 1/1, 失败 0/1
✅ 应用启动完成
```

## 最佳实践

### 1. 开发环境配置

```yaml
database:
  type: "sqlite"
  initialization:
    enabled: true
    mode: "full"          # 全覆盖，快速重置
    auto_detect: true
  
  sqlite:
    database: "data/dev.db"
```

### 2. 生产环境配置

```yaml
database:
  type: "postgresql"
  initialization:
    enabled: false        # 禁用自动初始化
    # 生产环境使用 Alembic 等专业工具
  
  postgresql:
    host: "${POSTGRES_HOST}"
    database: "${POSTGRES_DB}"
```

### 3. SQL 脚本最佳实践

```sql
-- ✅ 使用 IF NOT EXISTS
CREATE TABLE IF NOT EXISTS users (...);

-- ✅ 使用 ON CONFLICT
INSERT INTO roles (code, name) VALUES ('admin', '管理员')
ON CONFLICT (code) DO NOTHING;

-- ✅ 添加注释
-- 创建用户表
CREATE TABLE IF NOT EXISTS users (...);

-- ❌ 避免 DROP TABLE（增量模式下）
-- DROP TABLE users;  -- 危险！

-- ❌ 避免硬编码数据（生产环境）
-- INSERT INTO users (email) VALUES ('admin@example.com');
```

## 故障排查

### 问题1: 未找到 SQL 脚本

**错误信息**:

```
⚠️  未找到数据库初始化脚本: init_postgresql.sql
💡 请在以下位置创建脚本: scripts/db/init_postgresql.sql
```

**解决方案**:

1. 确认脚本文件存在
2. 检查文件名格式: `init_{database_type}.sql`
3. 或在配置中指定 `script_path`

### 问题2: SQL 执行失败

**错误信息**:

```
❌ SQL 执行失败: syntax error at or near "TABLE"
```

**解决方案**:

1. 检查 SQL 语法
2. 确认数据库类型匹配（PostgreSQL vs SQLite）
3. 查看详细错误日志

### 问题3: 表已存在

**正常日志** (incremental 模式):

```
⏭️  表已存在，跳过创建
```

这是正常的，增量模式会跳过已存在的表。

如需重建，使用 `mode: "full"` （开发环境）

## 参考资料

- [IStartupInitializer 接口](../src/pyspring/interfaces/IStartupInitializer.py)
- [DatabaseInitializer 实现](../src/pyspring/repositories/db/initializer.py)
- [RepositoriesConfigManager](../src/pyspring/repositories/config_manager.py)
- [pyspring init 命令](./PROJECT_INIT_GUIDE.md)

## 未来扩展

基于启动初始化器模式，未来可以实现：

- **配置验证器**: 启动时验证配置完整性
- **健康检查器**: 检查依赖服务可用性
- **数据迁移器**: 自动执行数据迁移
- **缓存预热器**: 预加载热数据
- **监控初始化**: 启动监控和追踪
- **许可证验证**: 验证软件授权

所有这些都可以通过实现 `IStartupInitializer` 接口并注册到 `StartupInitializerManager` 来完成！
