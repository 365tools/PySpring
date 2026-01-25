"""
统一异常处理器
提供全局异常捕获、格式化和日志记录
"""

import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from pyspring.core.abstracts.exceptions import AppError
from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.conditional import ConditionalOnMissingBean
from pyspring.ioc.annotations.scope import Singleton
from pyspring.log.instance import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from .base import IExceptionHandler
from ..core.response import Response, HttpResponse


@Component()
@Singleton
@ConditionalOnMissingBean(IExceptionHandler)
class GlobalExceptionHandler(IExceptionHandler):
    """
    全局异常处理器（框架默认实现）
    
    特性：
    - 详细的异常堆栈信息（包含项目相对路径）
    - 区分 HTTPException、ValidationError、通用异常
    - 结构化日志记录
    - 统一的错误响应格式
    
    用户可以继承此类或实现 IExceptionHandler 接口来自定义异常处理逻辑
    """

    @staticmethod
    def _project_root() -> Path:
        """
        更稳健地解析项目根(以src上方为界)
        """
        p = Path(__file__).resolve()
        if "src" in p.parts:
            return Path(*p.parts[: p.parts.index("src")])
        return p.parents[3] if len(p.parents) >= 4 else p.parent

    @staticmethod
    def _relpath(file_path: str) -> str:
        """相对路径(相对于项目根)"""
        try:
            root = GlobalExceptionHandler._project_root()
            return str(Path(file_path).resolve().relative_to(root)).replace("\\", "/")
        except Exception as e:
            logger.error(f"🚨 {e}")
            return file_path.replace("\\", "/")

    def format_exception_info(self, e: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """格式化异常信息，包含调用栈(仅保留项目相关的关键调用链，便于 IDE 点击)"""
        exc_type, exc_value, exc_traceback = sys.exc_info()

        # 获取调用栈信息(更健壮的异常格式化)
        try:
            tb_text = "".join(traceback.TracebackException.from_exception(e).format())
        except Exception as e2:
            logger.error(str(e2))
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            tb_text = "".join(tb_lines) if tb_lines else ""

        # 提取关键信息(最后一帧)
        error_info: Dict[str, Any] = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "file_location": "unknown",
            "line_number": "unknown",
            "function_name": "unknown",
            "traceback_summary": "",
            "full_traceback": tb_text,
        }

        # 提取最后一帧信息
        if exc_traceback:
            tb = exc_traceback
            while tb and tb.tb_next:
                tb = tb.tb_next
            if tb:
                frame = tb.tb_frame
                error_info.update({
                    "file_location": GlobalExceptionHandler._relpath(frame.f_code.co_filename),
                    "line_number": tb.tb_lineno,
                    "function_name": frame.f_code.co_name,
                })

        # 生成简化调用链(仅保留 src/ 下的帧，末尾最多3层)
        project_frames = []
        try:
            tb_iter = exc_traceback
            while tb_iter:
                f = tb_iter.tb_frame
                filename = GlobalExceptionHandler._relpath(f.f_code.co_filename)
                if "/src/" in ("/" + filename):
                    project_frames.append(f"{filename}:{tb_iter.tb_lineno} in {f.f_code.co_name}()")
                tb_iter = tb_iter.tb_next
            if project_frames:
                error_info["traceback_summary"] = " -> ".join(project_frames[-3:])
        except Exception as e3:
            logger.error(str(e3))
            pass

        # 添加上下文信息
        if context:
            error_info["context"] = context  # type: ignore[index]

        return error_info

    def log_exception(self, e: Exception, context: Optional[Dict[str, Any]] = None, level: str = "error"):
        """
        统一记录异常日志(结构化绑定)
        """
        info = self.format_exception_info(e, context)
        log_msg = f"❌ {info['error_type']}: {info['error_message']}"
        if info.get("traceback_summary"):
            log_msg += f" | 调用链: {info['traceback_summary']}"

        bound = logger.bind(
            error_type=info.get("error_type"),
            error_message=info.get("error_message"),
            file_location=info.get("file_location"),
            line_number=info.get("line_number"),
            function_name=info.get("function_name"),
            traceback_summary=info.get("traceback_summary"),
        )
        if context:
            bound = bound.bind(**context)

        getattr(bound, level if level in {"error", "warning", "critical"} else "error")(log_msg)

    def _build_http_response_payload(self, e: Exception, info: Dict[str, Any], details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {"path": info.get("file_location"), "traceback_summary": info.get("traceback_summary")}
        if details:
            payload.update(details)
        # 若是 AppError，合并其结构
        if isinstance(e, AppError):
            payload.update({
                "error": e.to_dict(),
            })
        return payload

    def to_http_error_response(self, e: Exception, *, message: Optional[str] = None, status_code: int = 500,
                               details: Optional[Dict[str, Any]] = None, include_trace: Optional[bool] = None) -> JSONResponse:
        """将异常转为统一 HTTP 错误响应(使用Response.error)"""
        include = include_trace if include_trace is not None else False
        info = self.format_exception_info(e, details)
        payload = self._build_http_response_payload(e, info, details)
        base = HttpResponse(code=status_code, message=(message or info.get("error_message")), data=payload)
        return Response.error(base, exc=e, include_trace=include, default_status_code=status_code)

    # ====================================================================================
    # 实现 IExceptionHandler 接口
    # ====================================================================================

    async def handle_http_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """处理 HTTP 异常（HTTPException）"""
        return self.to_http_error_response(
            exc,
            message=str(getattr(exc, "detail", exc)),
            status_code=getattr(exc, "status_code", 500),
            details={"path": str(request.url.path), "method": request.method},
            include_trace=False
        )

    async def handle_validation_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """处理验证异常（Pydantic ValidationError）"""
        validation_errors = []
        try:
            if isinstance(exc, ValidationError):
                for error in exc.errors():
                    validation_errors.append({
                        "field": ".".join(str(loc) for loc in error.get("loc", [])),
                        "message": error.get("msg"),
                        "type": error.get("type"),
                        "input": error.get("input"),
                    })
        except Exception as ee:
            logger.error(f"🚨 格式化验证错误失败: {ee}")

        base = HttpResponse(
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="请求数据验证失败",
            data={
                "validation_errors": validation_errors,
                "path": str(request.url.path),
                "method": request.method,
            },
        )
        return Response.error(
            base,
            exc=exc,
            include_trace=False,
            default_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    async def handle_general_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """处理通用异常（所有未被捕获的异常）"""
        # 记录详细日志
        self.log_exception(exc, context={
            "path": str(request.url.path),
            "method": request.method,
            "url": str(request.url)
        })

        # 若业务抛出AppError，可直接使用其code
        status_code = getattr(exc, "code", 500) if isinstance(exc, AppError) else 500
        message = getattr(exc, "message", str(exc)) if isinstance(exc, AppError) else str(exc)

        return self.to_http_error_response(
            exc,
            message=message,
            status_code=status_code,
            details={"path": str(request.url.path), "method": request.method},
            include_trace=True  # 通用异常显示完整堆栈
        )

    def handle_and_return_error(self, e: Exception, context: Optional[Dict[str, Any]] = None,
                                default_message: str = "操作失败") -> Dict[str, Any]:
        """
        处理异常并返回标准错误对象(通用场景，非HTTP路径)
        """
        self.log_exception(e, context)
        info = self.format_exception_info(e, context)
        body = {
            "success": False,
            "error": default_message,
            "error_details": {
                "type": info["error_type"],
                "message": info["error_message"],
                "location": f"{info['function_name']}() at line {info['line_number']}",
            },
            "context": context or {}
        }
        if isinstance(e, AppError):
            body["app_error"] = e.to_dict()
        return body

    # ====================================================================================
    # Spring Boot 风格：应用启动时注册全局异常处理
    # ====================================================================================

    @staticmethod
    def register_exception_handlers(app, handler: Optional['IExceptionHandler'] = None):
        """
        注册全局异常处理器到 FastAPI 应用
        
        支持自动从 IoC 容器获取异常处理器实例，或使用指定的处理器
        
        Args:
            app: FastAPI 应用实例
            handler: 异常处理器实例（可选）。如果不提供，则从 IoC 容器获取
            
        Returns:
            bool: 是否成功注册
            
        示例：
            # 使用默认处理器（从 IoC 容器自动获取）
            GlobalExceptionHandler.register_exception_handlers(app)
            
            # 使用自定义处理器
            custom_handler = MyExceptionHandler()
            GlobalExceptionHandler.register_exception_handlers(app, handler=custom_handler)
        """
        # 如果没有提供处理器，尝试从 IoC 容器获取
        if handler is None:
            try:
                from pyspring.ioc import ApplicationContext
                handler = ApplicationContext.get_instance().get_by_type(IExceptionHandler)
                logger.info(f"✅ 从 IoC 容器获取异常处理器: {type(handler).__name__}")
            except Exception as e:
                logger.warning(f"⚠️  无法从 IoC 容器获取异常处理器，使用默认实现: {e}")
                handler = GlobalExceptionHandler()

        # 注册三类异常处理
        app.add_exception_handler(StarletteHTTPException, handler.handle_http_exception)
        app.add_exception_handler(ValidationError, handler.handle_validation_exception)
        app.add_exception_handler(Exception, handler.handle_general_exception)

        logger.info(f"✅ 全局异常处理器已注册: {type(handler).__name__}")
        return True


# 装饰器：自动异常处理(通用)

def _wrap_sync(func: Callable, on_error: Callable[[Exception, Dict[str, Any]], Any], context_extractor=None):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            details = {}
            if context_extractor:
                try:
                    details = context_extractor(*args, **kwargs) or {}
                except Exception as ex:
                    logger.error(f"🚨 {ex}")
            return on_error(e, details)

    return wrapper


def _wrap_async(func: Callable, on_error: Callable[[Exception, Dict[str, Any]], Any], context_extractor=None):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            details = {}
            if context_extractor:
                try:
                    details = context_extractor(*args, **kwargs) or {}
                except Exception as ex:
                    logger.error(f"🚨 {ex}")
            return on_error(e, details)

    return wrapper


def handle_exceptions(default_message: str = "操作失败", context_extractor=None):
    """自动异常处理装饰器(通用返回 dict)"""

    def decorator(func):
        return _wrap_sync(
            func,
            lambda e, ctx: GlobalExceptionHandler.handle_and_return_error(e, ctx, default_message),
            context_extractor,
        )

    return decorator


def handle_async_exceptions(default_message: str = "操作失败", context_extractor=None):
    """
    异步函数自动异常处理装饰器(通用返回dict)
    """

    def decorator(func):
        return _wrap_async(
            func,
            lambda e, ctx: GlobalExceptionHandler.handle_and_return_error(e, ctx, default_message),
            context_extractor,
        )

    return decorator


# 针对 FastAPI 路由的便捷装饰器(直接返回JSONResponse)

def handle_http_exceptions(default_message: str = "操作失败", status_code: int = 500, context_extractor=None, include_trace: Optional[bool] = None):
    """同步路由专用装饰器：异常时返回统一 JSONResponse"""

    def decorator(func):
        return _wrap_sync(
            func,
            lambda e, details: GlobalExceptionHandler.to_http_error_response(e, message=default_message, status_code=status_code, details=details, include_trace=include_trace),
            context_extractor,
        )

    return decorator


def handle_async_http_exceptions(default_message: str = "操作失败", status_code: int = 500, context_extractor=None, include_trace: Optional[bool] = None):
    """
    异步路由专用装饰器：异常时返回统一JSONResponse
    """

    def decorator(func):
        return _wrap_async(
            func,
            lambda e, details: GlobalExceptionHandler.to_http_error_response(e, message=default_message, status_code=status_code, details=details, include_trace=include_trace),
            context_extractor,
        )

    return decorator
