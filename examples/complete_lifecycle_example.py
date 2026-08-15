"""
PySpring 完整生命周期示例

展示从应用启动到关闭的完整流程，包括：
1. FastAPI 应用启动
2. IOC 容器初始化
3. 日志系统
4. 自定义启动初始化器
5. 自定义关闭处理器
6. FastAPI 中间件
7. 依赖注入使用
8. 应用优雅关闭
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# PySpring 导入
from pyspring.core.ioc import ApplicationContext
from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.ioc.interfaces.core import IManaged
from pyspring.core.ioc.lifecycle.initializer import IStartupInitializer
from pyspring.core.ioc.lifecycle.shutdown import IShutdownHandler
from pyspring.core.log.instance import logger


# ============================================================================
# 1. 定义业务服务
# ============================================================================

@Component
@Singleton
class UserService(IManaged):
    """用户服务示例"""

    def __init__(self):
        self.users = {}
        logger.info("👤 UserService 实例创建")

    async def get_user(self, user_id: int):
        """获取用户"""
        return self.users.get(user_id, {"id": user_id, "name": f"User{user_id}"})

    async def create_user(self, user_id: int, name: str):
        """创建用户"""
        self.users[user_id] = {"id": user_id, "name": name}
        logger.info(f"✅ 创建用户: {name}")
        return self.users[user_id]


@Component
@Singleton
class OrderService(IManaged):
    """订单服务示例 - 展示依赖注入"""

    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.orders = {}
        logger.info("📦 OrderService 实例创建（注入了 UserService）")

    async def create_order(self, user_id: int, product: str):
        """创建订单"""
        user = await self.user_service.get_user(user_id)
        order_id = len(self.orders) + 1
        order = {
            "id": order_id,
            "user": user,
            "product": product,
            "status": "pending"
        }
        self.orders[order_id] = order
        logger.info(f"✅ 创建订单: {order_id} for {user['name']}")
        return order


# ============================================================================
# 2. 定义启动初始化器
# ============================================================================

@Component
@Singleton
class DatabaseInitializer(IStartupInitializer):
    """数据库初始化器"""

    def __init__(self):
        super().__init__(enabled=True)

    def get_name(self) -> str:
        return "数据库初始化器"

    async def initialize(self) -> bool:
        """初始化数据库连接"""
        logger.info("🗄️  正在初始化数据库连接...")
        await asyncio.sleep(0.5)  # 模拟连接延迟
        logger.info("✅ 数据库连接初始化完成")
        return True


@Component
@Singleton
class CacheInitializer(IStartupInitializer):
    """缓存初始化器"""

    def __init__(self):
        super().__init__(enabled=True)

    def get_name(self) -> str:
        return "缓存初始化器"

    async def initialize(self) -> bool:
        """初始化缓存连接"""
        logger.info("💾 正在初始化缓存连接...")
        await asyncio.sleep(0.3)  # 模拟连接延迟
        logger.info("✅ 缓存连接初始化完成")
        return True


@Component
@Singleton
class DataPreloadInitializer(IStartupInitializer):
    """数据预加载初始化器"""

    def __init__(self, user_service: UserService):
        super().__init__(enabled=True)
        self.user_service = user_service

    def get_name(self) -> str:
        return "数据预加载初始化器"

    async def initialize(self) -> bool:
        """预加载基础数据"""
        logger.info("📚 正在预加载基础数据...")

        # 创建一些初始用户
        await self.user_service.create_user(1, "张三")
        await self.user_service.create_user(2, "李四")
        await self.user_service.create_user(3, "王五")

        logger.info("✅ 基础数据预加载完成")
        return True


# ============================================================================
# 3. 定义关闭处理器
# ============================================================================

@Component
@Singleton
class DatabaseShutdownHandler(IShutdownHandler):
    """数据库关闭处理器"""

    def get_name(self) -> str:
        return "数据库关闭处理器"

    async def shutdown(self) -> bool:
        """关闭数据库连接"""
        logger.info("🗄️  正在关闭数据库连接...")
        await asyncio.sleep(0.3)  # 模拟关闭延迟
        logger.info("✅ 数据库连接已关闭")
        return True


@Component
@Singleton
class CacheShutdownHandler(IShutdownHandler):
    """缓存关闭处理器"""

    def get_name(self) -> str:
        return "缓存关闭处理器"

    async def shutdown(self) -> bool:
        """关闭缓存连接"""
        logger.info("💾 正在关闭缓存连接...")
        await asyncio.sleep(0.2)  # 模拟关闭延迟
        logger.info("✅ 缓存连接已关闭")
        return True


@Component
@Singleton
class StateSaveHandler(IShutdownHandler):
    """状态保存处理器"""

    def __init__(self, user_service: UserService, order_service: OrderService):
        self.user_service = user_service
        self.order_service = order_service

    def get_name(self) -> str:
        return "状态保存处理器"

    async def shutdown(self) -> bool:
        """保存应用状态"""
        logger.info("💾 正在保存应用状态...")
        logger.info(f"  - 用户数量: {len(self.user_service.users)}")
        logger.info(f"  - 订单数量: {len(self.order_service.orders)}")
        await asyncio.sleep(0.1)
        logger.info("✅ 应用状态已保存")
        return True


# ============================================================================
# 4. FastAPI 中间件
# ============================================================================

async def request_logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    logger.info(f"📨 收到请求: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"📤 响应状态: {response.status_code}")
    return response


async def timing_middleware(request: Request, call_next):
    """请求计时中间件"""
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.3f}s"
    logger.debug(f"⏱️  请求耗时: {process_time:.3f}s")
    return response


# ============================================================================
# 5. FastAPI 应用生命周期管理
# ============================================================================

# 全局上下文引用
app_context: ApplicationContext = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global app_context

    # ========== 启动阶段 ==========
    logger.info("=" * 80)
    logger.info("🚀 PySpring 应用启动开始")
    logger.info("=" * 80)

    try:
        # 1. 初始化 ApplicationContext
        logger.info("📦 步骤 1: 初始化 IOC 容器...")
        app_context = ApplicationContext.initialize(
            base_packages=['__main__'],  # 扫描当前模块
            enable_aop=True
        )
        logger.info("✅ IOC 容器初始化完成")

        # 2. 初始化所有生命周期服务（包括 IStartupInitializer）
        logger.info("\n📦 步骤 2: 执行启动初始化器...")
        await app_context.container.initialize_lifecycle_services()
        logger.info("✅ 所有启动初始化器执行完成")

        # 3. 显示已注册的服务
        logger.info("\n📦 步骤 3: 已注册的服务:")
        all_services = app_context.container.registry.all_names()
        for service_name in sorted(all_services):
            logger.info(f"  - {service_name}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ PySpring 应用启动完成，准备接受请求")
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}", exc_info=True)
        raise

    yield  # 应用运行期间

    # ========== 关闭阶段 ==========
    logger.info("\n" + "=" * 80)
    logger.info("👋 PySpring 应用关闭开始")
    logger.info("=" * 80)

    try:
        # 执行所有关闭处理器（包括 IShutdownHandler）
        logger.info("📦 执行关闭处理器...")
        await app_context.container.shutdown_lifecycle_services()
        logger.info("✅ 所有关闭处理器执行完成")

    except Exception as e:
        logger.error(f"❌ 应用关闭时发生错误: {e}", exc_info=True)

    logger.info("=" * 80)
    logger.info("✅ PySpring 应用已完全关闭")
    logger.info("=" * 80 + "\n")


# ============================================================================
# 6. 创建 FastAPI 应用
# ============================================================================

app = FastAPI(
    title="PySpring 完整生命周期示例",
    description="展示 PySpring 从启动到关闭的完整流程",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加自定义中间件
app.middleware("http")(request_logging_middleware)
app.middleware("http")(timing_middleware)


# ============================================================================
# 7. 异常处理器
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"❌ 未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": request.url.path
        }
    )


# ============================================================================
# 8. API 路由 - 展示依赖注入
# ============================================================================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "PySpring 完整生命周期示例",
        "status": "运行中",
        "endpoints": [
            "/users/{user_id}",
            "/users",
            "/orders",
            "/health"
        ]
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "container": "initialized" if app_context else "not initialized"
    }


@app.get("/users/{user_id}")
async def get_user(
        user_id: int,
        user_service: Annotated[UserService, Depends(lambda: ApplicationContext.service(UserService))]
):
    """获取用户（通过依赖注入）"""
    user = await user_service.get_user(user_id)
    return {"user": user}


@app.post("/users")
async def create_user(
        user_id: int,
        name: str,
        user_service: Annotated[UserService, Depends(lambda: ApplicationContext.service(UserService))]
):
    """创建用户（通过依赖注入）"""
    user = await user_service.create_user(user_id, name)
    return {"user": user, "message": "用户创建成功"}


@app.post("/orders")
async def create_order(
        user_id: int,
        product: str,
        order_service: Annotated[OrderService, Depends(lambda: ApplicationContext.service(OrderService))]
):
    """创建订单（通过依赖注入）"""
    order = await order_service.create_order(user_id, product)
    return {"order": order, "message": "订单创建成功"}


@app.get("/services")
async def list_services():
    """列出所有已注册的服务"""
    if not app_context:
        return {"error": "容器未初始化"}

    services = app_context.container.registry.all_names()
    return {
        "total": len(services),
        "services": sorted(services)
    }


# ============================================================================
# 9. 主程序入口
# ============================================================================

if __name__ == "__main__":
    """
    运行方式:
    1. 直接运行: python complete_lifecycle_example.py
    2. 使用 uvicorn: uvicorn complete_lifecycle_example:app --reload
    
    测试 API:
    - GET  http://localhost:8000/
    - GET  http://localhost:8000/health
    - GET  http://localhost:8000/users/1
    - POST http://localhost:8000/users?user_id=10&name=测试用户
    - POST http://localhost:8000/orders?user_id=1&product=手机
    - GET  http://localhost:8000/services
    
    停止应用: Ctrl+C
    """

    logger.info("🎯 启动 PySpring 完整生命周期示例应用")
    logger.info("📍 访问 http://localhost:8000 查看 API")
    logger.info("📖 访问 http://localhost:8000/docs 查看 API 文档")
    logger.info("🛑 按 Ctrl+C 停止应用\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
