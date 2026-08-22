# 中间件使用指南

## 当前配置

本项目**已使用框架提供的 RequestLoggingMiddleware**，无需额外配置。

查看 [main.py](../main.py) 中的配置：

```python
from pyspring.core.log.providers.loguru.middleware.request import RequestLoggingMiddleware

app.add_middleware(RequestLoggingMiddleware)
```

本目录下的文件（`request_logger.py`、`timing.py`）**仅作为教学示例**，展示如何编写自定义中间件。

---

## 框架提供的中间件

### 1. 请求日志中间件（推荐）

框架提供了功能完善的 `RequestLoggingMiddleware`，**强烈推荐使用**。

#### 使用方法

```python
# main.py
from pyspring.core.log.providers.loguru.middleware.request import RequestLoggingMiddleware

app = FastAPI(...)

# 注册中间件（使用 add_middleware）
app.add_middleware(RequestLoggingMiddleware)
```

#### 功能特性

| 特性                | 说明                                 |
|-------------------|------------------------------------|
| **Trace ID 支持**   | 自动生成/提取 X-Trace-ID 和 X-Request-ID  |
| **完整生命周期**        | 记录请求开始、完成、异常                       |
| **自动异常捕获**        | 集成 GlobalExceptionHandler，格式化错误响应  |
| **智能日志级别**        | 根据状态码自动选择 INFO/WARNING/ERROR       |
| **耗时统计**          | 精确到毫秒的请求处理时间                       |
| **ContextVar 隔离** | 多线程安全，避免 Trace ID 泄漏               |
| **响应头注入**         | 自动在响应中添加 X-Trace-ID 和 X-Request-ID |

#### 日志示例

```
2026-01-26 21:20:55.123 | INFO     | 🎢 127.0.0.1 - "POST /api/auth/login" - 请求开始
2026-01-26 21:20:55.456 | INFO     | ✅ 127.0.0.1 - "POST /api/auth/login" 200 - 耗时: 0.333s

2026-01-26 21:21:12.789 | WARNING  | ⚠️ 127.0.0.1 - "GET /api/users/999" 404 - 耗时: 0.012s

2026-01-26 21:22:03.456 | ERROR    | ❌ 127.0.0.1 - "POST /api/payment" 500 - 耗时: 0.789s
2026-01-26 21:22:03.457 | ERROR    | 🚨 127.0.0.1 - "POST /api/payment" - 异常: Database connection failed - 耗时: 0.789s
```

#### 状态码 Emoji 映射

- ✅ 2xx: 成功
- ⚠️ 4xx: 客户端错误（业务异常）
- ❌ 5xx: 服务器错误（系统异常）
- 🚨: 未捕获的异常

---

### 2. 认证中间件

框架提供了 `AuthenticationMiddleware`，自动处理 JWT 验证。

```python
from pyspring.security.authentication.web.middleware.auth import AuthenticationMiddleware

app.add_middleware(AuthenticationMiddleware)
```

---

## 自定义中间件（教学示例）

本项目的 `request_logger.py` 和 `timing.py` 仅作为教学示例，展示如何编写自定义中间件。

### request_logger.py（简化版）

```python
async def request_logging_middleware(request: Request, call_next):
    """简化版请求日志（教学示例）"""
    logger.info(f"🔵 请求开始: {request.method} {request.url.path}")
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(f"🟢 请求完成: {response.status_code} - {process_time:.3f}s")
    return response
```

**缺点**（相比框架版本）：

- ❌ 没有 Trace ID 支持（无法追踪分布式请求）
- ❌ 没有异常捕获（异常时不记录日志）
- ❌ 日志格式不统一（没有结构化字段）
- ❌ 没有根据状态码分级（所有日志都是 INFO）
- ❌ 没有 ContextVar 隔离（多请求可能混乱）

---

## 迁移到框架中间件

### 步骤 1: 更新 main.py

```python
# main.py
from pyspring.core.log.providers.loguru.middleware.request import RequestLoggingMiddleware

# 删除旧的自定义中间件
# app.middleware("http")(request_logging_middleware)  # ❌ 删除

# 使用框架中间件
app.add_middleware(RequestLoggingMiddleware)  # ✅ 推荐
```

### 步骤 2: 删除自定义文件（可选）

```bash
# 如果不再需要教学示例，可以删除
rm app/middleware/request_logger.py
```

### 步骤 3: 测试验证

```bash
# 启动应用
uvicorn app.main:app --reload

# 发送测试请求
curl http://localhost:8000/api/auth/login

# 查看日志
# 应该看到：
# 🎢 127.0.0.1 - "POST /api/auth/login" - 请求开始
# ✅ 127.0.0.1 - "POST /api/auth/login" 200 - 耗时: 0.123s
```

---

## 中间件执行顺序

中间件按**注册顺序的反序**执行（洋葱模型）：

```python
app.add_middleware(CORSMiddleware)  # 第 4 层（最外层）
app.add_middleware(RequestLoggingMiddleware)  # 第 3 层
app.add_middleware(AuthenticationMiddleware)  # 第 2 层
app.middleware("http")(timing_middleware)  # 第 1 层（最内层）
```

**执行流程**：

```
请求 → CORS → RequestLogging → Authentication → Timing → 路由处理
                                                          ↓
响应 ← CORS ← RequestLogging ← Authentication ← Timing ← 路由处理
```

**推荐顺序**：

1. `CORSMiddleware`（最外层，处理跨域）
2. `RequestLoggingMiddleware`（记录完整请求）
3. `AuthenticationMiddleware`（身份验证）
4. 自定义业务中间件

---

## 常见问题

### Q: 为什么推荐使用框架中间件？

A: 框架中间件经过充分测试，提供：

- ✅ 开箱即用的功能
- ✅ 统一的日志格式
- ✅ 与框架其他组件集成（如 GlobalExceptionHandler）
- ✅ 更好的性能和稳定性

### Q: 什么时候需要自定义中间件？

A: 只在以下场景：

- 框架没有提供对应功能
- 需要特殊的业务逻辑（如自定义限流、加密）
- 需要集成第三方系统

### Q: 如何同时使用多个日志中间件？

A: **不推荐**。多个日志中间件会导致：

- ❌ 日志重复
- ❌ 性能下降
- ❌ Trace ID 不一致

**推荐**：只使用框架的 `RequestLoggingMiddleware`。

### Q: 框架中间件支持哪些日志格式？

A: 框架中间件使用 Loguru，支持：

- JSON 格式（生产环境）
- 彩色控制台格式（开发环境）
- 自定义格式（通过配置）

---

## 总结

| 中间件                        | 状态    | 推荐度   | 说明           |
|----------------------------|-------|-------|--------------|
| `RequestLoggingMiddleware` | 框架提供  | ⭐⭐⭐⭐⭐ | 功能完善，强烈推荐    |
| `AuthenticationMiddleware` | 框架提供  | ⭐⭐⭐⭐⭐ | JWT 验证       |
| `request_logger.py`        | 自定义示例 | ⭐⭐    | 仅作教学，不推荐生产   |
| `timing.py`                | 自定义示例 | ⭐⭐⭐   | 可选，框架日志已包含耗时 |

**最佳实践**：优先使用框架中间件，只在必要时自定义。
