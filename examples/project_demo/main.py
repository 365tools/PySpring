"""
PySpring 完整项目演示 - 入口文件

模拟生产环境的启动逻辑，展示了：
1. 配置加载 (config/container.yaml)
2. 包扫描 (examples.project_demo.app)
3. 依赖注入
4. 生命周期管理
"""
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI

# -----------------------------------------------------------------------------
# 1. 环境准备：添加项目根目录到 sys.path
#    (这步通常在生产环境中通过 pip install -e . 或 PYTHONPATH 设置)
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# 还要添加当前目录，以便能够 import examples.project_demo...
sys.path.insert(0, str(PROJECT_ROOT / "examples"))

# 导入 PySpring 核心组件
from pyspring.ioc.manager import AppContainerManager
from pyspring.core.configuration.registry import ConfigRegistry
from pyspring.web.core.response import Response
from pyspring.web.handlers.exception import GlobalExceptionHandler
from pyspring.core.abstracts.exceptions import AppError

# 导入应用路由(稍后注册)
from examples.project_demo.app.api.endpoints import router as item_router


# -----------------------------------------------------------------------------
# 2. 定义生命周期：启动时初始化 IoC 容器
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("🚀 Demo App 启动中...")

    # [关键] 设置配置文件所在的目录 (模拟实际项目的 config 文件夹)
    # 默认 PySpring 会去 PROJ_ROOT/config 找，这里因为是嵌套示例，我们显式指定
    demo_config_dir = Path(__file__).parent / "config"
    ConfigRegistry.set_config_path(str(demo_config_dir))

    # [关键] 初始化容器管理器
    # 这会触发 container.yaml 的读取 -> 自动扫描 examples.project_demo.app 包下的所有服务
    manager = AppContainerManager()
    manager.register_all_services()

    # 执行其他启动初始化器 (Initializers)
    await manager.run_startup_initializers()

    print("✅ Demo App 启动完成!")
    print("=" * 60 + "\n")

    yield

    print("\n" + "=" * 60)
    print("🛑 Demo App 关闭中...")
    await manager.run_shutdown_handlers()
    print("=" * 60 + "\n")


# -----------------------------------------------------------------------------
# 3. 创建 FastAPI 应用
# -----------------------------------------------------------------------------
app = FastAPI(
    title="PySpring Shop Demo",
    version="1.0.0",
    lifespan=lifespan
)

# 注册统一异常处理器
app.add_exception_handler(AppError, GlobalExceptionHandler.app_error_handler if hasattr(GlobalExceptionHandler, 'app_error_handler') else None)
# 这里仅演示路由挂载
app.include_router(item_router)


@app.get("/")
def root():
    return Response.success({"message": "Welcome to PySpring Shop Demo!"})


# -----------------------------------------------------------------------------
# 4. 启动服务
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("🌍 服务运行在: http://127.0.0.1:8080")
    print("📚 API 文档: http://127.0.0.1:8080/docs")
    # 使用 uvicorn 启动
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
