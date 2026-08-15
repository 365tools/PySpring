"""
请求日志中间件
在请求开始和结束时记录日志，提供正确的日志顺序
支持详细的请求/响应日志（可配置）
"""

import json
import time
import uuid
from contextvars import ContextVar
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from pyspring.core.config_manager import ConfigManager
from pyspring.core.abstracts.exceptions import AppError
from pyspring.core.log.instance import logger
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

    def _sanitize_headers(self, headers: dict[str, str]) -> dict[str, str]:
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

        # 收集请求详细信息（可配置）
        request_details: dict[str, Any] = {}

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

        # 记录请求开始（合并基础信息和详情）
        if request_details and (self._log_request_details or self._log_request_headers or self._log_request_body):
            formatted_json = json.dumps(request_details, ensure_ascii=False, indent=2)
            logger.bind(trace_id=trace_id, **request_details).debug(
                f"🎢 {client_ip} - \"{method} {url}\" - 请求开始\n📥 请求详情:\n{formatted_json}"
            )
        else:
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

            # 收集响应详情（可配置）
            response_details: dict[str, Any] = {}

            if (self._log_response_details or self._log_response_body) and (200 <= status_code < 300):
                response_details["status"] = status_code

                if self._log_response_body:
                    try:
                        # FastAPI响应可能需要读取body_iterator
                        body_bytes = None

                        # 方式1: 直接有body属性（部分响应类型）
                        if hasattr(response, 'body'):
                            body_bytes = response.body
                        # 方式2: 有body_iterator（StreamingResponse等）
                        elif hasattr(response, 'body_iterator'):
                            body_iterator = getattr(response, 'body_iterator')
                            body_chunks = []
                            async for chunk in body_iterator:
                                body_chunks.append(chunk)
                            body_bytes = b"".join(body_chunks)

                            # 重新创建响应（因为body_iterator已被消费）
                            from starlette.responses import Response as StarletteResponse
                            response = StarletteResponse(
                                content=body_bytes,
                                status_code=response.status_code,
                                headers=dict(response.headers),
                                media_type=response.media_type,
                            )

                        # 解析body
                        if body_bytes:
                            raw = bytes(body_bytes)
                            try:
                                body_json = json.loads(raw.decode('utf-8'))
                                response_details["body"] = self._truncate_body(body_json)
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                response_details["body"] = self._truncate_body(raw.decode('utf-8', errors='replace'))
                    except Exception as e:
                        logger.debug(f"读取响应体失败: {e}")

            # 记录请求完成（合并基础信息和响应详情）
            if len(response_details) > 1:  # 有响应详情
                formatted_json = json.dumps(response_details, ensure_ascii=False, indent=2)
                log_method(f"{emoji} {client_ip} - \"{method} {url}\" {status_code} - 耗时: {process_time:.3f}s\n📤 响应详情:\n{formatted_json}")
            else:
                log_method(f"{emoji} {client_ip} - \"{method} {url}\" {status_code} - 耗时: {process_time:.3f}s")

            return response

        except Exception as e:
            # 请求异常日志（core 层仅负责日志记录，错误响应的格式化由 web 层全局异常处理器负责）
            process_time = time.time() - start_time

            status_code = getattr(e, "code", 500) if isinstance(e, AppError) else 500
            logger.bind(
                trace_id=trace_id,
                error_type=type(e).__name__,
                error_message=str(e),
                status_code=status_code,
                path=str(request.url.path),
                method=request.method,
                client_ip=client_ip,
                process_time=f"{process_time:.3f}s",
            ).error(f"❌ {type(e).__name__}: {e}")

            # 重新抛出异常，交由 web 层注册的全局异常处理器生成统一错误响应
            # （符合 Spring 职责分离：日志中间件记录日志，全局异常处理器生成响应）
            raise
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
