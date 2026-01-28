# IOC 依赖注入模式重构方案

## 问题描述

当前 Cache/DB 模块使用手动 `set_provider()` 模式，不是真正的依赖注入。这导致：

1. API 层无法直接通过 `Depends()` 获取完全初始化的服务
2. 服务创建绕过了 IOC 容器，无法管理生命周期
3. 配置和服务耦合在 Initializer 中

## 正确的 IOC 模式

### 方案 A：基于接口的自动选择（推荐）

```python
# ============================================================
# 1. 配置层（已完成）
# ============================================================
@Component
@Singleton
class CacheConfig(ConfigSection):
    yaml_config_file = "config/repositories.yaml"
    yaml_config_key = "cache"
    
    type: str = Field(default="memory")
    redis: RedisConfig = ...
    memory: MemoryConfig = ...


# ============================================================
# 2. 服务层 - 注册为 Component
# ============================================================
@Component
@Singleton
class RedisService(ICacheService):
    """Redis 服务实现"""
    
    def __init__(self, cache_config: CacheConfig):
        """通过构造函数注入配置"""
        self.config = cache_config.redis
        self._pool: Optional[ConnectionPool] = None
        
    async def connect(self):
        """延迟初始化连接池"""
        if self._pool is None:
            self._pool = ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.pool.max_connections,
            )
        return self._pool


@Component
@Singleton
class MemoryService(ICacheService):
    """内存缓存实现"""
    
    def __init__(self, cache_config: CacheConfig):
        self.config = cache_config.memory
        self._cache: Dict[str, Any] = {}


# ============================================================
# 3. 工厂模式 - 根据配置选择实现
# ============================================================
@Component
@Singleton
class CacheServiceFactory:
    """缓存服务工厂"""
    
    def __init__(
        self, 
        cache_config: CacheConfig,
        redis_service: RedisService,
        memory_service: MemoryService
    ):
        self.config = cache_config
        self.redis_service = redis_service
        self.memory_service = memory_service
    
    def get_service(self) -> ICacheService:
        """根据配置返回正确的服务"""
        if self.config.type.lower() == "redis":
            return self.redis_service
        elif self.config.type.lower() == "memory":
            return self.memory_service
        else:
            raise ValueError(f"Unsupported cache type: {self.config.type}")


# ============================================================
# 4. Manager 使用工厂
# ============================================================
@Component
@Singleton
class CacheManagerService(IManaged):
    """缓存管理服务"""
    
    def __init__(self, cache_factory: CacheServiceFactory):
        super().__init__()
        self._factory = cache_factory
        self._provider: Optional[ICacheService] = None
    
    @property
    def provider(self) -> ICacheService:
        """延迟获取服务（确保配置已加载）"""
        if self._provider is None:
            self._provider = self._factory.get_service()
        return self._provider
    
    async def get(self, key: str) -> Optional[Any]:
        """直接代理到服务"""
        return await self.provider.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        return await self.provider.set(key, value, ttl)


# ============================================================
# 5. Initializer 只负责连接初始化
# ============================================================
@Component
class CacheConnectionInitializer(IStartupInitializer):
    """缓存连接初始化器"""
    
    def __init__(self, cache_manager: CacheManagerService):
        super().__init__(enabled=True)
        self.cache_manager = cache_manager
    
    async def startup(self) -> bool:
        """初始化连接（不再创建服务）"""
        try:
            provider = self.cache_manager.provider  # 自动获取正确的服务
            
            # 如果是 Redis，初始化连接池
            if hasattr(provider, 'connect'):
                await provider.connect()
            
            # 测试连接
            if await provider.ping():
                logger.info(f"Cache service ready")
                return True
            else:
                logger.error(f"Cache ping failed")
                return False
                
        except Exception as e:
            logger.error(f"Cache initialization failed: {e}")
            return False


# ============================================================
# 6. API 层使用
# ============================================================
from fastapi import APIRouter, Depends
from pyspring.ioc.context import ApplicationContext

router = APIRouter()

def get_cache_manager() -> CacheManagerService:
    """依赖注入函数"""
    return ApplicationContext.get_instance().get_bean(CacheManagerService)

@router.get("/cache/{key}")
async def get_cache(
    key: str,
    cache_manager: Annotated[CacheManagerService, Depends(get_cache_manager)]
):
    """直接通过 IOC 容器获取完全初始化的服务"""
    value = await cache_manager.get(key)
    return {"key": key, "value": value}
```

### 方案 B：基于条件注册（更灵活）

```python
# 使用 @Conditional 注解根据配置动态注册
@Component
@Singleton
@Conditional(lambda: get_config().cache.type == "redis")
class RedisService(ICacheService):
    ...

@Component
@Singleton  
@Conditional(lambda: get_config().cache.type == "memory")
class MemoryService(ICacheService):
    ...

# Manager 直接注入接口（IOC 自动选择正确的实现）
@Component
@Singleton
class CacheManagerService:
    def __init__(self, cache_service: ICacheService):
        self.provider = cache_service  # 自动注入正确的实现
```

## 数据库模块重构

```python
# 1. 服务注册为 Component
@Component
@Singleton
class SqliteService(IDBService):
    def __init__(self, db_config: DatabaseConfig):
        self.config = db_config.sqlite
        self._engine: Optional[AsyncEngine] = None

@Component
@Singleton
class PostgresService(IDBService):
    def __init__(self, db_config: DatabaseConfig):
        self.config = db_config.postgresql
        self._engine: Optional[AsyncEngine] = None


# 2. 工厂选择
@Component
@Singleton
class DBServiceFactory:
    def __init__(
        self,
        db_config: DatabaseConfig,
        sqlite_service: SqliteService,
        postgres_service: PostgresService
    ):
        self.config = db_config
        self.sqlite = sqlite_service
        self.postgres = postgres_service
    
    def get_service(self) -> IDBService:
        db_type = self.config.type.lower()
        if db_type == "sqlite":
            return self.sqlite
        elif db_type == "postgresql":
            return self.postgres
        else:
            raise ValueError(f"Unsupported db type: {db_type}")


# 3. Manager 使用工厂
@Component
@Singleton
class DBManagerService(IManaged):
    def __init__(self, db_factory: DBServiceFactory):
        super().__init__()
        self._factory = db_factory
        self._provider: Optional[IDBService] = None
    
    @property
    def provider(self) -> IDBService:
        if self._provider is None:
            self._provider = self._factory.get_service()
        return self._provider
    
    async def service(self) -> IDBService:
        return self.provider
```

## 优势对比

| 特性      | 旧模式 (手动 set_provider) | 新模式 (IOC 注入) |
|---------|-----------------------|--------------|
| 依赖注入    | ❌ 手动创建                | ✅ 自动注入       |
| 生命周期    | ❌ 手动管理                | ✅ IOC 管理     |
| 配置注入    | ❌ 手动传参                | ✅ 自动注入       |
| API 可用性 | ❌ 需等待初始化              | ✅ 随时可用       |
| 测试友好    | ❌ 需要 mock Initializer | ✅ 直接 mock 接口 |
| 解耦程度    | ⚠️ Initializer 耦合     | ✅ 完全解耦       |

## 实施步骤

1. ✅ 配置类已经是 @Component @Singleton
2. ⭐ **将服务实现注册为 @Component**（RedisService, MemoryService 等）
3. ⭐ **创建 ServiceFactory**（根据配置选择实现）
4. ⭐ **重构 Manager**（使用 Factory，延迟初始化）
5. ⭐ **简化 Initializer**（只负责连接，不创建服务）
6. ✅ API 层可以直接 `Depends(get_manager)`

## 注意事项

1. **延迟初始化**：连接池应该在第一次使用时创建，而不是构造函数
2. **配置加载顺序**：确保配置在服务创建前加载完成
3. **循环依赖**：使用 Factory 模式打破循环
4. **单例保证**：所有服务都是 @Singleton，确保只有一个实例

## 结论

建议使用 **方案 A（工厂模式）**，因为：

- ✅ 所有服务都由 IOC 管理
- ✅ 配置自动注入
- ✅ API 层可以安全地依赖注入
- ✅ 测试友好
- ✅ 符合 SOLID 原则
