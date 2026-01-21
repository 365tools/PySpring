# PySpring IOC 新旧版本功能对比

## 一、核心功能对比表

| 功能                | 旧版本                                        | 新版本                               | 状态         |
|-------------------|--------------------------------------------|-----------------------------------|------------|
| **容器管理**          | `AppContainerManager()`                    | `ApplicationContext.initialize()` | ✅ 完全支持     |
| **组件扫描**          | `ModuleScanner`                            | `ComponentScanner`                | ✅ 完全支持     |
| **服务注册**          | 手动/装饰器/配置                                  | `@Component` / `@Bean`            | ✅ 更简洁      |
| **依赖注入**          | 构造函数注入                                     | 构造函数注入                            | ✅ 完全支持     |
| **作用域管理**         | `ISingletonService` 继承                     | `@Singleton` / `@Prototype`       | ✅ 更灵活      |
| **循环依赖**          | 手动检测 + 报错                                  | `LazyProxy` 自动解决                  | ✅ 增强       |
| **接口注入**          | 支持                                         | 支持 + `@Primary`                   | ✅ 增强       |
| **Bean工厂**        | 不支持                                        | `@Configuration` + `@Bean`        | ✅ 新增       |
| **条件注册**          | 不支持                                        | `@ConditionalOnMissingBean`       | ✅ 新增       |
| **懒加载**           | 不支持                                        | `@Lazy`                           | ✅ 新增       |
| **生命周期**          | `IStartupInitializer` + `IShutdownHandler` | `ILifecycle` + 兼容接口               | ✅ **完全兼容** |
| **配置加载**          | `IoCConfigLoader` 从YAML                    | `IoCConfigLoader` 支持              | ✅ **支持**   |
| **Initializer管理** | `LifecycleManager`                         | `StartupInitializerManager`       | ✅ **支持**   |
| **Shutdown管理**    | 手动调用                                       | `ShutdownHandlerManager`          | ✅ **增强**   |
| **AOP集成**         | `ServiceRegistrar` 支持                      | `AopIntegration` 自动代理             | ✅ **支持**   |

---

## 二、详细功能对比

### 2.1 容器初始化

#### 旧版本

```python
from pyspring.ioc.manager import AppContainerManager

# 初始化容器
container = AppContainerManager()
container.setup(modules=['myapp.services'])

# 获取服务
service = container.get(UserService)
# 或
service = container.get('user_service')
```

#### 新版本

```python
from pyspring.ioc import ApplicationContext

# 初始化容器
ctx = ApplicationContext.initialize(['myapp.services'])

# 获取服务
service = ctx.get_by_type(UserService)
# 或
service = ctx.get('user_service')
```

**状态**: ✅ **完全兼容**（API略有差异）

---

### 2.2 服务注册

#### 旧版本

```python
from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService


# 方式1：继承接口
class UserService(ISingletonService):
    async def get(self): pass

    async def save(self): pass


# 方式2：装饰器
from pyspring.ioc.annotations.decorators import service


@service
class UserService:
    pass


# 方式3：手动注册
container.bind_singleton('user_service', UserService)
```

#### 新版本

```python
from pyspring.ioc import Component, Singleton


@Component()
@Singleton
class UserService:
    pass


# 或使用语义化别名
from pyspring.ioc import Service


@Service()
@Singleton
class UserService:
    pass
```

**状态**: ✅ **完全支持**（更简洁）

---

### 2.3 生命周期管理

#### 旧版本

```python
from pyspring.core.abstracts.interfaces.initializer.startup import IStartupInitializer
from pyspring.core.abstracts.interfaces.handler.shutdown import IShutdownHandler


class AuthenticationInitializer(IStartupInitializer):
    async def initialize(self):
        """启动时初始化"""
        pass


class DBShutdownHandler(IShutdownHandler):
    async def shutdown(self):
        """关闭时清理"""
        pass
```

#### 新版本

```python
from pyspring.ioc import ILifecycle, Component, Singleton


@Component()
@Singleton
class DatabaseService(ILifecycle):
    async def on_init(self):
        """启动时初始化"""
        pass

    async def on_destroy(self):
        """关闭时清理"""
        pass
```

**状态**: ⚠️ **接口变更但兼容**

- 旧版：`IStartupInitializer` 和 `IShutdownHandler` 分离
- 新版：提供兼容接口 + 推荐使用统一的 `ILifecycle`

**两种迁移方式**：

1. **零改动迁移**：继续使用 `IStartupInitializer` / `IShutdownHandler`（完全兼容）
2. **推荐迁移**：改用统一的 `ILifecycle` 接口

**迁移方案**：

```python
# 旧代码
class MyInitializer(IStartupInitializer):
    async def initialize(self):
        # 初始化逻辑
        pass


# 新代码
@Component()
@Singleton
class MyService(ILifecycle):
    async def on_init(self):
        # 初始化逻辑（与旧版initialize相同）
        pass

    async def on_destroy(self):
        # 清理逻辑（可选）
        pass
```

---

### 2.4 依赖注入

#### 旧版本和新版本都支持

```python
@Component()
@Singleton
class UserService:
    def __init__(
            self,
            user_repo: IUserRepository,  # 接口注入
            config: AppConfig  # 类型注入
    ):
        self.user_repo = user_repo
        self.config = config
```

**状态**: ✅ **完全一致**

---

### 2.5 循环依赖处理

#### 旧版本

```python
# 会报错并提示循环依赖
❌ RecursionError: maximum
recursion
depth
exceeded
```

#### 新版本

```python
# 自动使用LazyProxy解决，透明处理
@Component()
@Singleton
class ServiceA:
    def __init__(self, service_b: 'ServiceB'):
        self.service_b = service_b  # 自动注入LazyProxy


@Component()
@Singleton
class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a  # 自动注入LazyProxy
```

**状态**: ✅ **增强**（自动解决）

---

### 2.6 Bean工厂方法

#### 旧版本

```python
# 不支持，需要手动注册
container.bind_singleton('db_config', lambda: DBConfig(...))
```

#### 新版本

```python
from pyspring.ioc import Configuration, Bean


@Configuration
class AppConfig:
    @Bean
    def db_config(self) -> DBConfig:
        return DBConfig(
            host="localhost",
            port=5432
        )

    @Bean
    def user_service(self, db_config: DBConfig) -> UserService:
        return UserService(db_config)
```

**状态**: ✅ **新增功能**

---

## 三、不兼容的功能

### 3.1 ✅ 配置文件加载（已支持）

#### 旧版本

```python
# config/container.yaml
services:
user_service:


class: myapp.services.UserService


singleton: true
```

#### 新版本

```python
# 支持！使用Bean工厂方式（推荐）
# config/container.yaml
scan_packages:
- myapp.services

services:
db_config:
factory: myapp.config.AppConfig.create_db_config
singleton: true
```

**状态**：✅ **支持**（推荐使用Bean工厂）

---

### 3.2 ✅ Initializer/Shutdown管理（已支持）

#### 旧版本

```python
# LifecycleManager 自动发现和管理
class LifecycleManager:
    def discover_initializers(self):
        # 自动发现所有 IStartupInitializer
        pass
```

#### 新版本

```python
# 完全兼容！自动发现和管理
from pyspring.ioc.lifecycle import IStartupInitializer, IShutdownHandler


@Component()
@Singleton
class MyInitializer(IStartupInitializer):
    async def initialize(self) -> bool:
        # 初始化逻辑
        return True

    def get_name(self) -> str:
        return "MyInitializer"


# 容器会自动发现并执行
ctx = ApplicationContext.initialize(['myapp'])
await ctx.container.initialize_lifecycle_services()  # 自动执行所有Initializer
await ctx.container.destroy_lifecycle_services()  # 自动执行所有ShutdownHandler
```

**状态**：✅ **完全兼容**

---

### 3.3 ✅ AOP自动代理（已支持）

#### 旧版本

```python
# ServiceRegistrar 自动为服务创建AOP代理
def register_service(self, service):
    if has_aspects(service):
        return create_proxy(service, aspects)
    return service
```

#### 新版本

```python
# 完全支持！自动AOP代理（默认启用）
from pyspring.ioc import ApplicationContext, Component, Singleton
from pyspring.aop import Aspect, Before


@Component()
@Singleton
@Aspect
class LoggingAspect:
    @Before(pointcut="execution(* UserService.*(..))")
    def log_before(self, join_point):
        print(f"调用: {join_point.method_name}")


# 初始化时启用AOP
ctx = ApplicationContext.initialize(['myapp'], enable_aop=True)


# UserService会自动被代理
@Component()
@Singleton
class UserService:
    def get_user(self, user_id):
        return f"User {user_id}"
```

**状态**：✅ **完全支持**（可选开关）

---

## 四、迁移优先级

### 🔴 高优先级（必须迁移）

1. **生命周期接口**
    - 所有 `IStartupInitializer` → `ILifecycle.on_init()`
    - 所有 `IShutdownHandler` → `ILifecycle.on_destroy()`

2. **服务注册**
    - 所有 `ISingletonService` → `@Component() + @Singleton`
    - 所有手动注册 → 装饰器注册

3. **容器获取**
    - `AppContainerManager()` → `ApplicationContext.get_instance()`

### 🟡 中优先级（建议迁移）

1. **移除强制CRUD方法**
    - 不需要实现 `get()`, `save()` 等方法

2. **接口继承改为标记**
    - `class MyService(ISingletonService)` → `@Component() @Singleton class MyService(IManaged)`

### 🟢 低优先级（可选）

1. **使用新特性**
    - `@Bean` 工厂方法
    - `@ConditionalOnMissingBean` 条件注册
    - `@Lazy` 懒加载

---

## 五、快速迁移检查清单

- [ ] 所有 `from pyspring.ioc.manager import AppContainerManager` 改为 `from pyspring.ioc import ApplicationContext`
- [ ] 所有 `AppContainerManager()` 改为 `ApplicationContext.get_instance()`
- [ ] 所有 `IStartupInitializer` 改为 `ILifecycle`
- [ ] 所有 `initialize()` 方法改为 `on_init()`
- [ ] 所有 `IShutdownHandler.shutdown()` 改为 `ILifecycle.on_destroy()`
- [ ] 所有 `ISingletonService` 继承改为 `@Singleton` 装饰器
- [ ] 移除不需要的 `get()`, `save()` 空方法实现
- [ ] 检查循环依赖是否被自动解决

---

## 六、结论

**新版本IOC功能覆盖率：100%** ✅

✅ **完全支持的核心功能**：

- 容器管理、组件扫描、依赖注入
- 作用域管理、接口注入
- 循环依赖处理（增强）
- 生命周期管理（兼容 + 增强）
- 配置文件加载（Bean工厂方式）
- Initializer/Shutdown自动管理
- AOP自动代理（可选开关）

⚠️ **需要改动的部分**：

1. **容器访问** - `AppContainerManager()` → `ApplicationContext.get_instance()`
2. **服务注册** - `ISingletonService继承` → `@Component + @Singleton`

✨ **新增功能**：

- `@Bean` 工厂方法
- `@ConditionalOnMissingBean` 条件注册
- `@Lazy` 懒加载
- `@Primary` 主要实现标记
- 自动循环依赖解决

**总体评价**：新版本在完全兼容旧版本核心功能的基础上，提供了更清晰的架构、更强大的功能和更好的开发体验。迁移成本主要在于接口调用方式的改变，实际业务逻辑无需修改。
