# PySpring 开发规范（DEV_GUIDELINES）

> 版本：v0.1
> 状态：草案（随架构重构同步落地）
> 适用范围：`packages/pyspring` 核心框架与 `packages/pyspring-cli` 的所有新增/重构代码

---

## 一、包划分规范

### 1.1 包类型与命名

PySpring 采用 **PEP 420 命名空间包** 组织多包架构：所有 starter 共享统一顶层命名空间 `pyspring`，发行包名（distribution name）与导入名（import name）解耦。

| 概念 | 规则 | 示例 |
|------|------|------|
| 发行包名 | `pyspring-<domain>`（安装/依赖引用） | `pyspring-security` |
| 导入命名空间 | `pyspring.<domain>`（代码 import） | `pyspring.security` |
| 组织级前缀 | 固定 `pyspring` | — |
| Starter 层级 | `pyspring.<domain>` | `pyspring.security` |
| Starter 内部 | `pyspring.<domain>.<sub>` | `pyspring.security.authentication` |

**三层语义结构**（类似 Spring 的 `org.springframework.security.web`）：

```
pyspring                ← 第一层：组织/产品命名空间（固定前缀，PEP 420）
├── pyspring.core       ← 第二层：Starter 级别
│   └── pyspring.core.ioc ← 第三层：Starter 内部层级
├── pyspring.web
├── pyspring.security
│   └── pyspring.security.authentication
├── pyspring.repositories
├── pyspring.health
└── pyspring.cli
```

**命名空间包要点**：
- 每个 starter 在 `src/pyspring/<domain>/` 提供自己的子包，安装后自动合并进 `pyspring` 命名空间。
- **禁止**：除根 scaffold 外的任何包在 `src/pyspring/` 下创建 `__init__.py`（否则会退化为普通包，导致命名空间无法合并跨包子模块）。
- **禁止**：在 `pyspring` 命名空间下使用与其它 starter 重名的子目录（如多个包各自提供 `core/`，会冲突）。

### 1.2 Starter 内部结构（强制）

```
pyspring-db-starter/
├── src/pyspring/db/              # 命名空间子包（无 pyspring/__init__.py）
│   ├── db_auto_config.py         # AutoConfiguration（@Configuration）
│   ├── spi/                      # 对外接口（SPI），本目录禁止业务逻辑
│   │   └── idb_manager.py
│   ├── impl/                     # 默认实现（@Service/@Component）
│   │   └── db_manager_service.py
│   ├── model/                    # 数据模型 / DTO（pydantic）
│   └── resources/
│       └── pyspring-autoconfigure.json  # 自动装配声明
└── pyproject.toml
```

### 1.3 目录职责约束

- `spi/`：**只允许接口/抽象基类/异常**，不允许具体实现。依赖方向：`impl → spi`。
- `impl/`：**只允许实现类**，对外通过 `spi` 暴露。
- `model/`：纯数据对象，不依赖业务逻辑。
- 禁止 `spi` 与 `impl` 互相 import。

---

## 二、命名规范

### 2.1 Python 模块/类

| 对象 | 规则 | 正确 | 错误 |
|------|------|------|------|
| 模块/文件 | snake_case | `jwt_token_service.py` | `JwtTokenService.py` |
| 类 | PascalCase | `class JwtTokenService` | `class jwt_token_service` |
| 函数/变量 | snake_case | `def get_token()` | `def getToken()` |
| 常量 | UPPER_SNAKE | `TOKEN_EXPIRE_SECONDS` | `tokenExpireSeconds` |

### 2.2 接口（SPI）

- 统一前缀 `I`：`IAuthProvider`、`ITokenService`、`IDBManager`。
- 接口文件放 `spi/`，文件名 = 类名去 `I` 转 snake_case：`IAuthProvider → auth_provider.py`。
- 抽象基类用 `Base` 前缀：`BaseConfigManager`（区别于 `I` 接口，用于提供部分默认逻辑的骨架）。

### 2.3 实现类

- 默认实现：语义具体化命名，避免无意义 `Impl` 后缀。
  - 正确：`JwtTokenService`、`MemoryCacheManager`
  - 避免：`TokenServiceImpl`
- 一个接口对应一个默认实现时，可用 `<Interface去I>Default`：`AuthProviderDefault`。

### 2.4 Bean 名称

- 默认由 scanner 从类名生成 snake_case（现有机制保留）。
- 如需显式命名，用 `@Component("custom_name")`。
- Bean 名必须在 starter 内唯一；跨 starter 可通过 `@Primary` 或 `@ConditionalOnMissingBean` 解决冲突。

---

## 三、接口（SPI）设计规范

### 3.1 接口声明三要素

1. **接口名**：`I` 前缀 + 业务动词/名词。
2. **职责单一**：一个接口只描述一个能力，避免上帝接口。
3. **默认实现 + 可替换**：接口必须有默认实现，且默认实现用 `@ConditionalOnMissingBean(接口)` 标注。

```python
# spi/auth_provider.py
class IAuthProvider(ABC):
    @abstractmethod
    def authenticate(self, credentials: dict) -> AuthResult: ...

# impl/auth_provider_default.py
@Service
@ConditionalOnMissingBean(IAuthProvider)
class AuthProviderDefault(IAuthProvider):
    def authenticate(self, credentials: dict) -> AuthResult:
        ...  # 默认实现
```

### 3.2 可替换规则

- 用户想替换默认实现：实现接口，并在 IoC 注册自己的 `@Service`。
- 用户想增强（不替换）：使用 AOP `@Around` 或装饰器模式包裹。
- **禁止**：修改 starter 内部默认实现类去适配单项目需求。

### 3.3 异常规范

- 接口方法应声明（或文档化）可能抛出的领域异常。
- 统一使用 `pyspring.core.abstracts.exceptions` 中的异常，禁止裸 `raise ValueError` 无上下文。

---

## 四、编码规范（check 源头修复依据）

### 4.1 编码与字符

- **所有文件 UTF-8 无 BOM**。
- **禁止非 ASCII 符号进入 print/日志**（Windows GBK 控制台会崩溃，见 `help.py` bug）。
  - 反例：`print(f"  \u279c {name}")` → 应替换为纯 ASCII 或使用日志系统。
- 中文字符串仅用于注释/文档，不用于运行时输出。

### 4.2 导入规范

- **强制显式子模块导入**，禁用包级 `__init__` 动态聚合导入（`imports-explicit` 规则）。
  - 反例：`from pyspring.security import IAuthProvider`（依赖 `__init__` 聚合）
  - 正确：`from pyspring.security.authentication.contracts.auth import IAuthProvider`
- 禁止函数内局部 import（除非确有循环依赖，需加注释说明）→ `imports-lift`。
- 禁止循环导入 → `imports-circular` 门禁。

### 4.3 类型注解

- 所有公共函数/方法必须有完整类型注解（返回类型 + 参数类型）。
- 启用 `basedpyright`，目标规则：
  - `reportMissingTypeStubs`、`reportUnknownParameterType`、`reportExplicitAny`（新代码禁止 `Any`）。
- 内部变量若类型复杂，使用 `TypeAlias` 而非裸 `Any`。

### 4.4 错误处理

- **禁止** `except: pass` 静默吞异常。
- 必须：`except Exception as e: logger.exception(...)` 或明确抛出。
- 所有异常需有上下文日志，便于线上排查。

### 4.5 禁止抑制（check 问题零容忍）

> 这是硬性约束。任何 check 检测出的问题必须**从源头修复**，禁止用抑制手段掩盖。

**禁止出现**：
- `# type: ignore` / `# pyright: ignore` / `# mypy: ignore`
- `# noqa` / `# flake8: noqa` / `# ruff: noqa` / `# pylint: disable`
- `except: pass` / `except Exception: pass` / `except: continue`
- `# pragma: no cover`
- 修改检查器配置调低严重级别 / 关闭规则来放行既有问题

**从源头修复方式**：
- 类型问题 → 补全注解，用 `TypeAlias`/`Generic`/`TypeGuard`/`assert isinstance` 收窄。
- 导入问题 → 重构依赖方向。
- 编码问题 → 转 UTF-8 并清理非 ASCII 输出。

### 4.6 日志规范

- 使用 `pyspring.log.instance.logger`（loguru）。
- 级别：DEBUG（细粒度）、INFO（生命周期）、WARNING（可恢复异常）、ERROR（需关注）。
- 日志消息**避免非 ASCII 符号**（修复 GBK 崩溃的根治）。

---

## 五、Starter 自动装配规范

### 5.1 声明文件

每个 starter 必须提供 `pyspring-autoconfigure.json`：

```json
{
  "name": "pyspring-db-starter",
  "version": "1.1.0",
  "autoConfiguration": "pyspring.db.db_auto_config.DBAutoConfiguration",
  "order": 10,
  "requires": ["pyspring-core"]
}
```

### 5.2 自动配置类约束

- 必须是 `@Configuration` 类，内含 `@Bean` 方法。
- 默认 Bean 必须标注 `@ConditionalOnMissingBean(接口)`。
- 禁止在自动配置类中做 I/O 副作用（连接池、日志初始化等应延迟到 Bean 实例化时）。

### 5.3 装配顺序

- `order` 越小越先加载（core=0，security=10，db=20...）。
- starter 间不得存在循环 `requires`。

---

## 六、命名空间包 pyproject 配置规范

每个 starter 的 `pyproject.toml` 必须使用命名空间包发现，并正确配置入口：

```toml
[tool.setuptools.packages.find]
where = ["src"]
include = ["pyspring.<domain>*"]   # 例如 "pyspring.security*"
namespaces = true                   # 关键：启用 PEP 420 命名空间包发现
exclude = ["*.tests", "*.tests.*", "tests.*", "tests"]

[tool.setuptools.package-data]
"pyspring.<domain>" = [             # 键名必须带引号（含点号，避免 TOML 嵌套解析）
    "py.typed",
]
```

**要点**：
- `include` 用 `pyspring.<domain>*`，**不用** `namespaces` 之外的其它方式（`find-namespace` 键在 setuptools pyproject 中无效，需用 `find` + `namespaces=true`）。
- `package-data` / `exclude-package-data` 的键名**必须加引号**（如 `"pyspring.security"`），否则 TOML 会把点号解析为嵌套表。
- entry-point（`[project.entry-points."pyspring.starters"]`）的模块路径指向 `pyspring.<domain>.autoconfigure...`。

---

## 七、测试规范

- 每个 starter 必须有对应的 `tests/`（单测 + 集成）。
- 新增/重构代码必须保证现有 `pyspring check` 通过，且不新增 warning。
- 测试隔离：优先使用 `Container.create()` 独立上下文，避免全局单例污染。

---

## 八、check 门禁（提交前强制）

```
uv run pyspring check --all
```

必须满足：
- 0 error
- 0 warning（不抑制，从源头修复）
- 无循环导入
- 无未解析引用
- 无编码问题

---

## 九、验收清单

- [ ] 新增代码符合本节命名/包划分/接口规范
- [ ] starter 声明了 `pyspring-autoconfigure.json`
- [ ] 默认实现标注 `@ConditionalOnMissingBean`
- [ ] `basedpyright` 无 error/warning
- [ ] `pyspring check --all` 通过
