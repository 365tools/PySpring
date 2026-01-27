"""
PySpring Token认证依赖示例

演示如何使用框架提供的Token认证依赖函数
"""
from typing import Annotated, Any, Optional

from fastapi import FastAPI, APIRouter, Depends, HTTPException, status

from pyspring.security.authentication.web.middleware.dependencies import (
    # Token验证模式
    get_current_user_from_token,
    require_authentication_from_token,
    # 工厂函数
    token_auth_dependency
)

app = FastAPI(title="PySpring Token认证示例")
router = APIRouter(prefix="/api", tags=["示例"])

# ============================================================================
# 类型别名定义（推荐做法）
# ============================================================================

# 强制认证用户
AuthenticatedUser = Annotated[Any, Depends(require_authentication_from_token)]

# 可选认证用户
OptionalUser = Annotated[Optional[Any], Depends(get_current_user_from_token)]

# 使用工厂函数创建
RequiredUser = Annotated[Any, Depends(token_auth_dependency(auto_error=True))]


# ============================================================================
# 路由示例
# ============================================================================

@router.get("/public")
async def public_endpoint():
    """
    公开端点 - 无需认证
    
    测试:
        curl http://localhost:8000/api/public
    """
    return {
        "message": "这是公开内容，任何人都可以访问",
        "data": "公开数据"
    }


@router.get("/optional-auth")
async def optional_auth_endpoint(user: OptionalUser):
    """
    可选认证端点 - 根据是否认证返回不同内容
    
    测试:
        # 无Token
        curl http://localhost:8000/api/optional-auth
        
        # 有Token
        curl -H "Authorization: Bearer YOUR_TOKEN" \
             http://localhost:8000/api/optional-auth
    """
    if user:
        return {
            "authenticated": True,
            "message": f"欢迎回来！",
            "user": {
                "id": getattr(user, 'id', None),
                "username": getattr(user, 'username', None),
                "email": getattr(user, 'email', None)
            },
            "premium_content": "这是付费内容..."
        }
    else:
        return {
            "authenticated": False,
            "message": "游客访问",
            "limited_content": "这是免费内容..."
        }


@router.get("/protected")
async def protected_endpoint(user: AuthenticatedUser):
    """
    受保护端点 - 强制认证
    
    测试:
        # 无Token - 返回401
        curl http://localhost:8000/api/protected
        
        # 有Token - 返回用户数据
        curl -H "Authorization: Bearer YOUR_TOKEN" \
             http://localhost:8000/api/protected
    """
    return {
        "message": "这是受保护的内容",
        "user": {
            "id": getattr(user, 'id', None),
            "username": getattr(user, 'username', None),
            "email": getattr(user, 'email', None)
        },
        "sensitive_data": "敏感信息..."
    }


@router.get("/profile")
async def get_profile(user: AuthenticatedUser):
    """
    获取用户资料 - 必须认证
    
    测试:
        curl -H "Authorization: Bearer YOUR_TOKEN" \
             http://localhost:8000/api/profile
    """
    return {
        "profile": {
            "id": getattr(user, 'id', None),
            "username": getattr(user, 'username', None),
            "email": getattr(user, 'email', None),
            "active": getattr(user, 'active', True),
            "roles": getattr(user, 'roles', [])
        }
    }


@router.post("/update-profile")
async def update_profile(
        user: AuthenticatedUser,
        username: Optional[str] = None,
        email: Optional[str] = None
):
    """
    更新用户资料 - 必须认证
    
    测试:
        curl -X POST \
             -H "Authorization: Bearer YOUR_TOKEN" \
             -H "Content-Type: application/json" \
             -d '{"username": "newname", "email": "new@example.com"}' \
             http://localhost:8000/api/update-profile
    """
    return {
        "message": "资料更新成功",
        "updated_by": getattr(user, 'id', None),
        "updates": {
            "username": username,
            "email": email
        }
    }


@router.get("/admin/dashboard")
async def admin_dashboard(user: AuthenticatedUser):
    """
    管理员仪表板 - 需要认证+管理员角色
    
    测试:
        curl -H "Authorization: Bearer ADMIN_TOKEN" \
             http://localhost:8000/api/admin/dashboard
    """
    # 检查管理员权限
    roles = getattr(user, 'roles', [])
    if 'admin' not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限才能访问"
        )

    return {
        "message": "管理员仪表板",
        "admin": getattr(user, 'username', None),
        "stats": {
            "total_users": 100,
            "active_users": 85,
            "revenue": 12345.67
        }
    }


@router.get("/user-info")
async def get_user_info(user: RequiredUser):
    """
    使用工厂函数创建的依赖
    
    测试:
        curl -H "Authorization: Bearer YOUR_TOKEN" \
             http://localhost:8000/api/user-info
    """
    return {
        "created_with": "token_auth_dependency(auto_error=True)",
        "user": user
    }


# ============================================================================
# 高级示例：组合依赖
# ============================================================================

async def get_premium_user(user: AuthenticatedUser) -> Any:
    """
    获取Premium用户 - 组合依赖示例
    
    先验证用户认证，再检查是否为Premium用户
    """
    subscription = getattr(user, 'subscription', 'free')
    if subscription != 'premium':
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="此功能需要Premium订阅"
        )
    return user


PremiumUser = Annotated[Any, Depends(get_premium_user)]


@router.get("/premium-feature")
async def premium_feature(user: PremiumUser):
    """
    Premium功能 - 需要Premium订阅
    
    测试:
        curl -H "Authorization: Bearer PREMIUM_USER_TOKEN" \
             http://localhost:8000/api/premium-feature
    """
    return {
        "message": "欢迎使用Premium功能",
        "user": getattr(user, 'username', None),
        "subscription": getattr(user, 'subscription', None),
        "premium_data": "特殊数据..."
    }


# ============================================================================
# 错误处理示例
# ============================================================================

@router.get("/custom-error-handling")
async def custom_error_handling(user: OptionalUser):
    """
    自定义错误处理示例
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_REQUIRED",
                "message": "请先登录以访问此功能",
                "login_url": "/api/auth/login"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not getattr(user, 'email_verified', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "请先验证您的邮箱",
                "verification_url": "/api/auth/verify-email"
            }
        )

    return {
        "message": "访问成功",
        "user": user
    }


# ============================================================================
# 应用配置
# ============================================================================

app.include_router(router)


@app.get("/")
async def root():
    """
    根路径 - API文档入口
    """
    return {
        "message": "PySpring Token认证示例API",
        "documentation": "/docs",
        "endpoints": {
            "public": "/api/public",
            "optional_auth": "/api/optional-auth",
            "protected": "/api/protected",
            "profile": "/api/profile",
            "admin": "/api/admin/dashboard",
            "premium": "/api/premium-feature"
        },
        "auth": {
            "method": "Bearer Token",
            "header": "Authorization: Bearer YOUR_TOKEN"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# ============================================================================
# 运行说明
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         PySpring Token认证依赖示例                           ║
    ╚══════════════════════════════════════════════════════════════╝
    
    启动服务器:
        python example_token_auth_dependencies.py
        
    或使用uvicorn:
        uvicorn example_token_auth_dependencies:app --reload
    
    访问API文档:
        http://localhost:8000/docs
    
    测试端点:
        1. 公开端点（无需Token）:
           curl http://localhost:8000/api/public
        
        2. 可选认证（无Token）:
           curl http://localhost:8000/api/optional-auth
        
        3. 可选认证（有Token）:
           curl -H "Authorization: Bearer YOUR_TOKEN" \\
                http://localhost:8000/api/optional-auth
        
        4. 受保护端点（必须有Token）:
           curl -H "Authorization: Bearer YOUR_TOKEN" \\
                http://localhost:8000/api/protected
    
    注意事项:
        - 此示例需要配置ITokenService和IUserManagerService
        - 框架会自动从IoC容器获取这些服务
        - 如果未配置，Token验证会返回None而不是抛出异常
    
    ╔══════════════════════════════════════════════════════════════╗
    ║  按 Ctrl+C 停止服务器                                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
