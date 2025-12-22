from typing import Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse

from pyspring.http.response import Response, HttpResponse
from pyspring.ioc.manager import AppContainerManager
from pyspring.log.loguru.ins import logger
from pyspring.security.auth.impl.device import DeviceAuthService


class DeviceCheckMiddleware:
    """
    设备认证
    """

    def __init__(self, enable_device_check: bool = True):
        self.enable_device_check = enable_device_check

        # 需要设备验证的路径前缀
        self.DEVICE_VERIFICATION_REQUIRED = [
            "/api/chat/",
            "/api/config/",
            # 根据需要添加更多需要设备验证的路径
        ]

    async def auth(self, path: str, request: Request, payload: dict) -> JSONResponse | bool:
        """
        设备认证
        """
        if not self.enable_device_check:
            return False

        if self.requires_device_verification(path):
            device_fingerprint = self.extract_device_fingerprint(request)
            token_fingerprint = payload.get("device_fingerprint")

            if not device_fingerprint:
                logger.warning(f"⚠️ 缺少设备指纹: {request.method} {path}")
                return Response.error(
                    HttpResponse(
                        code=status.HTTP_403_FORBIDDEN,
                        message="此操作需要设备验证",
                        data="请在请求Header中包含device-fingerprint")
                )

            if not token_fingerprint:
                logger.warning(f"⚠️ Token中缺少设备指纹: {request.method} {path}")
                return Response.error(
                    HttpResponse(
                        code=status.HTTP_403_FORBIDDEN,
                        message="Token中缺少设备信息",
                        data="请重新登录以绑定设备")
                )

            # 验证设备
            device_result = await self.verify_device(
                request.state.user_id,
                device_fingerprint,
                token_fingerprint
            )

            if not device_result["success"]:
                logger.warning(f"⚠️ 设备验证失败: {device_result['error']}")
                return Response.error(
                    HttpResponse(
                        code=device_result["status_code"],
                        message=device_result["error"],
                        data="设备未通过验证")
                )

            request.state.device_fingerprint = device_fingerprint
        return True

    def requires_device_verification(self, path: str) -> bool:
        """
        判断路径是否需要设备验证

        Args:
            path: 请求路径

        Returns:
            是否需要设备验证
        """

        for prefix in self.DEVICE_VERIFICATION_REQUIRED:
            if path.startswith(prefix):
                return True

        return False

    @staticmethod
    def extract_device_fingerprint(request: Request) -> Optional[str]:
        """
        从请求中提取设备指纹

        Args:
            request: 请求对象

        Returns:
            设备指纹, 如果不存在返回None
        """
        return request.headers.get("device-fingerprint") or request.headers.get("Device-Fingerprint")

    @staticmethod
    async def verify_device(user_id: int, device_fingerprint: str, token_fingerprint: str) -> dict:
        """
        验证设备指纹

        Args:
            user_id: 用户ID
            device_fingerprint: 请求Header中的设备指纹
            token_fingerprint: Token中的设备指纹

        Returns:
            验证结果
        """
        try:
            # 检查设备指纹是否匹配
            if device_fingerprint != token_fingerprint:
                return {
                    "success": False,
                    "error": "设备指纹不匹配",
                    "status_code": status.HTTP_403_FORBIDDEN
                }

            # 验证设备权限
            device_service: DeviceAuthService = AppContainerManager.service(DeviceAuthService)
            device_verification = await device_service.verify_device(user_id, device_fingerprint)

            if device_verification["status"] == "pending":
                return {
                    "success": False,
                    "error": "设备待审批，暂无访问权限",
                    "status_code": status.HTTP_403_FORBIDDEN
                }

            if device_verification["status"] == "expired":
                return {
                    "success": False,
                    "error": "设备权限已过期",
                    "status_code": status.HTTP_403_FORBIDDEN
                }

            if not device_verification["is_authorized"]:
                return {
                    "success": False,
                    "error": "设备未授权",
                    "status_code": status.HTTP_403_FORBIDDEN
                }

            return {"success": True}

        except Exception as e:
            logger.error(f"🚨 设备验证失败: {e}")
            return {
                "success": False,
                "error": "设备验证失败",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
