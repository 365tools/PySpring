# AOP 切面编程指南 (Aspect Oriented Programming)

AOP 允许你将横切关注点（如日志记录、事务管理、权限检查、性能监控）从业务逻辑中分离出来，使业务代码更纯粹。

## 1. 核心概念

- **切面 (Aspect)**: 一个包含横切逻辑的类。
- **通知 (Advice)**: 切面的具体行为，分为 `@Before`, `@After`, `@Around`。
- **切入点 (Pointcut)**: 定义增强逻辑应用在哪些方法上（支持正则表达式）。
- **代理 (Proxy)**: AOP 框架创建的对象，用于在目标对象方法调用前后执行通知。

## 2. 快速上手

### 步骤 1: 定义切面

创建一个类，继承 `Aspect` 或使用 `@aspect` 装饰器。

```python
from pyspring.aop.core import Aspect, Before, After, Around
from pyspring.log.instance import logger


class LoggingAspect(Aspect):
    # 匹配所有 Service 类的 create_ 开头的方法
    @Before(pointcut=".*Service\.create_.*")
    def log_before_create(self, target, method_name, args, kwargs):
        logger.info(f"正在创建资源: {method_name}, 参数: {args}")

    @After(pointcut=".*Service\.delete_.*")
    def log_after_delete(self, target, method_name, result):
        logger.info(f"资源删除完成: {method_name}")

    @Around(pointcut=".*Service\.complex_.*")
    def measure_time(self, proceed, target, method_name, args, kwargs):
        import time

        start = time.time()
        try:
            # 执行原始方法
            result = proceed()
            return result
        finally:
            cost = (time.time() - start) * 1000
            logger.info(f"方法 {method_name} 耗时: {cost:.2f}ms")
```

### 步骤 2: 注册切面

将切面类放在你的业务代码目录中（例如 `app/aspects`），并在 `config/container.yaml` 的 `scan.packages` 中配置好该路径。

只要加上 `@Component` 装饰器或直接继承 `Aspect` 基类，扫描器就能自动识别它。

```yaml
# config/container.yaml
scan:
  packages:
    - app.aspects  # <--- 你的切面代码所在包
```

*(注：系统会自动实例化扫描到的 Aspect 类)*

### 步骤 3: 自动代理

当你从容器获取 Service 时：

```python
user_service = container.get(UserService)
```

如果 `UserService` 的方法名匹配了 `LoggingAspect` 定义的正则规则，你拿到的 `user_service` 实际上是一个 **AopProxy** 包装对象。调用其方法时，会自动触发拦截逻辑。

## 3. 技术限制

1. **仅限容器托管对象**: 只有通过 IoC 容器获取的对象 (`container.get`) 才能被代理。手动 `new UserService()` 无法生效。
2. **方法内部调用失效**: 如果 `method_a` 内部调用了 `self.method_b`，且 `method_b` 也有切面，默认情况下 `self.method_b` 的切面**不会**触发（这是 Python 动态代理的常见限制）。
3. **Regex 性能**: 复杂的正则表达式可能会轻微拖慢实例化速度（仅在启动时）。

## 4. 最佳实践

- **日志审计**: 统一记录所有写操作（create/update/delete）的入参和操作人。
- **异常捕获**: 在 @Around 中统一捕获特定异常并转换为 API 错误码。
- **性能监控**: 统计慢 SQL 或慢服务调用。
