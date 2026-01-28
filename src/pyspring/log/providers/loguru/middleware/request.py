"""
请求日志中间件
在请求开始和结束时记录日志，提供正确的日志顺序
支持详细的请求/响应日志（可配置）
"""

import json
import time
import uuid
from contextvars import ContextVar
from typing import Dict, Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from pyspring.config_manager import ConfigManager
from pyspring.core.abstracts.exceptions import AppError
from pyspring.ioc import ApplicationContext
from pyspring.log.instance import logger
from pyspring.web.handlers.exception import GlobalExceptionHandler
from ..utils.trace_context import set_trace_id

REQUEST_ID_CTX: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件 - 确保正确的日志顺序
    同时在请求作用域内注入trace_id(ContextVar)，便于所有日志包含统一调用链标识
    
    支持详细日志配置：
    - logging.http.log_request_headers: 记录请求头
    - logging.http.log_request_body: 记录请求体
    - logging.http.log_response_body: 记录响应体
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # 读取配置
        app_config = ConfigManager.load_config('application', use_cache=True)
        log_config = ConfigManager.load_config('logging', use_cache=True)
        
        self._include_trace_in_response = app_config.get('web', {}).get('error', {}).get('include_trace', False)

        # HTTP 详细日志配置
        http_config = log_config.get('logging', {}).get('http', {})
        self._log_request_details = http_config.get('log_request_details', False)
        self._log_response_details = http_config.get('log_response_details', False)
        self._log_request_headers = http_config.get('log_request_headers', False)
        self._log_request_body = http_config.get('log_request_body', False)
        self._log_response_body = http_config.get('log_response_body', False)
        self._max_body_length = http_config.get('max_body_length', 1024)
        self._sensitive_headers = set(h.lower() for h in http_config.get('sensitive_headers', [
            'authorization', 'cookie', 'x-api-key', 'x-auth-token'
        ]))

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """过滤敏感请求头"""
        return {
            k: '***' if k.lower() in self._sensitive_headers else v
            for k, v in headers.items()
        }

    def _truncate_body(self, body: Any) -> Any:
        """截断过长的请求/响应体"""
        # 如果是字符串，直接截断
        if isinstance(body, str):
            if len(body) > self._max_body_length:
                return body[:self._max_body_length] + f"... (truncated, total: {len(body)} bytes)"
            return body

        # 如果是字典/列表等JSON对象，先序列化检查长度
        if isinstance(body, (dict, list)):
            json_str = json.dumps(body, ensure_ascii=False)
            if len(json_str) > self._max_body_length:
                # 如果太长，返回截断的字符串表示
                return json_str[:self._max_body_length] + f"... (truncated, total: {len(json_str)} bytes)"
            # 否则返回原对象
            return body

        return body

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

        # 记录请求开始（基础信息）
        logger.bind(trace_id=trace_id).info(f"🎢 {client_ip} - \"{method} {url}\" - 请求开始")

        # 记录详细请求信息（可配置）
        if self._log_request_details or self._log_request_headers or self._log_request_body:
            request_details: Dict[str, Any] = {}

            if self._log_request_headers:
                headers_dict = dict(request.headers.items())
                sanitized = self._sanitize_headers(headers_dict)
                request_details["headers"] = sanitized

            if self._log_request_body:
                try:
                    # 读取请求体（需要缓存，避免后续处理无法读取）
                    body_bytes = await request.body()
                    if body_bytes:
                        try:
                            # 尝试解析为JSON对象
                            body_json = json.loads(body_bytes.decode('utf-8'))
                            # 直接存储对象，而不是字符串
                            request_details["body"] = self._truncate_body(body_json)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # 非JSON或无法解码，记录原始字节
                            request_details["body"] = self._truncate_body(body_bytes.decode('utf-8', errors='replace'))
                except Exception as e:
                    logger.debug(f"读取请求体失败: {e}")

            if request_details:
                # 使用换行输出，避免JSON转义字符
                formatted_json = json.dumps(request_details, ensure_ascii=False, indent=2)
                logger.bind(trace_id=trace_id, **request_details).debug(
                    "📥 请求详情:\n" + formatted_json
                )

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

            # 记录响应详情（仅成功请求，失败请求在异常处理器中记录）
            if self._log_response_details or self._log_response_body:
                if 200 <= status_code < 300:
                    response_details: Dict[str, Any] = {"status": status_code}

                    if self._log_response_body:
                        try:
                            # 注意：StreamingResponse无法读取body，这里只处理JSONResponse等
                            if hasattr(response, 'body'):
                                body_bytes = response.body
                                if body_bytes:
                                    try:
                                        body_json = json.loads(body_bytes.decode('utf-8'))
                                        # 直接存储对象，而不是字符串
                                        response_details["body"] = self._truncate_body(body_json)
                                    except (json.JSONDecodeError, UnicodeDecodeError):
                                        response_details["body"] = self._truncate_body(body_bytes.decode('utf-8', errors='replace'))
                        except Exception as e:
                            logger.debug(f"读取响应体失败: {e}")

                    if len(response_details) > 1:  # 除了status还有其他字段
                        formatted_json = json.dumps(response_details, ensure_ascii=False, indent=2)
                        logger.bind(trace_id=trace_id, **response_details).debug(
                            "📤 响应详情:\n" + formatted_json
                        )

            return response

        except Exception as e:
            # 请求异常日志
            process_time = time.time() - start_time

            # 从 IoC 容器获取全局异常处理器单例
            handler = ApplicationContext.get_instance().get_by_type(GlobalExceptionHandler)

            # 使用全局异常处理器记录详细日志（包含完整堆栈）
            handler.log_exception(e, context={
                "path": str(request.url.path),
                "method": request.method,
                "url": str(request.url),
                "client_ip": client_ip,
                "process_time": f"{process_time:.3f}s"
            })

            # 格式化错误响应
            status_code = getattr(e, "code", 500) if isinstance(e, AppError) else 500
            message = getattr(e, "message", str(e)) if isinstance(e, AppError) else str(e)

            error_response = GlobalExceptionHandler.to_http_error_response(
                e,
                message=message,
                status_code=status_code,
                details={"path": str(request.url.path), "method": request.method},
                include_trace=self._include_trace_in_response  # 根据配置决定
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
