# CLI 模式静默日志说明

## 问题

在执行 `pyspring` 命令行工具时，会输出日志配置信息：

```
2026-01-23 01:17:44.870 | DEBUG | ✅ 已加载日志配置: D:\Project\...\logging.yaml
```

这些日志信息对于 CLI 工具来说是不必要的，会干扰用户的正常输出。

## 解决方案

### 自动检测 CLI 模式

通过两步确保 CLI 模式下的静默：

1. **设置环境变量标识 CLI 模式**
2. **立即禁用 loguru 默认输出**（在导入任何 PySpring 模块之前）

**src/pyspring/cli/main.py**:

```python
import os
import sys

# 标识 CLI 模式，让日志系统保持静默
os.environ['PYSPRING_CLI_MODE'] = '1'

# 在导入任何 PySpring 模块之前，先禁用 loguru 的默认输出
from loguru import logger
logger.remove()  # 移除所有默认 handler
logger.add(sys.stderr, level="ERROR", format="<red>Error:</red> {message}")

# 然后才导入其他模块
from .core.commands.loader import load_commands
```

这确保了即使在模块导入过程中有日志输出，也会被过滤掉。

### CLI 模式下的日志行为

在 CLI 模式下，日志系统会：

1. **静默正常日志**：INFO、DEBUG 等级别的日志不会输出
2. **只显示错误**：WARNING 及以上级别的日志才会输出到 stderr
3. **简化格式**：错误信息使用简洁的格式 `Error: {message}`

**src/pyspring/log/providers/loguru/services/service.py**:

```python
def _setup_logging(self):
    # 检查是否在 CLI 模式下运行
    is_cli_mode = os.environ.get('PYSPRING_CLI_MODE') == '1'
    
    # 移除默认处理器
    _loguru.remove()
    
    # CLI 模式下：只在出现 WARNING 及以上级别时才输出
    if is_cli_mode:
        _loguru.add(
            sys.stderr,  # 错误输出到 stderr
            format="<red>Error:</red> {message}",
            level="WARNING",
            colorize=True,
            backtrace=False,
            diagnose=False
        )
        return  # 跳过其他配置
    
    # 非 CLI 模式：正常加载配置
    # ...
```

## 效果对比

### 修改前

```bash
$ pyspring init
2026-01-23 01:17:44.870 | DEBUG | ✅ 已加载日志配置: ...
✨ Initializing PySpring project...
✅ Project initialized successfully!
```

### 修改后

```bash
$ pyspring init
✨ Initializing PySpring project...
✅ Project initialized successfully!
```

只有在出现错误时才会显示：

```bash
$ pyspring init
Error: Project directory already exists
```

## 适用场景

### CLI 模式（静默）

- 执行 `pyspring` 命令
- 日志级别：WARNING 及以上
- 输出：仅显示错误信息到 stderr

### 应用模式（正常）

- 作为库在其他项目中使用
- 日志级别：根据 `logging.yaml` 配置
- 输出：完整的日志信息

## 手动控制

如果您需要在 CLI 模式下启用详细日志（用于调试），可以临时取消环境变量：

```python
# 在 main.py 中
import os
# os.environ['PYSPRING_CLI_MODE'] = '1'  # 注释掉这行
```

或者添加 `--verbose` 参数来控制：

```python
# 未来可以实现
parser.add_argument('--verbose', '-v', action='store_true', 
                    help='Enable verbose logging')

if not args.verbose:
    os.environ['PYSPRING_CLI_MODE'] = '1'
```

## 相关文件

- [src/pyspring/cli/main.py](../../src/pyspring/cli/main.py) - CLI 入口
- [src/pyspring/log/providers/loguru/services/service.py](../../src/pyspring/log/providers/loguru/services/service.py) - 日志服务

## 更新日志

- **2026-01-23**: 实现 CLI 模式静默日志功能
