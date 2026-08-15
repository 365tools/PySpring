# PySpring 项目结构

本文档说明 PySpring 框架的项目结构和组织方式。

## 📁 目录结构

```
PySpring/
├── src/pyspring/              # 核心框架代码
│   ├── __init__.py
│   ├── cli.py                 # CLI 命令行工具
│   ├── init.py                # 项目初始化脚本
│   │
│   ├── core/                  # 核心组件
│   │
│   ├── exception/             # 异常处理
│   │   ├── errors.py          # 异常定义
│   │   └── handler.py         # 异常处理器
│   │
│   ├── http/                  # HTTP 相关
│   │   └── response.py        # 响应封装
│   │
│   ├── interfaces/            # 接口定义
│   │   ├── IService.py        # 服务接口
│   │   └── component.py       # @Component/@Service 注解
│   │
│   ├── ioc/                   # IoC 容器
│   │   ├── container.py       # 服务容器
│   │   ├── manager.py         # 容器管理器
│   │   └── validator.py       # 依赖校验器
│   │
│   ├── aop/                   # AOP 切面
│   │   ├── core.py            # 切面核心类
│   │   └── proxy.py           # 动态代理生成
│   │
│   ├── log/                   # 日志系统
│   │   ├── config.py          # 日志配置
│   │   ├── interface.py       # 日志接口
│   │   └── loguru/            # Loguru 实现
│   │       ├── config_manager.py
│   │       ├── context.py
│   │       ├── format.py
│   │       ├── http.py
│   │       ├── ins.py
│   │       └── service.py
│   │
│   ├── repositories/          # 数据存储
│   │   ├── cache/             # 缓存层
│   │   │   ├── config.py
│   │   │   ├── manager.py
│   │   │   ├── service.py
│   │   │   ├── memory/        # 内存缓存
│   │   │   └── redis/         # Redis 缓存
│   │   │
│   │   └── db/                # 数据库层
│   │       ├── config.py
│   │       ├── manager.py
│   │       ├── service.py
│   │       ├── doc/           # 使用文档
│   │       ├── models/        # 数据模型
│   │       ├── postgres/      # PostgreSQL
│   │       └── sqlite/        # SQLite
│   │
│   ├── security/              # 安全模块
│   │   └── auth/              # 认证授权
│   │       ├── chain.py       # 认证链
│   │       ├── config_manager.py
│   │       ├── encryption.py  # JWT 加密
│   │       ├── factory.py     # 提供者工厂
│   │       ├── impl/          # 实现类
│   │       │   ├── config.py
│   │       │   ├── login.py
│   │       │   ├── manager.py
│   │       │   ├── register.py
│   │       │   └── token.py
│   │       ├── interfaces/    # 接口定义
│   │       ├── middleware/    # 中间件
│   │       │   ├── auth.py
│   │       │   ├── role.py
│   │       │   └── utils.py
│   │       ├── models/        # 数据模型
│   │       └── providers/     # 认证提供者
│   │           ├── base.py
│   │           └── jwt_provider.py
│   │
│   ├── system/                # 系统配置
│   │   ├── env.py             # 环境变量
│   │   ├── config/            # 配置管理
│   │   │   ├── base.py
│   │   │   ├── loader.py
│   │   │   ├── manager.py
│   │   │   ├── registry.py
│   │   │   └── validators.py
│   │   ├── impl/              # 系统服务实现
│   │   └── interfaces/        # 系统服务接口
│   │
│   └── templates/             # 配置文件模板
│       ├── container.yaml
│       ├── logging.yaml
│       ├── repositories.yaml
│       └── security.yaml
│
├── docs/                      # 文档目录
│   ├── README.md              # 文档中心
│   ├── INSTALLATION_GUIDE.md  # 安装指南
│   ├── QUICK_REFERENCE.md     # 快速参考
│   ├── IOC_CONFIG_GUIDE.md    # IoC 配置
│   ├── IOC_SINGLETON_GUIDE.md # 单例服务
│   ├── SECURITY_CONFIG_GUIDE.md    # 安全配置
│   ├── JWT_ENCRYPTION_GUIDE.md     # JWT 加密
│   ├── JWT_ENCRYPTION_IMPLEMENTATION.md  # JWT 实现
│   ├── REPOSITORIES_CONFIG_GUIDE.md # 存储配置
│   └── LOGGING_CONFIG_GUIDE.md     # 日志配置
│
├── tests/                     # 测试文件
│   ├── test_singleton_simple.py   # 单例测试（简化）
│   └── test_singleton_refactor.py # 单例测试（完整）
│
├── tools/                     # 工具脚本
│   └── generate_encryption_key.py # 密钥生成
│
├── config/                    # 配置文件（开发用）
│   └── *.yaml
│
├── .env                       # 环境变量
├── .env.example               # 环境变量示例
├── .gitignore                 # Git 忽略
├── LICENSE                    # 许可证
├── README.md                  # 项目说明
├── CHANGELOG.md               # 更新日志
└── pyproject.toml             # 项目配置（构建/打包统一由各包 pyproject 管理）
```

## 🎯 核心模块说明

### IoC 容器 (ioc/)

提供依赖注入和服务管理功能。

**主要组件**:

- `ApplicationContext`: 应用上下文，管理所有服务实例（单例模式）
- `DynamicContainer`: 动态服务容器，支持运行时注册

**文档**: [IoC 容器与单例服务](docs/IOC_SINGLETON_GUIDE.md)

### 认证系统 (security/auth/)

基于责任链模式的认证架构。

**主要组件**:

- `AuthenticationChainManager`: 认证链管理器
- `SecurityConfigManager`: 安全配置管理
- `JWTEncryptionManager`: JWT 加密管理
- `JWTAuthProvider`: JWT 认证提供者

**文档**: [安全配置指南](docs/SECURITY_CONFIG_GUIDE.md)

### 数据存储 (repositories/)

统一的数据库和缓存访问层。

**主要组件**:

- `RepositoriesConfigManager`: 存储配置管理
- `CacheManager`: 缓存管理器
- `DBManager`: 数据库管理器

**文档**: [存储配置指南](docs/REPOSITORIES_CONFIG_GUIDE.md)

### 日志系统 (log/)

基于 Loguru 的日志管理。

**主要组件**:

- `LoggingConfigManager`: 日志配置管理
- `LoguruService`: Loguru 服务

**文档**: [日志配置指南](docs/LOGGING_CONFIG_GUIDE.md)

### 配置管理 (system/)

应用配置加载和管理。

**主要组件**:

- `ConfigRegistry`: 配置注册表
- `EnvConfigLoader`: 环境变量加载器
- `BaseConfigManager`: 配置管理基类

## 📝 配置文件

### 项目配置 (pyproject.toml)

项目元数据和依赖管理。

### 应用配置 (config/*.yaml)

- `container.yaml`: IoC 容器配置
- `logging.yaml`: 日志系统配置
- `repositories.yaml`: 数据库和缓存配置
- `security.yaml`: 认证授权配置

### 环境变量 (.env)

敏感配置和环境特定配置：

- JWT 密钥
- 数据库连接信息
- Redis 连接信息

## 🧪 测试

### 单元测试 (tests/)

- `test_singleton_simple.py`: 单例服务验证
- `test_singleton_refactor.py`: 完整功能测试

运行测试：

```bash
python tests/test_singleton_simple.py
```

## 🛠️ 开发工具

### CLI 工具 (cli.py)

命令行工具入口：

```bash
pyspring init [options] [target_dir]
```

### 初始化脚本 (init.py)

项目初始化核心逻辑。

### 工具脚本 (tools/)

- `generate_encryption_key.py`: 生成 JWT 加密密钥

## 📚 文档组织

### docs/ 目录

所有用户文档集中在 `docs/` 目录：

- **入门**: INSTALLATION_GUIDE.md, QUICK_REFERENCE.md
- **核心**: IOC_SINGLETON_GUIDE.md, IOC_CONFIG_GUIDE.md
- **安全**: SECURITY_CONFIG_GUIDE.md, JWT_ENCRYPTION_GUIDE.md
- **存储**: REPOSITORIES_CONFIG_GUIDE.md
- **日志**: LOGGING_CONFIG_GUIDE.md

### 模块文档

特定模块的详细文档放在模块内：

- `repositories/db/doc/` - 数据库管理器详细文档

## 🔄 工作流程

### 开发流程

1. 修改源代码在 `src/pyspring/`
2. 更新相关文档在 `docs/`
3. 添加测试在 `tests/`
4. 更新 CHANGELOG.md

### 发布流程

1. 更新版本号（`bump-version.ps1` 或手动，同步各包 `packages/*/pyproject.toml`）
2. 更新 CHANGELOG.md
3. 按包发布：`./scripts/publish-individual.ps1 <包名> test`（TestPyPI 验证）
4. 验证通过后发布正式：`./scripts/publish-individual.ps1 <包名> prod`

## 📦 打包

采用 **PEP 420 多包结构**，每个子包（`packages/<包名>/pyproject.toml`）独立定义：

- 项目元数据（名称、版本、许可证）
- 依赖项与可选依赖
- 构建后端（setuptools）与包发现配置
- 入口点（entry-points）
- 模板等 `package-data` 打包配置

打包/发布统一通过 `scripts/publish-individual.ps1`（或 `.sh`）按包执行。

## 🎨 代码风格

### 模块组织

- `interfaces/`: 接口定义（Protocol）
- `impl/`: 接口实现
- `config.py`: 配置类
- `manager.py`: 管理器类
- `service.py`: 服务类

### 命名约定

- 接口: `I` 前缀 (如 `IService`)
- 单例: `@Component` 注解
- 管理器: `*Manager` 后缀
- 配置: `*Config` 或 `*ConfigManager`

## 🔍 查找文件

### 按功能查找

- **认证相关**: `src/pyspring/security/auth/`
- **数据库**: `src/pyspring/repositories/db/`
- **缓存**: `src/pyspring/repositories/cache/`
- **日志**: `src/pyspring/log/`
- **配置**: `src/pyspring/system/config/`

### 按类型查找

- **接口定义**: `*/interfaces/`
- **实现类**: `*/impl/`
- **配置类**: `*config*.py`
- **管理器**: `*manager.py`

---

**适用版本**: PySpring 1.0+
