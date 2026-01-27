# 日志格式切换指南

## 当前格式（绝对路径 - 推荐）

```yaml
console:
  format: '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>File "{file.path}", line {line}</cyan> | {message}'
```

**效果**：

```
File "D:\Project\PycharmProjects\PySpring\test.py", line 46
```

✅ **优点**：IDEA 完美支持，点击即跳转
❌ **缺点**：路径较长

---

## 相对路径版本（简洁）

修改 `config/logging.yaml` 或 `src/pyspring/config/defaults/logging.yaml`：

```yaml
console:
  format: '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>File "{extra[file_relative]}", line {line}</cyan> | {message}'
```

**效果**：

```
File "test_ide_links.py", line 46
File "src/pyspring/log/instance.py", line 15
```

✅ **优点**：路径简洁，易读
❓ **待测试**：IDEA 是否支持相对路径的标准格式跳转

---

## 如何切换

### 方法1：修改用户配置（推荐）

创建或修改 `config/logging.yaml`：

```yaml
logging:
  console:
    # 相对路径版本
    format: '<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>File "{extra[file_relative]}", line {line}</cyan> | {message}'
```

### 方法2：修改框架默认配置

修改 `src/pyspring/config/defaults/logging.yaml` 中的 format 字段。

---

## 测试相对路径是否可跳转

运行测试：

```bash
python test_ide_links.py
```

在 IDEA 控制台中点击相对路径，看是否能跳转。

---

## 建议

1. **开发环境**：使用绝对路径（当前配置）
    - 保证 100% 可跳转

2. **生产环境**：可以使用相对路径
    - 日志文件更简洁
    - 不暴露完整路径

3. **如果相对路径也能跳转**：推荐使用相对路径
    - 既简洁又实用
