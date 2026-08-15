# PySpring 测试套件

PySpring 框架的完整测试套件，按 Starter 模块组织。

## 目录结构

```
tests/
├── conftest.py              # Pytest 配置（禁用 loguru 异步日志、清理 IoC 容器）
├── core/                    # pyspring-core 测试
│   ├── test_ioc_container.py      # IoC 容器
│   └── test_autoconfigure.py      # AutoConfiguration 装配
├── health/                  # pyspring-health 测试
│   └── test_health.py       # 健康检查
├── repositories/            # pyspring-repositories 测试
│   └── test_repositories.py # 数据库/缓存契约
├── security/                # pyspring-security 测试
│   └── test_security.py     # JWT/认证/密码契约
└── web/                     # pyspring-web 测试
    └── test_web.py          # 统一响应/异常
```

## 运行测试

### 运行所有测试

```bash
python -m pytest tests/ -v
```

### 运行特定模块的测试

```bash
# 运行核心（IoC/装配）测试
python -m pytest tests/core/ -v

# 运行安全模块测试
python -m pytest tests/security/ -v

# 运行数据访问测试
python -m pytest tests/repositories/ -v

# 运行 Web 测试
python -m pytest tests/web/ -v
```

## 测试统计

- **测试文件**：7 个
- **测试用例**：51 个
  - `core/`：12（IoC 容器 8 + AutoConfiguration 4）
  - `health/`：8
  - `repositories/`：13
  - `security/`：9
  - `web/`：9

## 测试配置（conftest.py）

- **禁用 loguru 异步队列**：`disable_loguru_enqueue` fixture，保证测试期间日志同步、输出可控。
- **清理 IoC 容器**：`cleanup_ioc_container` fixture，每个测试后清理容器状态，避免跨测试污染。
- **多包路径注入**：注入多个 `packages/*/src` 路径，使测试能解析所有 starter 的命名空间子包。

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
2. 确保测试使用 `ApplicationContext.initialize()` 获取容器。
3. 运行 `python -m pytest tests/<starter>/ -v` 验证。

## 质量门禁

- 所有测试通过：`python -m pytest tests/ -v`
- `pyspring check --all` 必须 0 error / 0 warning
- 禁止在测试中引入类型 / 静态检查抑制标记

详细说明见 [TEST_SUMMARY.md](TEST_SUMMARY.md)。
