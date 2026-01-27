# IntelliJ IDEA / PyCharm 控制台链接配置指南

## 问题描述

日志输出的绝对路径太长，不够简洁：

```
D:\Project\PycharmProjects\PySpring\verify_ide_jump.py:46
```

## 解决方案

### 方案1: 配置 IDEA 的 Output Filters（推荐）

IntelliJ IDEA 和 PyCharm 支持自定义输出过滤器来识别日志中的文件路径。

#### 配置步骤：

1. **打开设置**
    - `File` -> `Settings` (Windows/Linux)
    - `IntelliJ IDEA` -> `Preferences` (macOS)

2. **导航到控制台过滤器设置**
   ```
   Settings -> Editor -> General -> Console
   ```
   或搜索 `Console` 找到相关设置

3. **添加自定义 Output Filter**

   点击 `+` 添加新的过滤器，配置如下：

   **过滤器名称**: `PySpring Log Format`

   **正则表达式**:
   ```regex
   (?:.*\| )([a-zA-Z]:\\[^:]+\.py):(\d+)(?: \|.*)
   ```

   或者更宽松的模式：
   ```regex
   ([a-zA-Z]:[^:]+\.py):(\d+)
   ```

4. **配置捕获组**
    - File Path: `$1`
    - Line Number: `$2`

#### 验证配置

配置完成后，在控制台点击这样的路径应该能跳转：

```
D:\Project\PycharmProjects\PySpring\verify_ide_jump.py:46
```

---

### 方案2: 使用相对路径 + IDEA 智能匹配

修改日志格式使用项目相对路径，依赖 IDEA 的智能文件搜索。

**优点**:

- 日志更简洁
- IDEA 会智能搜索匹配的文件

**缺点**:

- 如果有同名文件可能需要手动选择
- 某些情况下无法自动跳转

**配置**:

修改 `config/logging.yaml`:

```yaml
console:
  format: "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[file_relative]}:{line}</cyan> | {message}"
```

输出效果:

```
verify_ide_jump.py:46
```

然后在 IDEA 中配置 Output Filter:

```regex
([a-zA-Z0-9_/\\]+\.py):(\d+)
```

---

### 方案3: 混合格式（最佳平衡）

在日志中同时包含简短标识和完整路径，格式优化为更易读的形式。

修改 `config/logging.yaml`:

```yaml
console:
  format: "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[file_relative]}</cyan>:<cyan>{line}</cyan> | <dim>{file.path}</dim> | {message}"
```

输出效果:

```
2026-01-27 22:00:00.000 | INFO     | verify_ide_jump.py:46 | D:\...\verify_ide_jump.py | 测试消息
                                      ↑ 易读               ↑ 可点击跳转
```

---

### 方案4: 使用 File 协议链接（高级）

某些终端支持 `file://` 协议链接，可以直接点击打开。

自定义日志格式:

```yaml
console:
  format: "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | file://{file.path}:{line} | {message}"
```

输出:

```
file://D:\Project\PycharmProjects\PySpring\verify_ide_jump.py:46
```

**注意**: 需要终端支持 `file://` 协议

---

## IDEA Output Filter 配置示例

### 示例1: 匹配绝对路径 (Windows)

```regex
Pattern: ([A-Z]:\\[^:]+\.py):(\d+)
File: $1
Line: $2
```

匹配:

```
D:\Project\PycharmProjects\PySpring\verify_ide_jump.py:46
```

### 示例2: 匹配相对路径

```regex
Pattern: ([a-zA-Z0-9_/\\.-]+\.py):(\d+)
File: $1
Line: $2
```

匹配:

```
src/pyspring/log/instance.py:42
verify_ide_jump.py:46
```

### 示例3: 匹配带前缀的路径

```regex
Pattern: (?:File |at |in )["']?([^"':]+\.py)["']?[:,]\s*(?:line\s+)?(\d+)
File: $1
Line: $2
```

匹配:

```
File "D:\Project\verify.py", line 46
at verify.py:46
in verify.py, line 46
```

---

## 推荐配置

### 开发环境（本地）

使用**绝对路径**，配置 IDEA Output Filter 支持点击跳转:

```yaml
# config/logging.yaml
console:
  format: "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {file.path}:{line} | {message}"
```

### 生产环境

使用**相对路径**，更简洁且隐藏敏感路径信息:

```yaml
# config/logging.yaml  
console:
  format: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[file_relative]}:{line} | {message}"
```

---

## 其他提示

### PyCharm 内置支持

PyCharm 默认已经支持以下格式:

- `File "path", line XX` (Python 异常格式)
- `path:line` (通用格式)
- `path(line)` (某些编译器格式)

### VS Code 支持

VS Code 的终端也支持链接识别，通常自动识别:

- 绝对路径:行号
- 相对路径:行号（相对于工作区）

### 调试技巧

在 IDEA 控制台中测试正则表达式:

1. 复制一行日志输出
2. Settings -> Console -> Output Filters -> Test
3. 粘贴日志，查看是否正确匹配

---

## 总结

| 方案     | 简洁度   | 可跳转性  | 推荐场景   |
|--------|-------|-------|--------|
| 绝对路径   | ⭐⭐    | ⭐⭐⭐⭐⭐ | 开发环境   |
| 相对路径   | ⭐⭐⭐⭐⭐ | ⭐⭐⭐   | 生产环境   |
| 混合格式   | ⭐⭐⭐   | ⭐⭐⭐⭐  | 需要两者平衡 |
| File协议 | ⭐⭐    | ⭐⭐⭐⭐  | 支持的终端  |

**建议**: 开发时使用绝对路径 + IDEA Output Filter 配置，既保证跳转功能，又通过 IDEA 优化显示。
