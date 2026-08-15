# PySpring 整体架构（Starter 化 + 命名空间包）

> 文档版本：v1.0
> 更新日期：2026-08-15

## 一、架构概览

PySpring 是一个构建于 FastAPI 之上的 Spring Boot 风格 Python 框架，采用 **uv 工作区 + PEP 420 命名空间包** 的多 Starter 架构。所有包共享统一 `pyspring` 顶层命名空间（发行包名与导入名解耦）：

```
packages/
├── pyspring/              # 聚合包（含 templates/）
├── pyspring-core/         # 核心层：IoC/AOP/日志/配置（始终加载）
├── pyspring-security/     # 安全：认证/授权/密码
├── pyspring-repositories/ # 数据：数据库/缓存
├── pyspring-web/          # Web：统一响应/异常
├── pyspring-health/       # 健康检查
└── pyspring-cli/          # 命令行工具
```

### 1.1 架构目标

1. **即插即用（Pluggable）**：每个 starter 是独立组件，不引用不影响核心功能。
2. **内置默认实现（Auto-configuration）**：引入即自带默认 Bean。
3. **支持外部扩展（SPI / Conditional）**：用户可实现接口替换默认实现。
4. **模块化拆分**：按职责组织为可独立引入的 starter。

---

## 二、Starter 划分

### 2.1 发行包 → 命名空间 → 职责

| 发行包 | 命名空间 | 职责 | 默认实现 | SPI 接口 |
|--------|---------|------|---------|---------|
| `pyspring-core` | `pyspring.core` | IoC / AOP / 日志 / 配置 | `ApplicationContext` | — |
| `pyspring-security` | `pyspring.security` | 认证（JWT）、授权（RBAC）、密码 | `DefaultAuthProvider`/`JWTService` | `IAuthProvider`/`ITokenService` |
| `pyspring-repositories` | `pyspring.repositories` | 数据库（PG/MySQL/SQLite）+ 缓存（Redis/Memory/Memcached） | `DBManagerService`/`MemoryCache` | `IDBService`/`ICacheService` |
| `pyspring-web` | `pyspring.web` | 统一响应、全局异常处理 | `ResponseBuilder`/`ExceptionHandler` | — |
| `pyspring-health` | `pyspring.health` | 健康检查（API/缓存/DB） | `HealthManager` | `IHealthIndicator` |

> **说明**：`pyspring-core` 始终随框架加载（对应 Spring 的 `spring-core`），其余为可选 starter。发行包名（`pyspring-security`）与导入命名空间（`pyspring.security`）解耦，遵循 PEP 420 命名空间包规范。

### 2.2 Starter 内部结构

```
pyspring-security/
├── src/pyspring/security/     # 命名空间子包（无 pyspring/__init__.py）
│   ├── autoconfigure/         # 自动装配（entry point 加载器）
│   │   └── __init__.py        # load() 返回 StarterDeclaration
│   ├── spi/                   # 对外接口（SPI）
│   ├── impl/                  # 默认实现
│   ├── model/                 # 数据模型 / DTO
│   └── ...
└── pyproject.toml
```

---

## 三、Starter 自动装配机制

### 3.1 装配方式

PySpring 通过 **Python entry points** 发现与装配 starter。每个 starter 在 `pyproject.toml` 注册 `pyspring.starters` 组 entry point，指向返回 `StarterDeclaration` 的加载函数：

```toml
[project.entry-points."pyspring.starters"]
pyspring-core = "pyspring.core.autoconfigure.core_starter:load"
pyspring-security = "pyspring.security.autoconfigure:load"
```

```python
# pyspring.security.autoconfigure/__init__.py
from pyspring.core.autoconfigure.declaration import StarterDeclaration


def load() -> StarterDeclaration:
    return StarterDeclaration(
        name="pyspring-security",
        scan_packages=("pyspring.security",),
        auto_configuration="pyspring.security.security_auto_config.SecurityAutoConfiguration",
        order=10,
        requires=("pyspring-core",),
    )
```

### 3.2 装配流程

1. `Container.initialize()` 启动 IoC 容器。
2. `AutoConfigurationLoader` 通过 `importlib.metadata` 发现所有 `pyspring.starters` entry point。
3. 按 `order` 排序，逐个执行加载函数收集 `scan_packages` 与自动配置类。
4. `@ConditionalOnMissingBean` 保证：用户若提供了同名接口实现，默认实现被替换。
5. 未引入的 starter 完全不扫描 → **即插即用，不引用不影响核心**。

---

## 四、核心机制

### 4.1 智能 IoC 容器

- 自动组件扫描与注册（`@Component` / `@Service` / `@Repository`）。
- 构造函数依赖注入。
- 单例生命周期管理 + 线程安全懒加载。
- 循环依赖 DAG 检测（启动时，杜绝运行时循环引用）。
- 启动扫描缓存，提升大型项目启动性能。

### 4.2 AOP 切面编程

- `@Before` / `@After` / `@Around` 声明式切面。
- 运行时动态代理，非侵入式增强业务逻辑。

### 4.3 三层配置系统

- 框架默认值 → 用户配置 → 环境变量，深度合并与覆盖。
- YAML 配置支持，环境变量插值。
- 配置文件经应用缓存加载，避免重复 I/O。

### 4.4 生产级安全

- 认证：JWT / API Key 等多种方式，责任链按优先级匹配。
- Token 负载加密（Fernet / AES-GCM）。
- 授权：RBAC 角色权限控制 + 白名单机制。

### 4.5 应用生命周期

- **Startup Initializers**：启动时自动执行数据迁移、缓存预热、服务探活。
- **Shutdown Handlers**：优雅停机，确保连接池关闭、资源释放。

### 4.6 统一数据抽象

- 数据库透明化：一套代码，配置即可在 PostgreSQL / MySQL / SQLite 间切换。
- 缓存抽象层：接口统一，从内存缓存平滑升级到 Redis，无需改业务代码。

---

## 五、CLI 工具

| 命令 | 说明 |
|------|------|
| `pyspring init` | 初始化标准项目结构 |
| `pyspring check` | 检查项目健康（循环依赖、导入、编码、版本一致性） |
| `pyspring dev` | 开发工作流辅助 |
| `pyspring clean` | 清理缓存与构建产物 |
| `pyspring security` | 安全相关检查 |
| `pyspring uv` | 封装 uv 环境管理 |

---

## 六、相关文档

- [模块职责清单](01-MODULE_INVENTORY.md)
- [开发规范](02-DEV_GUIDELINES.md)
- [测试与 pytest-xdist 并行实践](03-TESTING.md)
- [快速入门](../QUICK_START.md)
