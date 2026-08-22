# 灵活装饰器实现模式

## 问题背景

为什么 `@staticmethod` 可以不加括号，而自定义装饰器 `@Bean` 必须加括号？

```python
# Python内置装饰器 - 不需要括号
@staticmethod
def my_method():
    pass


# 自定义装饰器 - 必须加括号？
@Bean()  # 为什么不能像 @staticmethod 一样？
def my_bean():
    pass
```

## 原理解析

### @staticmethod 的实现

`@staticmethod` 是一个**描述符类实例**，它本身就是装饰器：

```python
class staticmethod:
    def __init__(self, func):
        self.func = func

    # ... 其他方法


# 使用时
@staticmethod  # 直接传入函数对象
def method():
    pass
```

### 普通装饰器工厂

而我们的 `@Bean()` 是一个**工厂函数**，返回装饰器：

```python
def Bean(name=None):
    def decorator(func):  # 这才是真正的装饰器
        setattr(func, "__pyspring_bean__", True)
        return func

    return decorator


# 使用时必须调用
@Bean()  # 必须加括号，返回 decorator
def method():
    pass
```

## 解决方案：智能装饰器

通过检查第一个参数类型，同时支持两种用法：

```python
def Bean(
    func_or_name: Optional[Callable | str] = None,
    *,
    name: Optional[str] = None,
    init_method: Optional[str] = None,
    destroy_method: Optional[str] = None,
):
    """
    支持三种用法的智能装饰器：
    1. @Bean          - 不加括号
    2. @Bean()        - 空括号
    3. @Bean(...)     - 带参数
    """

    # 判断：第一个参数是函数 且 没有name参数
    if callable(func_or_name) and name is None:
        # 用法1: @Bean 直接装饰
        func = func_or_name
        setattr(func, "__pyspring_bean__", True)
        return func

    # 用法2&3: @Bean() 或 @Bean(name=...)
    # 如果 func_or_name 是字符串，说明是位置参数传入的name
    actual_name = func_or_name if isinstance(func_or_name, str) else name

    def decorator(func):
        setattr(func, "__pyspring_bean__", True)
        if actual_name:
            setattr(func, "__pyspring_bean_name__", actual_name)
        if init_method:
            setattr(func, "__pyspring_init_method__", init_method)
        if destroy_method:
            setattr(func, "__pyspring_destroy_method__", destroy_method)
        return func

    return decorator
```

## 核心技巧

### 1. 参数设计

```python
def Bean(
    func_or_name: Optional[Callable | str] = None,  # 第一个位置参数：函数或名称
    *,                                               # 强制后续参数为关键字参数
    name: Optional[str] = None,                      # 明确的name参数
    ...
):
```

**关键点**：

- 第一个参数可以是函数或字符串
- `*` 确保其他参数只能通过关键字传递
- 避免混淆 `Bean("name")` 和 `Bean(func)`

### 2. 判断逻辑

```python
if callable(func_or_name) and name is None:
    # 直接装饰：@Bean
    return decorated_func
else:
    # 返回装饰器：@Bean() 或 @Bean(...)
    return decorator
```

**判断条件**：

1. `callable(func_or_name)` - 第一个参数是可调用对象
2. `name is None` - 没有显式传入name参数

两个条件**同时满足**才是直接装饰模式。

### 3. 属性设置陷阱

⚠️ **不要使用 `@wraps(func)`**：

```python
# ❌ 错误：@wraps 会重置自定义属性
from functools import wraps


def decorator(func):
    @wraps(func)  # 这会覆盖我们设置的属性！
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    setattr(wrapper, "__custom__", True)  # 属性会丢失
    return wrapper
```

```python
# ✅ 正确：直接在原函数上设置属性
def decorator(func):
    setattr(func, "__custom__", True)  # 直接设置
    return func  # 返回原函数
```

## 使用示例

```python
from pyspring.core.ioc.annotations.component import Bean, Configuration


@Configuration
class AppConfig:
    @Bean  # 用法1: 不加括号（像 @staticmethod）
    def simple_bean(self):
        return "simple"

    @Bean()  # 用法2: 空括号
    def another_bean(self):
        return "another"

    @Bean(name="custom")  # 用法3: 带name参数
    def named_bean(self):
        return "custom"

    @Bean(init_method="init", destroy_method="cleanup")  # 用法4: 多个参数
    def lifecycle_bean(self):
        return "lifecycle"
```

## 类型提示

```python
from typing import Callable, Optional, TypeVar, Union, overload

T = TypeVar('T')

@overload
def Bean(func: Callable[..., T]) -> Callable[..., T]: ...

@overload
def Bean(
    func_or_name: None = None,
    *,
    name: Optional[str] = None,
    init_method: Optional[str] = None,
    destroy_method: Optional[str] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

def Bean(func_or_name=None, *, name=None, init_method=None, destroy_method=None):
    # 实现...
```

## 对比总结

| 特性   | `@Bean`（可带可不带括号） | `@staticmethod` |
|------|------------------------|-----------------|
| 不加括号 | ✅                       | ✅               |
| 空括号  | ✅                       | ❌               |
| 带参数  | ✅                       | ❌               |
| 灵活性  | 高                       | 低               |

## 适用场景

这种模式适用于：

1. **可选参数装饰器** - 参数不是必需的
2. **简化API** - 减少用户的心智负担
3. **灵活用法** - 同时支持带括号和不带括号的调用方式

## 注意事项

1. **第一个参数命名** - 用 `func_or_name` 等明确的名称
2. **使用 `*` 分隔符** - 强制后续参数为关键字参数
3. **判断条件严格** - 确保不会误判
4. **文档清晰** - 在docstring中说明所有用法

## 测试验证

```python
# 测试所有用法
@Bean
def test1():
    pass


@Bean()
def test2():
    pass


@Bean(name="custom")
def test3():
    pass


assert hasattr(test1, "__pyspring_bean__")
assert hasattr(test2, "__pyspring_bean__")
assert hasattr(test3, "__pyspring_bean__")
assert getattr(test3, "__pyspring_bean_name__") == "custom"
```

## 参考资源

- [PEP 318 - Decorators for Functions and Methods](https://www.python.org/dev/peps/pep-0318/)
- [functools.wraps 文档](https://docs.python.org/3/library/functools.html#functools.wraps)
- [Descriptor HowTo Guide](https://docs.python.org/3/howto/descriptor.html)
