"""
统一 API 响应结构构造工具
- 返回 JSON：{"code": <http_status>, "message": <string|optional>, "data": <payload|optional>}
- code 使用 HTTP 状态码；message 为提示信息；data 为有效数据或错误信息
"""
import traceback as _tb
from typing import Any, Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

T = TypeVar("T")


class HttpResponse(BaseModel, Generic[T]):
    """通用返回对象(支持泛型以在OpenAPI中呈现data的具体类型)

    - code: 业务码(当与 HTTP 状态码一致时省略不返回)
    - message: 人类可读的提示信息(可选)
    - data: 负载对象(可选，类型由泛型参数T指定)
    """
    code: (int) | None = Field(default=None, description="Business/App code; omitted when equals HTTP status")
    message: (str) | None = Field(default=None, description="Human-readable message")
    success: (bool) | None = Field(default=None, description="Indicates if the request was successful")
    data: (T) | None = Field(default=None, description="Payload object")


def _json(result: HttpResponse[Any], status_code: int | None = None, headers: (dict[str, str]) | None = None) -> JSONResponse:
    """构造JSONResponse，避免重复代码；允许显式设置 HTTP 状态码、headers

    - 当code与最终HTTP状态码相同，按约定从响应体中移除code
    - 使用 jsonable_encoder 将不可JSON序列化的对象(如 set、datetime等)转换为可序列化形式
    """
    # 计算最终HTTP状态码(允许显式传入覆盖)
    final_status = status_code if status_code is not None else result.code
    result.success = (final_status is not None and 200 <= final_status < 300)

    # 生成内容(先 Pydantic dump，再经jsonable转换)
    raw_content = result.model_dump(exclude_none=True)
    content = jsonable_encoder(raw_content)

    # 遵循约定：当业务码与 HTTP 状态一致时，省略不返回 code
    if final_status is not None and content.get("code") == final_status:
        content.pop("code", None)

    return JSONResponse(
        status_code=final_status or 200,
        content=content,
        headers=headers,
    )


class Response:
    """统一 API 响应结构构造器(类静态方法)"""

    @staticmethod
    def success(result: Any, business_code: (int) | None = 200, message: (str) | None = None) -> JSONResponse:
        """成功响应：接收任意对象；Pydantic模型经model_dump，再经jsonable转换，避免属性(property)类型无法序列化"""
        http_status = business_code if business_code is not None else 200
        if isinstance(result, BaseModel):
            payload = result.model_dump()
        else:
            payload = result
        safe_payload = jsonable_encoder(payload, exclude_none=True)
        response = HttpResponse(code=http_status, data=safe_payload, message=message)
        return _json(response, status_code=http_status, headers=None)

    @staticmethod
    def error(
            result: HttpResponse[Any] | Exception | Any,
            headers: (dict[str, str]) | None = None,
            *,
            exc: (Exception) | None = None,
            include_trace: bool = False,
            error_id: (str) | None = None,
            default_status_code: int = 500,
    ) -> JSONResponse:
        """
        错误响应器:
        - 当入参为HttpResponse：保留其code/message/data，并合并诊断信息；如code为空，HTTP状态默认为default_status_code(默认500)
        - 当入参为Exception：自动构造HttpResponse(message=str(exc))，并合并诊断信息(error_type/reason/traceback)；HTTP状态为default_status_code
        - 当入参为任意数据(非HttpResponse/Exception)：将其作为data，message保持为空；HTTP状态为default_status_code

        统一保证返回的data为字典形状，便于前端消费
        """
        # 标准化为 HttpResponse + 捕获的异常对象
        captured_exc: (Exception) | None = exc
        if isinstance(result, HttpResponse):
            base_resp = result
        elif isinstance(result, Exception):
            captured_exc = result if captured_exc is None else captured_exc
            base_resp = HttpResponse(code=None, message=str(result), data=None)
        else:
            base_resp = HttpResponse(code=None, message=None, data=result)

        # 合并诊断信息到data中(不覆盖调用方已有键)
        payload: dict[str, Any] = {}
        if error_id is not None:
            payload.setdefault("error_id", error_id)
        if captured_exc is not None:
            payload.setdefault("error_type", captured_exc.__class__.__name__)
            payload.setdefault("reason", str(captured_exc))
            if include_trace:
                try:
                    tb_text = "\n".join(_tb.TracebackException.from_exception(captured_exc).format())
                    lines = tb_text.strip().splitlines()
                    payload.setdefault("traceback", "\n".join(lines[-8:]) if lines else tb_text)
                except Exception:
                    pass

        # 统一对base_data经jsonable转换，避免vars()/迭代属性对象报错
        base_data: Any = base_resp.data
        if isinstance(base_data, BaseModel):
            base_data = base_data.model_dump()
        safe_base = jsonable_encoder(base_data, exclude_none=True) if base_data is not None else None

        if isinstance(safe_base, dict):
            merged_data: dict[str, Any] = {**payload, **safe_base}
        elif safe_base is None:
            merged_data = {**payload} if payload else {}
        else:
            merged_data = {"value": safe_base, **payload}

        # 优化响应：如果 message 与 reason 相同，则不返回 message
        final_message = base_resp.message
        if final_message and "reason" in merged_data and final_message == merged_data["reason"]:
            final_message = None

        augmented = HttpResponse(code=base_resp.code, message=final_message, data=merged_data)
        http_status = augmented.code if augmented.code is not None else default_status_code
        return _json(augmented, status_code=http_status, headers=headers)
