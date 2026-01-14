"""
认证上下文使用示例

演示如何使用类似 Spring Boot 的方式获取当前用户信息
"""
from fastapi import APIRouter, Depends
from pyspring.ioc.manager import AppContainerManager
from pyspring.security.authentication.core.context import AuthContext
from pyspring.security.authentication.services.user.manager import UserManagerService

router = APIRouter()


# ==================== 方式1: 直接从上下文获取（最简单） ====================

@router.get("/api/profile")
async def get_profile():
    """
    获取当前用户信息 - 方式1: 直接从上下文获取
    
    类似 Spring Boot:
    UserDetails user = SecurityContextHolder.getContext().getAuthentication().getPrincipal()
    """
    # 直接从上下文获取，无需传递任何参数！
    user = AuthContext.get_current_user()

    if not user:
        return {"error": "未登录"}

    return {
        "user_id": user.user.user_id,
        "email": user.user.email,
        "name": f"{user.user.first_name} {user.user.last_name}",
        "roles": [role.name for role in user.roles] if user.roles else []
    }


@router.get("/api/my-orders")
async def get_my_orders():
    """获取当前用户的订单"""
    user = AuthContext.get_current_user()

    if not user:
        return {"error": "未登录"}

    # 使用用户信息查询订单
    user_id = user.user.id

    # TODO: 查询订单逻辑
    return {
        "user_id": user_id,
        "orders": []
    }


# ==================== 方式2: 通过 UserManagerService 获取 ====================

@router.get("/api/user/info")
async def get_user_info():
    """
    获取当前用户信息 - 方式2: 通过 UserManagerService
    
    适合需要完整用户服务功能的场景
    """
    container = AppContainerManager()
    user_manager = container.get(UserManagerService)

    # 不传 token 参数，自动从上下文获取
    user = await user_manager.get_current_user()

    return {
        "user": user.user.model_dump(),
        "roles": [role.model_dump() for role in user.roles] if user.roles else []
    }


# ==================== 方式3: 使用 FastAPI 依赖注入 ====================

async def get_current_user_dependency():
    """
    FastAPI 依赖注入函数
    
    可以在路由参数中使用 Depends(get_current_user_dependency)
    """
    user = AuthContext.get_current_user()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证"
        )
    return user


@router.get("/api/protected")
async def protected_route(user=Depends(get_current_user_dependency)):
    """
    受保护的路由 - 使用依赖注入
    
    类似 Spring Boot:
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<?> protectedEndpoint(@AuthenticationPrincipal UserDetails user)
    """
    return {
        "message": "这是受保护的路由",
        "user": user.user.email
    }


# ==================== 方式4: 在业务服务中使用 ====================

class OrderService:
    """订单服务示例"""

    async def create_order(self, product_id: int):
        """创建订单"""
        # 在业务逻辑中直接获取当前用户
        user = AuthContext.get_current_user()

        if not user:
            raise Exception("用户未登录")

        user_id = user.user.id

        # TODO: 创建订单逻辑
        return {
            "order_id": "ORD123",
            "user_id": user_id,
            "product_id": product_id
        }

    async def get_user_orders(self):
        """获取当前用户的所有订单"""
        user = AuthContext.get_current_user()

        if not user:
            return []

        user_id = user.user.id

        # TODO: 查询订单逻辑
        return []


# ==================== 方式5: 检查认证状态 ====================

@router.get("/api/status")
async def check_auth_status():
    """检查认证状态"""
    is_authenticated = AuthContext.is_authenticated()

    if is_authenticated:
        user = AuthContext.get_current_user()
        return {
            "authenticated": True,
            "user": user.user.email
        }
    else:
        return {
            "authenticated": False
        }


# ==================== Spring Boot 对比 ====================

"""
Spring Boot 方式:
-----------------
@RestController
public class UserController {
    
    @GetMapping("/api/profile")
    public ResponseEntity<?> getProfile() {
        // 获取当前用户
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UserDetails user = (UserDetails) auth.getPrincipal();
        
        return ResponseEntity.ok(user);
    }
    
    @GetMapping("/api/orders")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<?> getOrders(@AuthenticationPrincipal UserDetails user) {
        // 使用依赖注入获取用户
        return orderService.getUserOrders(user.getId());
    }
}

PySpring 方式（本示例）:
-----------------------
@router.get("/api/profile")
async def get_profile():
    # 获取当前用户
    user = AuthContext.get_current_user()
    
    return {"user": user.user.email}

@router.get("/api/orders")
async def get_orders(user = Depends(get_current_user_dependency)):
    # 使用依赖注入获取用户
    return await order_service.get_user_orders(user.user.id)

两者用法几乎完全一致！
"""

__all__ = ['router', 'get_current_user_dependency']
