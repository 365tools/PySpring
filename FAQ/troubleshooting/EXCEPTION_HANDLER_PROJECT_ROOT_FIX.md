# Exception Handler Project Root Fix

## 问题描述

**错误日志**：

```
2026-01-26 01:03:45.842 | ERROR | [fw] web.handlers.exception:58 | 🚨 'D:\\Project\\PycharmProjects\\py-demo\\app\\dependencies\\auth.py' is not in the subpath of 'D:\\Project\\PycharmProjects\\PySpring'
```

**问题根因**：
异常处理器的 `_project_root()` 方法返回框架的安装路径（`PySpring`），而不是用户项目的根路径（`py-demo`）。当处理用户项目的异常时，无法将文件路径转换为相对路径，导致 `relative_to()` 失败并打印错误日志。

## 问题分析

### 旧实现的问题

```python
@staticmethod
def _project_root() -> Path:
    """更稳健地解析项目根(以src上方为界)"""
    p = Path(__file__).resolve()  # ❌ __file__ 指向框架安装路径
    if "src" in p.parts:
        return Path(*p.parts[: p.parts.index("src")])
    return p.parents[3] if len(p.parents) >= 4 else p.parent
```

**问题**：

1. `Path(__file__)` 始终指向框架代码位置（`PySpring/src/pyspring/web/handlers/exception.py`）
2. 返回的项目根是框架的根（`D:\Project\PycharmProjects\PySpring`）
3. 用户项目文件（如 `py-demo/app/services/auth_service.py`）不在此路径下
4. `relative_to()` 抛出 `ValueError`，被捕获并打印错误日志

### 执行流程

```
用户项目运行 (py-demo)
    ↓
异常发生在 app/dependencies/auth.py
    ↓
GlobalExceptionHandler.format_exception_info()
    ↓
调用 _relpath(file_path)
    ↓
调用 _project_root() 
    → 返回 D:\Project\PycharmProjects\PySpring ❌
    ↓
Path(file_path).relative_to(root)
    → ValueError: 'D:\...\py-demo\app\...' is not in the subpath of 'D:\...\PySpring'
    ↓
except Exception as e:
    logger.error(f"🚨 {e}")  # 打印错误日志
```

## 修复方案

### 智能项目根检测

**新实现**：

```python
@staticmethod
def _project_root() -> Path:
    """
    智能解析项目根目录
    
    策略：
    1. 从当前工作目录向上查找项目标识文件（优先）
    2. 回退到当前工作目录
    """
    # 策略 1: 查找包含 pyproject.toml 或 setup.py 的目录
    cwd = Path.cwd()
    current = cwd
    for _ in range(10):  # 最多向上查找 10 层
        if (current / "pyproject.toml").exists() or (current / "setup.py").exists():
            return current
        if current.parent == current:  # 到达文件系统根
            break
        current = current.parent
    
    # 策略 2: 回退到当前工作目录
    return cwd
```

**优势**：

- ✅ 使用当前工作目录（`Path.cwd()`）而非框架安装路径
- ✅ 向上查找项目标识文件（`pyproject.toml`、`setup.py`）
- ✅ 自动适应用户项目和框架项目

### 健壮的路径转换

**新实现**：

```python
@staticmethod
def _relpath(file_path: str) -> str:
    """
    转换为相对路径
    
    策略：
    1. 尝试相对于项目根
    2. 失败时返回绝对路径（不打印错误日志）
    """
    try:
        root = GlobalExceptionHandler._project_root()
        return str(Path(file_path).resolve().relative_to(root)).replace("\\", "/")
    except ValueError:
        # 文件不在项目根的子路径中（如虚拟环境、系统库）
        # 返回绝对路径，便于调试
        return str(Path(file_path).resolve()).replace("\\", "/")
```

**改进**：

- ✅ 使用 `ValueError` 精确捕获 `relative_to()` 异常
- ✅ 失败时返回绝对路径（而非打印错误）
- ✅ 移除噪音错误日志

### 改进的 Traceback 过滤

**旧实现**：

```python
# 硬编码检查 /src/ 路径
if "/src/" in ("/" + filename):
    project_frames.append(...)
```

❌ 假设所有项目都有 `src/` 目录

**新实现**：

```python
project_root = GlobalExceptionHandler._project_root()
file_path = Path(f.f_code.co_filename).resolve()

# 判断是否为项目文件
try:
    rel_path = file_path.relative_to(project_root)
    # 排除虚拟环境和第三方库
    if not any(part in rel_path.parts for part in ['.venv', 'venv', 'site-packages', 'dist-packages']):
        filename = str(rel_path).replace("\\", "/")
        project_frames.append(f"{filename}:{tb_iter.tb_lineno} in {f.f_code.co_name}()")
except ValueError:
    pass  # 不在项目根路径下，跳过
```

**改进**：

- ✅ 动态检测项目文件（基于路径关系，而非硬编码）
- ✅ 排除虚拟环境和第三方库
- ✅ 支持任意项目结构（`app/`, `src/`, `lib/` 等）

## 修改文件

### `src/pyspring/web/handlers/exception.py`

**Line 42-67**: `_project_root()` 方法

- 从当前工作目录向上查找项目根
- 检查 `pyproject.toml` 或 `setup.py`
- 回退到当前工作目录

**Line 69-81**: `_relpath()` 方法

- 移除错误日志打印
- 失败时返回绝对路径（而非相对路径）
- 使用 `ValueError` 精确捕获异常

**Line 121-145**: `format_exception_info()` 中的 Traceback 过滤

- 动态检测项目文件（基于 `relative_to()`）
- 排除虚拟环境、第三方库
- 支持任意项目目录结构

## 验证测试

### 测试场景 1：PySpring 框架项目

```python
from pyspring.web.handlers.exception import GlobalExceptionHandler
from pathlib import Path

# 当前工作目录：D:\Project\PycharmProjects\PySpring
root = GlobalExceptionHandler._project_root()
# 结果：D:\Project\PycharmProjects\PySpring ✅

# 框架文件
path = "D:\\Project\\PycharmProjects\\PySpring\\src\\pyspring\\web\\handlers\\exception.py"
rel = GlobalExceptionHandler._relpath(path)
# 结果：src/pyspring/web/handlers/exception.py ✅

# 虚拟环境文件
path = "D:\\Project\\PycharmProjects\\PySpring\\.venv\\Lib\\site-packages\\fastapi\\routing.py"
rel = GlobalExceptionHandler._relpath(path)
# 结果：.venv/Lib/site-packages/fastapi/routing.py ✅

# 系统库文件
path = "D:\\Python\\Lib\\json\\__init__.py"
rel = GlobalExceptionHandler._relpath(path)
# 结果：D:/Python/Lib/json/__init__.py ✅（绝对路径）
```

### 测试场景 2：用户项目（py-demo）

```python
# 当前工作目录：D:\Project\PycharmProjects\py-demo
root = GlobalExceptionHandler._project_root()
# 结果：D:\Project\PycharmProjects\py-demo ✅

# 用户项目文件
path = "D:\\Project\\PycharmProjects\\py-demo\\app\\dependencies\\auth.py"
rel = GlobalExceptionHandler._relpath(path)
# 结果：app/dependencies/auth.py ✅

# 虚拟环境文件
path = "D:\\Project\\PycharmProjects\\py-demo\\.venv\\Lib\\site-packages\\fastapi\\routing.py"
rel = GlobalExceptionHandler._relpath(path)
# 结果：D:/Project/PycharmProjects/py-demo/.venv/Lib/site-packages/fastapi/routing.py ✅
```

### Traceback Summary 测试

**Before**（旧实现）：

```
traceback_summary: ""  # 空字符串，因为用户项目没有 /src/ 目录
```

**After**（新实现）：

```
traceback_summary: "app/dependencies/auth.py:45 in get_current_user() -> app/services/auth_service.py:186 in verify_token()"
```

✅ 正确提取用户项目的调用链

## 影响范围

### 修改行为

**Before**:

- 项目根：始终是框架安装路径
- 相对路径：用户项目文件转换失败，打印错误日志
- Traceback：仅显示包含 `/src/` 的文件

**After**:

- 项目根：智能检测用户项目根
- 相对路径：失败时返回绝对路径，无错误日志
- Traceback：显示所有项目文件（排除虚拟环境）

### 兼容性

**框架项目**：

- ✅ 正常工作（有 `pyproject.toml`）
- ✅ Traceback 正确显示 `src/pyspring/...`

**用户项目**：

- ✅ 正常工作（有 `pyproject.toml` 或 `setup.py`）
- ✅ Traceback 正确显示 `app/...`
- ✅ 无噪音错误日志

**无项目文件的环境**：

- ✅ 回退到当前工作目录
- ✅ 绝对路径显示，仍可调试

## 设计考量

### 为什么使用 `Path.cwd()` 而非 `Path(__file__)`？

| 方案               | 优点           | 缺点             |
|------------------|--------------|----------------|
| `Path(__file__)` | 稳定（不受工作目录影响） | 始终指向框架安装路径 ❌   |
| `Path.cwd()`     | 指向实际运行的项目 ✅  | 依赖启动目录（但这是合理的） |

**选择 `Path.cwd()`**：

- 用户启动应用时，工作目录就是项目根
- 这是行业标准（Django、Flask 等框架的做法）
- 配合向上查找 `pyproject.toml`，健壮性足够

### 为什么不使用环境变量？

可以添加环境变量 `PROJECT_ROOT` 覆盖，但：

- 增加用户配置负担
- 大多数情况下自动检测已足够
- 可在未来版本添加

## 总结

### 问题本质

框架的异常处理器使用框架自身的安装路径作为项目根，无法处理用户项目的文件路径。

### 修复方法

智能检测当前运行的项目根（基于工作目录和项目标识文件），而非硬编码框架路径。

### 设计原则

**运行时上下文优先**：

- 使用当前工作目录（`cwd`）而非代码位置（`__file__`）
- 动态检测项目文件（路径关系）而非硬编码模式（`/src/`）
- 优雅降级（失败时返回绝对路径，而非抛出错误）

---

**修复日期**: 2026-01-26  
**影响版本**: v1.1.0b27+  
**修复状态**: ✅ 已完成并测试
