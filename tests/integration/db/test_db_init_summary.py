"""
数据库自动初始化功能架构总结
"""

if __name__ == "__main__":
    print("=" * 80)
    print("PySpring 数据库自动初始化功能")
    print("=" * 80)

    print("""
## 架构设计

采用 **启动初始化器（Startup Initializer）模式**：

1. IStartupInitializer 接口
   - 所有启动初始化器的基类
   - 提供统一的执行流程和错误处理
   - 易于扩展新的初始化任务

2. StartupInitializerManager 管理器
   - 管理多个初始化器
   - 按顺序执行
   - 支持失败时停止

3. DatabaseInitializer 实现
   - 专门负责数据库表结构初始化
   - 支持增量/全覆盖模式
   - 自动检测 SQL 脚本路径

4. RepositoriesConfigManager
   - 读取 repositories.yaml 配置
   - 提供 get_database_initialization_config() 方法

## 核心组件

📄 src/pyspring/interfaces/IStartupInitializer.py
   - IStartupInitializer: 初始化器接口
   - StartupInitializerManager: 初始化器管理器

📄 src/pyspring/repositories/db/initializer.py
   - DatabaseInitializer: 数据库初始化器实现

📄 src/pyspring/repositories/config_manager.py
   - RepositoriesConfigManager: 配置管理器
   - get_database_initialization_config(): 获取初始化配置

📄 config/repositories.yaml
   - database.initialization: 初始化配置块

## 配置示例

```yaml
database:
  type: "postgresql"
  
  initialization:
    enabled: true              # 是否启用
    mode: "incremental"        # incremental 或 full
    script_path: null          # SQL 脚本路径（null=自动检测）
    auto_detect: true          # 是否自动检测脚本
```

## 使用示例

```python
from pyspring.core.abstracts.interfaces.IStartupInitializer import StartupInitializerManager
from pyspring.repositories.db.initializer import DatabaseInitializer
from pyspring.repositories.db.manager import DBManagerService
from pyspring.repositories.common.config_loader import RepositoriesConfigManager

@app.on_event("startup")
async def startup_event():
    # 1. 初始化数据库管理器
    db_manager = DBManagerService()
    db_service = await db_manager.service()
    
    # 2. 创建初始化器管理器
    manager = StartupInitializerManager()
    
    # 3. 读取配置并注册初始化器
    config = RepositoriesConfigManager()
    init_config = config.get_database_initialization_config()
    
    if init_config['enabled']:
        db_init = DatabaseInitializer(
            db_service=db_service,
            enabled=init_config['enabled'],
            mode=init_config['mode'],
            script_path=init_config['script_path'],
            auto_detect=init_config['auto_detect']
        )
        manager.register(db_init)
    
    # 4. 执行所有初始化器
    await manager.execute_all(stop_on_failure=True)
```
""")

    print("""
## 优势

✅ **职责分离**: DBManagerService 负责连接管理，DatabaseInitializer 负责初始化
✅ **扩展性强**: 可以轻松添加其他初始化器（缓存预热、配置验证等）
✅ **配置灵活**: 通过 YAML 轻松配置，无需修改代码
✅ **模式支持**: 增量模式（安全）和全覆盖模式（开发）
✅ **自动检测**: 智能查找 SQL 脚本，开箱即用

## 未来扩展

基于 IStartupInitializer 接口，可以轻松实现：

- CacheWarmupInitializer: 缓存预热
- ConfigValidatorInitializer: 配置验证
- HealthCheckInitializer: 健康检查
- DataMigrationInitializer: 数据迁移
- MonitoringInitializer: 监控初始化

所有初始化器统一管理，统一执行，统一日志！
""")

    print("\n" + "=" * 80)
    print("✅ 功能已完成！")
    print("=" * 80)
    print("""
创建的文件:
  - src/pyspring/interfaces/IStartupInitializer.py
  - src/pyspring/repositories/db/initializer.py
  - src/pyspring/repositories/config_manager.py (更新)
  - config/repositories.yaml (更新)
  - src/pyspring/templates/repositories.yaml (更新)
  - src/pyspring/init.py (更新 main.py 模板)
  - docs/DATABASE_AUTO_INIT.md
  - examples/main_with_db_init.py
  - tests/test_database_initializer.py

配置位置:
  - config/repositories.yaml -> database.initialization

使用方式:
  1. 配置 repositories.yaml
  2. 将 SQL 脚本放在 scripts/db/
  3. 在 main.py 中注册初始化器
  4. 启动应用，自动初始化数据库
""")
