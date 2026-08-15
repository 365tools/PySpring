# 更新日志

PySpring 的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [0.0.1] - 2026-08-15

### 🔄 版本回归

**项目版本整体回归至 `v0.0.1`**，作为新一轮架构重构（模块化 Starter 化）的起点。

#### 变更
- ✅ 核心框架 `pyspring` 版本：`1.1.0` → `0.0.1`
- ✅ CLI 工具 `pyspring-cli` 版本：`1.0.0` → `0.0.1`
- ✅ workspace 版本：`1.1.0` → `0.0.1`
- ✅ 同步更新依赖引用、`setup.py`、`_version.py` 回退版本

> 说明：此次回归为**破坏性重构的前置动作**，历史版本记录保留在下方。

---

## [1.2.0] - 2026-01-29

### 🎯 架构重构：CLI独立 + 分层导入

#### 重大变更

**CLI工具迁移到独立包**
- ✅ 创建独立的 `pyspring-cli` 包
- ✅ 生产环境无需安装CLI，减少依赖和包体积
- ✅ 开发环境推荐安装：`pip install pyspring[dev]`
- ✅ 独立安装CLI：`pip install pyspring-cli`

**分层显式导入重构**
- ✅ 核心模块显式导入，启动速度提升 **66%**（从2.5秒降至0.85秒）
- ✅ 可选模块延迟加载，内存占用减少 **44%**（从80MB降至45MB）
- ✅ 实现 `__getattr__` 延迟加载机制
- ✅ 改进错误处理，区分核心和可选模块

#### 新增

**pyspring-cli 独立包**
```bash
# 安装独立CLI工具
pip install pyspring-cli

# 或安装开发环境（包含CLI）
pip install pyspring[dev]

# 使用
pyspring init my-project
pyspring dev init-sync
pyspring check --all
```

**向后兼容层**
```python
# 旧代码仍可用（会发出 DeprecationWarning）
from pyspring.cli.main import main  # ⚠️ 已废弃

# 推荐新方式
pip install pyspring-cli
pyspring init  # 命令行使用
```

#### 改进

**性能优化**
- ✅ 启动时间：2.5秒 → 0.85秒（提升66%）
- ✅ 内存占用：80MB → 45MB（减少44%）
- ✅ 加载模块数：350+ → 187（减少47%）

**导入系统优化**
```python
# pyspring/__init__.py - 新的分层导入
from pyspring import ApplicationContext, Component  # 核心模块
from pyspring import security  # 延迟加载（首次访问时导入）
```

**错误处理改进**
```python
# utils/imports/auto.py
- 区分核心模块和可选模块
- 核心模块导入失败抛出异常
- 可选模块失败时发出警告（warn_on_error=True）
- 语法错误总是报告
```

#### 废弃

**pyspring.cli 模块**
- ⚠️ `pyspring.cli` 已废弃，将在 v2.0.0 移除
- ✅ 保留兼容层，自动重定向到 `pyspring-cli`
- ✅ 发出 `DeprecationWarning` 提示用户升级

#### 移除

**CLI入口点**
- ❌ 从主包的 `pyproject.toml` 移除 `[project.scripts]`
- ✅ CLI入口点迁移到 `pyspring-cli` 包

#### 迁移指南

**用户无需修改代码**
```python
# 框架API - 100%兼容，无需修改
from pyspring import ApplicationContext, Component
from pyspring.security import SecurityManager

# 正常使用
ctx = ApplicationContext.initialize()
```

**CLI工具需要独立安装**
```bash
# 旧方式（不再可用）
pip install pyspring  # CLI不再自动可用

# 新方式（推荐）
pip install pyspring[dev]  # 开发环境
# 或
pip install pyspring-cli   # 仅CLI工具
```

**测试验证**
```python
# 测试1: 框架导入性能
python test_import_performance.py
# 结果：✓ 0.846秒（提升66%）

# 测试2: CLI独立性
python test_cli_package.py
# 结果：✓ CLI未自动加载，需独立安装

# 测试3: 向后兼容
from pyspring.cli import main  # ⚠️ DeprecationWarning
# 结果：✓ 如安装pyspring-cli则正常工作
```

#### 文档更新

- 📝 新增 [ARCHITECTURE_REFACTORING_COMPLETE.md](ARCHITECTURE_REFACTORING_COMPLETE.md)
- 📝 新增 [IMPORT_OPTIMIZATION_PLAN.md](IMPORT_OPTIMIZATION_PLAN.md)
- 📝 新增 [CLEANUP_PLAN.md](CLEANUP_PLAN.md)
- 📝 更新 [PUBLISHING_GUIDE.md](docs/PUBLISHING_GUIDE.md)
- 📝 更新 [PUBLISH_CHECKLIST.md](docs/PUBLISH_CHECKLIST.md)

#### 技术细节

**包结构变化**
```
pyspring/                    # 核心框架
├── pyproject.toml          # 移除CLI入口点
└── src/pyspring/
    ├── __init__.py         # 重构为分层导入
    ├── cli/                # 兼容层（废弃）
    └── utils/imports/auto.py  # 改进错误处理

pyspring-cli/                # CLI独立包（新增）
├── pyproject.toml
└── src/pyspring_cli/
    ├── main.py             # CLI入口
    └── commands/           # 所有CLI命令
```

**依赖关系**
```toml
# pyspring/pyproject.toml
[project.optional-dependencies]
dev = [
    "pyspring-cli>=1.0.0",  # CLI作为可选依赖
    ...
]

# pyspring-cli/pyproject.toml
dependencies = [
    "pyspring>=1.1.0",      # CLI依赖核心框架
]
```

---

## [1.1.0b25] - 2026-01-24

### 🎯 Critical Fix: @ConditionalOnMissingBean 替换机制重构（正确方案）

#### 设计理念

**框架先注册，用户后替换** - 这是更合理的设计，因为：

1. ✅ 用户的实现依赖框架的底层服务（DBManagerService, IPasswordEncoder 等）
2. ✅ 框架服务必须先注册，才能注入到用户的 Bean 方法参数中
3. ✅ 用户的 Bean 可以安全地替换掉框架的 `@ConditionalOnMissingBean` Bean

#### 实现方案

**1. 扫描顺序恢复为：框架包 → 用户包**

```python
# 正确顺序（考虑依赖关系）
all_packages = [框架包...] + [用户包...]

# 原因：
# - 框架包先扫描 → DBManagerService, IPasswordEncoder 等底层服务先注册
# - 用户包后扫描 → CustomRegisterService 的依赖可以正确注入
```

**2. ServiceDefinition 添加 `is_conditional` 字段**

```python
@dataclass
class ServiceDefinition:
  is_conditional: bool = False  # 标记是否是 @ConditionalOnMissingBean
```

**3. 注册时传递条件标记**

```python
definition = ServiceDefinition(
  name=bean_name,
  is_bean=True,
  is_conditional=bool(conditional_type)  # 👈 保存条件信息
)
```

**4. Registry 支持替换逻辑**

```python
if existing.is_conditional and definition.is_bean:
    # 旧的是条件Bean，新的是用户Bean → 允许替换
    logger.debug(f"🔄 用户Bean替换条件Bean: '{name}'")
    logger.debug(f"   旧实现: {existing.config_class}.{existing.bean_method}() [框架默认]")
    logger.debug(f"   新实现: {definition.config_class}.{definition.bean_method}() [用户自定义]")
    pass  # 继续注册，覆盖旧的
```

#### 工作流程

```
1️⃣ 框架包先扫描（pyspring.security）
   ├─ 注册底层服务：DBManagerService, IPasswordEncoder ✅
   ├─ 注册默认实现：default_register_service() -> IRegisterService
   │  └─ 标记：is_conditional=True (因为有 @ConditionalOnMissingBean)
   └─ 容器状态：i_register_service → DefaultRegisterService [可被替换]

2️⃣ 用户包后扫描（app）
   ├─ 依赖注入成功：DBManagerService, IPasswordEncoder 已存在 ✅
   ├─ 注册用户实现：custom_register_service() -> IRegisterService
   │  ├─ 检测到重复：i_register_service 已存在
   │  ├─ 检查旧Bean：existing.is_conditional=True ✅
   │  ├─ 检查新Bean：definition.is_bean=True ✅
   │  └─ 允许替换：覆盖旧的 DefaultRegisterService
   └─ 容器状态：i_register_service → CustomRegisterService [用户自定义生效]
```

#### Debug 日志输出

```
🔄 用户Bean替换条件Bean: 'i_register_service' (IRegisterService → IRegisterService)
   旧实现: AuthenticationConfiguration.default_register_service() [框架默认]
   新实现: CustomRegisterServiceConfiguration.custom_register_service() [用户自定义]
```

#### 对比之前的错误方案

| 方案          | 扫描顺序      | 依赖注入          | 替换机制                         | 结果           |
|-------------|-----------|---------------|------------------------------|--------------|
| ❌ v1.1.0b24 | 用户先 → 框架后 | ❌ 失败（底层服务不存在） | @ConditionalOnMissingBean 跳过 | 用户Bean依赖注入报错 |
| ✅ v1.1.0b25 | 框架先 → 用户后 | ✅ 成功（底层服务已注册） | Registry 允许替换                | 用户Bean正常替换   |

---

## [1.1.0b24] - 2026-01-24 [REVERTED]

### 🎯 Critical Fix: @ConditionalOnMissingBean 机制修复

#### 问题描述

`@ConditionalOnMissingBean` 机制无法正常工作，用户的自定义实现无法替换框架的默认实现。

#### 根本原因

**扫描顺序错误**：框架包先扫描 → 用户包后扫描

```python
# 错误的顺序
all_packages = [框架包...] + [用户包...]
```

导致流程：

1. 框架的 `@Bean() @ConditionalOnMissingBean(IRegisterService)` 先注册
2. 此时容器中没有 `IRegisterService` → 注册框架默认实现
3. 用户的 `@Bean() -> IRegisterService` 后注册
4. 名称冲突 → 抛出 `ValueError: 服务 'i_register_service' 已注册`

#### 修复方案

**调整扫描顺序**：用户包先扫描 → 框架包后扫描

```python
# 正确的顺序
all_packages = [用户包...] + [框架包...]
```

正确流程：

1. ✅ 用户的 `@Bean() -> IRegisterService` 先注册
2. ✅ 框架的 `@ConditionalOnMissingBean(IRegisterService)` 检查
3. ✅ 发现已存在 → 跳过框架默认实现
4. ✅ 用户的自定义实现生效！

#### 影响范围

- ✅ 修复 `IRegisterService` 用户自定义实现
- ✅ 修复所有 `@ConditionalOnMissingBean` 标记的服务
- ✅ 恢复 Spring Boot "约定优于配置" 设计模式

---

## [1.1.0b23] - 2026-01-24

### 🐛 Bug Fixes

- **修复服务重复注册问题** (Critical)
  - 问题：多次调用 `Container.scan()` 时，配置类的 Bean 方法会被重复注册，导致 `ValueError: 服务 'xxx' 已注册`
  - 原因：容器没有追踪已处理的配置类，导致同一个 `@Configuration` 类的 `@Bean()` 方法被多次注册
  - 修复：在 Container 中添加 `_registered_component_types: Set[type]` 集合，追踪已处理的配置类
  - 影响：现在可以安全地多次调用 `scan()` 而不会导致重复注册错误

### 📝 Technical Details

```python
# Before (会重复注册):
for cls, metadata in components.items():
    if metadata.is_configuration:
        self._register_beans(metadata)  # 每次 scan() 都会注册

# After (防止重复):
for cls, metadata in components.items():
    if metadata.is_configuration:
        if cls not in self._registered_component_types:
            self._register_beans(metadata)
            self._registered_component_types.add(cls)  # 标记已处理
        else:
            logger.debug(f"⏩ 跳过已注册的配置类: {metadata.name}")
```

---

## [1.1.0b22] - 2026-01-24

### 🐛 Bug Fixes

* **配置文件打包问题**:
  - 修复框架配置文件未被包含在安装包中的问题
  - 更新 MANIFEST.in，添加 `recursive-include src/pyspring/config *.yaml`
  - 确保 framework.yaml 和 defaults/*.yaml 被正确打包

* **服务重复注册问题**:
  - 修复框架包被重复扫描导致的服务重复注册错误
  - 优化 ApplicationContext.initialize() 的包扫描逻辑
  - 自动去重：当用户在 base_packages 中指定框架包时自动过滤
  - 添加警告提示：框架包会自动扫描，无需手动配置

### 改进 (Improvements)

* **扫描逻辑优化**:
  - 合并框架包和用户包，一次性扫描（避免多次扫描）
  - 添加重复包检测和警告机制
  - 更清晰的日志输出

### 技术细节 (Technical Details)

**修复前的问题：**

```python
# 框架包被扫描
instance._container.scan(['pyspring.security', 'pyspring.repositories'])

# 用户包也包含框架包，导致重复扫描
instance._container.scan(['pyspring.security', 'app'])  # ❌ 重复！
```

**修复后的逻辑：**

```python
# 合并并去重
framework_packages = ['pyspring.security', 'pyspring.repositories']
user_packages = ['pyspring.security', 'app']

# 去重后只扫描一次
all_packages = ['pyspring.security', 'pyspring.repositories', 'app']
instance._container.scan(all_packages)  # ✅ 无重复
```

---

## [1.1.0b21] - 2026-01-24

### 🎯 重大重构 - 配置架构优化 (Major Refactoring - Configuration Architecture)

**问题诊断：**

- 配置文件职责不清：`config/` 目录用途模糊（框架测试？用户项目？）
- 配置层次混乱：框架配置、框架默认值、用户配置混在一起
- 无配置覆盖机制：用户无法优雅地覆盖框架默认值
- 用户体验差：不知道哪些配置可以改，哪些不能改

**解决方案：三层配置架构** ⭐

1. **框架级配置** (`src/pyspring/config/`)
  - `framework.yaml` - 框架核心行为（如自动扫描的包列表）
  - 🚫 用户不可编辑，打包到框架内部

2. **框架默认值** (`src/pyspring/config/defaults/`)
  - `security.yaml` - 安全模块默认配置
  - `database.yaml` - 数据库模块默认配置
  - `logging.yaml` - 日志模块默认配置
  - ✅ 用户可通过项目配置覆盖

3. **用户项目配置** (`<project>/config/`)
  - 用户自由编辑，覆盖框架默认值
  - 支持环境变量覆盖（最高优先级）

**配置加载顺序：** `框架默认值 < 用户配置 < 环境变量`

### 新增 (Added)

* **ConfigManager 配置管理器** (`src/pyspring/config_manager.py`):
  - 统一的配置加载接口
  - 自动深度合并框架默认值和用户配置
  - 支持环境变量覆盖（JWT_SECRET_KEY, POSTGRES_PASSWORD 等）
  - 配置缓存机制，提高性能
  - 便捷函数：`load_security_config()`, `load_database_config()`, `load_logging_config()`

* **框架默认配置目录** (`src/pyspring/config/defaults/`):
  - `security.yaml` - 认证、授权、密码策略、会话管理等默认配置
  - `database.yaml` - 缓存（Redis/Memory）、数据库（PostgreSQL/SQLite/MySQL）、ORM 等默认配置
  - `logging.yaml` - 控制台日志、文件日志、高级配置等默认值

* **配置架构分析文档** (`docs/CONFIG_ARCHITECTURE_ANALYSIS.md`):
  - 详细的问题诊断和解决方案
  - 三层配置架构原理和实施步骤
  - 配置覆盖规则和最佳实践

### 改进 (Improvements)

* **目录结构优化**:
  - 将 `config/` 移动到 `tests/config/`，明确其为测试配置
  - 创建 `src/pyspring/config/defaults/` 存放框架默认值
  - 分离框架级配置和用户级配置

* **配置加载器重构**:
  - `SecurityConfigManager` 现在使用 `ConfigManager` 加载配置
  - `RepositoriesConfigManager` 现在使用 `ConfigManager` 加载配置
  - 移除重复的配置加载逻辑
  - 统一的配置合并和环境变量覆盖机制

* **模板配置文件更新**:
  - 所有模板配置文件增加清晰的注释说明
  - 标明配置层级（框架级/用户级）和编辑权限
  - 提供配置覆盖示例

### 用户体验改进 (User Experience)

**改进前（混乱）：**

```yaml
# config/security.yaml - 不知道这是什么，能不能改？
authentication:
  jwt:
    access_token_expire: 3600
  # ... 很多配置，哪些能改？
```

**改进后（清晰）：**

```yaml
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PySpring 用户项目配置 - 安全配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✅ 此文件由用户维护，可自由编辑
# 🔄 此文件中的配置会覆盖框架默认值
# 💡 只需配置您要覆盖的值，未配置的项将使用框架默认值
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 示例：覆盖 JWT 配置
authentication:
  jwt:
    access_token_expire: 7200  # 覆盖框架默认的 3600 秒
```

### 技术细节 (Technical Details)

**配置文件映射关系：**

| 原路径       | 新路径                                   | 用途     |
|-----------|---------------------------------------|--------|
| `config/` | `tests/config/`                       | 测试配置   |
| -         | `src/pyspring/config/framework.yaml`  | 框架核心配置 |
| -         | `src/pyspring/config/defaults/*.yaml` | 框架默认值  |
| -         | `<project>/config/*.yaml`             | 用户项目配置 |

**配置覆盖示例：**

```python
# 框架默认值 (src/pyspring/config/defaults/security.yaml)
authentication:
  jwt:
    access_token_expire: 3600  # 1小时

# 用户配置 (config/security.yaml)
authentication:
  jwt:
    access_token_expire: 7200  # 覆盖为2小时
    
# 环境变量 (最高优先级)
# JWT_SECRET_KEY=your_secret → 覆盖 secret_key
```

---

## [1.1.0b20] - 2026-01-24

### 重大改进 (Major Improvements)

* **框架级包自动加载机制** ⭐:
  * ApplicationContext 现在自动优先扫描框架级包
  * 自动加载 `pyspring.security`（安全模块）和 `pyspring.repositories`（数据库仓储）
  * 用户无需在配置文件或代码中手动指定框架包的扫描顺序
  * 真正实现"约定优于配置"，简化用户配置

* **框架配置外部化** ⭐:
  * 创建 `src/pyspring/config/framework.yaml` 框架级配置文件
  * 框架包列表现在从配置文件读取，而非硬编码
  * 支持优雅降级：配置文件缺失时自动使用默认值
  * 提高框架的可维护性和灵活性

### 改进 (Improvements)

* **简化示例项目配置**:
  * 移除 container.yaml 中手动配置 `pyspring.security` 的要求
  * 移除 main.py 中手动指定框架包的代码
  * 用户只需配置自己的应用包（`app`）即可
  * 框架自动处理依赖加载顺序

* **优化日志输出**:
  * 添加框架级包扫描的 DEBUG 日志
  * 明确显示扫描顺序（框架包 → 用户包）

### 文档 (Documentation)

* 更新 ApplicationContext.initialize() 文档说明
* 更新示例项目注释，说明框架自动加载机制
* 更新 CustomRegisterServiceConfiguration 注释
* 新增 framework.yaml 配置文件说明（框架开发者使用）

### 技术细节

**之前的问题：**

```python
# 用户需要手动配置扫描顺序
ApplicationContext.initialize(
    base_packages=['pyspring.security', 'app']  # 顺序很重要！
)
```

**现在的解决方案：**

```python
# 框架自动处理，用户只需配置自己的包
ApplicationContext.initialize(
    base_packages=['app']  # 简单！
)

# 框架内部自动：
# 1. 先扫描 pyspring.security、pyspring.repositories
# 2. 然后扫描用户的 app 包
```

---

## [1.1.0b19] - 2026-01-24

### 重大变更 (Breaking Changes)

* **示例项目全面集成框架安全模块**:
  * 将示例项目从自定义认证改为使用框架的完整安全系统
  * User 模型现在继承 `BaseUserTable`（框架提供的用户表基类）
  * API 端点使用框架的 `ILoginService` 和 `IRegisterService`
  * DatabaseInitializer 使用框架的 `IRegisterService` 进行用户初始化

### 新增 (Features)

* **用户自定义扩展示例** ⭐:
  * 新增 `CustomRegisterService` 展示如何通过 `@ConditionalOnMissingBean` 机制自定义扩展
  * 展示如何实现框架接口并通过 `@Bean()` 注册
  * 框架自动检测用户实现，跳过默认实现
  * 完整的自定义字段处理、验证规则、后置操作示例
* **安全模块用户自定义指南**:
  * 新增 `SECURITY_USER_CUSTOMIZATION_GUIDE.md` 详细文档
  * 展示 `@ConditionalOnMissingBean` 机制的工作原理
  * 包含完整的自定义示例和最佳实践
  * 可自定义组件清单（IRegisterService、IPasswordEncoder、ILoginProvider 等）
* **项目功能覆盖总结**:
  * 新增 `EXAMPLE_PROJECT_COVERAGE.md` 总结文档
  * 详细列出示例项目覆盖的所有框架功能
  * 功能分类统计和学习路径建议

### 改进 (Improvements)

* **用户模型 (User)**:
  * 继承框架的 `BaseUserTable` 而不是自定义 Base
  * 自动获得框架提供的审计字段（creator, created_time 等）
  * 自动获得软删除支持（deleted 字段）
  * 添加详细注释说明框架提供的字段和自定义方式
* **数据库初始化器 (DatabaseInitializer)**:
  * 使用框架的 `IRegisterService` 替代自定义 AuthService
  * 自动处理数据库会话管理（无需手动 AsyncSessionLocal）
  * 支持角色分配（创建 ADMIN 角色）
  * 自动密码加密
  * 完整的事务安全保障
* **认证 API (auth.py)**:
  * 使用框架的 `ILoginService` 处理登录
  * 使用框架的 `IRegisterService` 处理注册
  * 返回完整的用户信息、角色、Token（包括 refreshToken）
  * 支持多种认证方式（框架自动扩展）
* **数据库会话 (session.py)**:
  * 添加与框架 DBManagerService 的集成说明
  * 使用框架的 Base 创建数据库表（包括角色权限表）
  * 添加详细注释说明框架和示例项目的会话管理
* **自定义认证服务 (auth_service.py)**:
  * 标记为"可选扩展示例"
  * 添加详细警告说明何时应使用框架服务
  * 添加框架 vs 自定义的对比表格
  * 保留作为学习目的和特殊业务需求的参考

### 文档 (Documentation)

* **安全集成指南** (`SECURITY_INTEGRATION_GUIDE.md`):
  * 框架安全架构概述
  * 快速开始指南（用户模型、注册、登录、初始化）
  * 自定义配置示例（用户表、密码加密、登录方式）
  * 框架 vs 自定义对比表
  * 数据库表结构说明
  * 常见问题解答
  * 最佳实践建议
  * 完整的 cURL 示例

### 修复 (Bug Fixes)

* **依赖注入顺序问题**:
  * 修复 CustomRegisterService 无法解析依赖的问题
  * 确保框架的安全模块（pyspring.security）先被扫描
  * 在 container.yaml 和 main.py 中添加 pyspring.security 到扫描包列表
  * 添加详细注释说明依赖注入的前提条件
* **数据库会话管理问题**:
  * 修复 DatabaseInitializer 中"数据库会话未初始化"错误
  * 通过使用框架的 IRegisterService 自动处理会话生命周期
  * 无需手动创建 User 对象和管理事务

### 其他说明

* **推荐架构**:
  * ✅ 使用框架的 `ILoginService`/`IRegisterService`（自动会话管理、角色权限、Token管理）
  * ✅ 继承 `BaseUserTable`（与框架完美集成）
  * ✅ 通过 `SecurityEntityConfiguration` 配置自定义实体映射
  * ✅ 实现 `ILoginProvider` 扩展认证方式（OAuth2、LDAP、短信等）
  * ❌ 避免自己实现认证逻辑（除非有特殊需求）

---

## [1.0.1] - 2026-01-13

### 新增 (Features)

* **AOP 切面编程支持**:
    * 新增 `pyspring.aop` 模块，支持 `@Before`, `@After`, `@Around` 增强。
    * 基于运行时期动态代理模式，实现业务与横切关注点（日志、事务）解耦。
    * 支持基于正则表达式的 Pointcut 匹配。
* **IoC 容器增强**:
    * **启动性能优化**: 引入 `.pyspring_cache` 文件指纹缓存，智能跳过未变更模块的重复扫描，显著提升启动速度。
    * **循环依赖检测**: 引入 DFS 算法构建依赖图，在启动阶段自动检测并拦截循环引用（Circular Dependency），避免运行时栈溢出。
    * **类型安全**: 全面转向 `Protocol` + `@runtime_checkable` 接口约束，移除已废弃的"魔术后缀"（Suffix-based）扫描策略，强化基于类型和 `@Component` 装饰器的注册机制。

### 优化 (Improvements)

* **CLI 架构重构**:
    * 重构 `pyspring` 命令行工具，采用模块化设计 (`src/pyspring/cli/commands`)。
    * 移除 `init` 命令中的"上帝对象"，拆分为 `core`, `templates`, `keygen` 独立模块。
    * 引入统一的 UI 工具库 (`src/pyspring/cli/core/ui.py`)，标准化终端输出风格。
    * 改为基于 `argparse` Subparsers 的标准架构，提升扩展性。
* **Service 单例语义明确化**: 明确所有 Service 默认为 Singleton（单例），并通过 `ContextVars` 解决 Web 并发场景下的上下文隔离问题。
* **文档重构**: 全面更新项目文档，新增 AOP 指南、IoC 深度解析章节。
* **代码规范**: 移除 `pyspring.system` 旧模块，修正 `src` 与 `tests` 导入路径不一致问题。

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
