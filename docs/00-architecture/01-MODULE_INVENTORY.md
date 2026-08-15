# PySpring 模块职责清单（MODULE_INVENTORY）

> 版本：v1.0
> 更新日期：2026-08-15
> 目的：梳理当前各模块的职责、依赖、SPI 接口与结构，为开发与扩展提供参考。

---

## 一、发行包总览

PySpring 采用 **PEP 420 命名空间包** 架构，所有 Starter 共享统一 `pyspring` 顶层命名空间：

```
packages/
├── pyspring/              # 聚合包（含 templates/、py.typed）
├── pyspring-core/         # pyspring.core：IoC/AOP/日志/配置
├── pyspring-security/     # pyspring.security：认证/授权/密码
├── pyspring-repositories/ # pyspring.repositories：数据库/缓存
├── pyspring-web/          # pyspring.web：统一响应/异常
├── pyspring-health/       # pyspring.health：健康检查
└── pyspring-cli/          # pyspring.cli：命令行工具
```

| 发行包 | 命名空间 | 职责 |
|--------|---------|------|
| `pyspring-core` | `pyspring.core` | IoC / AOP / 日志 / 配置 |
| `pyspring-security` | `pyspring.security` | 认证（JWT）+ 授权（RBAC）+ 密码 |
| `pyspring-repositories` | `pyspring.repositories` | DAL：db + cache |
| `pyspring-web` | `pyspring.web` | 统一响应、全局异常 |
| `pyspring-health` | `pyspring.health` | 健康检查 |
| `pyspring-cli` | `pyspring.cli` | 命令行工具 |
| `pyspring` | `pyspring` | 聚合 + 模板 |

---

## 二、pyspring-core（核心层）

### 2.1 目录结构

```
pyspring-core/src/pyspring/core/
├── ioc/                 # IoC 容器
│   ├── context.py       # ApplicationContext：容器核心
│   ├── scanner.py       # 组件扫描器
│   ├── resolver.py      # 依赖解析器
│   ├── registry.py      # 服务注册表
│   ├── lifecycle/       # 生命周期管理
│   ├── proxy/           # 代理工厂
│   ├── annotations/     # @Component/@Service/@Repository 等注解
│   └── interfaces/      # IoC 接口
├── aop/                 # AOP 切面编程
│   ├── facade.py        # 切面门面
│   ├── core.py          # AOP 核心
│   └── proxy.py         # create_proxy 动态代理
├── config/              # 配置
│   ├── loader.py        # 配置加载器
│   └── defaults/        # 框架默认配置（security/database/logging）
├── log/                 # 日志（loguru 封装、多 provider）
├── autoconfigure/       # 自动装配机制
│   ├── loader.py        # AutoConfigurationLoader
│   ├── declaration.py   # StarterDeclaration
│   └── core_starter.py  # 核心 starter 装配
├── context/             # 上下文
│   └── registry.py      # 上下文注册表
└── exception/           # 异常体系
```

### 2.2 职责

| 模块 | 职责 |
|------|------|
| `ioc/` | 组件扫描、依赖注入、生命周期、循环依赖检测、代理 |
| `aop/` | 切面定义与运行时动态代理 |
| `config/` | 三层配置加载（默认值/用户/环境变量） |
| `log/` | 结构化日志、多 provider 输出 |
| `autoconfigure/` | entry point 发现与装配 |
| `context/` | 上下文与容器管理 |

---

## 三、pyspring-security（安全层）

### 3.1 目录结构

```
pyspring-security/src/pyspring/security/
├── authentication/      # 认证
│   ├── provider/        # 认证提供者
│   ├── jwt/             # JWT 服务
│   ├── token/           # Token 服务
│   ├── web/             # 中间件与依赖
│   └── interfaces/      # IAuthProvider/ITokenService 等
├── authorization/       # 授权
│   ├── rbac/            # RBAC 权限
│   └── ...
├── password/            # 密码编码（BCrypt 等）
├── model/               # 数据模型
├── interfaces/          # SPI 接口
└── impl/                # 默认实现
```

### 3.2 职责

| 模块 | 职责 | SPI 接口 | 默认实现 |
|------|------|---------|---------|
| `authentication/` | JWT 认证、Token 签发与校验、认证链 | `IAuthProvider` / `ITokenService` | `JWTService` |
| `authorization/` | RBAC 角色权限、白名单 | `IAuthorizationService` | `DefaultAuthProvider` |
| `password/` | 密码编码与校验 | `IPasswordEncoder` | BCrypt |
| `web/` | 认证中间件、依赖注入函数 | — | — |

---

## 四、pyspring-repositories（数据层）

### 4.1 目录结构

```
pyspring-repositories/src/pyspring/repositories/
├── db/                  # 数据库
│   ├── interfaces/      # IDBService 等
│   ├── providers/       # 数据库驱动
│   │   ├── postgres/    # PostgreSQL
│   │   ├── mysql/       # MySQL
│   │   └── sqlite/      # SQLite
│   ├── initializer/     # 迁移与初始化
│   └── ...
├── cache/               # 缓存
│   ├── interfaces/      # ICacheService 等
│   └── providers/
│       ├── memory/      # 内存缓存
│       ├── redis/       # Redis
│       └── memcached/   # Memcached
└── config/              # 配置
```

### 4.2 职责

| 模块 | 职责 | SPI 接口 | 默认实现 |
|------|------|---------|---------|
| `db/` | ORM、迁移、连接池，多数据库切换 | `IDBService` | `DBManagerService` |
| `cache/` | 缓存抽象，多 provider | `ICacheService` | `MemoryCache` |
| `initializer/` | 数据库初始化和迁移 | — | — |

---

## 五、pyspring-web（Web 层）

| 模块 | 职责 |
|------|------|
| `web/response/` | 统一响应格式（`Response` / `HttpResponse`） |
| `web/exception/` | 全局异常处理与业务码 |
| `web/middleware/` | 中间件 |

## 六、pyspring-health（健康检查）

| 模块 | 职责 | SPI 接口 |
|------|------|---------|
| `health/indicators/` | 各健康指标（API/缓存/DB） | `IHealthIndicator` |
| `health/manager.py` | 健康检查管理器 | — |

## 七、pyspring-cli（命令行工具）

| 模块 | 职责 |
|------|------|
| `cli/core/` | 命令解析（argparse/subparsers）与命令加载 |
| `cli/commands/` | 各命令实现（init/check/dev/clean/security/uv/meta） |
| `cli/ui/` | 终端 UI（banner、表格、颜色） |
| `cli/utils/` | 工具函数 |
| `cli/main.py` | CLI 入口（entry point `pyspring`） |

---

## 八、跨模块依赖规则

- **单向依赖**：`pyspring-core` ← `pyspring-security` / `pyspring-repositories` / `pyspring-web` / `pyspring-health` ← `pyspring-cli`。
- **核心不依赖任何 starter**：各 starter 依赖 core，反向不成立。
- **starter 之间**：通过 SPI 接口交互，不直接依赖具体实现。

---

## 九、相关文档

- [整体架构](00-ARCHITECTURE.md)
- [开发规范](02-DEV_GUIDELINES.md)
- [测试与 pytest-xdist 并行实践](03-TESTING.md)
