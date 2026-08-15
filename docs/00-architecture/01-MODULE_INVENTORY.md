# PySpring 业务实现梳理（MODULE_INVENTORY）

> 版本：v0.1
> 目的：梳理当前各模块的职责、依赖、SPI 接口与冗余点，为 Starter 化拆分提供依据。

---

## 一、模块总览

```
packages/
├── pyspring/          # 核心框架 v1.1.0（src/pyspring）
└── pyspring-cli/      # CLI v1.0.0（src/pyspring_cli，依赖 pyspring）
```

### pyspring 内部功能包

| 包 | 职责 | 规模 | 建议归宿 |
|----|------|------|---------|
| `ioc/` | IoC 容器（Container/Scanner/Resolver/Registry/Lifecycle/Proxy/Annotations） | 31 py | **pyspring-core** |
| `aop/` | AOP（@Aspect/@Before/@After/@Around、动态代理） | 8 py | **pyspring-core** |
| `log/` | 日志（loguru 封装、多 provider） | 26 py | **pyspring-core** |
| `core/` | 框架基础（配置、上下文、异常、服务） | 11 py | **pyspring-core** |
| `config/` | 框架配置（defaults、framework.yaml、README） | — | **pyspring-core** |
| `security/` | 认证（JWT）+ 授权（RBAC）+ 用户管理 | 87 py | **pyspring-security-starter** |
| `repositories/` | DAL：db（PG/MySQL/SQLite）+ cache（Redis/Memory/Memcached） | 52 py | **pyspring-db-starter** / **pyspring-cache-starter** |
| `web/` | 统一响应、全局异常处理 | 6 py | **pyspring-web-starter** |
| `health/` | 健康检查（API/缓存/DB） | 3 py | **pyspring-health-starter** |
| `utils/` | 工具（config finder、imports auto） | 5 py | **pyspring-core** |
| `templates/` | 脚手架模板（`.template` 文件） | — | 归属 CLI 生成逻辑 |

---

## 二、核心层（pyspring-core）—— 始终加载

### 2.1 ioc/（智能 IoC 容器）

| 子模块 | 职责 | 关键类 | 状态 |
|--------|------|--------|------|
| `container/` | 容器核心、启动缓存 | `Container` | ✅ |
| `scanner/` | 两阶段扫描、替换检测 | `ComponentScanner` | ✅ |
| `resolver/` | 依赖解析 | — | ✅ |
| `registry/` | Bean 注册中心 | — | ✅ |
| `lifecycle/` | Initializer/Shutdown | `IInitializer`/`IShutdownHandler` | ✅ |
| `interfaces/` | SPI 接口 | `IManaged`/`IService` | ✅ |
| `proxy/` | 懒加载代理 | — | ✅ |
| `annotations/` | 装饰器 | `@Component`/`@Service`/`@ConditionalOnMissingBean`/`@Configuration`/`@Bean`/`@Primary`/`@Lazy`/`@Singleton`/`@Prototype` | ✅ |
| `config/` | IoC 配置加载 | `IOCConfigLoader` | ⚠️ 与 config 重复 |
| `context.py` | 全局单例访问点 | `ApplicationContext` | ⚠️ 需改造（单例） |
| `dependency.py` | 依赖工具 | — | ✅ |

### 2.2 aop/

- `core/models.py`：`@Aspect`/`@Before`/`@After`/`@Around`、`JoinPoint`/`Advice`。
- `proxy/`：`factory` + `wrapper` 动态代理。
- `facade.py`：`Aop` 统一入口。

### 2.3 log/

- `instance.py`：`logger` 单例。
- `providers/loguru/`：loguru 实现。
- `core/interface.py`：`ILogger` 接口（SPI）。

### 2.4 core/

- `abstracts/`：`ConfigSection`、异常基类（✅ 使用中）。
- `configuration/`：`ConfigLoader`/`AppSettings`（⚠️ 与 `config_manager.py` 重复）。
- `context/registry.py`：`ContextVar` 注册表。
- `services/system.py`：`SystemService`（⚠️ 曾为全局单例，重构中）。

### 2.5 config_manager.py（模块级）

- 三层配置管理（框架默认→用户→环境变量）。
- ⚠️ 与 `core/configuration`、`ioc/config/loader` 存在职责重复，需三选一统一。

---

## 三、Security Starter —— 可选引入

### 3.1 security/authentication（认证）

| 子模块 | 职责 | 关键 SPI 接口 |
|--------|------|--------------|
| `contracts/` | 接口与模型 | `IAuthProvider`/`ITokenService`/`IUserService`/`IPasswordEncoder`/`ILoginService` 等 |
| `providers/` | 认证源实现（密码/多字段登录） | 实现 `IAuthProvider` |
| `services/` | 认证服务 | 实现 `ILoginService` |
| `token/` | JWT 签发/校验 | 实现 `ITokenService`（⚠️ 可拆为独立 jwt-starter） |
| `factories/` | Provider 工厂 | — |
| `infrastructure/` | 基础设施 | — |
| `web/` | 认证相关 web 层 | — |
| `config/` | 认证配置 | — |

### 3.2 security/authorization（授权，RBAC）

| 子模块 | 职责 | 关键 SPI 接口 |
|--------|------|--------------|
| `contracts/` | 规则/角色/权限接口 | `IRule`/`IPermission`/`IRole` 等 |
| `rules/` | 规则引擎 | `IRuleEngine` |
| `decorators/` | `@require_authentication`/`@permission_dependency`/`@role_dependency` | — |

### 3.3 security/orm + core

- `orm/tables`：用户/角色/权限表。
- `core/config`、`core/database`：安全模块配置。

---

## 四、Repositories 层 —— DB / Cache Starter

### 4.1 db（数据库）

| 子模块 | 职责 | 关键接口 |
|--------|------|---------|
| `providers/` | postgres/mysql/sqlite 实现 | `IDBService`（各 provider 有独立接口） |
| `initializer/migration.py` | alembic 迁移 | — |
| `models/` | ORM 模型基类 | — |
| `service.py` | `DBManagerService` | `IDBManager` |
| `manager.py`/`factory.py` | 连接管理/工厂 | — |
| `base_service.py` | 通用 BaseService | — |
| `health.py` | DB 健康检查 | `IHealthIndicator` |
| `handler/` | 数据库事件 | — |

### 4.2 cache（缓存）

| 子模块 | 职责 | 关键接口 |
|--------|------|---------|
| `providers/` | redis/memory/memcached | `ICacheManager`（各 provider 有接口） |
| `service.py` | 缓存抽象 | `ICache` |

---

## 五、Web / Health —— 轻量 Starter

### 5.1 web/

- `core/`：统一响应格式。
- `handlers/base.py`、`handlers/exception.py`：全局异常处理（含 `IExceptionHandler` 接口）。

### 5.2 health/

- `manager.py`：`HealthManager`。
- `indicator/`：API/缓存/数据库健康指标（实现 `IHealthIndicator`）。

---

## 六、CLI（pyspring-cli）

| 模块 | 职责 |
|------|------|
| `main.py` | CLI 入口、动态注册命令 |
| `banner.py` | 启动横幅 |
| `commands/` | check/clean/dev/init/security/uv/meta |
| `core/` | 命令基础设施（base/loader）、parser、ui（console/help/report） |

> ⚠️ `core/ui/help.py:50` 存在 `\u279c` 编码崩溃 bug（GBK 控制台），需修复。

---

## 七、冗余与重复实现清单（供清理/重构）

| # | 类型 | 位置 | 建议 |
|---|------|------|------|
| 1 | 配置职责重复 | `config_manager.py` vs `core/configuration` vs `ioc/config/loader` | 三选一收敛 |
| 2 | 无意义代理 | `core/configuration/base.py` | 删除（见 REFACTORING_ANALYSIS） |
| 3 | 无用抽象 | `core/configuration/manager.py`（无实现） | 删除 |
| 4 | 全局单例 | `ioc/context.py` `_instance/_container` | 提供独立 `Container.create()` 工厂 |
| 5 | 功能重复 | `core/environment/loader.py` vs `ConfigLoader` | 合并 |
| 6 | 版本漂移 | 根 pyproject/CHANGELOG/setup.py | 统一到单一版本源 |
| 7 | 构建产物入库 | egg-info/build/.mypy_cache/data/app.db | 清理 + gitignore |

---

## 八、跨模块依赖关系（现状）

```
ioc ──> aop（代理）
ioc ──> log（logger）
ioc ──> core（异常/配置）
security ──> ioc, repositories(db), web
repositories ──> ioc, log
web ──> ioc, core
health ──> ioc, repositories(cache/db), web
```

> 目标：所有依赖方向收敛为 `starter → core`，禁止 starter 间互相依赖（除非显式 `requires`）。

---

## 九、下一步行动

1. 基于本清单，为每个模块确定"归属 starter + SPI 接口 + 默认实现"。
2. 标记每个类的"保留/拆分/删除/迁移"状态。
3. 产出每个 starter 的 `pyspring-autoconfigure.json` 声明。
