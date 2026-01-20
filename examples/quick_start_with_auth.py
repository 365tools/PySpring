"""
完整的 FastAPI + PySpring 认证系统启动示例

这是一个可以直接运行的完整示例，展示如何正确启用认证中间件
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from pyspring.log.providers.loguru.middleware.request import RequestLoggingMiddleware


# ==================== 应用生命周期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    【重要】认证系统需要在这里初始化！
    """
    print("=" * 60)
    print("🚀 应用启动中...")
    print("=" * 60)

    try:
        # 1. 初始化 IoC 容器
        from pyspring.ioc.manager import AppContainerManager
        print("📦 正在注册服务...")
        ioc_manager = AppContainerManager()
        ioc_manager.register_all_services()
        print("✅ 服务注册完成")

        # 2. 运行启动初始化器（会自动初始化认证系统）
        print("🔧 正在运行启动初始化器...")
        await ioc_manager.run_startup_initializers()
        print("✅ 初始化器执行完成")

        print("=" * 60)
        print("✅ 应用启动成功！认证系统已就绪")
        print("=" * 60)

    except Exception as e:
        print("=" * 60)
        print(f"❌ 应用启动失败: {e}")
        print("=" * 60)
        raise

    yield

    # 关闭时清理
    print("=" * 60)
    print("👋 应用正在关闭...")
    print("=" * 60)


# ==================== 创建应用 ====================

def create_app() -> FastAPI:
    """
    创建 FastAPI 应用
    
    Returns:
        配置好的 FastAPI 应用实例
    """
    app = FastAPI(
        title="PySpring API",
        version="1.0.0",
        description="完整的认证系统示例",
        lifespan=lifespan  # 【重要】必须设置 lifespan
    )

    # 添加中间件（注意顺序）

    # 1. 请求日志中间件（最外层）
    app.add_middleware(RequestLoggingMiddleware)

    # 2. 认证中间件
    app.add_middleware(
        AuthenticationMiddleware,
        enable_role_check=True  # 可选：是否启用角色验证
    )

    # 3. CORS 中间件（如果需要）
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


# ==================== 路由示例 ====================

app = create_app()


@app.get("/")
async def root():
    """根路径"""
    return {"message": "Hello PySpring!"}


@app.get("/health")
async def health():
    """健康检查（白名单路径）"""
    return {"status": "ok"}


@app.get("/api/profile")
async def get_profile():
    """获取当前用户信息（需要认证）"""
    from pyspring.security.authentication.core.context import AuthContext

    user = AuthContext.get_current_user()

    if not user:
        return {"error": "未登录"}

    return {
        "user_id": user.user.user_id,
        "email": user.user.email,
        "name": f"{user.user.first_name} {user.user.last_name}",
        "roles": [role.name for role in user.roles] if user.roles else []
    }


@app.post("/api/auth/login")
async def login():
    """登录接口（白名单路径）"""
    # TODO: 实现登录逻辑
    return {"message": "登录接口"}


@app.get("/api/protected")
async def protected():
    """受保护的路由"""
    from pyspring.security.authentication.core.context import AuthContext

    user = AuthContext.get_current_user()
    return {
        "message": "这是受保护的路由",
        "user": user.user.email if user else None
    }


# ==================== 运行应用 ====================

if __name__ == "__main__":
    import uvicorn
from pyspring.security.authentication.web.middleware.auth import AuthenticationMiddleware

    print("\n" + "=" * 70)
    print("🎯 启动 PySpring 应用")
    print("=" * 60)
    print("📝 文档地址: http://localhost:8000/docs")
    print("🔐 认证系统: 已启用")
    print("=" * 60 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False  # 生产环境设为 False
    )

# ==================== 重要提示 ====================

"""
❗️ 为什么认证提供者是 0 个？

原因：
认证提供者需要在应用启动时通过 run_startup_initializers() 来初始化。

解决方案：
1. 必须在 FastAPI 的 lifespan 中调用 run_startup_initializers()
2. 确保 AuthenticationInitializer 被 IoC 容器扫描到

完整流程：
┌─────────────────────────────────────────────┐
│ 1. FastAPI 启动                              │
│    └─> lifespan() 执行                       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 2. 注册 IoC 服务                             │
│    └─> register_all_services()              │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 3. 运行启动初始化器                          │
│    └─> run_startup_initializers()           │
│        └─> AuthenticationInitializer        │
│            └─> 初始化认证提供者链            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 4. 认证中间件可以正常工作                    │
│    └─> 认证提供者数量 > 0                    │
└─────────────────────────────────────────────┘

配置文件：config/security.yaml
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
authentication:
  enabled: true
  
  whitelist:
    paths:
      - path: "/health"
        method: "*"
      - path: "/api/auth/login"
        method: "POST"
      - path: "/docs"
        method: "*"
  
  providers:
    - name: "jwt"
      type: "JWTAuthProvider"
      enabled: true
      priority: 1
      config:
        token_sources: ["header", "cookie", "query"]
        token_prefix: "Bearer"

如果配置文件不存在，系统会自动创建默认的 JWT 提供者。

检查认证提供者是否成功注册：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
启动日志应该显示：
🔐 正在初始化认证系统...
🚀 开始初始化认证系统...
✅ 认证系统初始化完成，共 X 个提供者
✅ 认证系统初始化完成
🔒 全局认证中间件已启动 (基于认证链)
   - 认证提供者: X 个  ← 这里应该 > 0
"""
