# 中文显示问题解决方案

## 🔍 问题原因

Windows PowerShell默认使用GBK编码（代码页936），而Python和loguru使用UTF-8编码，导致中文字符显示为乱码。

## ✅ 解决方案

### 方案1：使用批处理文件运行（推荐）

直接双击 `run_tests.bat`，自动设置UTF-8编码：

```bash
tests\security\run_tests.bat
```

### 方案2：手动设置PowerShell编码

在运行测试**之前**，先执行以下命令：

```powershell
# 切换代码页到UTF-8
chcp 65001

# 然后运行测试
python tests/security/run_all_tests.py
```

### 方案3：使用PowerShell脚本

右键点击 `run_tests.ps1` → "使用PowerShell运行"

或在PowerShell中执行：

```powershell
.\tests\security\run_tests.ps1
```

### 方案4：永久设置PowerShell编码

在PowerShell配置文件中添加UTF-8设置：

```powershell
# 1. 打开PowerShell配置文件
notepad $PROFILE

# 2. 添加以下内容
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 3. 保存并重启PowerShell
```

## 📝 技术说明

测试文件已包含以下编码设置：

```python
import sys
import io

# 设置标准输出编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

但是，**loguru库的日志输出不受此影响**，仍然需要在终端层面设置UTF-8代码页（`chcp 65001`）才能正确显示。

## 🎯 验证编码设置

运行以下命令检查当前代码页：

```powershell
chcp
```

应该看到：

- `Active code page: 65001` ✅ UTF-8（正确）
- `Active code page: 936` ❌ GBK（会乱码）

## 🚀 快速运行测试

```bash
# Windows用户（推荐）
tests\security\run_tests.bat

# PowerShell用户
chcp 65001
python tests/security/run_all_tests.py

# 或使用pytest
chcp 65001
pytest tests/security/ -v
```

## ❓ 常见问题

**Q: 为什么有些输出正常，有些乱码？**  
A: Python的print输出已被重定向到UTF-8，但loguru日志库直接写入stderr，绕过了我们的编码设置。

**Q: 能否让loguru也输出UTF-8？**  
A: 可以配置loguru，但最简单的方案是设置终端代码页（`chcp 65001`）。

**Q: 乱码影响测试结果吗？**  
A: 不影响！只是显示问题，所有测试逻辑正常运行。
