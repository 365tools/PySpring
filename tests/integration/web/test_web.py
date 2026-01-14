"""
Web 模块测试

测试 pyspring.web 下的响应封装和异常处理逻辑
"""
import json
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.pyspring.web.core.response import Response, HttpResponse
from src.pyspring.web.handlers.exception import GlobalExceptionHandler
from src.pyspring.core.abstracts.exceptions import AppError


class TestResponse:
    """测试统一响应封装 Response"""

    def test_success_response_structure(self):
        """测试成功响应的标准结构"""
        data = {"id": 1, "name": "test"}
        resp = Response.success(data)

        assert isinstance(resp, JSONResponse)
        assert resp.status_code == 200

        content = json.loads(resp.body)
        assert content["success"] is True
        assert content["data"] == data
        # code 与 status_code 相同 (200) 时不返回 code
        assert "code" not in content

    def test_success_response_with_message(self):
        """测试带消息的成功响应"""
        resp = Response.success(None, message="Operation successful")
        content = json.loads(resp.body)
        assert content["message"] == "Operation successful"

    def test_success_response_with_business_code(self):
        """测试自定义业务码的成功响应"""
        # 201 Created
        resp = Response.success({"id": 1}, business_code=201)
        assert resp.status_code == 201
        content = json.loads(resp.body)
        assert "code" not in content  # 201 == 201, omit

    def test_pydantic_serialization(self):
        """测试 Pydantic 模型的序列化"""

        class User(BaseModel):
            id: int
            username: str

        user = User(id=1, username="user1")
        resp = Response.success(user)
        content = json.loads(resp.body)
        assert content["data"] == {"id": 1, "username": "user1"}

    def test_error_response_from_exception(self):
        """测试从异常构建错误响应"""
        exc = ValueError("Invalid value")
        resp = Response.error(exc, default_status_code=400)

        assert resp.status_code == 400
        content = json.loads(resp.body)
        assert content["success"] is False
        assert content["message"] == "Invalid value"
        assert content["data"]["error_type"] == "ValueError"

    def test_error_response_from_http_response(self):
        """测试从 HttpResponse 对象构建错误响应"""
        error_obj = HttpResponse(code=403, message="Forbidden access", data={"reason": "no_token"})
        resp = Response.error(error_obj)

        assert resp.status_code == 403
        content = json.loads(resp.body)
        assert content["message"] == "Forbidden access"
        assert content["data"]["reason"] == "no_token"


class TestGlobalExceptionHandler:
    """测试全局异常处理器"""

    def test_project_root_resolution(self):
        """测试项目根目录解析"""
        root = GlobalExceptionHandler._project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_format_exception_info(self):
        """测试异常信息格式化"""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            info = GlobalExceptionHandler.format_exception_info(e)

            assert info["error_type"] == "ValueError"
            assert info["error_message"] == "Test error"
            # 应该能捕获到当前文件名
            assert "test_web.py" in info["file_location"] or "test_web" in info["file_location"]

    def test_app_error_integration(self):
        """测试 AppError 集成"""
        # 创建一个最小的 FastAPI 应用来测试异常处理器的集成
        app = FastAPI()

        # 注册异常处理器
        # 注意: 实际使用中通常在 add_exception_handler 中调用 GlobalExceptionHandler 的方法
        # 这里我们模拟一个 handler
        @app.exception_handler(AppError)
        async def app_error_handler(request: Request, exc: AppError):
            return Response.error(
                HttpResponse(code=exc.code, message=exc.message, data=exc.details),
                default_status_code=exc.code
            )

        @app.get("/error")
        def trigger_error():
            raise AppError(code=418, message="I'm a teapot", details={"type": "teapot"})

        client = TestClient(app)
        response = client.get("/error")

        assert response.status_code == 418
        content = response.json()
        # code被省略了，因为与 HTTP status_code 一致
        assert "code" not in content
        assert content["message"] == "I'm a teapot"
        assert content["data"]["type"] == "teapot"

    def test_traceback_summary(self):
        """测试调用栈摘要生成"""

        def inner_func():
            raise RuntimeError("Deep error")

        def outer_func():
            inner_func()

        try:
            outer_func()
        except RuntimeError as e:
            info = GlobalExceptionHandler.format_exception_info(e)
            assert info["full_traceback"] is not None
            # trace stack info might be empty if we are not in src/ context rigorously, 
            # but basic fields should be there
            assert info["function_name"] == "inner_func"
