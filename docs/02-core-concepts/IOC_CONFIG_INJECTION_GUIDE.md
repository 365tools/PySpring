# IOC 框架扩展：配置对象注入

## 📋 设计方案

### 当前状态

IOC 容器已经支持配置对象注入，通过 `AppSettings` 演示：

```python
@Component
@Singleton
class AppSettings(BaseSettings):
    """主配置类，通过 IOC 管理"""
    database: DatabaseConfig = ...
    redis: RedisConfig = ...
    logging: LoggingConfig = ...

@Component
class SystemService:
    def __init__(self, settings: AppSettings):
        # IOC 自动注入 AppSettings
        self.settings = settings
```

### 扩展方案

#### 方案 A：将 CacheConfig 注册为独立组件（推荐）

**优点**：

- 配置独立管理
- 灵活性高，可单独注入
- 解耦更好

**实现**：

```python
# repositories/cache/config.py

@Component
@Singleton
class CacheConfig(ConfigSection):
    """缓存配置（由IOC管理）"""
    type: str = Field(default="memory")
    redis: RedisConfig = Field(default_factory=RedisConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)

# 使用
@Component
class CacheConnectionInitializer:
    def __init__(self, cache_config: CacheConfig, cache_manager: CacheManagerService):
        # IOC 自动注入 CacheConfig
        self.cache_config = cache_config
        self.cache_manager = cache_manager
```

#### 方案 B：通过 AppSettings 访问（当前方式）

**优点**：

- 配置集中管理
- 已有实现，无需修改

**实现**：

```python
# 使用 AppSettings 已包含的 cache 配置
@Component
class CacheConnectionInitializer:
    def __init__(self, settings: AppSettings, cache_manager: CacheManagerService):
        # 通过 settings.cache 访问缓存配置
        # 需要在 AppSettings 中添加 cache 字段
        self.cache_config = settings.cache
        self.cache_manager = cache_manager
```

---

## 🎯 推荐实现：方案 A + AppSettings 整合

**步骤**：

### 1. 为 CacheConfig 添加 @Component 注解

```python
# repositories/cache/config.py

from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton

@Component
@Singleton
class CacheConfig(ConfigSection):
    """缓存配置（由IOC管理）"""
    type: str = Field(default="memory", description="缓存类型：redis、memory")
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis配置")
    memory: MemoryConfig = Field(default_factory=MemoryConfig, description="内存缓存配置")
```

### 2. 在 AppSettings 中引用 CacheConfig

```python
# core/configuration/models.py

@Component
@Singleton
class AppSettings(BaseSettings):
    """主配置类"""
    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)  # 新增
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    authentication: AuthenticationConfig = Field(default_factory=AuthenticationConfig)
```

### 3. 在 Initializer 中注入

```python
# repositories/cache/initializer/connection.py

from pyspring.ioc.lifecycle.startup import IStartupInitializer
from pyspring.ioc.annotations.component import Component
from ..config import CacheConfig
from ..manager import CacheManagerService

@Component
class CacheConnectionInitializer(IStartupInitializer):
    """缓存连接初始化器"""
    
    def __init__(self, cache_config: CacheConfig, cache_manager: CacheManagerService):
        """
        Args:
            cache_config: 缓存配置（IOC自动注入）
            cache_manager: 缓存管理器（IOC自动注入）
        """
        super().__init__(enabled=True)
        self.cache_config = cache_config
        self.cache_manager = cache_manager
    
    async def startup(self) -> bool:
        """初始化缓存服务"""
        cache_type = self.cache_config.type.lower()
        
        if cache_type == "redis":
            from ..providers.redis.services.service import RedisService
            provider = RedisService(
                host=self.cache_config.redis.host,
                port=self.cache_config.redis.port,
                db=self.cache_config.redis.db,
                password=self.cache_config.redis.password,
                pool_config=self.cache_config.redis.pool.model_dump()
            )
        elif cache_type == "memory":
            from ..providers.memory.services.service import MemoryService
            provider = MemoryService(
                max_size=self.cache_config.memory.max_size,
                ttl=self.cache_config.memory.ttl
            )
        else:
            raise ValueError(f"不支持的缓存类型: {cache_type}")
        
        self.cache_manager.set_provider(provider)
        
        if await provider.ping():
            logger.info(f"✅ {cache_type.capitalize()} 缓存服务已就绪")
            return True
        else:
            logger.error(f"❌ {cache_type.capitalize()} Ping 失败")
            return False
    
    def get_name(self) -> str:
        return "缓存连接初始化器"
```

---

## 🔧 IOC 框架如何支持配置注入

### 工作原理

1. **配置类注册**：
    - 配置类添加 `@Component` + `@Singleton` 注解
    - IOC 扫描时识别并注册到容器

2. **依赖解析**：
    - DependencyResolver 分析构造函数参数类型
    - 通过参数类型匹配容器中的配置对象
    - 自动注入到构造函数

3. **生命周期**：
    - 配置对象作为 Singleton 只实例化一次
    - 所有依赖此配置的服务共享同一实例

### 配置加载流程

```
1. IOC 容器启动
   ↓
2. 扫描发现 @Component 标注的配置类
   ↓
3. 实例化配置对象（Pydantic 自动从环境变量/YAML加载）
   ↓
4. 注册到容器（Singleton）
   ↓
5. 其他服务构造函数请求配置对象
   ↓
6. IOC 容器自动注入已实例化的配置
```

---

## ✅ 优势

1. **类型安全**：配置对象有完整的类型注解
2. **自动加载**：Pydantic 自动从环境变量加载
3. **解耦**：配置与业务逻辑分离
4. **可测试**：可以轻松 Mock 配置对象
5. **统一管理**：所有配置通过 IOC 容器管理

---

## 📌 注意事项

### 1. 配置类必须是 Pydantic BaseSettings 或 ConfigSection

```python
# ✅ 正确
@Component
@Singleton
class CacheConfig(ConfigSection):
    type: str = Field(default="memory")

# ❌ 错误
@Component
class CacheConfig:  # 不继承 BaseSettings/ConfigSection
    type: str = "memory"
```

### 2. 避免循环依赖

```python
# ❌ 配置类不应该依赖业务服务
@Component
class CacheConfig(ConfigSection):
    def __init__(self, logger: LoggerService):  # 不要这样做
        ...

# ✅ 配置类应该无依赖
@Component
class CacheConfig(ConfigSection):
    type: str = Field(default="memory")
```

### 3. 配置优先级

Pydantic 配置加载优先级（从高到低）：

1. 环境变量（`CACHE__TYPE=redis`）
2. `.env` 文件
3. Field 默认值

---

## 🎯 总结

**不需要修改 IOC 框架核心代码**，当前实现已经支持配置对象注入！

只需：

1. 为 `CacheConfig` 添加 `@Component` + `@Singleton` 注解
2. 在需要配置的地方通过构造函数参数注入
3. IOC 容器自动解析并注入

这就是为什么 `SystemService` 可以注入 `AppSettings` 的原因——同样的机制适用于所有配置类！
