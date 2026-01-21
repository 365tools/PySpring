# 新版PySpring IOC框架使用指南

**版本**: 2.0  
**重构日期**: 2026-01-21  
**状态**: ✅ 完成

---

## 一、架构概览

### 1.1 设计理念

新版IOC框架遵循以下设计原则：

1. **职责单一**：每个模块只负责一件事
2. **清晰分层**：扫描 → 注册 → 解析 → 实例化
3. **解耦设计**：模块之间通过接口通信
4. **最佳实践**：遵循Spring框架的设计理念

### 1.2 包结构

```
src/pyspring/ioc/
├── interfaces/              # 接口定义
│   ├── core.py             # IManaged, ILifecycle
│   └── services.py         # ICrudService, IRepository
├── annotations/            # 注解装饰器
│   ├── scope.py           # @Singleton, @Prototype
│   └── component.py       # @Component, @Bean, @Configuration
├── scanner/               # 组件扫描
│   ├── config.py         # 扫描配置
│   └── scanner.py        # 组件扫描器
├── registry/             # 服务注册
│   └── registry.py       # 服务注册表
├── resolver/             # 依赖解析
│   └── resolver.py       # 依赖解析器
├── proxy/                # 代理模式
│   └── lazy.py          # 懒加载代理
├── container/            # IOC容器
│   └── container.py      # 容器实现
└── context.py            # 应用上下文
```

---

## 二、核心接口

### 2.1 IManaged - 标记接口

```python
from pyspring.ioc.interfaces.core import IManaged

# 方式1：实现接口（推荐用于明确需要被管理的类）
class UserService(IManaged):
    pass

# 方式2：使用装饰器（更简洁）
from pyspring.ioc import Component, Singleton

@Component()
@Singleton
class UserService:
    pass
```

**使用场景**:

- ✅ 明确标记类需要被IOC管理
- ✅ 支持类型检查和IDE提示
- ✅ 不强制实现任何方法

### 2.2 ILifecycle - 生命周期接口

```python
from pyspring.ioc.interfaces.core import ILifecycle, IManaged
from pyspring.ioc import Component, Singleton

@Component()
@Singleton
class DatabaseService(IManaged, ILifecycle):
    def __init__(self):
        self.connection = None
    
    async def on_init(self):
        """服务初始化（依赖注入完成后调用）"""
        self.connection = await create_connection()
        print("数据库连接已建立")
    
    async def on_destroy(self):
        """服务销毁（容器关闭前调用）"""
        if self.connection:
            await self.connection.close()
            print("数据库连接已关闭")
```

**使用场景**:

- 需要在构造后进行资源初始化
- 需要在销毁前清理资源
- 建立/关闭数据库连接、网络连接等

---

## 三、注解系统

### 3.1 作用域注解

#### @Singleton - 单例模式

```python
from pyspring.ioc import Component, Singleton

@Component()
@Singleton
class ConfigService:
    """整个应用只有一个实例"""
    pass
```

**特点**:

- 容器启动时创建（除非标记为@Lazy）
- 全局共享同一实例
- 线程安全

**使用场景**:

- ✅ 无状态服务
- ✅ 配置管理器
- ✅ 缓存管理器
- ✅ 数据库连接池

#### @Prototype - 原型模式

```python
from pyspring.ioc import Component, Prototype

@Component()
@Prototype
class TaskProcessor:
    """每次请求都创建新实例"""
    def __init__(self):
        self.state = {}
```

**使用场景**:

- ✅ 有状态的服务
- ✅ 需要独立状态的对象
- ✅ 临时使用的对象

### 3.2 组件注解

#### @Component - 通用组件

```python
from pyspring.ioc import Component, Singleton

@Component()  # 使用默认名称
@Singleton
class EmailService:
    pass

@Component(name="custom_email")  # 自定义名称
@Singleton
class EmailService:
    pass

@Component(primary=True)  # 标记为主要候选者
@Singleton
class PrimaryEmailService:
    pass
```

#### @Service, @Repository - 语义化别名

```python
from pyspring.ioc import Service, Repository, Singleton

@Service()  # 语义上更清晰：这是一个业务服务
@Singleton
class AuthenticationService:
    pass

@Repository()  # 语义上更清晰：这是一个数据仓储
@Singleton
class UserRepository:
    pass
```

#### @Configuration + @Bean - 工厂方法

```python
from pyspring.ioc import Configuration, Bean
from myapp.services import EmailService, SMTPConfig

@Configuration
class AppConfig:
    
    @Bean
    def smtp_config(self) -> SMTPConfig:
        """配置对象"""
        return SMTPConfig(
            host="smtp.gmail.com",
            port=587
        )
    
    @Bean
    def email_service(self, smtp_config: SMTPConfig) -> EmailService:
        """复杂的对象构造"""
        service = EmailService(smtp_config)
        service.setup()
        return service
    
    @Bean(name="custom_cache")
    def cache_service(self) -> ICacheService:
        """自定义Bean名称"""
        return RedisCache()
```

#### @ConditionalOnMissingBean - 条件注册

```python
from pyspring.ioc import Configuration, Bean, ConditionalOnMissingBean


@Configuration
class DefaultConfig:

    @Bean
    @ConditionalOnMissingBean(IAuthProvider)
    def default_auth_provider(self) -> IAuthProvider:
        """仅当用户没有定义自己的AuthProvider时才注册"""
        return DefaultAuthProvider()
```

---

## 四、依赖注入

### 4.1 构造函数注入（推荐）

```python
from pyspring.ioc import Component, Singleton

@Component()
@Singleton
class UserService:
    def __init__(
        self,
        user_repo: IUserRepository,  # 接口注入
        email_service: EmailService,  # 具体类注入
        config: AppConfig             # 按参数名注入
    ):
        self.user_repo = user_repo
        self.email_service = email_service
        self.config = config
```

**解析优先级**:

1. 接口类型匹配（抽象类/Protocol）
2. 具体类型匹配
3. 参数名匹配

### 4.2 接口注入

```python
from abc import ABC, abstractmethod
from pyspring.ioc import Component, Singleton, Primary

# 定义接口
class INotificationService(ABC):
    @abstractmethod
    def send(self, message: str):
        pass

# 多个实现
@Component()
@Singleton
@Primary  # 标记为主要实现
class EmailNotificationService(INotificationService):
    def send(self, message: str):
        print(f"Email: {message}")

@Component()
@Singleton
class SMSNotificationService(INotificationService):
    def send(self, message: str):
        print(f"SMS: {message}")

# 使用时
@Component()
@Singleton
class OrderService:
    def __init__(self, notification: INotificationService):
        # 自动注入Primary实现（EmailNotificationService）
        self.notification = notification
```

---

## 五、应用启动

### 5.1 基本启动

```python
from pyspring.ioc import ApplicationContext

# 初始化IOC容器
ctx = ApplicationContext.initialize([
    'myapp.services',
    'myapp.repositories',
    'myapp.controllers'
])

# 获取服务
user_service = ctx.get_by_type(UserService)
# 或
user_service = ctx.get('user_service')

# 初始化生命周期服务
await ctx.container.initialize_lifecycle_services()
```

### 5.2 FastAPI集成

```python
from fastapi import FastAPI
from pyspring.ioc import ApplicationContext

app = FastAPI()

@app.on_event("startup")
async def startup():
    # 初始化IOC容器
    ctx = ApplicationContext.initialize(['myapp'])
    await ctx.container.initialize_lifecycle_services()

@app.on_event("shutdown")
async def shutdown():
    # 销毁生命周期服务
    ctx = ApplicationContext.get_instance()
    await ctx.container.destroy_lifecycle_services()

@app.get("/users")
async def get_users():
    ctx = ApplicationContext.get_instance()
    user_service = ctx.get_by_type(UserService)
    return await user_service.get_all()
```

---

## 六、高级特性

### 6.1 循环依赖处理

新框架自动使用懒加载代理解决循环依赖：

```python
# ServiceA 依赖 ServiceB
@Component()
@Singleton
class ServiceA:
    def __init__(self, service_b: 'ServiceB'):
        self.service_b = service_b  # 自动使用LazyProxy

# ServiceB 依赖 ServiceA
@Component()
@Singleton
class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a  # 自动使用LazyProxy
```

**工作原理**:

1. 检测到潜在循环依赖
2. 自动注入 `LazyProxy` 而非真实实例
3. 第一次访问属性时才获取真实实例
4. 真实实例被缓存，后续访问直接返回

### 6.2 懒加载

```python
from pyspring.ioc import Component, Singleton, Lazy

@Component()
@Singleton
@Lazy  # 延迟到第一次使用时才实例化
class ExpensiveService:
    def __init__(self):
        # 耗时的初始化操作
        import time
        time.sleep(5)
```

### 6.3 条件Bean

```python
from pyspring.ioc import Configuration, Bean, ConditionalOnMissingBean


@Configuration
class SecurityConfig:

    @Bean
    @ConditionalOnMissingBean(IAuthProvider)
    def default_auth_provider(self) -> IAuthProvider:
        """提供默认实现，允许用户覆盖"""
        return JWTAuthProvider()
```

---

## 七、与旧版本的对比

| 特性              | 旧版                                         | 新版                                          |
|-----------------|--------------------------------------------|---------------------------------------------|
| **接口设计**        | `ISingletonService` 继承 `IService`，强制实现CRUD | `IManaged` 纯标记接口，可选实现 `ILifecycle`          |
| **作用域**         | 通过继承接口声明                                   | 通过装饰器声明 `@Singleton`, `@Prototype`          |
| **注册方式**        | 4种方式混乱                                     | 统一为 `@Component` 和 `@Bean`                  |
| **循环依赖**        | 手动检测，容易递归                                  | 自动使用 `LazyProxy` 解决                         |
| **包结构**         | 单个大文件 `registrar.py`                       | 清晰分层：scanner, registry, resolver, container |
| **Initializer** | 被错误注册为普通组件                                 | 自动排除，由 LifecycleManager 管理                  |

---

## 八、迁移指南

### 8.1 替换接口继承

**旧版**:

```python
from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService

class MyService(ISingletonService):
    async def get(self): pass  # 被迫实现
    async def save(self): pass
```

**新版**:

```python
from pyspring.ioc import Component, Singleton
from pyspring.ioc.interfaces import IManaged

@Component()
@Singleton
class MyService(IManaged):
    # 不需要实现任何强制方法
    pass
```

### 8.2 替换手动注册

**旧版**:

```python
# 手动在某处创建和注册
container.bind_singleton('my_service', MyService)
```

**新版**:

```python
# 使用装饰器，自动扫描注册
@Component()
@Singleton
class MyService:
    pass
```

### 8.3 替换懒加载

**旧版**:

```python
from pyspring.ioc.manager import AppContainerManager

class MyService:
    @property
    def dependency(self):
        if self._dependency is None:
            self._dependency = AppContainerManager().get(SomeService)
        return self._dependency
```

**新版**:

```python
# 直接注入，框架自动处理循环依赖
@Component()
@Singleton
class MyService:
    def __init__(self, dependency: SomeService):
        self.dependency = dependency
```

---

## 九、常见问题

### Q1: 如何排除某些类不被扫描？

在 `scanner/config.py` 中配置排除规则，或者不使用 `@Component` 装饰器。

### Q2: 如何处理List注入？

```python
# 当前版本暂不支持List注入
# 建议使用以下方式：

@Component()
@Singleton
class MyService:
    def __init__(self, container: Container):
        self.container = container
    
    def get_all_handlers(self):
        return self.container.get_all_of_type(IHandler)
```

### Q3: Initializer还需要特殊处理吗？

不需要！新框架自动排除Initializer，它们由 `LifecycleManager` 专门管理。

### Q4: 如何调试注册了哪些服务？

```python
ctx = ApplicationContext.get_instance()
print(ctx.container.registry.all_names())
```

---

## 十、最佳实践

### ✅ 推荐

1. **优先使用构造函数注入**
2. **接口和实现分离**
3. **为复杂对象使用 @Bean 工厂方法**
4. **使用 @ConditionalOnMissingBean 提供默认实现**
5. **明确标记作用域（@Singleton 或 @Prototype）**

### ❌ 避免

1. **避免在构造函数中执行耗时操作** - 使用 `ILifecycle.on_init()`
2. **避免循环依赖** - 虽然框架能处理，但最好重新设计
3. **避免在Bean方法中调用 `container.get()`** - 使用参数注入
4. **避免手动创建服务实例** - 让IOC容器管理

---

**文档版本**: 1.0  
**最后更新**: 2026-01-21
