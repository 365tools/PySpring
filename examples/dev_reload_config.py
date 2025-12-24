"""
开发环境配置 - 解决热重载问题

解决数据库文件变动导致的热重载卡死问题
"""

# ==================== 方式1: 使用 watchfiles 配置（推荐） ====================

# 在 uvicorn.run() 中配置
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        # 忽略特定目录/文件模式
        reload_excludes=[
            "*.db",
            "*.sqlite",
            "*.sqlite3",
            "data/*",
            "src/data/*",
            "*.log",
            "logs/*",
            "__pycache__/*",
            ".pytest_cache/*",
        ],
        # 或者指定只监听特定目录
        reload_dirs=["src/pyspring", "examples"],
    )

# ==================== 方式2: 使用环境变量 ====================

# .env 文件
"""
# 开发环境设置
RELOAD_ENABLED=true
RELOAD_DIRS=src/pyspring,examples
RELOAD_EXCLUDES=*.db,*.log,data/*
"""

# main.py 中读取


def start_dev_server():
    reload_enabled = os.getenv("RELOAD_ENABLED", "false").lower() == "true"
    reload_dirs = os.getenv("RELOAD_DIRS", "").split(",")
    reload_excludes = os.getenv("RELOAD_EXCLUDES", "").split(",")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload_enabled,
        reload_dirs=[d.strip() for d in reload_dirs if d.strip()],
        reload_excludes=[e.strip() for e in reload_excludes if e.strip()],
    )


# ==================== 方式3: 配置文件方式 ====================

# watchfiles.yaml
"""
paths:
  - src/pyspring
  - examples

exclude:
  - "*.db"
  - "*.sqlite"
  - "data/*"
  - "*.log"
  - "__pycache__"
"""

# 读取配置
import yaml


def load_reload_config():
    with open("watchfiles.yaml") as f:
        config = yaml.safe_load(f)
    return config


config = load_reload_config()
uvicorn.run(
    "main:app",
    reload=True,
    reload_dirs=config["paths"],
    reload_excludes=config["exclude"],
)

# ==================== 方式4: 手动控制热重载（最灵活） ====================

# 创建配置类
from pydantic_settings import BaseSettings


class DevConfig(BaseSettings):
    """开发环境配置"""
    reload_enabled: bool = True
    reload_delay: float = 0.25  # 热重载延迟（秒）

    # 监听目录
    reload_dirs: list[str] = ["src/pyspring", "examples"]

    # 排除模式
    reload_excludes: list[str] = [
        "*.db", "*.sqlite", "*.sqlite3",
        "data/*", "src/data/*",
        "*.log", "logs/*",
        "__pycache__/*", ".pytest_cache/*",
        ".idea/*", ".vscode/*",
    ]

    class Config:
        env_file = ".env"
        env_prefix = "DEV_"


# 使用
config = DevConfig()

uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8000,
    reload=config.reload_enabled,
    reload_delay=config.reload_delay,
    reload_dirs=config.reload_dirs,
    reload_excludes=config.reload_excludes,
)

# ==================== 方式5: 生产环境关闭热重载 ====================

# 根据环境自动配置
import os

ENV = os.getenv("ENVIRONMENT", "development")

if ENV == "production":
    # 生产环境：关闭热重载
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=4,  # 多进程
    )
else:
    # 开发环境：启用热重载，但排除数据文件
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=[
            "*.db", "*.sqlite", "data/*",
            "*.log", "logs/*",
        ],
    )

# ==================== 推荐的完整配置 ====================

"""
# .env 文件
ENVIRONMENT=development
DEV_RELOAD_ENABLED=true
DEV_RELOAD_DIRS=src/pyspring,examples
DEV_RELOAD_EXCLUDES=*.db,*.sqlite,*.log,data/*,__pycache__/*

# main.py
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

def main():
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            workers=4,
        )
    else:
        # 开发环境配置
        reload_dirs = os.getenv("DEV_RELOAD_DIRS", "src").split(",")
        reload_excludes = os.getenv("DEV_RELOAD_EXCLUDES", "*.db,*.log").split(",")
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[d.strip() for d in reload_dirs],
            reload_excludes=[e.strip() for e in reload_excludes],
        )

if __name__ == "__main__":
    main()
"""

# ==================== 常见问题排查 ====================

"""
问题1: 数据库文件变动触发热重载
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
症状：每次数据库写入都会触发重载，导致应用重启卡死

解决：
1. 在 reload_excludes 中添加 "*.db", "data/*"
2. 或将数据库文件移到项目外
3. 或使用远程数据库（PostgreSQL/MySQL）

问题2: 日志文件触发热重载
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
症状：日志写入触发重载

解决：
1. 在 reload_excludes 中添加 "*.log", "logs/*"
2. 或将日志输出到 stdout（推荐容器化部署）

问题3: __pycache__ 触发热重载
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
症状：Python 编译缓存触发重载

解决：
1. 在 reload_excludes 中添加 "__pycache__/*"
2. 设置 PYTHONDONTWRITEBYTECODE=1 环境变量

问题4: 热重载卡死
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
症状：检测到变更后无响应

解决：
1. 增加 reload_delay（如 0.5 秒）
2. 减少监听的目录范围（只监听源码目录）
3. 使用 --reload-delay 参数

命令行方式：
uvicorn main:app --reload \
    --reload-dir src/pyspring \
    --reload-dir examples \
    --reload-exclude "*.db" \
    --reload-exclude "*.log" \
    --reload-exclude "data/*" \
    --reload-delay 0.5
"""
