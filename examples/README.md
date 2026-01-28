# PySpring 生命周期完整示例

这个目录包含了两个完整的 PySpring 生命周期示例，从应用启动到关闭的全流程演示。

## 📁 示例文件

### 1. `complete_lifecycle_example.py` - 基础完整示例

**适合初学者**，展示了 PySpring 的核心生命周期功能。

#### 包含特性：

- ✅ FastAPI 应用集成
- ✅ IOC 容器初始化 (`ApplicationContext.initialize()`)
- ✅ 组件注册 (`@Component`, `@Singleton`)
- ✅ 依赖注入（构造函数注入）
- ✅ 启动初始化器 (`IStartupInitializer`)
- ✅ 关闭处理器 (`IShutdownHandler`)
- ✅ FastAPI 中间件（日志、计时）
- ✅ 全局异常处理
- ✅ 生命周期日志跟踪
- ✅ API 路由与依赖注入集成

#### 运行方式：

```bash
# 直接运行
python complete_lifecycle_example.py

# 或使用 uvicorn
uvicorn complete_lifecycle_example:app --reload
```

#### 测试 API：

```bash
# 首页
curl http://localhost:8000/

# 健康检查
curl http://localhost:8000/health

# 获取用户
curl http://localhost:8000/users/1

# 创建用户
curl -X POST "http://localhost:8000/users?user_id=10&name=测试用户"

# 创建订单
curl -X POST "http://localhost:8000/orders?user_id=1&product=手机"

# 查看所有服务
curl http://localhost:8000/services
```

---

### 2. `advanced_lifecycle_example.py` - 高级特性示例

**适合进阶用户**，展示了 PySpring 的高级功能和最佳实践。

#### 包含特性：

- ✅ 配置类 (`@Configuration`, `@Bean`)
- ✅ Bean 工厂方法
- ✅ 完整生命周期接口 (`ILifecycle`: `on_init`, `on_destroy`)
- ✅ 多作用域支持 (`@Singleton`, `@Prototype`)
- ✅ 复杂依赖注入（多层依赖）
- ✅ 配置对象注入
- ✅ 启动初始化器（带依赖顺序）
- ✅ 关闭处理器（带优先级）
- ✅ 数据库服务模拟
- ✅ 缓存服务模拟
- ✅ 仓储模式 (Repository Pattern)
- ✅ 请求上下文（Prototype 示例）

#### 运行方式：

```bash
# 直接运行
python advanced_lifecycle_example.py

# 或使用 uvicorn
uvicorn advanced_lifecycle_example:app --reload --port 8001
```

#### 测试 API：

```bash
# 首页
curl http://localhost:8001/

# 健康检查（查看服务连接状态）
curl http://localhost:8001/health

# 获取用户（第一次从数据库，第二次从缓存）
curl http://localhost:8001/users/1
curl http://localhost:8001/users/1

# 创建用户
curl -X POST "http://localhost:8001/users?name=新用户&email=new@example.com"

# 查看所有服务（含作用域信息）
curl http://localhost:8001/services

# 测试 Prototype 作用域（每次创建新实例）
curl http://localhost:8001/context
```

---

## 🔄 生命周期流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    应用启动阶段                               │
├─────────────────────────────────────────────────────────────┤
│ 1. FastAPI 启动                                              │
│ 2. lifespan() 上下文管理器被调用                            │
│ 3. ApplicationContext.initialize([...])                     │
│    ├─ 创建 Container                                        │
│    ├─ 扫描指定包的所有组件                                   │
│    ├─ 注册 @Component 类                                    │
│    ├─ 注册 @Configuration 和 @Bean                          │
│    └─ 构建依赖关系图                                         │
│ 4. container.initialize_lifecycle_services()                │
│    ├─ 创建所有 Singleton 实例                               │
│    ├─ 调用 ILifecycle.on_init()                            │
│    └─ 执行所有 IStartupInitializer.initialize()            │
│ 5. 应用就绪，开始接受请求                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    运行阶段                                   │
├─────────────────────────────────────────────────────────────┤
│ • 处理 HTTP 请求                                             │
│ • FastAPI Depends() 触发依赖注入                            │
│ • ApplicationContext.service(ServiceType) 获取服务          │
│ • Singleton: 复用实例                                        │
│ • Prototype: 每次创建新实例                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    应用关闭阶段                               │
├─────────────────────────────────────────────────────────────┤
│ 1. 收到 Ctrl+C 或关闭信号                                    │
│ 2. lifespan() 上下文管理器 yield 后继续执行                 │
│ 3. container.shutdown_lifecycle_services()                  │
│    ├─ 执行所有 IShutdownHandler.shutdown()                 │
│    └─ 调用 ILifecycle.on_destroy()                         │
│ 4. 清理资源                                                  │
│ 5. 应用完全关闭                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 核心概念说明

### 1. ApplicationContext（应用上下文）

替代旧版的 `AppContainerManager`，是 PySpring 的核心入口。

```python
# 初始化（应用启动时调用一次）
ctx = ApplicationContext.initialize([
    'your_app.services',
    'your_app.repositories'
])

# 获取服务实例
user_service = ctx.get_by_type(UserService)

# 或使用静态方法（适合 FastAPI Depends）
service = ApplicationContext.service(UserService)
```

### 2. 组件注册

#### @Component - 自动注册为组件

```python
@Component
@Singleton
class UserService(IManaged):
    def __init__(self, db: DatabaseService):
        self.db = db
```

#### @Configuration + @Bean - 工厂方法

```python
@Configuration
class AppConfig:
    @Bean()
    @Singleton
    def database_config(self) -> dict:
        return {"host": "localhost", "port": 5432}
```

### 3. 作用域

| 作用域 | 装饰器          | 行为                   |
|-----|--------------|----------------------|
| 单例  | `@Singleton` | 容器中只有一个实例，多次获取返回同一对象 |
| 原型  | `@Prototype` | 每次获取都创建新实例           |

### 4. 生命周期接口

#### ILifecycle - 完整生命周期钩子

```python
class MyService(ILifecycle, IManaged):
    async def on_init(self):
        """实例创建后调用 - 用于初始化资源"""
        await self.connect_database()

    async def on_destroy(self):
        """实例销毁前调用 - 用于清理资源"""
        await self.close_database()
```

#### IStartupInitializer - 启动初始化器

```python
@Component
class DatabaseInit(IStartupInitializer):
    def get_name(self) -> str:
        return "数据库初始化器"
    
    async def initialize(self) -> bool:
        """应用启动时执行"""
        await create_tables()
        return True
```

#### IShutdownHandler - 关闭处理器

```python
@Component
class DatabaseShutdown(IShutdownHandler):
    def get_name(self) -> str:
        return "数据库关闭处理器"

    async def shutdown(self) -> bool:
        """应用关闭时执行"""
        await close_connections()
        return True
```

### 5. 依赖注入

PySpring 使用**构造函数注入**，自动解析依赖：

```python
@Component
class OrderService(IManaged):
    # 构造函数参数会被自动注入
    def __init__(self,
                 user_service: UserService,  # 注入 UserService
                 db: DatabaseService,  # 注入 DatabaseService
                 cache: CacheService,  # 注入 CacheService
                 config: dict):  # 注入配置 Bean
        self.user_service = user_service
        self.db = db
        self.cache = cache
        self.config = config
```

### 6. FastAPI 集成

#### 在路由中使用依赖注入：

```python
from fastapi import Depends
from typing import Annotated


@app.get("/users/{user_id}")
async def get_user(
        user_id: int,
        # 通过 Depends 注入服务
        user_service: Annotated[
            UserService,
            Depends(lambda: ApplicationContext.service(UserService))
        ]
):
    return await user_service.get_user(user_id)
```

---

## 🎯 最佳实践

### 1. 应用启动

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pyspring.ioc import ApplicationContext


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动阶段
    ctx = ApplicationContext.initialize(['your_app'])
    await ctx.container.initialize_lifecycle_services()

    yield  # 运行

    # 关闭阶段
    await ctx.container.shutdown_lifecycle_services()


app = FastAPI(lifespan=lifespan)
```

### 2. 服务类设计

```python
# ✅ 推荐：轻量级构造函数，耗时操作放在 on_init
@Component
@Singleton
class MyService(ILifecycle, IManaged):
    def __init__(self, config: dict):
        # 只接收依赖，不做耗时操作
        self.config = config
        self.connection = None

    async def on_init(self):
        # 耗时的初始化操作
        self.connection = await create_connection(self.config)


# ❌ 不推荐：构造函数中做耗时操作
@Component
class BadService(IManaged):
    def __init__(self):
        # 构造函数中同步阻塞
        self.connection = connect_sync()  # 不推荐！
```

### 3. 依赖注入顺序

PySpring 会自动处理依赖顺序，但要注意**循环依赖**：

```python
# ❌ 循环依赖（会导致错误）
class ServiceA(IManaged):
    def __init__(self, b: ServiceB): ...

class ServiceB(IManaged):
    def __init__(self, a: ServiceA): ...  # 循环依赖！

# ✅ 解决方案：重构设计或使用中介者模式
```

### 4. 配置管理

```python
# 推荐：使用 @Configuration 集中管理配置
@Configuration
class AppConfig:
    @Bean()
    def database_config(self) -> DatabaseConfig:
        return DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432))
        )
    
    @Bean()
    def redis_config(self) -> RedisConfig:
        return RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379))
        )
```

---

## 🔍 调试技巧

### 1. 查看已注册的服务

```python
ctx = ApplicationContext.get_instance()
services = ctx.container.registry.all_names()
for name in sorted(services):
    print(f"  - {name}")
```

### 2. 查看服务详细信息

```python
definition = ctx.container.registry.get("user_service")
print(f"类型: {definition.service_type}")
print(f"作用域: {definition.scope}")
print(f"是否Bean: {definition.is_bean}")
```

### 3. 启用详细日志

```python
from pyspring.log.instance import logger
import logging

logger.setLevel(logging.DEBUG)
```

---

## 📖 相关文档

- [IOC 容器指南](../docs/02-core-concepts/IOC_CONTAINER.md)
- [新版框架使用指南](../docs/IOC_NEW_FRAMEWORK_GUIDE.md)
- [迁移指南](../docs/IOC_MIGRATION_GUIDE.md)

---

## ❓ 常见问题

### Q1: 如何在非 FastAPI 环境中使用？

```python
from pyspring.ioc import ApplicationContext

# 初始化
ctx = ApplicationContext.initialize(['your_package'])
await ctx.container.initialize_lifecycle_services()

# 使用服务
user_service = ctx.get_by_type(UserService)
result = await user_service.do_something()

# 关闭
await ctx.container.shutdown_lifecycle_services()
```

### Q2: 如何处理异步初始化？

使用 `ILifecycle.on_init()` 方法，它是异步的：

```python
class MyService(ILifecycle, IManaged):
    async def on_init(self):
        # 异步初始化
        await self.async_setup()
```

### Q3: 如何控制初始化器执行顺序？

通过依赖注入自动控制。如果 InitializerB 依赖 ServiceA，而 ServiceA 在 InitializerA 中初始化，那么 InitializerA 会先执行。

### Q4: `ApplicationContext` 和旧版 `AppContainerManager` 有什么区别？

| 特性     | AppContainerManager（旧版）                                                | ApplicationContext（新版）                                |
|--------|------------------------------------------------------------------------|-------------------------------------------------------|
| 初始化方式  | `manager = AppContainerManager()`<br>`manager.register_all_services()` | `ctx = ApplicationContext.initialize([...])`          |
| 生命周期管理 | `await manager.run_startup_initializers()`                             | `await ctx.container.initialize_lifecycle_services()` |
| 关闭     | `await manager.run_shutdown_handlers()`                                | `await ctx.container.shutdown_lifecycle_services()`   |
| 获取服务   | `manager.service(ServiceType)`                                         | `ApplicationContext.service(ServiceType)`             |

---

## 🎓 学习路径

1. **初学者**: 先运行 `complete_lifecycle_example.py`，理解基础流程
2. **进阶**: 运行 `advanced_lifecycle_example.py`，学习高级特性
3. **实战**: 参考示例，创建自己的 PySpring 应用

---

## 💡 提示

- 启动应用后访问 `/docs` 可以看到自动生成的 API 文档
- 使用 `Ctrl+C` 优雅关闭应用，可以看到完整的关闭流程日志
- 所有示例都包含详细的日志输出，便于理解执行流程
