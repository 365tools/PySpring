"""
PySpring 认证 + 授权完整集成示例

演示如何将Token认证与权限/角色授权深度集成

功能演示：
1. Token认证（ITokenService）
2. 权限验证（IPermissionService.has_permission）
3. 角色验证（IPermissionService.has_role）
4. 组合使用（先认证，再授权）

运行方式：
    python examples/example_auth_authorization_integration.py
    
测试：
    # 1. 注册用户（自动分配guest角色）
    curl -X POST http://localhost:8000/auth/register \
        -H "Content-Type: application/json" \
        -d '{"username":"testuser","email":"test@test.com","password":"test123"}'
    
    # 注意：角色不能在注册时指定，默认分配 'guest' 角色
    # 其他角色（如admin、manager）需要通过管理后台授予
    
    # 2. 登录获取Token
    curl -X POST http://localhost:8000/auth/login \\
        -H "Content-Type: application/json" \\
        -d '{"identifier":"test@test.com","password":"test123"}'
    
    # identifier 可以是: username/email/phone/user_id
    # 框架会根据 config/security.yaml 中的 identifier_fields 配置自动匹配
    
    # 3. 访问需要权限的路由
    curl http://localhost:8000/api/users \\
        -H "Authorization: Bearer YOUR_TOKEN"
    
    # 4. 访问需要管理员的路由
    curl http://localhost:8000/api/admin/dashboard \\
        -H "Authorization: Bearer YOUR_TOKEN"
"""

from typing import Annotated, Any

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

# ============================================================================
# 导入PySpring依赖
# ============================================================================
from pyspring.security.authentication.web.middleware.dependencies import (
    # Token认证
    require_authentication_from_token,
    get_current_user_from_token,

    # 权限/角色依赖
    permission_dependency,
    role_dependency,
)

# ============================================================================
# 类型别名定义
# ============================================================================

# 认证类型
AuthenticatedUser = Annotated[Any, Depends(require_authentication_from_token)]
OptionalUser = Annotated[Any, Depends(get_current_user_from_token)]

# 权限类型
UserReadPermission = Annotated[Any, Depends(permission_dependency("user:read"))]
UserWritePermission = Annotated[Any, Depends(permission_dependency("user:write"))]
UserDeletePermission = Annotated[Any, Depends(permission_dependency("user:delete"))]

OrderReadPermission = Annotated[Any, Depends(permission_dependency("order:read"))]
OrderWritePermission = Annotated[Any, Depends(permission_dependency("order:write"))]
OrderDeletePermission = Annotated[Any, Depends(permission_dependency("order:delete"))]

# 角色类型
AdminOnly = Annotated[Any, Depends(role_dependency("admin"))]
ManagerOnly = Annotated[Any, Depends(role_dependency("manager"))]
UserOnly = Annotated[Any, Depends(role_dependency("user"))]


# ============================================================================
# 请求/响应模型
# ============================================================================

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    # 注意：角色不能在注册时指定，防止权限提升攻击
    # 新用户默认分配 'guest' 角色
    # 其他角色（如admin、manager）需要通过管理后台授予


class LoginRequest(BaseModel):
    identifier: str  # 可以是 username/email/phone/user_id，由 YAML 配置决定
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    roles: list[str]


# ============================================================================
# FastAPI应用
# ============================================================================

app = FastAPI(
    title="PySpring 认证授权集成示例",
    description="演示Token认证与权限/角色授权的深度集成",
    version="1.0.0"
)


# ============================================================================
# 1. 公开路由（无需认证）
# ============================================================================

@app.get("/")
async def root():
    """首页 - 公开访问"""
    return {
        "message": "PySpring 认证授权集成示例",
        "endpoints": {
            "register": "POST /auth/register",
            "login": "POST /auth/login",
            "profile": "GET /api/profile (需要认证)",
            "users": "GET /api/users (需要 user:read 权限)",
            "create_user": "POST /api/users (需要 user:write 权限)",
            "delete_user": "DELETE /api/users/{id} (需要 user:delete 权限)",
            "admin_dashboard": "GET /api/admin/dashboard (需要 admin 角色)",
            "manager_approve": "POST /api/manager/approve (需要 manager 角色)",
        }
    }


@app.get("/public/info")
async def public_info():
    """公开信息 - 无需认证"""
    return {"message": "这是公开信息，任何人都可以访问"}


# ============================================================================
# 2. 认证路由（仅需Token认证，无权限要求）
# ============================================================================

@app.get("/api/profile")
async def get_profile(user: AuthenticatedUser):
    """
    获取用户资料
    
    要求：Token认证
    """
    return {
        "message": "用户资料",
        "user_id": getattr(user, 'id', None) or getattr(user, 'user_id', None),
        "username": getattr(user, 'username', 'Unknown'),
        "email": getattr(user, 'email', 'Unknown'),
    }


@app.get("/api/optional")
async def optional_route(user: OptionalUser):
    """
    可选认证路由
    
    要求：可选Token认证
    """
    if user:
        return {
            "message": "已登录用户",
            "user_id": getattr(user, 'id', None) or getattr(user, 'user_id', None)
        }
    else:
        return {"message": "未登录游客"}


# ============================================================================
# 3. 权限路由（需要特定权限）
# ============================================================================

@app.get("/api/users")
async def list_users(user: UserReadPermission):
    """
    获取用户列表
    
    要求：user:read 权限
    """
    user_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)
    return {
        "message": "用户列表",
        "requested_by": user_id,
        "required_permission": "user:read",
        "users": [
            {"id": 1, "username": "alice"},
            {"id": 2, "username": "bob"},
        ]
    }


@app.post("/api/users")
async def create_user(user: UserWritePermission):
    """
    创建用户
    
    要求：user:write 权限
    """
    user_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)
    return {
        "message": "用户创建成功",
        "created_by": user_id,
        "required_permission": "user:write",
        "new_user": {"id": 3, "username": "charlie"}
    }


@app.delete("/api/users/{user_id_to_delete}")
async def delete_user(user_id_to_delete: int, user: UserDeletePermission):
    """
    删除用户
    
    要求：user:delete 权限
    """
    operator_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)
    return {
        "message": "用户删除成功",
        "deleted_by": operator_id,
        "required_permission": "user:delete",
        "deleted_user_id": user_id_to_delete
    }


# ============================================================================
# 4. 订单相关权限路由
# ============================================================================

@app.get("/api/orders")
async def list_orders(user: OrderReadPermission):
    """
    获取订单列表
    
    要求：order:read 权限
    """
    user_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)
    return {
        "message": "订单列表",
        "requested_by": user_id,
        "required_permission": "order:read",
        "orders": [
            {"id": 1, "amount": 100},
            {"id": 2, "amount": 200},
        ]
    }


@app.post("/api/orders")
async def create_order(user: OrderWritePermission):
    """
    创建订单
    
    要求：order:write 权限
    """
    user_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)
    return {
        "message": "订单创建成功",
        "created_by": user_id,
        "required_permission": "order:write",
        "new_order": {"id": 3, "amount": 300}
    }


@app.delete("/api/orders/{order_id}")
async def delete_order(order_id: int, user: OrderDeletePermission):
    """
    删除订单
    
    要求：order:delete 权限
    """
    operator_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)
    return {
        "message": "订单删除成功",
        "deleted_by": operator_id,
        "required_permission": "order:delete",
        "deleted_order_id": order_id
    }


# ============================================================================
# 5. 角色路由（需要特定角色）
# ============================================================================

@app.get("/api/admin/dashboard")
async def admin_dashboard(user: AdminOnly):
    """
    管理员仪表板
    
    要求：admin 角色
    """
    user_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)
    return {
        "message": "管理员仪表板",
        "admin_id": user_id,
        "required_role": "admin",
        "stats": {
            "total_users": 100,
            "total_orders": 500,
            "total_revenue": 10000
        }
    }


@app.post("/api/admin/users/{user_id}/ban")
async def ban_user(user_id: int, user: AdminOnly):
    """
    封禁用户
    
    要求：admin 角色
    """
    admin_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)
    return {
        "message": "用户封禁成功",
        "admin_id": admin_id,
        "required_role": "admin",
        "banned_user_id": user_id
    }


@app.post("/api/manager/approve")
async def manager_approve(user: ManagerOnly):
    """
    经理审批
    
    要求：manager 角色
    """
    manager_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)
    return {
        "message": "审批成功",
        "manager_id": manager_id,
        "required_role": "manager",
        "approved": True
    }


@app.get("/api/manager/reports")
async def manager_reports(user: ManagerOnly):
    """
    经理报告
    
    要求：manager 角色
    """
    manager_id = getattr(user, 'id', None) or getattr(user, 'user_id', None)
    return {
        "message": "报告列表",
        "manager_id": manager_id,
        "required_role": "manager",
        "reports": [
            {"id": 1, "title": "销售报告"},
            {"id": 2, "title": "库存报告"},
        ]
    }


# ============================================================================
# 6. 健康检查
# ============================================================================

@app.get("/health")
async def health_check():
    """健康检查"""
    from pyspring.ioc.context import ApplicationContext
    from pyspring.security.authentication.contracts.token import ITokenService
    from pyspring.security.authorization.contracts.permission import IPermissionService

    try:
        ctx = ApplicationContext.get_instance()
        token_service = ctx.get_by_type(ITokenService)
        permission_service = ctx.get_by_type(IPermissionService)

        return {
            "status": "healthy",
            "services": {
                "token_service": "available" if token_service else "unavailable",
                "permission_service": "available" if permission_service else "unavailable"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")


# ============================================================================
# 启动说明
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 80)
    print("PySpring 认证授权集成示例")
    print("=" * 80)
    print("\n架构说明：")
    print("  - Token认证: ITokenService（自动从IoC容器获取）")
    print("  - 用户管理: IUserManagerService（自动从IoC容器获取）")
    print("  - 权限服务: IPermissionService（自动从IoC容器获取）")
    print("\n使用的依赖函数：")
    print("  1. require_authentication_from_token - 强制Token认证")
    print("  2. get_current_user_from_token - 可选Token认证")
    print("  3. permission_dependency(permission) - 权限检查")
    print("  4. role_dependency(role) - 角色检查")
    print("\n路由分类：")
    print("  - 公开路由: /, /public/*")
    print("  - 认证路由: /api/profile, /api/optional")
    print("  - 权限路由: /api/users, /api/orders (需要特定权限)")
    print("  - 角色路由: /api/admin/*, /api/manager/* (需要特定角色)")
    print("\n测试流程：")
    print("  1. 启动应用（确保数据库已初始化）")
    print("  2. 注册新用户（自动分配guest角色）")
    print("  3. 登录获取Token")
    print("  4. 使用Token访问受保护路由")
    print("  5. 验证权限和角色检查")
    print("\n安全说明：")
    print("  - 注册时不能指定角色，防止权限提升攻击")
    print("  - 新用户默认分配 'guest' 角色")
    print("  - 其他角色（如admin、manager）需要通过管理后台授予")
    print("\n启动服务器...")
    print("=" * 80 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
