"""
异常处理器抽象基类

提供可替换的异常处理器接口，支持用户自定义实现
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from fastapi import Request
from fastapi.responses import JSONResponse


class IExceptionHandler(ABC):
    """
    异常处理器接口
    
    用户可以继承此接口实现自定义异常处理逻辑
    """

    @abstractmethod
    def format_exception_info(self, e: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        格式化异常信息
        
        Args:
            e: 异常对象
            context: 上下文信息
            
        Returns:
            格式化后的异常信息字典
        """
        pass

    @abstractmethod
    def log_exception(self, e: Exception, context: Optional[Dict[str, Any]] = None, level: str = "error"):
        """
        记录异常日志
        
        Args:
            e: 异常对象
            context: 上下文信息
            level: 日志级别
        """
        pass

    @abstractmethod
    async def handle_http_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """
        处理 HTTP 异常（HTTPException）
        
        Args:
            request: FastAPI 请求对象
            exc: HTTP 异常
            
        Returns:
            JSON 响应
        """
        pass

    @abstractmethod
    async def handle_validation_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """
        处理验证异常（Pydantic ValidationError）
        
        Args:
            request: FastAPI 请求对象
            exc: 验证异常
            
        Returns:
            JSON 响应
        """
        pass

    @abstractmethod
    async def handle_general_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """
        处理通用异常（所有未被捕获的异常）
        
        Args:
            request: FastAPI 请求对象
            exc: 异常对象
            
        Returns:
            JSON 响应
        """
        pass


__all__ = ['IExceptionHandler']
