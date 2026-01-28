# 自定义异常处理器指南

## 概述

PySpring 框架提供了强大的异常处理器系统，支持用户自定义异常处理逻辑。

## 框架默认异常处理器

框架提供的 `GlobalExceptionHandler` 具有以下特性：

✅ **详细的异常堆栈**

- 自动提取项目相对路径
- 显示调用链（最后 3 帧）
- 完整 traceback 信息

✅ **区分异常类型**

- HTTPException: HTTP 错误
- ValidationError: 请求数据验证失败
- 通用异常: 所有未捕获的异常

✅ **结构化日志**

- 绑定错误类型、文件位置、行号、函数名
- 调用链摘要

✅ **统一响应格式**

```json
{
  "code": 500,
  "message": "错误消息",
  "data": {
    "error_type": "ValueError",
    "file_location": "src/app/services/user.py",
    "line_number": 42,
    "traceback_summary": "app/api/users.py:15 -> app/services/user.py:42",
    "full_traceback": "..."
  }
}
```

## 使用方式

### 1. 使用框架默认处理器（推荐）

**main.py:**

```python
from fastapi import FastAPI
from pyspring.web.handlers.exception import GlobalExceptionHandler

app = FastAPI()

# 自动从 IoC 容器获取异常处理器（默认 GlobalExceptionHandler）
GlobalExceptionHandler.register_exception_handlers(app)
```

**特点:**

- 无需任何配置
- 自动注册为 IoC 组件
- 使用 `@ConditionalOnMissingBean`，可被用户实现替换

---

### 2. 继承框架处理器（自定义部分逻辑）

**app/config/exception_config.py:**

```python
from typing import Dict, Any, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from pyspring.ioc import Component, Singleton
from pyspring.web.handlers.exception import GlobalExceptionHandler
from pyspring.log.instance import logger


@Component
@Singleton
class CustomExceptionHandler(GlobalExceptionHandler):
    """自定义异常处理器（继承框架实现）"""

    async def handle_general_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """重写通用异常处理，添加自定义逻辑"""

        # 1. 添加额外的日志记录
        logger.warning(f"🔔 自定义异常处理: {type(exc).__name__}")

        # 2. 可以在这里发送告警通知（钉钉、邮件等）
        # await self.send_alert_notification(exc)

        # 3. 调用父类方法处理基础逻辑
        return await super().handle_general_exception(request, exc)

    def log_exception(self, e: Exception, context: Optional[Dict[str, Any]] = None, level: str = "error"):
        """自定义日志格式"""
        # 添加额外的上下文信息
        if context is None:
            context = {}
        context["app_version"] = "1.0.0"
        context["environment"] = "production"

        # 调用父类方法
        super().log_exception(e, context, level)
```

**main.py:**

```python
from pyspring.web.handlers.exception import GlobalExceptionHandler

# 不需要手动指定，框架会自动检测到你的 CustomExceptionHandler
# 因为它实现了 IExceptionHandler 接口，且没有 @ConditionalOnMissingBean
GlobalExceptionHandler.register_exception_handlers(app)
```

---

### 3. 完全自定义实现（实现接口）

**app/config/exception_config.py:**

```python
from typing import Dict, Any, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from pyspring.ioc import Component, Singleton
from pyspring.web.handlers.base import IExceptionHandler
from pyspring.log.instance import logger


@Component
@Singleton
class MyCustomExceptionHandler(IExceptionHandler):
    """完全自定义的异常处理器"""

    def format_exception_info(self, e: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """自定义异常信息格式"""
        return {
            "error_class": type(e).__name__,
            "error_msg": str(e),
            "context": context or {}
        }

    def log_exception(self, e: Exception, context: Optional[Dict[str, Any]] = None, level: str = "error"):
        """自定义日志记录"""
        logger.error(f"❌ 错误: {type(e).__name__} - {str(e)}")

    async def handle_http_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """处理 HTTP 异常"""
        self.log_exception(exc, {"path": str(request.url.path)})
        return JSONResponse(
            status_code=getattr(exc, "status_code", 500),
            content={"error": str(exc)}
        )

    async def handle_validation_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """处理验证异常"""
        self.log_exception(exc, {"path": str(request.url.path)})
        return JSONResponse(
            status_code=422,
            content={"error": "验证失败"}
        )

    async def handle_general_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """处理通用异常"""
        self.log_exception(exc, {
            "path": str(request.url.path),
            "method": request.method
        })
        return JSONResponse(
            status_code=500,
            content={"error": "服务器内部错误"}
        )
```

---

## 组件替换机制

PySpring 框架使用 **继承检测机制** 自动替换组件：

### 工作原理

1. **扫描阶段**  
   框架扫描所有带 `@Component` 的类

2. **类型映射**  
   建立 `类型 → 组件列表` 的映射表

3. **继承检测**  
   检测子类是否继承了父类（使用 `issubclass()`）

4. **自动替换**
    - 框架的 `GlobalExceptionHandler` 使用 `@ConditionalOnMissingBean(IExceptionHandler)`
    - 用户的 `CustomExceptionHandler extends GlobalExceptionHandler`
    - 框架检测到继承关系 → 自动替换

### 日志输出示例

```
🔄 检测到替换: custom_exception_handler (CustomExceptionHandler) 替换 global_exception_handler (GlobalExceptionHandler)
⏩ 跳过条件组件 global_exception_handler: 已被 custom_exception_handler 替换
✅ custom_exception_handler (singleton) [conditional]
✅ 从 IoC 容器获取异常处理器: CustomExceptionHandler
✅ 全局异常处理器已注册: CustomExceptionHandler
```

---

## 最佳实践

### ✅ 推荐做法

1. **继承扩展而非重写全部**
   ```python
   class CustomExceptionHandler(GlobalExceptionHandler):
       # 只重写需要自定义的方法
       async def handle_general_exception(self, request: Request, exc: Exception):
           # 添加自定义逻辑
           await self.send_alert(exc)
           # 调用父类方法
           return await super().handle_general_exception(request, exc)
   ```

2. **保留详细日志**  
   框架的日志包含完整堆栈和调用链，对排查问题非常有帮助

3. **统一响应格式**  
   使用框架的 `Response.error()` 保持前后端接口一致性

### ❌ 避免做法

1. **不要捕获异常后丢弃堆栈**
   ```python
   # ❌ 错误示例
   try:
       ...
   except Exception as e:
       return {"error": str(e)}  # 丢失了调用栈！
   ```

2. **不要简化日志输出**
   ```python
   # ❌ 错误示例
   logger.error(str(e))  # 缺少上下文和堆栈
   
   # ✅ 正确示例
   self.log_exception(e, context={"path": request.url.path})
   ```

---

## 故障排查

### 问题：异常信息不完整

**症状：** 日志只显示 "操作失败"，看不到错误栈

**原因：** 使用了简化的异常处理器（如旧版 example 模板）

**解决：**

1. 检查 `main.py` 是否使用框架的 `GlobalExceptionHandler`
2. 确认没有使用自定义的 `global_exception_handler` 中间件
3. 重启应用查看日志

### 问题：自定义处理器不生效

**症状：** 创建了 `CustomExceptionHandler` 但仍使用默认处理器

**原因：**

1. 没有添加 `@Component` 注解
2. 没有继承 `GlobalExceptionHandler` 或实现 `IExceptionHandler`
3. 包路径未被扫描

**解决：**

```python
from pyspring.ioc import Component, Singleton
from pyspring.web.handlers.exception import GlobalExceptionHandler


@Component  # ← 必须添加
@Singleton
class CustomExceptionHandler(GlobalExceptionHandler):  # ← 必须继承
    ...
```

---

## 版本变更

### v1.1.0b27+

- ✅ 添加 `IExceptionHandler` 接口
- ✅ `GlobalExceptionHandler` 注册为 IoC 组件
- ✅ 支持继承替换机制
- ✅ 新增 `register_exception_handlers()` 方法
- ⚠️  `register_global_exception_handlers()` 已废弃

### v1.1.0b26 及之前

- 使用静态方法 `register_global_exception_handlers()`
- 不支持 IoC 注入
- 需要手动传递处理器实例
