# 更新日志

PySpring 的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.0.0] - 2025-12-24

### 新增

**IoC 容器与依赖注入**

- 带自动依赖解析的 IoC（控制反转）容器
- 通过 `ISingletonService` 接口实现单例服务生命周期管理
- 基于类型和名称的注入策略
- 线程安全的懒初始化
- 自动服务扫描和注册

**应用生命周期管理**

- 用于可扩展启动任务的 `IStartupInitializer` 接口
- 用于集中初始化编排的 `StartupInitializerManager`
- 用于优雅资源清理的 `IShutdownHandler` 接口
- 自动发现初始化器和处理器

**数据库自动初始化**

- 用于应用启动时自动创建架构的 `DatabaseInitializer`
- 增量模式：仅安全创建缺失的表
- 完整模式：完全重建架构（仅开发环境）
- 智能 SQL 脚本路径检测（scripts/db/、scripts/、db/）
- 通过 `repositories.yaml` 配置驱动

**安全与认证**

- RBAC（基于角色的访问控制）授权系统
- 带 Token 加密的 JWT 认证（Fernet/AES-GCM 算法）
- 使用责任链模式的认证链
- 灵活的白名单配置（精确匹配、前缀、正则表达式）
- Token 自动续期机制

**数据访问层**

- 统一的缓存抽象，支持 Memory/Redis 透明切换
- 多数据库支持（PostgreSQL、SQLite）
- 自动连接池管理
- 数据库和缓存连接生命周期管理
- 降级服务模式的故障转移机制

**日志基础设施**

- 基于 Loguru 的结构化日志系统
- 彩色控制台输出，增强开发体验
- 自动日志轮转（基于大小和时间）
- 支持 JSON 格式用于日志聚合
- 上下文请求跟踪和过滤

**项目脚手架**

- 用于项目初始化的 `pyspring init` CLI 命令
- 标准化项目结构生成（app/、config/、scripts/、tests/、logs/、data/）
- 基于模板的代码生成系统
- 自动生成 JWT 密钥
- 环境变量模板创建
- 从 SQLAlchemy 模型生成 SQL 脚本

**配置管理**

- 基于 YAML 的配置系统
- 环境变量插值
- 配置验证和类型检查
- 所有框架组件的集中配置
- 开发环境的热重载支持

**CLI 工具**

- `pyspring init` - 使用标准结构初始化新项目
- `pyspring diagnose` - 安装验证的诊断工具
- 模板同步工具 (`tools/sync_templates.py`)
- 加密密钥生成器

### 变更

- 从 `requirements.txt` 迁移到 `pyproject.toml` 以符合现代 Python 打包标准
- 将所有配置模板统一到 `src/pyspring/templates/` 目录
- 将文档重新组织为六个逻辑类别
- 优化数据库初始化器的错误处理和日志记录

### 修复

- 单例服务创建中的线程安全问题
- 应用关闭时的连接池清理
- 复杂 YAML 配置的环境变量解析
- SQL 脚本路径检测边界情况

### 文档

**新文档结构**

- [01-getting-started/](docs/01-getting-started/) - 安装和快速开始
- [02-core-concepts/](docs/02-core-concepts/) - IoC 容器和架构
- [03-configuration/](docs/03-configuration/) - 配置系统
- [04-features/](docs/04-features/) - 功能模块
- [05-advanced/](docs/05-advanced/) - 高级主题
- [06-troubleshooting/](docs/06-troubleshooting/) - 问题解决

**关键文档**

- 框架优化报告 - 设计决策分析与未来路线图

- 安装指南 - 详细的设置说明

- 安装指南 - 详细的设置说明
- 快速参考 - 命令和配置速查表
- IoC 容器指南 - 依赖注入模式
- 安全配置 - 认证和授权设置
- JWT 加密指南 - Token 加密实现
- 数据库自动初始化 - 自动架构管理
- 模板管理 - 自定义代码生成

### 技术细节

**依赖项**

- FastAPI >= 0.104.0
- SQLAlchemy >= 2.0.0
- Loguru >= 0.7.0
- Pydantic >= 2.0.0
- Redis >= 5.0.0
- Cryptography >= 41.0.0

**Python 版本**

- 需要 Python 3.12+

**包结构**

```
pyspring/
├── core/           # 核心框架组件
├── ioc/            # IoC 容器
├── security/       # 认证和授权
├── repositories/   # 数据访问层
├── log/            # 日志系统
├── system/         # 配置管理
└── templates/      # 代码生成模板
```

---

## 发布说明

### 1.0.0 的新特性

PySpring 1.0.0 是框架的首个稳定版本。此版本提供完整的、生产就绪的基础设施，用于构建具有 Spring Boot 风格架构的企业级 Python Web 应用。

**亮点：**

- 完整的 IoC 容器和依赖注入
- 生产就绪的认证和授权
- 自动数据库架构初始化
- 统一的数据访问抽象
- 专业的日志基础设施
- 全面的文档

**快速开始：**

```bash
pip install pyspring
pyspring init
```

**从预发布版本迁移：**
如果您正在使用预发布版本，请参阅 [迁移指南](docs/05-advanced/SECURITY_MIGRATION_GUIDE.md)。

---

## 贡献

我们欢迎贡献！请参阅我们的[贡献指南](#贡献)了解详情。

- **Bug 报告**: [GitHub Issues](https://github.com/365tools/PySpring/issues)
- **功能请求**: [GitHub Discussions](https://github.com/365tools/PySpring/discussions)
- **Pull Requests**: [GitHub Pull Requests](https://github.com/365tools/PySpring/pulls)

---

## 许可证

本项目采用 Apache License 2.0 许可 - 详见 [LICENSE](LICENSE) 文件。

---

## 链接

- **文档**: [docs/](docs/)
- **示例**: [examples/](examples/)
- **GitHub**: https://github.com/365tools/PySpring
- **PyPI**: https://pypi.org/project/pyspring/

---

*有关较早版本和详细版本历史，请参阅 [GitHub Releases](https://github.com/365tools/PySpring/releases)。*
