"""
请求日志中间件
在请求开始和结束时记录日志，提供正确的日志顺序
"""

import time
import uuid
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from pyspring.core.abstracts.exceptions import AppError
from pyspring.log.instance import logger
from pyspring.log.providers.loguru.utils.trace_context import set_trace_id
from pyspring.web.handlers.exception import GlobalExceptionHandler

REQUEST_ID_CTX: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件 - 确保正确的日志顺序
    同时在请求作用域内注入trace_id(ContextVar)，便于所有日志包含统一调用链标识
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """
        处理请求并记录日志
        """
        start_time = time.time()

        # 请求开始日志
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)

        # 优先使用 X-Trace-ID 或 X-Request-ID，否则生成新 ID
        trace_id = (
                request.headers.get("X-Trace-ID")
                or request.headers.get("X-Request-ID")
                or str(uuid.uuid4())
        )

        # 设置到 ContextVar
        token = REQUEST_ID_CTX.set(trace_id)
        set_trace_id(trace_id)

        logger.bind(trace_id=trace_id).info(f"🎢 {client_ip} - \"{method} {url}\" - 请求开始")

        try:
            # 处理请求
            response: Response = await call_next(request)

            # 设置响应头
            try:
                response.headers.setdefault('X-Trace-ID', trace_id)
                response.headers.setdefault('X-Request-ID', trace_id)
            except Exception as e:
                logger.error(f"🚨 {e}")
                pass

            # 计算处理时间
            process_time = time.time() - start_time

            # 请求完成日志
            status_code = response.status_code

            # 根据状态码选择不同的emoji和日志级别
            if 200 <= status_code < 300:
                emoji = "✅"
                log_method = logger.info
            elif 400 <= status_code < 500:
                emoji = "⚠️"
                log_method = logger.warning
            else:
                emoji = "❌"
                log_method = logger.error

            log_method(f"{emoji} {client_ip} - \"{method} {url}\" {status_code} - 耗时: {process_time:.3f}s")

            return response

        except Exception as e:
            # 请求异常日志
            process_time = time.time() - start_time
            logger.error(f"🚨 {client_ip} - \"{method} {url}\" - 异常: {str(e)} - 耗时: {process_time:.3f}s")

            # 使用全局异常处理器格式化响应
            status_code = getattr(e, "code", 500) if isinstance(e, AppError) else 500
            message = getattr(e, "message", str(e)) if isinstance(e, AppError) else str(e)

            error_response = GlobalExceptionHandler.to_http_error_response(
                e,
                message=message,
                status_code=status_code,
                details={"path": str(request.url.path), "method": request.method},
                include_trace=True
            )

            # 设置响应头
            try:
                error_response.headers.setdefault('X-Trace-ID', trace_id)
                error_response.headers.setdefault('X-Request-ID', trace_id)
            except Exception as ex:
                logger.error(f"🚨 {ex}")
                pass

            return error_response
        finally:
            try:
                REQUEST_ID_CTX.reset(token)
            except Exception as e:
                logger.error(f"🚨 {e}")
                pass
            # 清理上下文，避免泄漏到后续请求
            try:
                set_trace_id(None)
            except Exception as e:
                logger.error(f"🚨 {e}")
                pass
