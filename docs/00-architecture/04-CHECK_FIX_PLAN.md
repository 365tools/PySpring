# PySpring Check 修复计划（CHECK_FIX_PLAN）

> 版本：v0.1
> 目的：系统性修复 `pyspring check` 暴露的所有 error/warning，**从源头修复，不抑制**。

---

## 一、check 命令能力矩阵

`pyspring check` 提供以下子检查（来源 `commands/check.py`）：

| 子命令 | 职责 | 修复方式 |
|--------|------|---------|
| `basedpyright` | 深度类型检查（IDE 风格诊断） | 补全类型注解、消除 `Any`、修抽象使用 |
| `encoding` | UTF-8 无 BOM 校验 | `--fix` 转码 |
| `diagnose` | 环境/Python/安装诊断 | 按报告修复环境 |
| `imports-circular` | 循环导入检测（AST） | 重构导入方向 |
| `imports-explicit` | 包级导入→显式子模块 | `--fix` |
| `imports-lift` | 局部导入→模块顶层 | `--fix` |
| `imports-refactor` | 相对/绝对导入转换 | `--fix` |
| `imports-validate` | 缺失模块解析 | `--fix` |
| `imports-reset` | 重建 pyspring 导入（危险） | 慎用 |
| `references` | 未解析符号引用 | `--fix` |

---

## 二、已确认的阻塞性 Bug（P0）

### 2.1 `help.py` GBK 编码崩溃

**文件**：`packages/pyspring-cli/src/pyspring_cli/core/ui/help.py:50`

**现象**：运行 `pyspring check`（无子命令时）抛 `UnicodeEncodeError: 'gbk' codec can't encode character '\u279c'`。

**根因**：`print(f"  {Colors.OKCYAN}\u279c {name:<{max_len}}...")` 使用 Unicode 箭头字符 `➜`（U+279C），Windows 默认 GBK 控制台无法编码。

**修复方案（从源头）**：
- 方案 A（推荐）：将 UI 输出的 Unicode 装饰符替换为纯 ASCII（如 `>`、`-`、`|`）。
- 方案 B：为 CLI 配置 UTF-8 输出流（`sys.stdout.reconfigure(encoding='utf-8')`），但治标不治本且可能影响其他工具。
- 方案 C：统一走日志系统而非 `print`。

**符合规范**：DEV_GUIDELINES §4.1「禁止非 ASCII 符号进入 print/日志」。

**命令验证**：
```bash
uv run pyspring check  --all   # 修复后应正常输出，无崩溃
```

---

## 三、修复策略（从源头，不抑制）

### 3.0 禁止抑制总则（硬性约束）

> 所有问题**必须从源头解决**。以下抑制手段在项目中**严格禁止**，出现即视为违规：

| 类别 | 禁止 | 源头修复 |
|------|------|---------|
| 类型 | `# type: ignore` / `# pyright: ignore` / `# mypy: ignore` | 补全类型、`TypeAlias`/`Generic`/`TypeGuard` |
| Lint | `# noqa` / `# ruff: noqa` / `# flake8: noqa` / `# pylint: disable` | 修正代码符合规范 |
| 异常 | `except: pass` / `except Exception: pass` / `except: continue` | 记录日志或明确处理 |
| 覆盖 | `# pragma: no cover` | 补测试覆盖 |
| 配置 | 调低 `basedpyright`/`ruff` 严重级别、关闭规则 | 逐个修复至通过 |

> **动态抑制同样禁止**：不得通过修改 `pyproject.toml` / 检查器配置将规则降级为 off 或 warning 来放行既有问题。正确做法是保持规则为 error，并把问题全部修好。

### 3.1 类型检查（basedpyright）

**原则**：不在代码中加 `# type: ignore` / `# pyright: ignore` 抑制错误，而是补齐类型信息。

| 规则 | 修复动作 |
|------|---------|
| `reportExplicitAny` | 用具体类型/`TypeAlias`/`Generic` 替代 `Any` |
| `reportUnknownParameterType` | 补全参数类型注解 |
| `reportDeprecated` | 升级到新 API（如旧 `system_service.get()`） |
| `reportAbstractUsage` | 实现抽象方法或用 `@abstractmethod` 标注 |
| `reportMissingTypeStubs` | 补充类型存根或 `py.typed` |

### 3.2 导入检查

- `imports-circular`：调整模块结构，依赖方向统一为 `starter → core`。
- `imports-explicit`：将 `from pkg import X` 改为 `from pkg.sub import X`。
- `imports-lift`：局部 import 移到顶层（需确认无循环依赖）。

### 3.3 编码检查

- 全量转 UTF-8 无 BOM。
- 清理非 ASCII 控制字符（如 `\u279c`、特殊 emoji 日志符号）。

---

## 四、执行流程

```
阶段 A：修复阻塞 bug
  1. 修复 help.py 编码崩溃
  2. 确认 `uv run pyspring check --all` 可完整跑完

阶段 B：获取基线
  3. 运行 basedpyright --severity all，导出全部 error/warning 清单

阶段 C：分类修复
  4. 按「类型 / 导入 / 编码 / 引用」分类，从源头逐类修复

阶段 D：门禁验证
  5. 重复运行 check --all，目标 0 error / 0 warning
  6. 无任何 --suppress / ignore 抑制
```

---

## 五、验收标准

- [ ] `uv run pyspring check --all` 完整执行无崩溃
- [ ] `basedpyright --severity all` 0 error / 0 warning
- [ ] 编码检查 0 问题（全 UTF-8 无 BOM）
- [ ] 循环导入 0
- [ ] 未解析引用 0
- [ ] 全项目无任何抑制记号：`# type: ignore`、`# pyright: ignore`、`# mypy: ignore`、`# noqa`、`# ruff: noqa`、`# flake8: noqa`、`# pylint: disable`、`# pragma: no cover`
- [ ] 全项目无 `except: pass` / `except Exception: pass` 吞异常
- [ ] `pyproject.toml` / 检查器配置中无通过降级严重级别来放行问题的设置
- [ ] 所有规则保持 error 级别，问题全部从源头修复通过
