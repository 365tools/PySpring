"""
统一的应用异常类型。
- AppError：业务/运行时异常的统一基类，包含 code（HTTP/业务码）、message、details（上下文）、category（类别）
- ValidationAppError：用于请求数据校验失败的标准异常（HTTP 422）

使用示例：
    # 直接抛出业务异常
    raise AppError("资源不存在", code=404, details={"id": 123}, category="Resource")

    # 自定义细分异常类型
    class NotFoundError(AppError):
        def __init__(self, resource: str, resource_id: int):
            super().__init__(
                f"{resource} 不存在",
                code=404,
                details={"resource": resource, "id": resource_id},
                category="Resource",
            )

    # 参数验证失败（例如 Pydantic 验证错误汇总）
    raise ValidationAppError(details={"validation_errors": [{"field": "name", "message": "必填"}]})

    # 序列化为字典，用于日志或响应体合并
    try:
        ...
    except AppError as e:
        payload = e.to_dict()
        # {"type": "AppError", "message": "...", "code": 400, "details": {...}}
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class AppError(Exception):
    """应用/领域异常的统一基类。

    属性：
        code：HTTP/业务状态码（默认 400）
        message：人类可读错误信息
        details：可选上下文载荷，便于客户端或日志定位问题
        category：可选错误类别标识（例如 Resource/Auth/Validation 等）
    """

    def __init__(
            self,
            message: str,
            *,
            code: int = 400,
            details: Optional[Dict[str, Any]] = None,
            category: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.category = category

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
            **({"category": self.category} if self.category else {}),
        }


class ValidationAppError(AppError):
    """标准化的校验异常（HTTP 422）。

    可用于表单/JSON 体的字段级校验失败，details 建议包含结构化的错误列表：
        {
            "validation_errors": [
                {"field": "name", "message": "必填", "type": "value_error.missing"},
                {"field": "age", "message": "必须为正整数"}
            ]
        }
    """

    def __init__(self, message: str = "请求数据验证失败", *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=422, details=details)


class CircularDependencyError(AppError):
    """循环依赖异常"""

    def __init__(self, message: str, cycle: list = None):
        super().__init__(
            message,
            code=500,
            details={"cycle": cycle} if cycle else None,
            category="IoC"
        )
