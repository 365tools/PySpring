# PySpring 测试与 pytest-xdist 并行实践

> 版本：v0.1
> 状态：草案
> 适用范围：PySpring 仓库所有包（`packages/*`）与 `tests/` 目录的测试开发

---

## 一、为什么需要并行测试

### 1.1 测试规模

PySpring 是一个多包（7 个 starter）的框架仓库，测试分为两类：

| 类型 | 位置 | 数量 | 说明 |
|------|------|------|------|
| 单元测试 | `tests/{core,web,health,repositories,security}/` | 51 | 覆盖各包的 IoC、自动装配、接口契约 |
| CLI 集成测试 | `tests/cli/` | 59 | 通过 `subprocess` 调用真实 `pyspring` 命令 |

其中 **CLI 集成测试**是主要性能瓶颈：每个命令都通过 `subprocess` 启动一个新 Python 进程，串行执行 58 个测试约需 **60 秒**。

### 1.2 并行的收益

```
串行（默认）:  tests/cli  ≈ 61s     完整套件 ≈ 70s+
并行（-n auto）: tests/cli  ≈ 17s    完整套件 ≈ 22s    （约 3~3.6 倍加速）
```

> ⚠️ **并行加速的关键前提**：测试之间**相互独立、无共享状态**。这正是 PySpring 测试设计的准则（见 §3.1）。

---

## 二、安装与配置

### 2.1 安装 pytest-xdist

在根 `pyproject.toml` 的 dev 依赖中加入：

```toml
[project.optional-dependencies]
dev = [
    # ...
    "pytest-xdist>=3.6.0",
]
```

安装（uv workspace）：

```bash
uv sync --all-packages --extra dev   # 或 uv pip install pytest-xdist
```

### 2.2 配置默认并行

在 `[tool.pytest.ini_options]` 中添加 `addopts`，让 pytest 默认按 CPU 核数并行：

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = ["-n", "auto"]   # auto = 自动使用所有可用 CPU 核
markers = [
    "slow: slow-running tests (e.g. basedpyright full type-check)",
]
```

`-n auto` 会自动检测本机 CPU 核数并启动对应数量的 worker，无需手动指定。

---

## 三、进阶优化

### 3.1 测试隔离（并行安全的关键）

pytest-xdist 的每个 worker 是**独立进程**，天然隔离了模块级单例、环境变量等全局状态。但要让测试真正可并行，还需主动隔离：

- **环境变量隔离**：CLI 集成测试用 `PYSPRING_HOME` 指向独立的 `tmp_path`，避免污染真实配置：

```python
@pytest.fixture()
def cli_env(tmp_path):
    env = dict(os.environ)
    env["PYSPRING_HOME"] = str(tmp_path / "home")
    return env
```

- **临时目录隔离**：用 pytest 内置 `tmp_path` fixture，每个测试独享临时目录，测试后自动清理。

> 只要测试满足"无共享可变状态"，并行就是安全的——甚至比串行更稳（每个测试在独立进程里，互相不可能干扰）。

### 3.2 用 marker 标记慢测试

对耗时很长的测试（如 `basedpyright` 全量类型检查），用 `slow` marker 标记，默认跳过、按需运行：

```python
import pytest

@pytest.mark.slow
def test_basedpyright():
    ...
```

```bash
pytest tests/ -m "not slow"   # 快速回归（跳过慢测试）
pytest tests/ -m slow         # 只跑慢测试
```

### 3.3 在 CI 中并行

CI 的 `uv run pytest tests/` 会自动继承 `addopts = ["-n", "auto"]`，无需额外配置即可并行加速。也可显式指定 worker 数：

```yaml
# .github/workflows/ci.yml
run: uv run pytest tests/ -n auto
```

---

## 四、常用命令

```bash
# 完整测试（默认并行）
pytest tests/

# 跳过慢测试（快速回归）
pytest tests/ -m "not slow"

# 只测 CLI 集成测试
pytest tests/cli/

# 指定 worker 数
pytest tests/ -n 4

# 关闭并行（串行调试，便于看单个进程日志）
pytest tests/ -n 0
```

---

## 五、注意事项与常见问题

### 5.1 并行 + asyncio

pytest-asyncio 的 `asyncio_mode = "auto"` 在并行下正常工作——每个 worker 是独立进程，各自管理自己的 event loop，无跨进程冲突。

### 5.2 并行 + subprocess 测试

CLI 集成测试通过 `subprocess` 启动真实命令。并行时多个 CLI 进程同时启动，可能占用较多系统资源。若资源紧张，可降低 worker 数（`-n 2`）。每个测试的 `PYSPRING_HOME` 已隔离，**不会相互干扰**。

### 5.3 并行关闭的场景

以下场景建议用 `-n 0`（串行）：
- 调试单个测试的完整输出（并行会打散日志）
- 排查疑似共享状态的测试（用 `pytest -n 0 --durations=10` 定位）

### 5.4 依赖仓库上下文的命令

部分命令（如 `imports-unused` 重构命令）**依赖仓库/git 上下文**，在系统临时目录（仓库外）下运行会失败。此类测试应在**仓库内的隔离目录**（如 `tests/cli/_work/`）运行，并用 fixture 自动清理。

---

## 六、性能对比参考

| 测试集 | 串行 | 并行（-n auto） | 加速比 |
|--------|------|----------------|--------|
| `tests/core`（单元） | — | 6.6s | — |
| `tests/cli`（集成） | 61s | 17s | **3.6x** |
| 完整套件（109 tests） | 70s+ | 22s | **3x+** |

---

*本文档为 PySpring 工程实践的一部分，随测试策略演进持续更新。*
