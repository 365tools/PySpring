# PySpring 测试总结

## 目录结构

PySpring 的测试按 **Starter 模块** 拆分，与命名空间包架构一一对应：

```
tests/
├── conftest.py                    # Pytest 配置（禁用 loguru 异步日志、清理 IoC 容器）
├── core/                          # pyspring-core 测试
│   ├── test_ioc_container.py      # IoC 容器（扫描、按类型获取 Bean）
│   └── test_autoconfigure.py      # AutoConfiguration 装配（entry point 发现、排序）
├── health/                        # pyspring-health 测试
│   └── test_health.py             # 健康状态、健康检查、整体状态聚合
├── repositories/                  # pyspring-repositories 测试
│   └── test_repositories.py       # DB/缓存配置、IDBService/ICacheService 契约
├── security/                      # pyspring-security 测试
│   └── test_security.py           # JWT/认证配置、BCrypt、密码/Token/登录契约
└── web/                           # pyspring-web 测试
    └── test_web.py                # 统一 Response 成功/错误、HttpResponse 模型
```

## 测试统计

- **测试文件**：7 个
- **测试用例**：51 个
  - `core/`：12（IoC 容器 8 + AutoConfiguration 4）
  - `health/`：8
  - `repositories/`：13
  - `security/`：9
  - `web/`：9

## 覆盖的核心功能

### 1. IoC 容器（core）
- 容器初始化与组件扫描
- `@Component` / `@Service` 注册
- 按类型获取 Bean（`get_by_type`）
- 未注册服务异常
- 多实现按类型聚合（`get_all_of_type`）

### 2. AutoConfiguration 装配（core）
- entry point 发现所有已安装 starter
- 按 `order` 排序
- 扫描包去重
- 核心 starter 最先装配

### 3. 健康检查（health）
- 健康状态枚举
- 健康检查结果模型
- 指标发现 / 手动添加 / 执行
- 整体状态聚合

### 4. 数据访问（repositories）
- 数据库配置默认值（SQLite / PostgreSQL）
- 缓存配置（Memory / Redis）
- `IDBService` / `ICacheService` 接口契约

### 5. 安全（security）
- JWT / 认证配置模型
- BCrypt 密码编码器
- `IPasswordEncoder` / `ITokenService` / `ILoginProvider` 契约

### 6. Web（web）
- 统一 `Response` 成功 / 错误响应
- `HttpResponse` 模型
- 业务码约定

## 运行测试

### 使用 pytest（推荐）

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行某个 Starter 的测试
python -m pytest tests/core/ -v
python -m pytest tests/security/ -v
```

### 使用 run_tests.bat

```bash
run_tests.bat
```

## 测试配置（conftest.py）

- **禁用 loguru 异步队列**：`disable_loguru_enqueue` fixture，保证测试期间日志同步、输出可控。
- **清理 IoC 容器**：`cleanup_ioc_container` fixture，每个测试后清理容器单例状态，避免跨测试污染。
- **多包路径注入**：注入多个 `packages/*/src` 路径，使测试能解析所有 starter 的命名空间子包。

## 最佳实践

1. **隔离性**：每个测试独立运行，不依赖其他测试的状态。
2. **可重复性**：测试结果一致，不受运行顺序影响。
3. **降级友好**：外部依赖（Redis、PostgreSQL）缺失时优雅降级。
4. **清晰反馈**：失败时提供明确错误信息。

## 添加新测试

```python
# tests/<starter>/test_your_feature.py
from pyspring.core.ioc.context import ApplicationContext


def test_your_functionality():
    """测试你的新功能"""
    ctx = ApplicationContext.initialize(base_packages=["your_package"])
    assert ctx is not None
```

1. 在对应的 `<starter>` 目录（core/health/repositories/security/web）创建测试文件。
2. 确保测试使用 `ApplicationContext.initialize()`（而非全局单例）。
3. 运行 `python -m pytest tests/<starter>/ -v` 验证。

## 质量门禁

- 所有测试通过：`python -m pytest tests/ -v`
- `pyspring check --all` 必须 0 error / 0 warning
- 禁止在测试中引入类型 / 静态检查抑制标记
