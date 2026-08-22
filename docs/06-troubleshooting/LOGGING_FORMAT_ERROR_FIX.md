# 日志格式 KeyError 问题修复指南

## 问题描述

当 PySpring 作为依赖在其他项目中使用时，可能会遇到以下日志错误：

```
--- Logging error in Loguru Handler #1 ---
KeyError: 'session_id'
--- End of logging error ---
```

或者：

```
KeyError: 'file_relative'
```

## 问题原因

这个问题由两个原因导致：

### 1. 日志格式使用了不存在的字段

在日志格式中使用了 `{extra[field_name]}` 语法访问 extra 字段，但该字段未通过 `logger.bind()` 提供：

```yaml
# 有问题的格式
format: "{time} | {level} | {extra[session_id]} | {message}"
```

如果代码中没有 `logger.bind(session_id="xxx")`，就会触发 `KeyError: 'session_id'`。

### 2. filter 函数未正确添加必需字段

如果使用了自定义过滤器，但过滤器没有确保必需字段存在，也会导致错误。

## 解决方案

### ✅ 方案 1: 使用安全的日志格式（推荐）

**修改前（有风险）**:

```yaml
logging:
  console:
    format: "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[file_relative]}</cyan>:<cyan>{line}</cyan> | {message}"
```

**修改后（安全）**:

```yaml
logging:
  console:
    # 使用内置字段，不依赖 extra
    format: "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{file.name}</cyan>:<cyan>{line}</cyan> | {message}"
```

### ✅ 方案 2: 确保过滤器添加所有必需字段

如果你必须使用 `extra[field_name]`，确保过滤器正确处理：

```python
def add_custom_fields(record):
    """确保所有必需的 extra 字段都存在"""
    # 确保 extra 字典存在
    if "extra" not in record:
        record["extra"] = {}

    # 添加缺失的字段
    if "file_relative" not in record["extra"]:
        try:
            record["extra"]["file_relative"] = record["file"].name
        except AttributeError, KeyError:
            record["extra"]["file_relative"] = "unknown"

    # 添加其他自定义字段
    if "session_id" not in record["extra"]:
        record["extra"]["session_id"] = "no-session"

    return record
```

## PySpring 已修复的内容

### 1. 智能 SafeExtraDict - 通用解决方案 ✨

PySpring 使用了一个更优雅的解决方案：**SafeExtraDict**，它能自动处理任何缺失的字段！

**核心实现**:

```python
class _SafeExtraDict(dict):
    """安全的 extra 字典，访问不存在的键时返回空字符串而不是抛出 KeyError"""
    
    def __missing__(self, key):
        """当访问不存在的键时返回空字符串"""
        return ""
    
    def __getitem__(self, key):
        """重写 __getitem__ 以支持 __missing__"""
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.__missing__(key)
```

**在过滤器中使用**:

```python
@staticmethod
def _add_relative_path(record):
    # 确保 extra 字典存在并包装为 SafeDict
    if "extra" not in record:
        record["extra"] = _SafeExtraDict()
    elif not isinstance(record["extra"], _SafeExtraDict):
        # 将现有的 extra 字典包装为 SafeDict
        record["extra"] = _SafeExtraDict(record["extra"])
    
    # ... 其他逻辑
    return record
```

**这意味着什么？**

✅ **完全通用**：您可以在日志格式中使用**任何字段**，不仅限于预定义的字段：

```yaml
format: "{extra[session_id]} | {extra[custom_field]} | {extra[anything]} | {message}"
```

✅ **零配置**：字段不存在时自动显示为空字符串，无需预先定义

✅ **灵活绑定**：通过 `logger.bind()` 随时添加字段值：

```python
logger.bind(session_id="sess123", custom_field="value").info("Message")
```

✅ **性能优化**：不需要遍历和预填充大量字段，只在访问时才处理

### 2. 更新了默认日志格式

所有模板和配置文件中的日志格式已更新为使用内置字段：

**控制台日志**:

```yaml
format: "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{file.name}</cyan>:<cyan>{line}</cyan> | {message}"
```

**文件日志**:

```yaml
format: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {file.name}:{line} | {message}"
```

## 最佳实践

### ✅ 推荐：使用 Loguru 内置字段

这些字段始终可用，无需额外处理：

| 字段             | 说明        | 示例                        |
|----------------|-----------|---------------------------|
| `{time}`       | 时间戳       | `2026-01-23 10:30:45.123` |
| `{level}`      | 日志级别      | `INFO`, `ERROR`           |
| `{message}`    | 日志消息      | `User login successful`   |
| `{file.name}`  | 文件名       | `service.py`              |
| `{file.path}`  | 完整路径      | `/path/to/service.py`     |
| `{line}`       | 行号        | `42`                      |
| `{function}`   | 函数名       | `login_user`              |
| `{module}`     | 模块名       | `auth.service`            |
| `{name}`       | logger 名称 | `pyspring.auth`           |
| `{process.id}` | 进程 ID     | `12345`                   |
| `{thread.id}`  | 线程 ID     | `67890`                   |

### ✅ 支持的 extra 字段（框架）

**好消息**：您可以在日志格式中使用**任何 extra 字段**！

PySpring 使用 `SafeExtraDict` 自动处理所有缺失字段，返回空字符串而不是抛出错误。

| 字段类型                     | 默认值         | 说明          |
|--------------------------|-------------|-------------|
| **任何未定义字段**              | `""` (空字符串) | 自动处理，不会报错   |
| `{extra[file_relative]}` | 自动计算        | 相对于项目根目录的路径 |

**使用示例 - 任何字段都可以**：

```yaml
# config/logging.yaml
logging:
  console:
    # ✅ 这些字段都可以安全使用，即使没有通过 bind() 提供
    format: "{time} | {extra[session_id]} | {extra[request_id]} | {extra[user_id]} | {message}"
    # 或者使用自定义字段
    format: "{time} | {extra[my_custom_field]} | {extra[anything_you_want]} | {message}"
```

**代码中绑定字段值**：

```python
from pyspring.log.instance import logger

# 默认情况（字段不存在，显示为空）
logger.info("User action")
# 输出: 2026-01-23 10:30:45 | INFO |  |  |  | User action
#                                     ↑  ↑  ↑ 空字段

# 绑定部分字段
logger.bind(session_id="sess_abc123").info("User action")
# 输出: 2026-01-23 10:30:45 | INFO | sess_abc123 |  |  | User action

# 绑定多个字段
bound_logger = logger.bind(session_id="sess_abc123", user_id="user_456", request_id="req_789")
bound_logger.info("User action")
# 输出: 2026-01-23 10:30:45 | INFO | sess_abc123 | req_789 | user_456 | User action

# 甚至可以使用自定义字段
logger.bind(my_custom_field="custom_value", another_field="another_value").info("Custom log")
# 输出: 2026-01-23 10:30:45 | INFO | custom_value | another_value | Custom log
```

### ⚠️ 谨慎使用 extra 字段

如果必须使用自定义字段：

```python
# 1. 使用 bind() 提供字段
logger = logger.bind(request_id="abc123", user_id=42)
logger.info("User action")

# 2. 在格式中使用
format: "{time} | {level} | {extra[request_id]} | {message}"
```

### 🔒 防御性编程

如果不确定字段是否存在，使用 Python 格式字符串的条件语法：

```yaml
# 不推荐（会抛出 KeyError）
format: "{extra[session_id]} | {message}"

# 推荐（字段不存在时显示 'N/A'）
format: "{extra.get('session_id', 'N/A')} | {message}"
```

但注意：Loguru 的格式字符串不支持 `.get()` 语法，所以最好确保字段存在或使用内置字段。

## 支持的日志字段

您可以在 `logging.yaml` 中使用**任何字段**，完全不用担心 KeyError：

```yaml
# ✅ 这些都不会报错，即使字段不存在
format: "{time} | {extra[session_id]} | {message}"
format: "{time} | {extra[request_id]} | {extra[user_id]} | {message}"
format: "{time} | {extra[custom_field_1]} | {extra[custom_field_2]} | {message}"
```

字段不存在时显示为空字符串，可以通过 `logger.bind()` 随时提供值。

## 常见问题

### Q1: 我需要显示相对路径怎么办？

A: 使用 `{file.name}` 显示文件名，这是最安全的选择。如果需要完整路径，使用 `{file.path}`。

也可以安全使用 `{extra[file_relative]}` 显示相对路径。

### Q2: 我能使用 `extra[file_relative]` 吗？

A: 可以！`file_relative` 字段会自动添加，无需担心 KeyError。

### Q3: 为什么会出现 `KeyError: 'session_id'`？

A: 当日志格式中使用了 `{extra[session_id]}`，但代码中没有使用 `logger.bind(session_id="xxx")` 提供该字段时，Loguru 尝试访问不存在的字段会导致 KeyError。

**解决方法**：

- 框架使用 `SafeExtraDict` 自动处理所有缺失字段
- 字段不存在时返回空字符串，不会报错
- 无需修改您的日志格式或代码

### Q4: 如何调试日志格式问题？

A: 使用最简单的格式测试：

```yaml
format: "{time} | {level} | {message}"
```

然后逐步添加字段，直到找到导致错误的字段。

### Q5: 我可以添加自己的自定义字段吗？

A: 当然可以！框架支持任何自定义字段。

**直接在格式中使用（无需预定义）**：

```yaml
format: "{time} | {extra[my_field]} | {extra[another_field]} | {message}"
```

**通过 bind() 提供值**：

```python
# 方式 1: 单次使用
logger.bind(my_field="value1", another_field="value2").info("Message")

# 方式 2: 创建绑定的 logger
custom_logger = logger.bind(my_field="value1")
custom_logger.info("Message 1")
custom_logger.info("Message 2")  # 所有日志都会包含 my_field
```

**动态字段示例**：

```python
# Web 请求中使用
def handle_request(request):
    request_logger = logger.bind(
        request_id=request.id, user_id=request.user.id if request.user else "anonymous", ip_address=request.client.host
    )
    request_logger.info("Processing request")
    # ... 业务逻辑
    request_logger.info("Request completed")
```

不需要在任何地方预定义这些字段，直接使用即可！

## 相关文档

- [日志配置指南](../03-configuration/LOGGING_CONFIG_GUIDE.md)
- [Loguru 官方文档](https://loguru.readthedocs.io/)
