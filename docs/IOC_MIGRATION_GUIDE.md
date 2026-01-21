# PySpring IOC 迁移示例

## 一、生命周期接口迁移

### 1.1 IStartupInitializer 迁移

#### 旧代码

```python
from pyspring.core.abstracts.interfaces.initializer.startup import IStartupInitializer
from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService


class AuthenticationInitializer(IStartupInitializer, ISingletonService):
    def __init__(self, enabled: bool = True):
        IStartupInitializer.__init__(self, enabled)

    async def initialize(self) -> bool:
        """初始化认证系统"""
        # 初始化逻辑
        return True

    def get_name(self) -> str:
        return "AuthenticationInitializer"
```

#### 新代码（选项1：完全兼容）

```python
from pyspring.ioc import Component, Singleton
from pyspring.ioc.lifecycle import IStartupInitializer


@Component()
@Singleton
class AuthenticationInitializer(IStartupInitializer):
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)

    async def initialize(self) -> bool:
        """初始化认证系统"""
        # 初始化逻辑（代码不变）
        return True

    def get_name(self) -> str:
        return "AuthenticationInitializer"
```

#### 新代码（选项2：使用新接口）

```python
from pyspring.ioc import Component, Singleton, ILifecycle


@Component()
@Singleton
class AuthenticationService(ILifecycle):
    async def on_init(self):
        """初始化认证系统"""
        # 原来initialize()中的逻辑
        pass

    async def on_destroy(self):
        """清理（可选）"""
        pass
```

---

### 1.2 IShutdownHandler 迁移

#### 旧代码

```python
from pyspring.core.abstracts.interfaces.handler.shutdown import IShutdownHandler


class DBShutdownHandler(IShutdownHandler):
    async def shutdown(self) -> bool:
        """关闭数据库连接"""
        await self.connection.close()
        return True

    def get_name(self) -> str:
        return "DBShutdownHandler"
```

#### 新代码（选项1：完全兼容）

```python
from pyspring.ioc import Component, Singleton
from pyspring.ioc.lifecycle import IShutdownHandler


@Component()
@Singleton
class DBShutdownHandler(IShutdownHandler):
    async def shutdown(self) -> bool:
        """关闭数据库连接"""
        await self.connection.close()
        return True

    def get_name(self) -> str:
        return "DBShutdownHandler"
```

#### 新代码（选项2：使用新接口）

```python
from pyspring.ioc import Component, Singleton, ILifecycle


@Component()
@Singleton
class DatabaseService(ILifecycle):
    async def on_init(self):
        """建立连接"""
        self.connection = await create_connection()

    async def on_destroy(self):
        """关闭连接"""
        await self.connection.close()
```

---

## 二、服务注册迁移

### 2.1 ISingletonService 迁移

#### 旧代码

```python
from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService


class UserService(ISingletonService):
    # 必须实现这些方法（即使不需要）
    async def get(self, *args, **kwargs):
        raise NotImplementedError()

    async def save(self, *args, **kwargs):
        raise NotImplementedError()

    # 实际业务方法
    async def find_user(self, user_id: int):
        return await self.user_repo.find_by_id(user_id)
```

#### 新代码

```python
from pyspring.ioc import Component, Singleton, IManaged


@Component()
@Singleton
class UserService(IManaged):
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    # 只需要实现实际业务方法
    async def find_user(self, user_id: int):
        return await self.user_repo.find_by_id(user_id)
```

---

### 2.2 装饰器注册迁移

#### 旧代码

```python
from pyspring.ioc.annotations.decorators import service, component


@service
class EmailService:
    pass


@component(name="custom_cache", singleton=True)
class CacheService:
    pass
```

#### 新代码

```python
from pyspring.ioc import Service, Component, Singleton


@Service()
@Singleton
class EmailService:
    pass


@Component(name="custom_cache")
@Singleton
class CacheService:
    pass
```

---

## 三、容器访问迁移

### 3.1 容器初始化

#### 旧代码

```python
from pyspring.ioc.manager import AppContainerManager

# 初始化
container = AppContainerManager()
container.setup(modules=['myapp.services'])

# 获取服务
user_service = container.get(UserService)
```

#### 新代码

```python
from pyspring.ioc import ApplicationContext

# 初始化
ctx = ApplicationContext.initialize(['myapp.services'])

# 获取服务
user_service = ctx.get_by_type(UserService)
```

---

### 3.2 懒加载获取容器

#### 旧代码

```python
from pyspring.ioc.manager import AppContainerManager


class MyService:
    def some_method(self):
        # 懒加载获取
        container = AppContainerManager()
        dependency = container.get(SomeDependency)
```

#### 新代码

```python
from pyspring.ioc import ApplicationContext


class MyService:
    def some_method(self):
        # 懒加载获取
        ctx = ApplicationContext.get_instance()
        dependency = ctx.get_by_type(SomeDependency)
```

---

## 四、AOP集成迁移

### 4.1 使用AOP

#### 旧代码

```python
# AOP自动集成，无需特殊处理
from pyspring.aop import Aspect, Before


@Aspect
class LoggingAspect:
    @Before(pointcut="execution(* UserService.*(..))")
    def log_before(self, join_point):
        print(f"调用方法: {join_point.method_name}")


# UserService会自动被代理
class UserService(ISingletonService):
    pass
```

#### 新代码

```python
# 需要启用AOP（默认已启用）
from pyspring.ioc import ApplicationContext

ctx = ApplicationContext.initialize(['myapp'], enable_aop=True)

# Aspect定义不变
from pyspring.aop import Aspect, Before, Component, Singleton


@Component()
@Singleton
@Aspect
class LoggingAspect:
    @Before(pointcut="execution(* UserService.*(..))")
    def log_before(self, join_point):
        print(f"调用方法: {join_point.method_name}")


# UserService会自动被代理（如果有切面匹配）
from pyspring.ioc import Component, Singleton


@Component()
@Singleton
class UserService:
    pass
```

---

## 五、配置文件迁移

### 5.1 YAML配置

#### 旧版配置文件 (config/container.yaml)

```yaml
services:
  user_service:
    class: myapp.services.UserService
    singleton: true

  db_config:
    class: myapp.config.DatabaseConfig
    singleton: true
    properties:
      host: localhost
      port: 5432
```

#### 新版配置文件（推荐：Bean工厂方式）

```yaml
# config/container.yaml
scan_packages:
  - myapp.services
  - myapp.repositories

exclude_packages:
  - myapp.tests

services:
  # 使用工厂方法（推荐）
  db_config:
    factory: myapp.config.AppConfig.create_db_config
    singleton: true
```

```python
# myapp/config.py
from pyspring.ioc import Configuration, Bean


@Configuration
class AppConfig:
    @staticmethod
    @Bean
    def create_db_config():
        return DatabaseConfig(
            host="localhost",
            port=5432
        )
```

#### 最佳实践：完全使用装饰器

```python
from pyspring.ioc import Component, Singleton


@Component()
@Singleton
class UserService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo


@Component()
@Singleton
class DatabaseConfig:
    def __init__(self):
        self.host = "localhost"
        self.port = 5432
```

---

## 六、完整应用迁移示例

### 6.1 FastAPI应用

#### 旧代码

```python
from fastapi import FastAPI
from pyspring.ioc.manager import AppContainerManager

app = FastAPI()


@app.on_event("startup")
async def startup():
    container = AppContainerManager()
    container.setup(modules=['myapp'])

    # 手动初始化
    lifecycle = container.lifecycle
    await lifecycle.startup()


@app.on_event("shutdown")
async def shutdown():
    container = AppContainerManager()
    lifecycle = container.lifecycle
    await lifecycle.shutdown()


@app.get("/users")
async def get_users():
    container = AppContainerManager()
    user_service = container.get(UserService)
    return await user_service.get_all()
```

#### 新代码

```python
from fastapi import FastAPI
from pyspring.ioc import ApplicationContext

app = FastAPI()


@app.on_event("startup")
async def startup():
    # 初始化容器
    ctx = ApplicationContext.initialize(['myapp'])

    # 自动初始化所有生命周期服务（包括Initializer）
    await ctx.container.initialize_lifecycle_services()


@app.on_event("shutdown")
async def shutdown():
    # 自动销毁所有生命周期服务（包括ShutdownHandler）
    ctx = ApplicationContext.get_instance()
    await ctx.container.destroy_lifecycle_services()


@app.get("/users")
async def get_users():
    ctx = ApplicationContext.get_instance()
    user_service = ctx.get_by_type(UserService)
    return await user_service.get_all()
```

---

### 6.2 使用配置文件

#### 新代码

```python
from fastapi import FastAPI
from pyspring.ioc import ApplicationContext

app = FastAPI()


@app.on_event("startup")
async def startup():
    # 使用配置文件初始化
    ctx = ApplicationContext.initialize(
        config_file='config/container.yaml',
        enable_aop=True
    )
    await ctx.container.initialize_lifecycle_services()


@app.on_event("shutdown")
async def shutdown():
    ctx = ApplicationContext.get_instance()
    await ctx.container.destroy_lifecycle_services()
```

---

## 七、迁移检查清单

### 必须更改

- [ ] 所有 `from pyspring.ioc.manager import AppContainerManager`
    - → `from pyspring.ioc import ApplicationContext`

- [ ] 所有 `AppContainerManager().get()`
    - → `ApplicationContext.get_instance().get_by_type()`

- [ ] 所有 `class XxxService(ISingletonService)`
    - → `@Component() @Singleton class XxxService(IManaged)`

- [ ] 所有 `class XxxInitializer(IStartupInitializer)`
    - → `from pyspring.ioc.lifecycle import IStartupInitializer`

- [ ] 所有 `class XxxHandler(IShutdownHandler)`
    - → `from pyspring.ioc.lifecycle import IShutdownHandler`

### 可选优化

- [ ] 移除不需要的 `get()`, `save()` 空方法实现
- [ ] 使用 `@Bean` 替代复杂的工厂逻辑
- [ ] 使用 `@ConditionalOnMissingBean` 提供默认实现
- [ ] 统一 Initializer 和普通服务为 `ILifecycle`

### 测试验证

- [ ] 所有服务能正常注入
- [ ] 初始化器按预期执行
- [ ] 关闭处理器按预期执行
- [ ] 循环依赖自动解决
- [ ] AOP切面正常工作

---

## 八、常见问题

### Q: 为什么要统一为ILifecycle？

A: 简化接口，一个接口包含初始化和销毁逻辑，更符合面向对象设计。但为了兼容性，仍然保留 `IStartupInitializer` 和 `IShutdownHandler`。

### Q: 旧代码能直接运行吗？

A: 不能。因为旧的 `AppContainerManager` 已删除，必须迁移到 `ApplicationContext`。但接口层面提供了兼容（如 `IStartupInitializer`）。

### Q: 配置文件还支持吗？

A: 支持，但推荐使用装饰器 + Bean工厂方式，更灵活且类型安全。

### Q: AOP需要额外配置吗？

A: 不需要，默认启用。如果不需要AOP，可以设置 `enable_aop=False`。

---

**迁移优先级**：

1. 🔴 高优先级：容器访问、生命周期接口
2. 🟡 中优先级：服务注册方式、AOP集成
3. 🟢 低优先级：配置文件优化、新特性使用
