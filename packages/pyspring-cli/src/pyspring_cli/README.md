# PySpring 命令行工具 (CLI)

PySpring CLI 提供了一套工具，帮助你管理、配置和排查 PySpring 项目的问题。

## 目录结构

CLI 模块的组织结构如下：

```
pyspring/cli/
├── commands/           # 命令实现
│   ├── check.py        # 'check' 命令入口
│   ├── check/      # 'check' 命令逻辑 (导入检查, 编码检查等)
│   ├── diagnose.py     # 'diagnose' 命令入口
│   ├── diagnose/   # 'diagnose' 命令逻辑
│   ├── init.py         # 'init' 命令入口
│   ├── init/       # 'init' 命令逻辑 (模板, 密钥生成等)
│   ├── uv.py           # 'uv' 命令入口
│   └── uv/         # 'uv' 命令逻辑
├── core/               # 共享 CLI 核心工具 (UI, 格式化)
└── main.py             # CLI 主入口 (参数解析与分发)
```

## 可用命令

### 1. `pyspring init`

初始化一个新的 PySpring 项目结构和配置文件。

- **用法**: `pyspring init [target_dir]`
- **选项**:
    - `--minimal` (`-m`): 仅创建最小化的必要配置文件。
    - `--force` (`-f`): 强制覆盖现有文件。
    - `--skip-env`: 跳过 `.env` 文件的生成。

### 2. `pyspring check`

检查项目健康状况和代码完整性。

- **子命令**:
    - `import`: 递归检查项目中的导入错误。
        - `pyspring check import [target_dir]`
    - `encoding`: 检查非 UTF-8 编码的文件或带有 BOM 的文件。
        - `pyspring check encoding --fix`: 自动修复编码问题。

### 3. `pyspring diagnose`

诊断安装和环境问题。此工具会检查你的 Python 环境、PySpring 安装状态以及虚拟环境状态，用于解决 IDE 中的 "Unresolved reference" (未解析的引用) 错误。

- **用法**: `pyspring diagnose`

### 4. `pyspring uv`

管理基于 `uv` 的虚拟环境。

- **子命令**:
    - `setup`: 创建虚拟环境并安装依赖。
    - `install`: 安装 PySpring 依赖。
    - `rebuild`: 清理并重建环境。
    - `status`: 显示当前环境状态。

## 开发指南

如何添加新命令：

1. 在 `commands/` 目录下创建一个 `new_command.py` 文件。
2. 如果逻辑复杂，创建一个 `new_command/` 包来存放具体实现。
3. 在 `new_command.py` 中实现 `register_subcommand(subparsers)` 函数。
4. 在 `pyspring/cli/main.py` 中注册新命令。
