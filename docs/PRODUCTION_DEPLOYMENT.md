# 生产环境部署指南

本文档说明如何在生产环境中使用 PySpring，以及如何优化依赖以减少不必要的包安装。

---

## 📦 安装场景

### 场景 1：生产环境 - 最小化安装

**使用场景**：Docker 容器、生产服务器、Lambda 函数等

```bash
# 只安装运行时依赖（不包含开发工具）
pip install pyspring

# 或使用 uv（更快）
uv pip install pyspring
```

**安装的内容**：

- ✅ PySpring 核心框架（IoC、AOP、配置等）
- ✅ FastAPI、Uvicorn 等运行时依赖
- ✅ CLI 工具代码（但不使用）
- ❌ 测试工具（pytest 等）
- ❌ 代码格式化工具（black、flake8 等）

**CLI 说明**：

- CLI 代码会被安装，但通常不在生产环境使用
- CLI 依赖都是 Python 标准库，无额外包开销
- 代码体积约 50 KB，可忽略不计

---

### 场景 2：开发环境 - 完整安装

**使用场景**：本地开发、CI/CD 测试环境

```bash
# 安装框架 + CLI 工具 + 开发工具
pip install pyspring[full]

# 或分步安装
pip install pyspring[cli]  # 框架 + CLI（CLI 目前无额外依赖）
pip install pyspring[dev]  # 框架 + 测试工具
```

**安装的内容**：

- ✅ PySpring 核心框架
- ✅ CLI 工具（用于 `pyspring init`、`pyspring check` 等）
- ✅ 测试工具（pytest、pytest-asyncio、httpx）
- ✅ 代码质量工具（black、flake8、mypy）

---

### 场景 3：临时使用 CLI - 零安装

**使用场景**：快速创建新项目，不想全局安装

```bash
# 使用 uvx 临时执行（推荐）
uvx --from pyspring pyspring init my-project --example

# 或使用 pipx（一次性安装到隔离环境）
pipx run --spec pyspring pyspring init my-project --example
```

**特点**：

- ✅ 无需提前安装 PySpring
- ✅ CLI 在临时环境中运行，用完即删
- ✅ 适合首次体验或偶尔使用

---

## 🚀 生产环境最佳实践

### 方式 1：使用 requirements.txt（传统）

```bash
# requirements.txt
pyspring>=1.0.0

# 锁定版本（推荐）
pyspring==1.0.0
```

### 方式 2：使用 pyproject.toml + uv（现代）

```toml
[project]
dependencies = [
    "pyspring>=1.0.0",
]
```

```bash
# 安装
uv pip install -r pyproject.toml
```

### 方式 3：Docker 多阶段构建（推荐）

```dockerfile
# Dockerfile
FROM python:3.12-slim AS builder

WORKDIR /app

# 只安装生产依赖
COPY pyproject.toml .
RUN pip install --no-cache-dir pyspring

COPY . .

# 运行阶段（更小的镜像）
FROM python:3.12-slim

WORKDIR /app

# 从构建阶段复制已安装的包
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app /app

# 运行应用（不使用 CLI）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔍 CLI 在生产环境的影响分析

### 代码体积

```bash
# PySpring CLI 模块大小
src/pyspring/cli/          ~50 KB（Python 代码）
├── commands/              ~35 KB
├── core/                  ~10 KB
└── main.py                ~5 KB

# 对比：整个 PySpring 包
src/pyspring/              ~500 KB

# CLI 占比：10%
```

### 依赖分析

**CLI 当前依赖**：

```python
# 全部是 Python 标准库，无额外 PyPI 包
import argparse
import sys
import os
import re
from pathlib import Path
from typing import *
```

**无额外依赖**意味着：

- ✅ 不会增加安装时间
- ✅ 不会增加镜像大小（除了 50 KB 代码）
- ✅ 不会引入额外的安全风险

### 运行时影响

- ✅ CLI 模块不会在应用启动时自动加载
- ✅ 只有执行 `pyspring` 命令才会加载 CLI 代码
- ✅ 生产环境不调用 CLI，运行时开销为 **0**

---

## ⚙️ 高级优化：完全排除 CLI

如果你的生产环境对包大小极度敏感（如 AWS Lambda），可以手动排除 CLI：

### 方式 1：使用 pip install 时排除

```bash
# 1. 克隆仓库
git clone https://github.com/365tools/PySpring.git
cd PySpring

# 2. 修改 pyproject.toml，临时排除 CLI
# 添加到 [tool.setuptools.packages.find]
# exclude = ["pyspring.cli*"]

# 3. 本地构建并安装
pip install .
```

### 方式 2：构建自定义 wheel

```bash
# 1. 创建自定义构建脚本
cat > build_no_cli.py << 'EOF'
import shutil
import os
from pathlib import Path

# 临时备份 CLI 目录
cli_path = Path("src/pyspring/cli")
cli_backup = Path("src/pyspring/cli.backup")

if cli_path.exists():
    shutil.move(str(cli_path), str(cli_backup))
    
# 构建包
os.system("python -m build")

# 恢复 CLI 目录
if cli_backup.exists():
    shutil.move(str(cli_backup), str(cli_path))
EOF

# 2. 运行构建
python build_no_cli.py

# 3. 安装生成的 wheel
pip install dist/pyspring-*.whl
```

---

## 📊 不同安装方式的对比

| 安装方式                         | 包大小     | CLI 可用 | 适用场景     |
|------------------------------|---------|--------|----------|
| `pip install pyspring`       | ~500 KB | ✅ 是    | 生产环境（标准） |
| `pip install pyspring[cli]`  | ~500 KB | ✅ 是    | 开发环境（明确） |
| `pip install pyspring[full]` | ~15 MB  | ✅ 是    | 开发环境（完整） |
| `uvx --from pyspring ...`    | 临时      | ✅ 是    | 临时使用 CLI |
| 自定义构建（排除 CLI）                | ~450 KB | ❌ 否    | 极致优化     |

---

## 🎯 推荐策略

### 小型项目/微服务

```bash
# 生产环境：标准安装（包含 CLI，但不使用）
pip install pyspring

# 理由：
# - 安装简单，一行命令
# - CLI 只占 50 KB，可忽略
# - 避免复杂的构建流程
```

### 大型企业应用

```bash
# 生产环境：使用 pyproject.toml 管理
[project]
dependencies = [
    "pyspring>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pyspring[full]",
]

# 安装：
# 生产：uv pip install .
# 开发：uv pip install .[dev]
```

### Serverless / Lambda

```bash
# 极致优化：自定义构建排除 CLI
# 或使用 Lambda Layer 共享 PySpring
# 参考：方式 2 自定义 wheel
```

---

## 🔄 未来规划

### CLI 增强（可选依赖）

未来可能添加的 CLI 增强库：

```toml
[project.optional-dependencies]
cli = [
    "rich>=13.0.0",      # 彩色输出和进度条
    "click>=8.0.0",      # 更强大的 CLI 框架
    "inquirer>=3.0.0",   # 交互式提示
]
```

安装方式：

```bash
# 生产环境：不安装 CLI 增强
pip install pyspring

# 开发环境：安装增强 CLI
pip install pyspring[cli]
```

### 完全分离 CLI 包（长期）

如果 CLI 变得很重，可能会：

1. 创建独立的 `pyspring-cli` 包
2. 保持 `pyspring` 核心包轻量
3. 用户按需安装：`pip install pyspring-cli`

---

## ✅ 总结

**当前状态**（v1.0.0）：

- ✅ CLI 代码会被安装到生产环境（50 KB）
- ✅ CLI 无额外 PyPI 依赖（只用标准库）
- ✅ 运行时性能无影响（不自动加载）
- ✅ 对生产环境影响可忽略

**推荐做法**：

- **生产环境**：直接 `pip install pyspring`，无需担心 CLI
- **开发环境**：使用 `pip install pyspring[full]` 获取完整工具链
- **临时使用**：使用 `uvx --from pyspring pyspring init` 零安装创建项目
- **极致优化**：仅在 Lambda 等场景考虑自定义构建排除 CLI

**关键原则**：
> **过早优化是万恶之源** - 50 KB 的 CLI 代码对 99% 的应用来说都是可以接受的。
> 只有在极端场景（如 Lambda 50 MB 限制）才需要考虑排除 CLI。

---

## 📚 相关文档

- [安装指南](01-getting-started/INSTALLATION_GUIDE.md)
- [CLI 使用指南](04-features/CLI_GUIDE.md)
- [PyPI 发布指南](PUBLISHING_GUIDE.md)
- [Docker 部署示例](05-advanced/DOCKER_GUIDE.md)
