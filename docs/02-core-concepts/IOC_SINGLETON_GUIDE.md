# IoC 容器与单例服务使用指南

## 概述

PySpring 框架提供了强大的 IoC (控制反转) 容器，支持依赖注入和单例模式管理。所有被容器托管的服务都通过 `@Component` / `@Service` 注解标记，由容器统一管理生命周期，确保线程安全和一致性。

## 核心概念

### IoC 容器

IoC 容器负责管理应用中所有服务的创建、生命周期和依赖关系。它提供：

- **自动依赖注入**: 自动解析并注入构造函数的依赖
- **单例管理**: 确保单例服务在应用生命周期内只创建一次
- **线程安全**: 保证多线程环境下的创建安全
- **懒加载**: 服务在首次使用时才创建
- **循环依赖检测**: 启动时通过 DAG 分析杜绝运行时循环引用

### 注册服务

使用注解将类注册到容器：

```python
from pyspring.core.ioc.annotations.component import Component


@Component  # 默认单例
class UserService:
    def __init__(self, db_manager: "DBManagerService"):
        self.db = db_manager

    def get_users(self):
        return self.db.query("SELECT * FROM users")
```

## 使用容器

### 初始化容器

```python
from pyspring.core.ioc import ApplicationContext

# 初始化并扫描指定包
app_context = ApplicationContext.initialize(base_packages=["app"])
```

### 获取服务

```python
# 按类型获取唯一实例
user_service = app_context.get_by_type(UserService)

# 获取全部实现（多实现场景）
all_services = app_context.get_all_of_type(IUserService)
```

### 在 FastAPI 路由中使用依赖注入

```python
from fastapi import APIRouter, Depends
from pyspring.core.ioc import ApplicationContext

router = APIRouter()
app_context = ApplicationContext.initialize(base_packages=["app"])


def get_user_service() -> UserService:
    """依赖注入函数"""
    return app_context.get_by_type(UserService)


@router.get("/users")
async def list_users(user_service: UserService = Depends(get_user_service)):
    return user_service.get_users()
```

## 单例模式最佳实践

### 1. 避免循环依赖

不要在单例的 `__init__` 中通过容器动态获取其他单例（可能导致循环依赖）：

```python
from pyspring.core.ioc.annotations.component import Component


# ✅ 推荐：通过构造函数注入依赖
@Component
class ServiceA:
    def __init__(self, service_b: "ServiceB"):
        self.service_b = service_b

    def do_something(self):
        self.service_b.process()


# ❌ 不推荐：在 __init__ 中动态获取，可能引发循环依赖
@Component
class ServiceA_bad:
    def __init__(self):
        ctx = ApplicationContext.initialize(base_packages=["app"])
        self.service_b = ctx.get_by_type(ServiceB)  # 危险
```

### 2. 合理使用缓存

对于频繁访问的服务，可以在类初始化时通过构造函数注入缓存引用，而非每次动态获取。

### 3. 单例的线程安全

容器保证单例的**创建过程**是线程安全的，但单例服务的**内部可变状态**需要开发者自己保证线程安全：

```python
import threading
from pyspring.core.ioc.annotations.component import Component


@Component
class CounterService:
    def __init__(self):
        self._lock = threading.Lock()
        self._counter = 0

    def increment(self):
        with self._lock:
            self._counter += 1
            return self._counter
```

### 4. 高并发请求隔离

单例默认共享状态，但在处理每个请求的独立数据时，可结合 `ContextVars` 实现请求级隔离，避免跨请求数据污染。

## 常见问题

### Q1: 什么类适合用单例？

满足以下条件之一的类适合使用单例模式：

- **配置管理类**: 应用配置在运行时通常不变
- **资源管理类**: 数据库连接池、缓存管理器等
- **日志管理类**: 全局日志配置和记录
- **全局状态管理**: 需要在应用范围内共享状态的类

### Q2: 单例和普通服务有什么区别？

| 特性 | 单例服务 (`@Component`/`@Service`) | 普通服务（每次创建） |
|------|------------------------------|-------------------|
| 生命周期 | 应用启动到结束 | 每次创建新实例 |
| 内存占用 | 低（只有一个实例） | 随实例数增加 |
| 状态共享 | 是 | 否 |
| 线程安全 | 需要注意 | 无需考虑 |
| 适用场景 | 配置、资源管理 | 业务逻辑、请求处理 |

### Q3: 容器本身是单例吗？

`ApplicationContext` 由 `initialize()` 创建并返回。每个 `initialize()` 调用产生独立容器实例，支持多上下文与更好的测试隔离。

### Q4: 如何在测试中隔离容器？

每个测试独立调用 `ApplicationContext.initialize()`，并在测试后清理容器状态，避免跨测试污染（参见 `tests/conftest.py` 的 `cleanup_ioc_container` fixture）。

## 相关文档

- [IoC 容器配置指南](IOC_CONFIG_GUIDE.md)
- [IoC 容器配置注入指南](IOC_CONFIG_INJECTION_GUIDE.md)
- [IoC 配置自动加载](IOC_CONFIG_AUTO_LOADING.md)
- [AOP 切面编程指南](AOP_GUIDE.md)

---

**文档版本**: 2.0
**适用版本**: PySpring 0.0.1（Starter 化架构）
