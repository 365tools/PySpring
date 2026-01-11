"""
启用 AuthenticationMiddleware 的完整示例

演示如何在 FastAPI 应用中启用全局认证中间件
"""
from fastapi import FastAPI
from pyspring.security.authentication.middleware.auth import AuthenticationMiddleware


# ==================== 方式1: 创建应用时直接添加（推荐） ====================

def create_app_with_auth():
    """创建带认证的 FastAPI 应用（推荐方式）"""
    app = FastAPI(
        title="My API",
        version="1.0.0"
    )

    # 添加认证中间件
    app.add_middleware(
        AuthenticationMiddleware,
        enable_role_check=True  # 是否启用角色验证（可选，默认从配置读取）
    )

    # 注册路由
    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    @app.get("/api/profile")
    async def get_profile():
        from pyspring.security.authentication.context import AuthContext
        user = AuthContext.get_current_user()
        return {"email": user.user.email if user else None}

    return app


# ==================== 方式2: 从配置文件读取设置 ====================

def create_app_from_config():
    """从配置文件读取设置"""
    app = FastAPI()

    # 不传参数，自动从 config/security.yaml 读取配置
    app.add_middleware(AuthenticationMiddleware)

    return app


# ==================== 方式3: 在 lifespan 中初始化（复杂场景，推荐） ====================

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("🚀 应用启动...")

    # 1. 初始化 IoC 容器
    from pyspring.ioc.manager import AppContainerManager
    ioc_manager = AppContainerManager()
    ioc_manager.register_all_services()

    # 2. 运行启动初始化器（会自动初始化认证系统）
    await ioc_manager.run_startup_initializers()

    yield

    # 关闭时清理
    print("👋 应用关闭...")


def create_app_with_lifespan():
    """带生命周期管理的应用（推荐用于生产环境）"""
    app = FastAPI(lifespan=lifespan)

    # 添加认证中间件
    app.add_middleware(AuthenticationMiddleware)

    return app


# ==================== 方式4: 完整的生产环境配置 ====================

def create_production_app():
    """生产环境完整配置"""
    app = FastAPI(
        title="Production API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )

    # 1. CORS 中间件（如果需要）
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. 认证中间件（必须在 CORS 之后）
    app.add_middleware(
        AuthenticationMiddleware,
        enable_role_check=True  # 生产环境启用角色验证
    )

    # 3. 其他中间件...

    return app


# ==================== 方式5: 使用配置类管理 ====================

from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """应用配置"""
    enable_auth: bool = True
    enable_role_check: bool = True

    class Config:
        env_file = ".env"


def create_app_from_settings():
    """从配置类创建应用"""
    config = AppConfig()
    app = FastAPI()

    if config.enable_auth:
        app.add_middleware(
            AuthenticationMiddleware,
            enable_role_check=config.enable_role_check
        )

    return app


# ==================== 实际使用示例 ====================

# main.py
"""
from fastapi import FastAPI
from pyspring.security.authentication.middleware.auth import AuthenticationMiddleware

app = FastAPI()

# 启用认证中间件
app.add_middleware(AuthenticationMiddleware)

# 或者自定义配置
app.add_middleware(
    AuthenticationMiddleware,
    enable_role_check=True      # 启用角色验证
)

@app.get("/api/profile")
async def get_profile():
    from pyspring.security.authentication.context import AuthContext
    user = AuthContext.get_current_user()
    return {"email": user.user.email}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

# ==================== 配置文件示例 ====================

"""
config/security.yaml
-------------------
authentication:
  enabled: true
  
  # 白名单配置
  whitelist:
    paths:
      - path: "/health"
        method: "*"
      - path: "/api/auth/login"
        method: "POST"
      - path: "/api/auth/register"
        method: "POST"
      - path: "/docs"
        method: "*"
      - path: "/redoc"
        method: "*"
      - path: "/openapi.json"
        method: "*"
    
    # 前缀匹配
    prefixes:
      - "/public/"
      - "/static/"
  
  # 认证提供者配置
  providers:
    - name: "jwt"
      type: "JWTAuthProvider"
      enabled: true
      priority: 1
      config:
        token_sources: ["header", "cookie", "query"]
        token_prefix: "Bearer"

authorization:
  enabled: true
  
  # 角色权限配置
  roles:
    admin:
      permissions:
        - "user:read"
        - "user:write"
        - "system:admin"
    user:
      permissions:
        - "user:read"
"""

# ==================== .env 文件示例 ====================

"""
.env
----
# 认证配置
AUTH_ENABLED=true
ENABLE_ROLE_CHECK=true

# JWT 配置
AUTH_SECRET_KEY=your-secret-key-here
AUTH_ALGORITHM=HS256
AUTH_ACCESS_TOKEN_EXPIRE=3600
AUTH_REFRESH_TOKEN_EXPIRE=2592000
"""

# ==================== 运行示例 ====================

if __name__ == "__main__":
    import uvicorn

    # 选择一种方式创建应用
    app = create_app_with_auth()
    # app = create_app_from_config()
    # app = create_app_with_lifespan()
    # app = create_production_app()
    # app = create_app_from_settings()

    # 运行应用
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发环境启用热重载
    )

__all__ = [
    'create_app_with_auth',
    'create_app_from_config',
    'create_app_with_lifespan',
    'create_production_app',
    'create_app_from_settings'
]
