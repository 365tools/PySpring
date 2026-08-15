# PySpring + uv 快速设置指南

## 什么是 uv？

[uv](https://github.com/astral-sh/uv) 是一个极快的 Python 包管理器，用 Rust 编写，比 pip 快 10-100 倍。

## 安装 uv

### Windows（PowerShell）

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Linux/Mac

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

验证安装：

```bash
uv --version
```

## 🚀 快速设置 PySpring 项目

### 方法 1: 使用 PySpring CLI（推荐）

PySpring 内置了对 `uv` 的原生支持。

```bash
# 设置 uv 环境 (创建 venv 并安装依赖)
pyspring uv setup

# 开发模式 (安装开发依赖)
pyspring uv setup --dev

# 重建环境 (删除旧 venv 并重来)
pyspring uv setup --rebuild

# 查看状态
pyspring uv status
```

### 方法 2: 手动步骤

```powershell
# 1. 进入项目目录
cd D:\Project\PycharmProjects\FastAPIProject

# 2. 创建虚拟环境
uv venv

# 3. 激活虚拟环境
.venv\Scripts\Activate.ps1

# 4. 安装 PySpring
uv pip install pyspring

# 或开发模式
uv pip install -e D:\Project\PycharmProjects\PySpring

# 5. 验证
python -c "from pyspring.log.loguru.logger import logger; print('✅ 成功!')"
```

## 📦 使用 pyproject.toml 管理依赖

创建 `pyproject.toml`：

```toml
[project]
name = "your-project"
version = "0.1.0"
description = "FastAPI project with PySpring"
requires-python = ">=3.12"
dependencies = [
    "pyspring>=1.1.0",
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
]
```

同步依赖：

```bash
uv pip sync
```

## 🔄 重建虚拟环境

### 完全重建（推荐）

```powershell
# 使用脚本（推荐）
.\setup_uv.ps1 -Rebuild

# 或手动
Remove-Item -Recurse -Force .venv
uv venv
.venv\Scripts\Activate.ps1
uv pip install pyspring
```

### 仅重新安装包

```bash
# 重新安装所有包
uv pip install --force-reinstall pyspring

# 或从 requirements.txt
uv pip install -r requirements.txt
```

## 🆚 uv vs pip 对比

| 操作     | pip                         | uv                          |
|--------|-----------------------------|-----------------------------|
| 创建虚拟环境 | `python -m venv venv`       | `uv venv`                   |
| 激活虚拟环境 | `venv\Scripts\Activate.ps1` | `uv\Scripts\Activate.ps1`   |
| 安装包    | `pip install pyspring`      | `uv pip install pyspring`   |
| 列出包    | `pip list`                  | `uv pip list`               |
| 卸载包    | `pip uninstall pyspring`    | `uv pip uninstall pyspring` |
| 速度     | 慢                           | **快 10-100 倍** ⚡            |

## 🔧 配置 IDE（使用 .venv）

### VS Code

1. **选择解释器**
   ```
   Ctrl+Shift+P → "Python: Select Interpreter"
   选择: .\.venv\Scripts\python.exe
   ```

2. **配置 settings.json**
   ```json
   {
       "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
       "python.terminal.activateEnvironment": true
   }
   ```

3. **重启窗口**
   ```
   Ctrl+Shift+P → "Developer: Reload Window"
   ```

### PyCharm

1. **设置解释器**
   ```
   File → Settings → Project → Python Interpreter
   → Add Interpreter → Existing Environment
   → 选择: .venv\Scripts\python.exe
   ```

2. **重建缓存**
   ```
   File → Invalidate Caches / Restart
   ```

## 💡 常见问题

### Q1: uv 创建的虚拟环境目录名是什么？

**A**: uv 默认创建 `.venv` 目录（注意前面有点），而不是 `venv`。

### Q2: 如何在 uv 虚拟环境中运行 pyspring 命令？

**A**:

```powershell
# 方法 1: 激活虚拟环境后直接运行
.venv\Scripts\Activate.ps1
pyspring check

# 方法 2: 使用完整路径
.venv\Scripts\python.exe -m pyspring.diagnose

# 方法 3: 使用 uv run（如果支持）
uv run pyspring check
```

### Q3: uv 安装的包在哪里？

**A**:

```
.venv\Lib\site-packages\pyspring\
```

### Q4: 如何验证 PySpring 安装正确？

**A**:

```powershell
# 方法 1: 运行诊断
.venv\Scripts\python.exe -m pyspring.diagnose

# 方法 2: 测试导入
.venv\Scripts\python.exe -c "from pyspring.log.loguru.logger import logger; print('✅')"

# 方法 3: 查看已安装的包
uv pip show pyspring
```

### Q5: 如何更新 PySpring？

**A**:

```bash
# 更新到最新版本
uv pip install --upgrade pyspring

# 或重新安装
uv pip install --force-reinstall pyspring
```

## 📋 完整工作流示例

### 新项目从零开始

```powershell
# 1. 创建项目目录
mkdir MyProject
cd MyProject

# 2. 复制设置脚本
Copy-Item D:\Project\PycharmProjects\PySpring\tools\setup_uv.ps1 .

# 3. 运行设置
.\setup_uv.ps1

# 4. 激活虚拟环境
.venv\Scripts\Activate.ps1

# 5. 初始化 PySpring 配置
pyspring init

# 6. 在 VS Code 中打开
code .

# 7. 选择 Python 解释器
# Ctrl+Shift+P → Python: Select Interpreter → .\.venv\Scripts\python.exe

# 8. 开始开发
# 创建 main.py 并开始编码
```

### 现有项目添加 PySpring

```powershell
# 1. 进入项目目录
cd D:\Project\PycharmProjects\FastAPIProject

# 2. 如果已有虚拟环境，重建它
Remove-Item -Recurse -Force .venv

# 3. 创建新的虚拟环境并安装 PySpring
uv venv
.venv\Scripts\Activate.ps1
uv pip install pyspring

# 4. 初始化配置
pyspring init

# 5. 重启 IDE
```

## 🎯 快速命令参考

```powershell
# 虚拟环境管理
uv venv                              # 创建虚拟环境
.venv\Scripts\Activate.ps1           # 激活（Windows）
deactivate                           # 退出

# 包管理
uv pip install pyspring              # 安装包
uv pip install -e path/to/pyspring   # 开发模式
uv pip list                          # 列出包
uv pip show pyspring                 # 显示包信息
uv pip uninstall pyspring            # 卸载包
uv pip sync                          # 同步依赖

# PySpring 命令
pyspring init                        # 初始化项目
pyspring check                    # 诊断问题

# 重建环境（完整）
Remove-Item -Recurse -Force .venv; uv venv; .venv\Scripts\Activate.ps1; uv pip install pyspring
```

## 📚 相关资源

- [uv 官方文档](https://github.com/astral-sh/uv)
- [PySpring 文档](../README.md)
- [解决 Unresolved Reference](FIX_UNRESOLVED_REFERENCE.md)
- [诊断指南](DIAGNOSE_GUIDE.md)

## 💬 提示

- ⚡ uv 比 pip 快得多，推荐使用
- 📁 uv 使用 `.venv` 而不是 `venv`
- 🔄 使用 `setup_uv.ps1 -Rebuild` 快速重建环境
- 🔧 IDE 配置选择 `.venv\Scripts\python.exe`
- ✅ 使用 `pyspring check` 验证安装

**使用 uv 让 PySpring 项目设置更快、更简单！** 🚀
