# PySpring 配置架构分析与重构方案

## 问题诊断

### 当前配置文件混乱的问题

**问题1：配置文件职责不清**

- `config/` 目录的配置文件到底是谁用的？
    - 是框架开发者测试用的？
    - 还是示例项目的配置？
    - 还是用户项目应该有的配置？

**问题2：配置层次模糊**

- 没有明确区分：框架级配置 vs 用户级配置
- framework.yaml 新加入后，更加混乱
- 用户不知道哪些配置可以改，哪些不能改

**问题3：配置文件重复**

- `config/container.yaml` vs `src/pyspring/templates/config/container.yaml`
- 两个文件内容相似但不完全相同，容易混淆

---

## 配置层次设计原则

### 三层配置架构

#### 1. 框架级配置（Framework Level）

**位置：** `src/pyspring/config/`  
**维护者：** 框架开发者  
**用户权限：** 🚫 不可编辑（打包到框架内部）

**职责：**

- 框架内部行为控制
- 框架组件初始化顺序
- 框架默认值定义

**文件列表：**

```
src/pyspring/config/
├── framework.yaml          # 框架核心配置
│   ├── scan_packages       # 框架要扫描的内部包
│   ├── auto_configuration  # 自动配置开关
│   └── internal_settings   # 框架内部设置
│
└── defaults/               # 框架默认值（可被用户覆盖）
    ├── security.yaml       # 安全模块默认配置
    ├── database.yaml       # 数据库模块默认配置
    └── logging.yaml        # 日志模块默认配置
```

#### 2. 用户项目配置（User Project Level）

**位置：** `<user_project>/config/`  
**维护者：** 用户  
**用户权限：** ✅ 完全可编辑

**职责：**

- 应用程序配置（端口、名称等）
- 数据库连接信息
- 自定义业务配置
- 覆盖框架默认值

**文件列表：**

```
user_project/config/
├── application.yaml        # 应用基本配置
├── database.yaml           # 数据库配置
├── security.yaml           # 安全配置（覆盖框架默认）
└── custom.yaml             # 用户自定义配置
```

#### 3. 配置模板（Templates）

**位置：** `src/pyspring/templates/`  
**维护者：** 框架开发者  
**用户权限：** 📋 脚手架模板（复制后可编辑）

**职责：**

- `pyspring init` 生成项目时使用
- 提供最佳实践示例
- 包含详细注释说明

**文件列表：**

```
src/pyspring/templates/
├── config/                     # 配置文件模板
│   ├── application.yaml.template
│   ├── database.yaml.template
│   └── security.yaml.template
└── example/config/             # 完整示例项目配置
    ├── application.yaml
    └── database.yaml
```

---

## 配置优先级与覆盖规则

### 配置加载顺序

```
1. 框架默认配置（src/pyspring/config/defaults/）
   ↓
2. 用户项目配置（user_project/config/）
   ↓ （覆盖）
3. 环境变量（JWT_SECRET_KEY 等）
   ↓ （覆盖）
4. 代码中显式指定的参数
```

### 配置覆盖示例

**框架默认配置** (`src/pyspring/config/defaults/security.yaml`):

```yaml
security:
  jwt:
    access_token_expire: 3600  # 1小时
  password:
    min_length: 8
```

**用户覆盖配置** (`user_project/config/security.yaml`):

```yaml
security:
  jwt:
    access_token_expire: 7200  # 覆盖为2小时
  # password.min_length 保持框架默认值 8
```

---

## 重构方案

### 阶段1：清理现有配置

1. **明确 `config/` 目录用途**
    - 选项A：作为框架测试配置，重命名为 `tests/config/`
    - 选项B：作为示例项目配置，移动到 `examples/demo_project/config/`
    - **推荐选项A**：测试配置应该和测试代码在一起

2. **整理 framework.yaml**
    - 保留在 `src/pyspring/config/framework.yaml`
    - 仅包含框架内部配置（如 scan_packages）

3. **创建 defaults/ 目录**
   ```
   src/pyspring/config/defaults/
   ├── security.yaml       # 安全模块默认值
   ├── database.yaml       # 数据库模块默认值
   └── logging.yaml        # 日志模块默认值
   ```

### 阶段2：实现配置加载逻辑

```python
class ConfigManager:
    def load_config(self, config_name: str):
        # 1. 加载框架默认配置
        framework_defaults = self._load_framework_defaults(config_name)
        
        # 2. 加载用户项目配置
        user_config = self._load_user_config(config_name)
        
        # 3. 合并配置（用户配置覆盖框架默认）
        merged_config = self._deep_merge(framework_defaults, user_config)
        
        # 4. 应用环境变量覆盖
        final_config = self._apply_env_overrides(merged_config)
        
        return final_config
```

### 阶段3：更新文档和模板

1. 更新所有模板文件的注释
2. 说明哪些配置项可以覆盖
3. 提供配置覆盖示例

---

## 各配置文件的明确定位

### src/pyspring/config/framework.yaml

```yaml
# 框架级配置
# ⚠️  此文件由框架维护，用户不应修改
# 📦 打包到 PySpring 包内部

framework:
  # 框架自动扫描的包（内部组件）
  scan_packages:
    - pyspring.security
    - pyspring.repositories
  
  # 自动配置开关
  auto_configuration:
    enabled: true
    
  # 内部行为
  internal:
    lazy_loading: false
    strict_mode: true
```

### src/pyspring/config/defaults/security.yaml

```yaml
# 安全模块默认配置
# ✅ 用户可通过项目配置覆盖这些值
# 📄 此文件提供框架的默认行为

security:
  authentication:
    enabled: true
    jwt:
      algorithm: "HS256"
      access_token_expire: 3600
  
  password:
    min_length: 8
    require_uppercase: true
    require_digits: true
```

### user_project/config/security.yaml（用户项目）

```yaml
# 用户安全配置
# ✅ 此文件由用户维护
# 🔄 覆盖框架默认值

security:
  authentication:
    jwt:
      access_token_expire: 7200  # 覆盖为2小时
      secret_key: ${JWT_SECRET_KEY}  # 从环境变量读取
  
  password:
    min_length: 10  # 覆盖为10位
```

---

## 推荐的目录结构

### 最终配置目录结构

```
PySpring/
├── src/pyspring/
│   ├── config/
│   │   ├── framework.yaml           # 框架核心配置（不可修改）
│   │   └── defaults/                # 框架默认值（可覆盖）
│   │       ├── security.yaml
│   │       ├── database.yaml
│   │       └── logging.yaml
│   │
│   └── templates/
│       ├── config/                  # 配置模板（生成项目时复制）
│       │   ├── application.yaml.template
│       │   ├── database.yaml.template
│       │   └── security.yaml.template
│       │
│       └── example/                 # 完整示例项目
│           └── config/
│               ├── application.yaml
│               └── database.yaml
│
├── tests/
│   └── config/                      # 测试配置（从 config/ 移过来）
│       ├── application.yaml
│       ├── container.yaml
│       └── security.yaml
│
└── examples/
    └── demo_project/
        └── config/                  # 示例项目配置
            ├── application.yaml
            └── database.yaml
```

---

## 实施步骤

### Step 1: 移动现有配置文件

```bash
# 将根目录的 config/ 移动到 tests/config/
mv config/ tests/config/

# 或移动到 examples/
mkdir -p examples/demo_project
mv config/ examples/demo_project/config/
```

### Step 2: 创建 defaults/ 目录

```bash
mkdir -p src/pyspring/config/defaults/

# 提取框架默认值到 defaults/
# security.yaml, database.yaml, logging.yaml
```

### Step 3: 实现 ConfigManager

- 创建配置加载器
- 实现深度合并逻辑
- 支持环境变量覆盖

### Step 4: 更新所有引用

- 更新代码中的配置加载路径
- 更新文档说明
- 更新测试用例

---

## 用户体验改进

### 改进前（混乱）

```python
# 用户不知道该怎么配置
# 也不知道 pyspring.security 是什么
ApplicationContext.initialize(
    base_packages=['pyspring.security', 'app'],  # ❓ 为什么要加这个？
    config_file='config/container.yaml'
)
```

### 改进后（清晰）

```python
# 框架自动处理一切
ApplicationContext.initialize(
    base_packages=['app'],  # ✅ 只需配置自己的包
    # 框架会自动：
    # 1. 加载 src/pyspring/config/framework.yaml（框架配置）
    # 2. 加载 src/pyspring/config/defaults/*.yaml（框架默认值）
    # 3. 加载 config/*.yaml（用户配置，覆盖默认值）
)
```

---

## 配置文档示例

### 框架文档应该这样写：

#### 配置层次说明

```
📦 框架级配置（你不需要修改）
   src/pyspring/config/
   ├── framework.yaml      # 框架内部行为
   └── defaults/           # 框架默认值

✏️  你的项目配置（你可以修改）
   your_project/config/
   ├── application.yaml    # 应用配置
   ├── database.yaml       # 数据库配置
   └── security.yaml       # 安全配置（覆盖框架默认）

📋 配置模板（pyspring init 时生成）
   生成新项目时，框架会自动创建配置文件
```

#### 配置覆盖示例

```yaml
# 你的 config/security.yaml 可以覆盖框架默认值：

security:
  jwt:
    access_token_expire: 7200  # 覆盖框架默认的 3600
  password:
    min_length: 10             # 覆盖框架默认的 8
```

---

## 总结

### 当前问题

1. ❌ config/ 目录用途不明确
2. ❌ 框架配置和用户配置混在一起
3. ❌ 没有配置覆盖机制
4. ❌ 用户不知道哪些配置可以改

### 改进后

1. ✅ 三层配置架构清晰（框架级/默认值/用户级）
2. ✅ 配置文件职责明确
3. ✅ 支持配置覆盖机制
4. ✅ 用户体验友好
5. ✅ 遵循"约定优于配置"原则

### 下一步行动

1. 决定 `config/` 目录的去向（tests/ 还是 examples/）
2. 创建 `defaults/` 目录并提取框架默认值
3. 实现 ConfigManager 配置加载器
4. 更新文档和模板
5. 更新测试用例
