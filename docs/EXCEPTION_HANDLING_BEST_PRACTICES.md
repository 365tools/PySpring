# 全局异常处理器最佳实践

## 概述

PySpring 框架提供了完善的全局异常处理机制（`GlobalExceptionHandler`），可以**自动捕获、记录和格式化所有异常**，无需在每个 API 端点手动编写 `try-catch`。

## 核心原则

> **"让框架处理异常，专注业务逻辑"**

### ❌ 不推荐（手动捕获）

```python
@router.post("/register")
async def register(request: RegisterRequest):
    try:
        result = await register_service.register(...)
        return Response.success(result)
    except ValueError as e:
        logger.warning(f"验证失败: {e}")
        return Response.error(HTTPException(...))
    except Exception as e:
        logger.exception("注册失败")
        return Response.error(HTTPException(...))
```

### ✅ 推荐（直接抛出）

```python
@router.post("/register")
async def register(request: RegisterRequest):
    # 直接调用服务，异常会被全局处理器自动捕获
    result = await register_service.register(...)
    return Response.success(result)
```

---

## 框架提供的异常处理能力

### 1. 自动异常分类

全局处理器会智能区分不同类型的异常：

| 异常类型              | HTTP 状态码      | 是否记录堆栈 | 用途                  |
|-------------------|---------------|--------|---------------------|
| `HTTPException`   | 自定义 (4xx/5xx) | ❌ 否    | 业务验证错误（用户已存在、权限不足等） |
| `AppError`        | 自定义 (400+)    | ✅ 是    | 自定义业务异常（带详细上下文）     |
| `ValidationError` | 422           | ❌ 否    | Pydantic 数据验证失败     |
| 其他异常              | 500           | ✅ 是    | 未预期的系统错误            |

### 2. 详细的日志记录

全局处理器的 `log_exception()` 方法会自动记录：

```python
❌ ValueError: 邮箱已存在
调用链:
└─ app / api / auth.py: 185 in register
result = await register_service.register(user_info)
└─ app / services / custom_register_service.py: 120 in register
raise ValueError("邮箱已存在")

错误详情:
error_type: ValueError
error_message: 邮箱已存在
traceback: [完整堆栈]
```

### 3. 统一的错误响应格式

```json
{
  "success": false,
  "code": 400,
  "message": "邮箱已存在",
  "data": {
    "error": {
      "type": "ValueError",
      "message": "邮箱已存在",
      "details": {
        "email": "test@example.com"
      }
    }
  }
}
```

---

## 使用指南

### 场景 1：业务验证错误（推荐抛出 `HTTPException`）

当用户输入不合法、资源不存在等业务错误时，直接抛出 `HTTPException`：

```python
from fastapi import HTTPException, status


async def register(user_info: UserInfo):
    # 检查邮箱是否存在
    if await self._email_exists(user_info.user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 继续处理...
```

**效果**：

- ✅ 自动返回 400 状态码
- ✅ 不记录错误堆栈（因为是业务错误，不是bug）
- ✅ 返回友好的错误消息

---

### 场景 2：自定义业务异常（推荐使用 `AppError`）

当需要携带额外上下文信息时，使用框架的 `AppError`：

```python
from pyspring.core.abstracts.exceptions import AppError


async def register(user_info: UserInfo):
    # 检查用户名黑名单
    if user_info.user.username in BLACKLIST:
        raise AppError(
            message="用户名不可用",
            code=400,
            details={
                "username": user_info.user.username,
                "reason": "在黑名单中"
            },
            category="Validation"
        )

    # 继续处理...
```

**效果**：

- ✅ 自动返回自定义状态码
- ✅ 记录详细的错误上下文
- ✅ 响应体包含 `details` 字段
- ✅ 支持错误分类（`category`）

**响应示例**：

```json
{
  "success": false,
  "code": 400,
  "message": "用户名不可用",
  "data": {
    "error": {
      "type": "AppError",
      "message": "用户名不可用",
      "code": 400,
      "category": "Validation",
      "details": {
        "username": "admin",
        "reason": "在黑名单中"
      }
    }
  }
}
```

---

### 场景 3：未预期的系统错误（让异常传播）

当发生数据库连接失败、第三方 API 调用失败等系统错误时，**不要捕获**，让异常传播到全局处理器：

```python
async def register(user_info: UserInfo):
    # 直接调用数据库，不捕获异常
    result = await self.session.execute(
        insert(UserModel).values(...)
    )
    await self.session.commit()

    # 调用第三方服务（如发送邮件），不捕获异常
    await email_service.send_welcome_email(user_info.user.email)

    return result
```

**效果**：

- ✅ 全局处理器自动记录**完整错误堆栈**
- ✅ 返回 500 状态码
- ✅ 生产环境下隐藏敏感信息
- ✅ 包含调用链和上下文（path、method、url）

**日志输出**：

```
ERROR | ❌ OperationalError: (psycopg2.OperationalError) FATAL:  database "mydb" does not exist
调用链:
  └─ app/api/auth.py:185 in register
       result = await register_service.register(user_info)
  └─ app/services/custom_register_service.py:150 in register
       await self.session.commit()
  └─ sqlalchemy/ext/asyncio/session.py:1234 in commit
       ...

错误详情:
  error_type: OperationalError
  error_message: FATAL: database "mydb" does not exist
  path: /api/auth/register
  method: POST
  url: http://localhost:8000/api/auth/register
```

---

## 自定义异常类型（进阶）

### 定义领域异常

```python
from pyspring.core.abstracts.exceptions import AppError


class ResourceNotFoundError(AppError):
    """资源不存在异常"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} 不存在",
            code=404,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            },
            category="Resource"
        )


class InsufficientBalanceError(AppError):
    """余额不足异常"""

    def __init__(self, required: float, available: float):
        super().__init__(
            message="余额不足",
            code=400,
            details={
                "required": required,
                "available": available,
                "shortfall": required - available
            },
            category="Payment"
        )
```

### 使用自定义异常

```python
async def purchase(user_id: str, amount: float):
    user = await user_repository.get(user_id)
    if not user:
        raise ResourceNotFoundError("用户", user_id)

    if user.balance < amount:
        raise InsufficientBalanceError(
            required=amount,
            available=user.balance
        )

    # 继续处理...
```

**效果**：

- ✅ 清晰的异常语义
- ✅ 类型安全（IDE 提示）
- ✅ 自动包含详细上下文
- ✅ 全局处理器统一处理

---

## 何时需要手动捕获异常？

只在以下**极少数**情况下需要手动 `try-catch`：

### 1. 需要异常恢复逻辑

```python
async def send_notification(user_id: str):
    try:
        # 尝试发送邮件
        await email_service.send(user_id)
    except EmailServiceError:
        # 邮件失败时降级到短信
        logger.warning(f"邮件发送失败，降级到短信")
        await sms_service.send(user_id)
```

### 2. 需要记录额外上下文后重新抛出

```python
async def process_batch(items: List[Item]):
    for index, item in enumerate(items):
        try:
            await process_item(item)
        except Exception as e:
            # 记录批次上下文
            logger.exception(f"处理第 {index} 条数据失败: {item.id}")
            # 重新抛出，让全局处理器返回错误响应
            raise AppError(
                message=f"批处理失败于第 {index} 条",
                code=500,
                details={"index": index, "item_id": item.id}
            ) from e
```

### 3. 需要清理资源（使用 `finally`）

```python
async def upload_file(file):
    temp_path = None
    try:
        temp_path = await save_temp_file(file)
        result = await upload_to_s3(temp_path)
        return result
    finally:
        # 无论成功还是失败，都清理临时文件
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
```

---

## 对比示例

### ❌ 反模式（过度捕获）

```python
@router.post("/register")
async def register(request: RegisterRequest):
    try:
        # 手动捕获每种异常
        user = await register_service.register(...)
        return Response.success(user)
    except ValueError as e:
        # 重复记录日志
        logger.warning(f"验证失败: {e}")
        return Response.error(HTTPException(...))
    except HTTPException as e:
        # 不必要的包装
        return Response.error(e)
    except Exception as e:
        # 手动记录堆栈
        logger.exception("注册失败")
        return Response.error(HTTPException(...))
```

**问题**：

- ❌ 代码冗余（每个端点都要重复）
- ❌ 日志重复（手动记录 + 全局处理器记录）
- ❌ 不一致（不同端点可能记录不同格式）
- ❌ 难以维护（修改错误处理需要改所有端点）

---

### ✅ 最佳实践（信任框架）

```python
from pyspring.core.abstracts.exceptions import AppError


@router.post("/register")
async def register(request: RegisterRequest):
    """用户注册
    
    框架会自动处理所有异常：
    - HTTPException: 返回对应状态码，不记录堆栈
    - AppError: 返回自定义状态码，记录详细上下文
    - 其他异常: 记录完整堆栈，返回 500
    """
    # 直接调用服务，不需要 try-catch
    result = await register_service.register(...)
    return Response.success(result)


# 在服务层抛出异常
class CustomRegisterService:
    async def register(self, user_info: UserInfo):
        # 业务验证
        if await self._email_exists(user_info.user.email):
            raise HTTPException(
                status_code=400,
                detail="邮箱已被注册"
            )

        # 自定义验证
        if user_info.user.username in BLACKLIST:
            raise AppError(
                message="用户名不可用",
                code=400,
                details={"username": user_info.user.username},
                category="Validation"
            )

        # 数据库操作（不捕获异常）
        result = await self.session.execute(...)
        await self.session.commit()

        return result
```

**优点**：

- ✅ 代码简洁（没有 try-catch 噪音）
- ✅ 统一处理（所有端点行为一致）
- ✅ 详细日志（全局处理器自动记录）
- ✅ 易于维护（修改异常处理只需改全局处理器）

---

## 总结

### 核心原则

1. **信任框架**：不要在 API 端点手动捕获异常
2. **业务异常用 HTTPException 或 AppError**：清晰表达业务错误
3. **系统异常直接抛出**：让全局处理器记录详细堆栈
4. **只在需要恢复/清理时手动捕获**：极少数场景

### 快速决策树

```
遇到错误时，我应该...

┌─ 是业务验证错误？（用户输入不合法、资源不存在）
│  └─ ✅ 抛出 HTTPException 或 AppError
│
├─ 需要携带详细上下文？（错误分类、结构化数据）
│  └─ ✅ 抛出 AppError
│
├─ 是系统错误？（数据库连接失败、第三方 API 失败）
│  └─ ✅ 不捕获，让异常传播到全局处理器
│
└─ 需要异常恢复或资源清理？
   └─ ✅ 手动 try-catch，处理后重新抛出或恢复
```

### 示例对照表

| 场景           | ❌ 反模式                           | ✅ 最佳实践                           |
|--------------|---------------------------------|----------------------------------|
| 用户输入验证失败     | `try-except` 包装 `HTTPException` | 直接抛出 `HTTPException`             |
| 邮箱已存在        | 手动返回 `Response.error()`         | 抛出 `HTTPException(400, "邮箱已注册")` |
| 数据库连接失败      | `try-except` 记录日志并返回 500        | 不捕获，让全局处理器处理                     |
| 需要记录额外上下文    | 手动 `logger.exception()`         | 抛出 `AppError` 携带 `details`       |
| 邮件发送失败，降级到短信 | ❌（需要恢复逻辑）                       | ✅ 手动 `try-except` 恢复             |

---

## 框架源码参考

- 全局异常处理器：`src/pyspring/web/handlers/exception.py`
- 异常基类：`src/pyspring/core/abstracts/exceptions.py`
- Example 模板：`src/pyspring/templates/example/app/api/auth.py.template`
