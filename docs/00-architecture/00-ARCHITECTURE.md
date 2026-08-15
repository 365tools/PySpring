# PySpring 整体架构调整与模块化优化方案

> 文档版本：v0.1（草案）
> 编制日期：2026-08-15
> 编制背景：针对 PySpring 框架向 Spring Boot Starter 模式演进的整体架构规划

---

## 一、背景与目标

### 1.1 现状概述

PySpring 是一个构建于 FastAPI 之上的 Spring Boot 风格 Python 框架，当前采用 uv 工作区双包结构：

```
packages/
├── pyspring/          # 核心框架 v1.1.0
└── pyspring-cli/      # CLI 工具 v1.0.0（依赖 pyspring）
```

核心框架 `pyspring` 内部含 11 个功能包（`ioc`、`aop`、`core`、`security`、`repositories`、`web`、`health`、`log`、`utils`、`config`、`templates`），通过 `framework.yaml` 集中式硬编码扫描包列表，`ApplicationContext` 为全局单例。

### 1.2 业务目标

用户期望将当前"集中式、强耦合"的架构演进为 **Spring Boot Starter 模式**：

1. **即插即用（Pluggable）**：每个 starter 是独立组件，不引用不影响核心功能。
2. **内置默认实现（Auto-configuration）**：引入即自带默认 Bean。
3. **支持外部扩展（SPI / Conditional）**：用户可实现接口替换默认实现。
4. **模块化拆分**：按职责将现有大包拆分为可独立引入的 starter。

### 1.3 关键约束

> **本方案允许破坏性重构**：不保留任何向后兼容代码、兼容别名、兼容垫片（shim）或 deprecated 标记。所有重构遵循现代最佳实践，宁可改变公共 API，也不维护历史包袱。

- **无兼容层**：不保留旧的 `ApplicationContext.get_instance()` 单例、`Inject` 别名、旧导入路径等兼容代码。
- **纯最佳实践**：命名、包结构、装配机制、API 全部按当前最优设计重做。
- **破坏性变更一次到位**：被废弃的 API 直接删除，而非标记 deprecated 过渡。
- **检查问题零容忍（不抑制，从源头解决）**：`pyspring check` 检测出的任何 error / warning 都必须从源头修复，**禁止**任何形式的抑制手段（见 §5.4 专项约束）。
- **可逐步落地**：改造应分阶段，每阶段可独立验证（`pyspring check` + 测试）。

---

## 二、现状诊断（关键发现）

### 2.1 已具备的 Starter 化基础（可复用）

| 能力 | 现状 | 说明 |
|------|------|------|
| `@ConditionalOnMissingBean` | ✅ 已实现 | 支持默认实现可被用户覆盖，是 Starter 的核心机制 |
| `@Configuration` / `@Bean` | ✅ 已实现 | 支持配置类声明式注册 Bean |
| 类型映射 / 替换检测 | ✅ 已实现 | scanner 第三阶段自动检测替换关系 |
| `@ConditionalOnMissingBean` 自动标记组件 | ✅ 已实现 | 条件组件自动注册 |
| framework.yaml `auto_configuration.enabled` | ✅ 已声明 | 有字段但未真正驱动"按依赖装配" |

### 2.2 核心问题（需改造）

| # | 问题 | 影响 | 位置 |
|---|------|------|------|
| P0-1 | `framework.yaml` 集中式硬编码扫描 `security/repositories/web` | 无法即插即用；引入 starter 必须改配置文件 | `context.py` / `framework.yaml` |
| P0-2 | `ApplicationContext` 全局单例（类变量 `_instance/_container`） | 测试隔离差；多上下文场景受限 | `ioc/context.py`（**彻底删除单例，改独立容器工厂**） |
| P1-3 | 配置系统职责重复：`config_manager.py` vs `core/configuration` vs `ioc/config/loader` | 用户不知用哪个；维护成本高 | 多处 |
| P1-4 | 版本漂移：根 `pyproject` 1.1.0 / `CHANGELOG` 1.2.0 / `setup.py` 1.1.0b8 | 发布混乱 | 多处 |
| P1-5 | CLI `help.py` 用 `\u279c` 字符在 GBK 控制台崩溃 | `pyspring check` 无法运行 | `pyspring-cli/.../ui/help.py:50` |
| P2-6 | 构建产物/缓存目录被提交（egg-info、build、.mypy_cache、data/app.db） | 污染仓库 | 仓库根 |
| P2-7 | `core` 模块重构未完全收尾（security 等可能仍用旧 API） | 跨模块迁移风险 | 多模块 |

---

## 三、目标架构设计

### 3.1 分层架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (User Application)                  │
│   app/ (用户业务代码，通过 @Service/@Component 注册)           │
├─────────────────────────────────────────────────────────────┤
│              Starter 自动配置层 (Auto-Configuration)          │
│   ┌──────────────┬──────────────┬──────────────┬───────────┐ │
│   │ security     │ repositories │ web          │ health    │ │
│   │ -starter     │ -starter     │ -starter     │ -starter  │ │
│   │ -jwt-starter │ -cache-starter│             │           │ │
│   └──────┬───────┴──────┬───────┴──────┬───────┴───────────┘ │
│          ▼              ▼              ▼                     │
│   ┌─────────────────────────────────────────────────────┐   │
│   │       核心层 (Core)：ioc / aop / log / config        │   │
│   │   Container · Scanner · Resolver · Proxy            │   │
│   └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                     CLI 层 (pyspring-cli)                    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Starter 运行机制（核心设计）

借鉴 Spring Boot `spring.factories` / `AutoConfiguration.imports` 机制，PySpring 引入 **AutoConfiguration 声明式装配**：

```
每个 starter 包自带：
└── <starter>/
    ├── auto_config.py          # AutoConfiguration 配置类（@Configuration）
    ├── spi/                    # 接口定义（SPI，可被用户扩展）
    ├── impl/                   # 默认实现（@ConditionalOnMissingBean）
    ├── model/                  # 数据模型 / DTO
    └── resources/
        └── pyspring-autoconfigure.json   # 自动装配声明清单（新）
```

**自动装配声明清单**（替代硬编码扫描）：

```json
{
  "autoConfiguration": "pyspring.security.security_starter.SecurityAutoConfiguration",
  "enableOnMissingClass": [],
  "dependencies": [],
  "order": 0
}
```

**装配流程**：

1. `Container.initialize()` 彻底移除 `framework.yaml` 的 `scan_packages` 机制（直接删除，不留降级路径）。
2. 启动时通过 **entry point** 发现所有已安装的 starter。
3. 按 `pyspring-autoconfigure.json` 中的 `order` 排序，逐个执行 `auto_config` 配置类。
4. `@ConditionalOnMissingBean` 保证：用户若提供了同名接口实现，默认实现被替换。
5. 未引入的 starter 完全不扫描 → **即插即用，不引用不影响核心**。

### 3.3 装配方式对比

| 方式 | 说明 | 优点 | 缺点 | 选用 |
|------|------|------|------|------|
| A. Entry Point（`importlib.metadata.entry_points`） | PyPI 包注册 `pyspring.starters` | 标准、独立安装即自动发现 | 工作区本地开发需注册 | ✅ 推荐 |
| B. 声明清单扫描（`pyspring-autoconfigure.json`） | 包内资源文件 | 可控、可见 | 需约定扫描路径 | ✅ 组合使用 |

> `framework.yaml` 集中式扫描机制已**废弃删除**，不再提供任何兼容白名单。

---

## 四、Starter 模块拆分规划

### 4.1 拆分原则

- **单一职责**：一个 starter 解决一个横切关注点。
- **依赖最小化**：starter 尽量只依赖核心层，不依赖兄弟 starter。
- **默认可用**：每个 starter 引入后无需额外配置即有默认实现。
- **SPI 化**：对外暴露接口，内部实现可替换。

### 4.2 Starter 划分清单

| 目标 Starter | 来源（现有包） | 职责 | 默认实现 | SPI 接口 |
|--------------|---------------|------|---------|---------|
| `pyspring-core` | `ioc`/`aop`/`log`/`config` | 容器、AOP、日志、配置（**不可缺省，始终加载**） | Container/Scanner/Proxy | `IManaged` |
| `pyspring-security-starter` | `security/` | 认证（JWT）、授权（RBAC）、用户管理 | `DefaultAuthProvider`/`JWTService` | `IAuthProvider`/`ITokenService` |
| `pyspring-security-jwt-starter` | `security/authentication/token` | JWT 专属（可选，依赖 security 核心） | `JwtTokenService` | `ITokenService` |
| `pyspring-db-starter` | `repositories/db` | ORM、迁移、连接池（PG/MySQL/SQLite） | `DBManagerService` | `IDBManager` |
| `pyspring-cache-starter` | `repositories/cache` | Redis/Memory/Memcached 缓存 | `MemoryCache` | `ICacheManager` |
| `pyspring-web-starter` | `web/` | 统一响应、全局异常处理 | `ResponseBuilder`/`ExceptionHandler` | — |
| `pyspring-health-starter` | `health/` | 健康检查（API/缓存/DB） | `HealthManager` | `IHealthIndicator` |

> **说明**：`pyspring-core` 始终随框架加载（对应 Spring 的 `spring-core`），其余为可选 starter。

### 4.3 依赖关系

```
pyspring-cli
   └── pyspring-core (始终)
          ├── pyspring-security-starter ── pyspring-security-jwt-starter
          ├── pyspring-db-starter
          ├── pyspring-cache-starter
          └── pyspring-web-starter
                 └── pyspring-health-starter
```

---

## 五、开发规范（包划分 / 命名 / 接口）

> 详细规范见独立文档 `08-architecture/02-DEV_GUIDELINES.md`，本节为摘要。

### 5.1 包命名规范

| 层级 | 命名规则 | 示例 |
|------|---------|------|
| Starter 包 | `<domain>-starter` | `pyspring-db-starter` |
| 内部 SPI 包 | `spi/` | `security_starter/spi/` |
| 内部实现包 | `impl/` | `security_starter/impl/` |
| 自动配置包 | `xxx_auto_config.py` | `db_auto_config.py` |
| Python 模块名 | snake_case | `jwt_token_service.py` |

### 5.2 接口命名规范

- 接口（SPI）统一前缀 `I`：`IAuthProvider`、`ITokenService`、`IDBManager`。
- 接口文件集中放 `spi/`，实现放 `impl/`。
- 默认实现类名 = 功能 + `Impl` 或具体化：`JwtTokenService`（不叫 `TokenServiceImpl` 若语义具体）。
- 抽象基类用 `Base` 前缀：`BaseConfigManager`。

### 5.3 编码规范（check 源头修复）

- 全 UTF-8，禁用非 ASCII 控制字符（修复 `\u279c` 问题）。
- 所有导入显式子模块，避免包级 `__init__` 动态导入导致循环依赖（`imports-explicit`）。
- 类型注解完整，启用 `basedpyright`（`reportExplicitAny` 等规则）。
- 无 `except: pass` 吞异常，必须记录或抛出。

### 5.4 专项约束：检查问题零容忍（不抑制，从源头解决）

> 这是贯穿整个重构的**硬性约束**，非可选建议。任何 `pyspring check` 检测出的问题，都必须通过修正代码本身解决，**不得**用任何抑制手段掩盖。

**明确禁止的抑制手段**（代码中出现即视为违规，check 门禁不通过）：

| 类别 | 禁止写法 | 从源头修复方式 |
|------|---------|--------------|
| 类型抑制 | `# type: ignore`、`# pyright: ignore`、`# mypy: ignore` | 补齐类型注解、用 `TypeAlias`/`Generic`/`cast`（仅在语义正确时） |
| 静态检查抑制 | `# noqa`、`# flake8: noqa`、`# ruff: noqa`、`# pylint: disable` | 修代码使其符合规范 |
| 异常吞没 | `except: pass`、`except Exception: pass`、`except: continue` | 记录日志（`logger.exception`）或明确处理/重抛 |
| 覆盖忽略 | `# pragma: no cover` | 补测试覆盖，而非跳过 |
| 宽松类型 | `: Any = ...`、`# type: ignore[no-any-return]` | 用具体类型或受控 `TypeVar`/`Generic` |

**禁止的动态抑制**：
- 关闭检查器严重级别以"通过"（如 `basedpyright` 的 `--severity` 调低不作为规避手段）。
- 修改 `pyproject.toml` 将规则改为 warning/off 来放行既有问题。
- 用 `getattr(obj, 'x', None)` 滥用兜底掩盖属性缺失（应为明确接口）。

**正确姿势**：
- 类型信息不完整 → 补全注解，而非忽略。
- 导入循环 → 重构依赖方向，而非局部 import 兜底注释。
- 编码问题 → 转 UTF-8 并清理非 ASCII 输出，而非换输出流绕过。
- 无法静态确定 → 用 `TypeGuard`/`assert isinstance` 显式收窄，而非 `Any` 放行。

**门禁要求**：每次提交前 `pyspring check --all` 必须 **0 error / 0 warning**，且全项目禁止出现上表任何抑制记号。

---

## 六、实施路线（分阶段）

### 阶段 0：健康基线（先修复，保证可验证）
- [ ] 修复 CLI `help.py` 编码崩溃（P1-5），使 `pyspring check` 可运行。
- [ ] 运行 `pyspring check --all`，记录全部 error/warning 基线。
- [ ] 统一版本号（P1-4）。

### 阶段 1：清理冗余（任务 1）
- [ ] 清理提交的构建产物（egg-info/build）、缓存目录、测试数据库。
- [ ] 删除已知冗余文件（`core/REFACTORING_ANALYSIS.md` 中 P0 清单，如 `configuration/base.py`、`manager.py`）。

### 阶段 2：梳理业务实现（任务 2）
- [ ] 产出模块清单文档，标注每个包/类的职责、依赖、SPI 接口。
- [ ] 识别跨模块旧 API 残留（`system_service.get()` 等），建立迁移清单。

### 阶段 3：Starter 化核心改造（任务 3）
- [ ] 新增 AutoConfiguration 装配机制（`pyspring-autoconfigure.json` + 装配器）。
- [ ] 删除 `framework.yaml` 集中式扫描，改为 starter 声明式装配（**彻底删除，不留降级**）。
- [ ] 拆分 `security` / `repositories` / `web` / `health` 为独立 starter。

### 阶段 4：规范落地（任务 4）
- [ ] 发布 `DEV_GUIDELINES.md`，按新规范统一包划分、命名、接口。
- [ ] 同步重构 `core` 残留（单例、配置重复）。

### 阶段 5：Check 清零（任务 5）
- [ ] 运行 `pyspring check --all` 直至 0 error / 0 warning，全部从源头修复，不抑制。

---

## 七、风险与决策

> 本重构允许破坏性变更，故不存在"兼容性回退"风险。以下仅关注**设计正确性与演进安全**。

| 风险 | 决策 / 缓解措施 |
|------|---------|
| 全局单例 `ApplicationContext` 残留 | 彻底移除类变量单例，改为 `Container.create()` 独立上下文工厂；`inject` 等便利 API 直接基于容器实例，不再走全局状态 |
| Starter 自动发现失败 | Entry Point + 声明清单双机制；安装即发现，无白名单回退 |
| 循环依赖 | 严格依赖方向（starter→core），`imports-circular` 检查门禁 |
| 破坏性重构引入回归 | 阶段化实施 + 每阶段 `pyspring check --all` + 完整测试门禁 |
| 被弃用 API 残留 | 直接删除而非标记 deprecated，杜绝历史包袱蔓延 |

---

## 八、交付物清单

- [ ] `docs/08-architecture/00-ARCHITECTURE.md`（本文档）
- [ ] `docs/08-architecture/01-MODULE_INVENTORY.md`（业务实现梳理）
- [ ] `docs/08-architecture/02-DEV_GUIDELINES.md`（开发规范）
- [ ] `docs/08-architecture/03-CLEANUP_PLAN.md`（清理方案）
- [ ] `docs/08-architecture/04-CHECK_FIX_PLAN.md`（check 修复计划）
