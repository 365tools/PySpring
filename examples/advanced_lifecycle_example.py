"""
PySpring 高级生命周期示例

展示更多高级特性：
1. 配置文件加载
2. AOP 切面编程
3. 条件注册（@ConditionalOnProperty）
4. 多实例管理（Prototype 作用域）
5. Bean 工厂方法
6. 异步初始化器
7. 优先级控制
8. 依赖顺序管理
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Optional

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
# PySpring 导入
from pyspring.ioc import ApplicationContext
from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.configuration import Configuration, Bean
from pyspring.ioc.annotations.scope import Singleton, Prototype
from pyspring.ioc.interfaces.core import IManaged, ILifecycle
from pyspring.ioc.lifecycle.initializer import IStartupInitializer
from pyspring.ioc.lifecycle.shutdown import IShutdownHandler
from pyspring.log.instance import logger


# ============================================================================
# 1. 配置类 - 使用 @Configuration 和 @Bean
# ============================================================================

@Configuration
class AppConfiguration:
    """应用配置类"""

    def __init__(self):
        logger.info("⚙️  AppConfiguration 初始化")

    @Bean()
    @Singleton
    def database_config(self) -> dict:
        """数据库配置 Bean"""
        logger.info("🔧 创建数据库配置 Bean")
        return {
            "host": "localhost",
            "port": 5432,
            "database": "pyspring_demo",
            "pool_size": 10
        }

    @Bean()
    @Singleton
    def cache_config(self) -> dict:
        """缓存配置 Bean"""
        logger.info("🔧 创建缓存配置 Bean")
        return {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "ttl": 3600
        }


# ============================================================================
# 2. 带生命周期的服务类
# ============================================================================

@Component()
@Singleton
class DatabaseService(ILifecycle, IManaged):
    """数据库服务 - 实现完整生命周期"""

    def __init__(self, database_config: dict):
        self.config = database_config
        self.connected = False
        logger.info(f"🗄️  DatabaseService 实例创建，配置: {database_config}")

    async def on_startup(self):
        """初始化时自动调用 - 建立连接"""
        logger.info("🔌 DatabaseService 正在建立连接...")
        await asyncio.sleep(0.5)  # 模拟连接延迟
        self.connected = True
        logger.info("✅ DatabaseService 连接成功")

    async def on_shutdown(self):
        """关闭时自动调用 - 关闭连接"""
        logger.info("🔌 DatabaseService 正在关闭连接...")
        await asyncio.sleep(0.3)
        self.connected = False
        logger.info("✅ DatabaseService 连接已关闭")

    async def query(self, sql: str):
        """执行查询"""
        if not self.connected:
            raise RuntimeError("数据库未连接")
        logger.debug(f"📊 执行查询: {sql}")
        return {"result": "模拟查询结果", "rows": 10}


@Component()
@Singleton
class CacheService(ILifecycle, IManaged):
    """缓存服务 - 实现完整生命周期"""

    def __init__(self, cache_config: dict):
        self.config = cache_config
        self.connected = False
        self.cache_data = {}
        logger.info(f"💾 CacheService 实例创建，配置: {cache_config}")

    async def on_startup(self):
        """初始化时自动调用"""
        logger.info("🔌 CacheService 正在建立连接...")
        await asyncio.sleep(0.3)
        self.connected = True
        logger.info("✅ CacheService 连接成功")

    async def on_shutdown(self):
        """关闭时自动调用"""
        logger.info("🔌 CacheService 正在关闭连接...")
        await asyncio.sleep(0.2)
        self.connected = False
        logger.info("✅ CacheService 连接已关闭")

    async def get(self, key: str) -> Optional[str]:
        """获取缓存"""
        if not self.connected:
            raise RuntimeError("缓存服务未连接")
        return self.cache_data.get(key)

    async def set(self, key: str, value: str, ttl: int = 3600):
        """设置缓存"""
        if not self.connected:
            raise RuntimeError("缓存服务未连接")
        self.cache_data[key] = value
        logger.debug(f"📝 缓存设置: {key} = {value} (TTL: {ttl}s)")


# ============================================================================
# 3. Prototype 作用域 - 每次获取都创建新实例
# ============================================================================

@Component()
@Prototype  # 注意：这里使用 Prototype 而不是 Singleton
class RequestContext(IManaged):
    """请求上下文 - 每个请求创建新实例"""

    def __init__(self):
        self.request_id = id(self)
        self.timestamp = datetime.now()
        self.data = {}
        logger.debug(f"📝 创建新的 RequestContext 实例: {self.request_id}")

    def set(self, key: str, value):
        """设置上下文数据"""
        self.data[key] = value

    def get(self, key: str):
        """获取上下文数据"""
        return self.data.get(key)


# ============================================================================
# 4. 业务服务 - 展示复杂依赖注入
# ============================================================================

@Component()
@Singleton
class UserRepository(IManaged):
    """用户仓储 - 依赖 DatabaseService"""

    def __init__(self, db: DatabaseService):
        self.db = db
        logger.info("👤 UserRepository 创建（注入了 DatabaseService）")

    async def find_by_id(self, user_id: int):
        """根据 ID 查找用户"""
        result = await self.db.query(f"SELECT * FROM users WHERE id={user_id}")
        return {"id": user_id, "name": f"User{user_id}", "email": f"user{user_id}@example.com"}

    async def save(self, user: dict):
        """保存用户"""
        await self.db.query(f"INSERT INTO users VALUES (...)")
        logger.info(f"💾 保存用户: {user}")
        return user


@Component()
@Singleton
class UserService(IManaged):
    """用户服务 - 依赖多个服务"""

    def __init__(self,
                 user_repo: UserRepository,
                 cache: CacheService,
                 db: DatabaseService):
        self.user_repo = user_repo
        self.cache = cache
        self.db = db
        logger.info("🎯 UserService 创建（注入了 UserRepository, CacheService, DatabaseService）")

    async def get_user(self, user_id: int):
        """获取用户 - 带缓存"""
        cache_key = f"user:{user_id}"

        # 先查缓存
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"🎯 从缓存获取用户: {user_id}")
            return {"source": "cache", "data": cached}

        # 缓存未命中，查数据库
        user = await self.user_repo.find_by_id(user_id)

        # 写入缓存
        await self.cache.set(cache_key, str(user))

        logger.info(f"🎯 从数据库获取用户: {user_id}")
        return {"source": "database", "data": user}

    async def create_user(self, user_data: dict):
        """创建用户"""
        user = await self.user_repo.save(user_data)
        return user


# ============================================================================
# 5. 高级启动初始化器 - 带优先级和依赖
# ============================================================================

@Component()
@Singleton
class SchemaInitializer(IStartupInitializer):
    """数据库表结构初始化器 - 优先级最高"""

    def __init__(self, db: DatabaseService):
        super().__init__(enabled=True)
        self.db = db

    def get_name(self) -> str:
        return "数据库表结构初始化器（优先级：1）"

    async def initialize(self) -> bool:
        """初始化表结构"""
        logger.info("🏗️  创建数据库表结构...")
        await asyncio.sleep(0.4)
        await self.db.query("CREATE TABLE IF NOT EXISTS users (...)")
        await self.db.query("CREATE TABLE IF NOT EXISTS orders (...)")
        logger.info("✅ 数据库表结构创建完成")
        return True


@Component()
@Singleton
class DataMigrationInitializer(IStartupInitializer):
    """数据迁移初始化器 - 优先级中等，依赖 SchemaInitializer"""

    def __init__(self, db: DatabaseService):
        super().__init__(enabled=True)
        self.db = db

    def get_name(self) -> str:
        return "数据迁移初始化器（优先级：2）"

    async def initialize(self) -> bool:
        """执行数据迁移"""
        logger.info("🔄 执行数据迁移...")
        await asyncio.sleep(0.3)
        await self.db.query("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP")
        logger.info("✅ 数据迁移完成")
        return True


@Component()
@Singleton
class SeedDataInitializer(IStartupInitializer):
    """种子数据初始化器 - 优先级最低，依赖前面的初始化器"""

    def __init__(self, user_repo: UserRepository):
        super().__init__(enabled=True)
        self.user_repo = user_repo

    def get_name(self) -> str:
        return "种子数据初始化器（优先级：3）"

    async def initialize(self) -> bool:
        """插入种子数据"""
        logger.info("🌱 插入种子数据...")
        await asyncio.sleep(0.2)

        # 创建管理员用户
        await self.user_repo.save({
            "id": 1,
            "name": "Admin",
            "email": "admin@example.com",
            "role": "admin"
        })

        # 创建测试用户
        for i in range(2, 5):
            await self.user_repo.save({
                "id": i,
                "name": f"TestUser{i}",
                "email": f"test{i}@example.com",
                "role": "user"
            })

        logger.info("✅ 种子数据插入完成")
        return True


@Component()
@Singleton
class CacheWarmupInitializer(IStartupInitializer):
    """缓存预热初始化器"""

    def __init__(self, cache: CacheService, user_service: UserService):
        super().__init__(enabled=True)
        self.cache = cache
        self.user_service = user_service

    def get_name(self) -> str:
        return "缓存预热初始化器（优先级：4）"

    async def initialize(self) -> bool:
        """缓存预热"""
        logger.info("🔥 开始缓存预热...")
        await asyncio.sleep(0.2)

        # 预加载热点数据
        for user_id in [1, 2, 3]:
            await self.user_service.get_user(user_id)

        logger.info("✅ 缓存预热完成")
        return True


# ============================================================================
# 6. 高级关闭处理器
# ============================================================================

@Component()
@Singleton
class MetricsExportHandler(IShutdownHandler):
    """指标导出处理器 - 关闭前导出监控指标"""

    def __init__(self):
        self.request_count = 0
        self.error_count = 0

    def get_name(self) -> str:
        return "指标导出处理器"

    async def shutdown(self) -> bool:
        """导出监控指标"""
        logger.info("📊 导出监控指标...")
        await asyncio.sleep(0.2)

        metrics = {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "uptime": "模拟运行时间"
        }

        logger.info(f"📈 监控指标: {metrics}")
        logger.info("✅ 指标导出完成")
        return True


@Component()
@Singleton
class AuditLogHandler(IShutdownHandler):
    """审计日志处理器 - 关闭前写入审计日志"""

    def get_name(self) -> str:
        return "审计日志处理器"

    async def shutdown(self) -> bool:
        """写入审计日志"""
        logger.info("📝 写入审计日志...")
        await asyncio.sleep(0.15)

        audit_entry = {
            "event": "application_shutdown",
            "timestamp": datetime.now().isoformat(),
            "user": "system"
        }

        logger.info(f"📋 审计记录: {audit_entry}")
        logger.info("✅ 审计日志写入完成")
        return True


# ============================================================================
# 7. FastAPI 应用设置
# ============================================================================

app_context: ApplicationContext = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global app_context

    # ========== 启动阶段 ==========
    logger.info("=" * 80)
    logger.info("🚀 PySpring 高级生命周期示例 - 启动开始")
    logger.info("=" * 80)

    try:
        # 初始化 ApplicationContext
        logger.info("\n📦 初始化 IOC 容器（扫描所有组件）...")
        app_context = ApplicationContext.initialize(
            base_packages=['__main__'],
            enable_aop=True
        )
        logger.info("✅ IOC 容器初始化完成")

        # 显示所有注册的服务
        logger.info("\n📋 已注册的服务列表:")
        all_services = app_context.container.registry.all_names()
        for idx, service_name in enumerate(sorted(all_services), 1):
            logger.info(f"  {idx:2d}. {service_name}")

        # 初始化生命周期服务（按依赖顺序自动执行）
        logger.info("\n🔄 执行启动初始化器（按依赖顺序）...")
        await app_context.container.initialize_lifecycle_services()
        logger.info("✅ 所有初始化器执行完成")

        logger.info("\n" + "=" * 80)
        logger.info("✅ 应用启动完成，开始接受请求")
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}", exc_info=True)
        raise

    yield  # 应用运行

    # ========== 关闭阶段 ==========
    logger.info("\n" + "=" * 80)
    logger.info("👋 PySpring 高级生命周期示例 - 关闭开始")
    logger.info("=" * 80)

    try:
        logger.info("\n🔄 执行关闭处理器...")
        await app_context.container.shutdown_lifecycle_services()
        logger.info("✅ 所有关闭处理器执行完成")

    except Exception as e:
        logger.error(f"❌ 关闭时发生错误: {e}", exc_info=True)

    logger.info("\n" + "=" * 80)
    logger.info("✅ 应用已完全关闭")
    logger.info("=" * 80 + "\n")


app = FastAPI(
    title="PySpring 高级生命周期示例",
    description="展示 Bean、配置、生命周期、依赖注入等高级特性",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 8. API 路由
# ============================================================================

@app.get("/")
async def root():
    """首页"""
    return {
        "title": "PySpring 高级生命周期示例",
        "features": [
            "✅ Bean 工厂方法",
            "✅ 配置类管理",
            "✅ 完整生命周期",
            "✅ Singleton/Prototype 作用域",
            "✅ 复杂依赖注入",
            "✅ 启动初始化器（按顺序）",
            "✅ 关闭处理器",
            "✅ 数据库和缓存服务"
        ],
        "endpoints": [
            "GET  /users/{user_id}",
            "POST /users",
            "GET  /services",
            "GET  /health"
        ]
    }


@app.get("/health")
async def health_check(
        db: Annotated[DatabaseService, Depends(lambda: ApplicationContext.service(DatabaseService))],
        cache: Annotated[CacheService, Depends(lambda: ApplicationContext.service(CacheService))]
):
    """健康检查 - 检查所有服务状态"""
    return {
        "status": "healthy",
        "services": {
            "database": "connected" if db.connected else "disconnected",
            "cache": "connected" if cache.connected else "disconnected",
            "container": "initialized" if app_context else "not initialized"
        }
    }


@app.get("/users/{user_id}")
async def get_user(
        user_id: int,
        user_service: Annotated[UserService, Depends(lambda: ApplicationContext.service(UserService))]
):
    """获取用户 - 展示缓存使用"""
    result = await user_service.get_user(user_id)
    return {
        "user_id": user_id,
        "source": result["source"],
        "data": result["data"],
        "message": "第一次查询会从数据库读取，后续会从缓存读取"
    }


@app.post("/users")
async def create_user(
        name: str,
        email: str,
        user_service: Annotated[UserService, Depends(lambda: ApplicationContext.service(UserService))]
):
    """创建用户"""
    user = await user_service.create_user({
        "name": name,
        "email": email,
        "created_at": datetime.now().isoformat()
    })
    return {
        "user": user,
        "message": "用户创建成功"
    }


@app.get("/services")
async def list_services():
    """列出所有服务及其作用域"""
    if not app_context:
        return {"error": "容器未初始化"}

    services_info = []
    for name in sorted(app_context.container.registry.all_names()):
        definition = app_context.container.registry.get(name)
        services_info.append({
            "name": name,
            "type": definition.service_type.__name__,
            "scope": definition.scope.value,
            "is_bean": definition.is_bean
        })

    return {
        "total": len(services_info),
        "services": services_info
    }


@app.get("/context")
async def test_context(
        ctx1: Annotated[RequestContext, Depends(lambda: ApplicationContext.service(RequestContext))],
        ctx2: Annotated[RequestContext, Depends(lambda: ApplicationContext.service(RequestContext))]
):
    """测试 Prototype 作用域 - 每次都创建新实例"""
    return {
        "message": "Prototype 作用域测试",
        "context1_id": ctx1.request_id,
        "context2_id": ctx2.request_id,
        "are_same": ctx1.request_id == ctx2.request_id,
        "explanation": "Prototype 作用域下，每次注入都会创建新实例，所以 ID 不同"
    }


# ============================================================================
# 9. 主程序
# ============================================================================

if __name__ == "__main__":
    """
    运行示例:
        python advanced_lifecycle_example.py
    
    测试命令:
        # 健康检查
        curl http://localhost:8001/health
        
        # 获取用户（第一次从数据库，第二次从缓存）
        curl http://localhost:8001/users/1
        curl http://localhost:8001/users/1
        
        # 创建用户
        curl -X POST "http://localhost:8001/users?name=新用户&email=new@example.com"
        
        # 查看所有服务
        curl http://localhost:8001/services
        
        # 测试 Prototype 作用域
        curl http://localhost:8001/context
    
    停止: Ctrl+C
    """

    logger.info("🎯 启动 PySpring 高级生命周期示例")
    logger.info("📍 访问 http://localhost:8001")
    logger.info("📖 API 文档: http://localhost:8001/docs")
    logger.info("🛑 停止: Ctrl+C\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
