<div align="center">

# PySpring

**企业级 Python Web 开发框架**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-powered-009688.svg)](https://fastapi.tiangolo.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[English](README.md) | [中文文档](README_CN.md) | [文档中心](docs/) | [更新日志](CHANGELOG_CN.md)

</div>

---

## 概述

**PySpring** 是一个现代化的企业级 Python Web 框架，设计灵感源于 Spring Boot。基于 FastAPI 构建，提供生产就绪的基础设施，包括 IoC 容器、认证授权、数据访问和完善的日志系统，帮助开发者构建可扩展的应用程序。

### 为什么选择 PySpring？

- **🏗️ Spring 风格架构** - Java 开发者熟悉的概念：IoC、依赖注入、生命周期管理
- **⚡ 生产就绪** - 经过实战验证的认证、缓存、数据库连接模式
- **🔧 配置驱动** - 通过 YAML 集中管理所有框架组件配置
- **🛡️ 安全优先** - JWT 加密、RBAC、认证链和灵活的白名单机制
- **📦 模块化设计** - 松耦合组件，清晰的职责分离

---

## 核心特性

### IoC 容器与依赖注入

PySpring 提供强大的 IoC 容器用于管理应用组件及其依赖关系。

- **单例服务管理** - 通过 `ISingletonService` 接口统一生命周期管理
- **自动依赖解析** - 基于类型和名称的注入策略
- **线程安全初始化** - 保证多线程环境下的单例创建安全
- **懒加载** - 服务在首次使用时实例化，优化启动性能

### 应用生命周期管理

基于初始化器模式的可扩展启动初始化系统。

- **启动初始化器** - 应用引导任务的可插拔组件
- **数据库自动初始化** - 应用启动时自动创建数据库架构
    - **增量模式** - 仅安全创建缺失的表
    - **完整模式** - 完全重建架构（仅开发环境）
    - **智能检测** - 自动解析 SQL 脚本路径
- **关闭处理器** - 应用终止时优雅清理资源

### 安全与认证

生产级安全基础设施，配置灵活。

- **认证链** - 使用责任链模式组合认证处理器
- **JWT 加密** - 使用 Fernet/AES-GCM 算法加密 Token 载荷
- **RBAC 授权** - 完整的基于角色的访问控制系统
- **多设备管理** - 设备跟踪和认证
- **灵活白名单** - 支持精确匹配、前缀匹配和正则表达式

### 数据访问层

统一的数据存储抽象，透明的提供者切换。

- **缓存抽象** - Memory/Redis 缓存无缝切换，无需修改代码
- **数据库支持** - PostgreSQL、SQLite 统一接口
- **连接池** - 自动管理数据库和缓存连接
- **配置驱动** - 所有存储设置通过 YAML 配置管理

### 日志基础设施

基于 Loguru 构建的结构化日志系统。

- **结构化日志** - 支持 JSON 格式用于日志聚合
- **自动轮转** - 基于大小和时间的日志文件轮转
- **彩色控制台输出** - 增强开发体验
- **上下文过滤器** - 请求上下文跟踪和过滤

### 项目脚手架

快速项目搭建的命令行工具。

- **标准化结构** - 使用 `pyspring init` 生成完整项目布局
- **模板系统** - 可自定义的代码生成模板
- **自动配置** - 自动生成 JWT 密钥和环境变量
- **生产就绪** - 生成的 `main.py` 包含完整启动逻辑

---

## 安装

### 前置要求

- Python 3.12 或更高版本
- pip 或 uv 包管理器

### 通过 pip 安装

```bash
pip install pyspring
```

### 通过 uv 安装（推荐，速度更快）

[uv](https://github.com/astral-sh/uv) 是一个极快的 Python 包管理器，比 pip 快 10-100 倍：

```bash
# 安装 uv（首次使用）
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 创建虚拟环境并安装 PySpring
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1 # Windows
uv pip install pyspring
```

### 从源码安装

```bash
git clone https://github.com/365tools/PySpring.git
cd PySpring
pip install -e .
```

详细安装说明请参见 [安装指南](docs/01-getting-started/INSTALLATION_GUIDE.md)。

---

## 快速开始

### 1. 初始化项目

创建标准化结构的新项目：

```bash
pyspring init
```

这将生成完整的应用结构：

```
your-project/
├── app/                       # 应用代码
│   ├── api/                  # API 路由和端点
│   ├── models/               # 数据模型和架构
│   ├── services/             # 业务逻辑层
│   └── utils/                # 工具函数
├── config/                    # 配置文件
│   ├── container.yaml        # IoC 容器配置
│   ├── logging.yaml          # 日志配置
│   ├── repositories.yaml     # 数据库和缓存配置
│   └── security.yaml         # 认证和授权配置
├── scripts/db/               # 数据库脚本
│   ├── init_incremental.sql  # 安全增量初始化
│   └── init_full.sql         # 完整架构重建
├── tests/                    # 测试套件
├── logs/                     # 日志文件
├── data/                     # 数据目录
├── main.py                   # 应用入口
├── .env                      # 环境变量（自动生成）
├── .env.example             # 环境变量模板
├── .gitignore               # Git 忽略规则
└── pyproject.toml           # 项目元数据和依赖
```

### 2. 配置环境

`.env` 文件已自动生成安全的 JWT 密钥。根据需要配置其他设置：

```bash
# JWT 配置（自动生成）
JWT_SECRET_KEY=<自动生成的密钥>
JWT_ENCRYPTION_KEY=<自动生成的加密密钥>

# 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your-user
POSTGRES_PASSWORD=your-password
POSTGRES_DB=your-database

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. 配置数据库自动初始化

编辑 `config/repositories.yaml`：

```yaml
database:
  initialization:
    enabled: true              # 启用自动初始化
    mode: incremental          # 使用安全增量模式
    auto_detect: true          # 自动检测脚本路径
    # script_path: scripts/db/init_incremental.sql  # 或手动指定
```

**初始化模式：**

- `incremental`: 安全模式 - 仅创建缺失的表，保留现有数据
- `full`: 危险模式 - 删除并重建所有表（仅开发环境）

### 4. 运行应用

生成的 `main.py` 包含完整的启动逻辑：

```bash
uvicorn main:app --reload
```

启动时，应用自动执行初始化任务：

```
🔧 [DatabaseInitializer] 开始初始化...
✅ [DatabaseInitializer] 数据库初始化完成
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. 访问 API

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

---

## 核心概念

### IoC 容器与单例服务

PySpring 的核心是 **IoC（控制反转）容器**，提供依赖注入和单例生命周期管理：

```python
from pyspring.interfaces.ISingleton import ISingletonService

class UserService(ISingletonService):
    """单例服务示例"""
    
    def __init__(self):
        super().__init__()
        # 初始化逻辑
    
    async def initialize(self) -> bool:
        """异步初始化钩子"""
        # 设置资源
        return True
    
    async def cleanup(self) -> None:
        """清理钩子"""
        # 释放资源
        pass

# 使用服务
from pyspring.ioc.manager import AppContainerManager

container = AppContainerManager()
service = container.get(UserService)
```

**优势：**

- 🔒 线程安全的单例创建
- ⚡ 首次使用时懒初始化
- 🔄 完整的生命周期管理（初始化、清理）
- 📦 自动依赖解析

### 应用生命周期

使用 **初始化器模式** 管理启动任务：

```python
from pyspring.interfaces.IStartupInitializer import (
    IStartupInitializer, 
    StartupInitializerManager
)

class CacheWarmupInitializer(IStartupInitializer):
    """缓存预热初始化器"""
    
    async def execute(self) -> bool:
        # 缓存预热逻辑
        logger.info("缓存预热完成")
        return True

# 在应用启动时注册
@app.on_event("startup")
async def startup():
    manager = StartupInitializerManager()
    manager.register(DatabaseInitializer())     # 数据库初始化
    manager.register(CacheWarmupInitializer())  # 缓存预热
    await manager.execute_all()
```

**特性：**

- 🎯 集中管理启动任务
- 📊 按顺序执行并记录日志
- 🛡️ 支持错误处理和回滚
- 🔌 易于扩展

### 认证链

支持多种认证方式的灵活认证架构：

```python
# 配置多个认证处理器
auth_chain = [
    WhitelistAuthHandler(),  # 白名单检查
    JWTAuthHandler(),        # JWT 验证
    RBACAuthHandler(),       # 权限检查
]
```

### 统一配置

所有配置通过 YAML 文件管理，支持环境变量：

```yaml
# config/security.yaml
authentication:
  jwt:
    secret_key: ${JWT_SECRET_KEY}
    algorithm: HS256
    access_token_expire_minutes: 30
```

---

## CLI 工具

### 可用命令

```bash
# 初始化新项目
pyspring init

# 诊断安装和导入问题
pyspring diagnose

# 高级初始化选项
pyspring init --force          # 覆盖现有文件
pyspring init --minimal        # 最小项目结构
pyspring init --skip-env       # 跳过 .env 文件生成
```

### 诊断工具

排查安装或导入问题：

```bash
pyspring diagnose
```

诊断工具会检查：

- ✅ Python 环境（版本、路径、虚拟环境）
- ✅ PySpring 安装状态
- ✅ 模块导入功能
- ✅ Python 搜索路径配置
- ✅ 提供具体解决方案

详细故障排除请参见 [故障排除指南](docs/06-troubleshooting/)。

### 模板系统

所有生成的文件来自可自定义的模板，位于 `src/pyspring/templates/`。

**自定义模板：**

1. 编辑源文件（如 `pyproject.toml`、`examples/main_with_db_init.py`）
2. 运行 `python tools/sync_templates.py` 同步到模板目录
3. 重新安装：`pip install -e .`

---

## 文档

完整文档位于 [docs/](docs/) 目录，分为六个类别：

### 🚀 [入门指南](docs/01-getting-started/)

- [安装指南](docs/01-getting-started/INSTALLATION_GUIDE.md) - 详细的安装和设置
- [项目初始化](docs/01-getting-started/PROJECT_INIT_GUIDE.md) - 完整的 `pyspring init` 指南
- [快速参考](docs/01-getting-started/QUICK_REFERENCE.md) - 命令和配置速查表

### 🏗️ [核心概念](docs/02-core-concepts/)

- [IoC 容器与单例服务](docs/02-core-concepts/IOC_SINGLETON_GUIDE.md) - 依赖注入和生命周期
- [IoC 容器配置](docs/02-core-concepts/IOC_CONFIG_GUIDE.md) - 容器配置
- [项目结构](docs/02-core-concepts/PROJECT_STRUCTURE.md) - 框架架构

### ⚙️ [配置](docs/03-configuration/)

- [配置架构](docs/03-configuration/CONFIG_ARCHITECTURE.md) - 配置文件组织
- [应用配置](docs/03-configuration/APPLICATION_CONFIG_GUIDE.md) - 应用和服务器设置
- [日志配置](docs/03-configuration/LOGGING_CONFIG_GUIDE.md) - 日志系统设置
- [数据存储配置](docs/03-configuration/REPOSITORIES_CONFIG_GUIDE.md) - 数据库和缓存
- [安全配置](docs/03-configuration/SECURITY_CONFIG_GUIDE.md) - 认证和授权

### ✨ [功能模块](docs/04-features/)

- [JWT 加密](docs/04-features/JWT_ENCRYPTION_GUIDE.md) - Token 加密指南
- [JWT 实现](docs/04-features/JWT_ENCRYPTION_IMPLEMENTATION.md) - 加密内部原理
- [数据库自动初始化](docs/04-features/DATABASE_AUTO_INIT.md) - 自动架构创建
- [模板管理](docs/04-features/TEMPLATE_MANAGEMENT.md) - 模板系统使用

### 🎓 [高级主题](docs/05-advanced/)

- [框架迁移](docs/05-advanced/SECURITY_MIGRATION_GUIDE.md) - 从其他框架迁移
- [项目集成](docs/05-advanced/INSTALLATION_OTHER_PROJECT.md) - 集成到现有项目
- [uv 包管理器](docs/05-advanced/SETUP_WITH_UV.md) - 使用 uv 快速安装

### 🔧 [故障排除](docs/06-troubleshooting/)

- [诊断指南](docs/06-troubleshooting/DIAGNOSE_GUIDE.md) - 使用诊断工具
- [IDE 配置](docs/06-troubleshooting/FIX_UNRESOLVED_REFERENCE.md) - 修复 IDE 问题
- [SQL 问题](docs/06-troubleshooting/SQL_ISSUES.md) - 数据库问题解决

---

## 示例

### 完整应用

```python
from fastapi import FastAPI
from pyspring.interfaces.IStartupInitializer import StartupInitializerManager
from pyspring.repositories.db.initializer import DatabaseInitializer

app = FastAPI(title="PySpring Application")

@app.on_event("startup")
async def startup():
    """应用启动时执行初始化任务"""
    manager = StartupInitializerManager()
    manager.register(DatabaseInitializer())
    await manager.execute_all()

@app.get("/")
async def root():
    return {"message": "欢迎使用 PySpring!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

更多示例请查看 [examples/](examples/) 目录：

- [配置使用](examples/config_usage_example.py) - 配置管理模式
- [JWT 加密](examples/jwt_encryption_example.py) - Token 加密实现
- [日志设置](examples/logging_example.py) - 结构化日志配置

---

## 贡献

欢迎贡献！我们感谢 Bug 报告、功能请求和代码贡献。

### 如何贡献

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 开发设置

```bash
# 克隆仓库
git clone https://github.com/365tools/PySpring.git
cd PySpring

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 运行代码检查
black src/
flake8 src/
```

### 贡献指南

- 遵循 [PEP 8](https://pep8.org/) 代码风格
- 为新功能添加测试
- 更新 API 变更的文档
- 确保所有测试通过后再提交 PR

---

## 许可证

本项目采用 **Apache License 2.0** 许可证 - 详见 [LICENSE](LICENSE) 文件。

### 版权声明

版权所有 © 2025 [Yingchun] (365tools)

本项目基于 Apache License 2.0 许可证开放源代码。您可以自由使用、修改和分发本软件，但需要遵守许可证条款。

完整的许可证文本请访问：http://www.apache.org/licenses/LICENSE-2.0

**重要说明：**

- 本软件按"原样"提供，不提供任何明示或暗示的保证
- 使用本软件即表示您同意遵守 Apache License 2.0 的所有条款
- 本项目在个人时间独立开发，不涉及任何商业实体的专有或机密信息

---

## 致谢

PySpring 的构建得益于以下优秀开源项目的启发和支持：

### 设计灵感

- **[Spring Boot](https://spring.io/projects/spring-boot)** - 设计理念、架构模式和 IoC 容器概念

### 核心框架

- **[FastAPI](https://fastapi.tiangolo.com/)** - 高性能现代 Python Web 框架
- **[Uvicorn](https://www.uvicorn.org/)** - 闪电般快速的 ASGI 服务器
- **[Pydantic](https://docs.pydantic.dev/)** - 使用 Python 类型注解的数据验证和设置管理
- **[Starlette](https://www.starlette.io/)** - 轻量级 ASGI 框架/工具包（FastAPI 基础）

### 安全与认证

- **[python-jose](https://github.com/mpdavis/python-jose)** - JWT 的 JavaScript 对象签名和加密（JOSE）
- **[Passlib](https://passlib.readthedocs.io/)** - 全面的密码哈希框架
- **[Cryptography](https://cryptography.io/)** - 加密配方和原语

### 数据库与 ORM

- **[SQLAlchemy](https://www.sqlalchemy.org/)** - 强大的 SQL 工具包和 ORM
- **[Alembic](https://alembic.sqlalchemy.org/)** - 数据库迁移工具
- **[asyncpg](https://github.com/MagicStack/asyncpg)** - 快速的 PostgreSQL 数据库客户端库
- **[aiosqlite](https://github.com/omnilib/aiosqlite)** - SQLite 的异步支持

### 缓存与存储

- **[Redis](https://redis.io/)** - 内存数据结构存储
- **[redis-py](https://github.com/redis/redis-py)** - Python Redis 客户端

### 日志与配置

- **[Loguru](https://github.com/Delgan/loguru)** - Python 日志变得简单优雅
- **[PyYAML](https://pyyaml.org/)** - YAML 解析器和发射器
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** - 环境变量管理

### 依赖注入

- **[dependency-injector](https://github.com/ets-labs/python-dependency-injector)** - 依赖注入框架

### 开发工具

- **[pytest](https://pytest.org/)** - 测试框架
- **[Black](https://black.readthedocs.io/)** - 代码格式化工具
- **[mypy](http://mypy-lang.org/)** - 静态类型检查器

我们感谢这些项目的所有维护者和贡献者的出色工作。

---

## 支持与社区

### 获取帮助

- **文档**: [docs/](docs/)
- **示例**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/365tools/PySpring/issues)
- **讨论**: [GitHub Discussions](https://github.com/365tools/PySpring/discussions)

### 报告问题

报告问题时，请包含：

- PySpring 版本 (`pip show pyspring`)
- Python 版本 (`python --version`)
- 操作系统
- 最小可复现示例
- 错误消息和堆栈跟踪

### 功能请求

欢迎功能请求！请：

- 先检查现有 issues
- 清楚描述使用场景
- 说明为何对社区有益

---

<div align="center">

**使用 PySpring 构建企业级 Python 应用** 🚀

[文档](docs/) • [示例](examples/) • [贡献](#贡献) • [许可证](#许可证)

</div>
