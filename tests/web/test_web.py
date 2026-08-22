"""
pyspring-web：统一响应测试

验证独立 web starter 的核心能力：
- 成功响应构造（success 标记、data）
- 错误响应构造（异常、HttpResponse、任意数据）
- 业务码与 HTTP 状态一致时省略 code（框架约定）
"""

import json

from pyspring.web.core.response import HttpResponse, Response


class TestResponseSuccess:
    """成功响应"""

    def test_success_with_data(self):
        resp = Response.success({"name": "test"})
        assert resp.status_code == 200
        body = json.loads(resp.body)
        assert body["success"] is True
        assert body["data"] == {"name": "test"}

    def test_success_with_message(self):
        resp = Response.success(None, message="done")
        body = json.loads(resp.body)
        assert body["success"] is True
        assert body["message"] == "done"

    def test_success_http_status(self):
        resp = Response.success({"ok": True}, business_code=201)
        assert resp.status_code == 201
        body = json.loads(resp.body)
        assert body["success"] is True


class TestResponseError:
    """错误响应"""

    def test_error_with_exception(self):
        resp = Response.error(ValueError("boom"))
        assert resp.status_code == 500
        body = json.loads(resp.body)
        assert body["success"] is False
        # 异常信息放在 data 中（error_type + reason）
        assert body["data"]["error_type"] == "ValueError"
        assert body["data"]["reason"] == "boom"

    def test_error_with_http_response(self):
        http_resp = HttpResponse(code=400, data={"field": "invalid"}, message="bad request")
        resp = Response.error(http_resp)
        assert resp.status_code == 400
        body = json.loads(resp.body)
        assert body["success"] is False
        assert body["data"] == {"field": "invalid"}

    def test_error_with_raw_data(self):
        resp = Response.error({"reason": "custom"})
        body = json.loads(resp.body)
        assert body["success"] is False
        assert body["data"] == {"reason": "custom"}


class TestHttpResponse:
    """HttpResponse 模型"""

    def test_http_response_creation(self):
        resp = HttpResponse(code=200, data={"a": 1}, message="ok")
        assert resp.code == 200
        assert resp.data == {"a": 1}
        assert resp.message == "ok"

    def test_http_response_generic(self):
        resp = HttpResponse[int](code=200, data=42)
        assert resp.data == 42

    def test_http_response_success_attr(self):
        resp = HttpResponse(code=200, data=None)
        assert resp.success is None  # 未设置时默认为 None，由 _json 计算
