"""
认证相关常量定义
"""


class RevokeTokenReason:
    """撤销令牌原因"""
    # 用户重新登录
    USER_LOGIN = "用户重新登录"
    # 用户登出
    USER_LOGOUT = "用户登出"
    # 管理员操作
    ADMIN_REVOKE = "管理员撤销"


__all__ = ["RevokeTokenReason"]
