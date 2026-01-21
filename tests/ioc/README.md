# IOC 测试套件

本目录包含 PySpring IOC 容器的完整测试用例。

## 测试文件

### 装饰器测试

#### test_bean_decorator_flexible.py

测试 `@Bean` 装饰器的灵活用法（新增）。

**测试内容：**

- `@Bean` - 不加括号（像 `@staticmethod`）
- `@Bean()` - 空括号
- `@Bean(name="...")` - 带name参数
- `@Bean(init_method=..., destroy_method=...)` - 带生命周期方法
- `@Bean(name=..., init_method=..., destroy_method=...)` - 所有参数

```bash
python tests/ioc/test_bean_decorator_flexible.py
```

### 集成测试

#### test_authentication_ioc.py

测试完整的 Authentication 模块 IOC 注入（新增）。

**测试内容：**

- SecurityConfigManager 注入
- TokenService 注入
- ResponseBuilder 注入（通过TokenService）
- Token 生成和解析
- 策略模式（Token Generator）
- Bean方法注册（12个Bean）
- IOC 递归扫描

```bash
python tests/ioc/test_authentication_ioc.py
```

### 模块架构测试

#### 1. test_cache_ioc.py

测试 Cache 模块的 IOC 注入架构：

- 服务自动注册和注入
- Factory 模式验证
- Manager 延迟初始化
- API 层使用场景

```bash
python tests/ioc/test_cache_ioc.py
```

#### 2. test_db_ioc.py

测试 DB 模块的 IOC 注入架构：

- 服务自动注册和注入
- Factory 模式验证
- Manager 延迟初始化
- API 层使用场景

```bash
python tests/ioc/test_db_ioc.py
```

#### 3. test_repositories_ioc.py

测试 Repositories 模块完整集成（Cache + DB）：

- 多模块同时使用
- 完整 API 层场景模拟
- 缓存 + 数据库协同工作

```bash
python tests/ioc/test_repositories_ioc.py
```

## 运行所有测试

使用测试运行器批量执行：

```bash
# 从项目根目录运行
python tests/ioc/run_all_tests.py
```

或使用PowerShell：

```powershell
Push-Location d:\Project\PycharmProjects\PySpring
python tests\ioc\run_all_tests.py
Pop-Location
```

## 测试结果示例

```
================================================================================
IOC 测试套件
================================================================================

✅ PASS - test_bean_decorator_flexible.py
✅ PASS - test_authentication_ioc.py

总计: 2/2 通过
================================================================================
```

## 架构验证要点

### ✅ Bean装饰器灵活性（新增）

- [x] 支持无括号用法（`@Bean`）
- [x] 支持空括号用法（`@Bean()`）
- [x] 支持带参数用法（`@Bean(name="...")`）
- [x] 属性正确设置在方法上

### ✅ IOC容器功能（新增）

- [x] 递归扫描子包
- [x] Component注册
- [x] Bean方法注册
- [x] Bean覆盖Component
- [x] 依赖注入解析
- [x] 策略模式支持

### ✅ 正确的 IOC 模式

1. **服务注册**：使用 `@Component` 装饰器，由 IOC 容器管理
2. **配置注入**：构造函数接收配置对象（如 `CacheConfig`），不是手动参数
3. **Factory 模式**：Factory 通过构造函数注入配置和所有服务实现
4. **延迟初始化**：Manager 使用 `@property provider` 延迟从 factory 获取服务
5. **API 层安全**：`Depends(lambda: get_bean(Manager))` 永远不会得到 None

### ❌ 旧的错误模式（已修复）

1. ~~Manager 有空的 `__init__()`~~
2. ~~Initializer 手动创建服务：`RedisService(host, port, ...)`~~
3. ~~Initializer 调用 `manager.set_provider(service)`~~
4. ~~API 层使用时 provider 可能为 None~~
5. ~~Bean装饰器必须加括号~~（已支持无括号）
6. ~~@wraps 导致属性丢失~~（直接在原函数设置）
7. ~~Bean方法未被扫描~~（修复装饰器语法）
8. ~~SecurityConfigManager重复注册~~（Bean覆盖Component）

## 已修复的关键问题

### 1. Bean装饰器灵活性

**问题**：`@Bean` 必须加括号，不能像 `@staticmethod` 一样使用。

**解决**：

- 实现智能参数检测
- 支持 `@Bean`、`@Bean()` 和 `@Bean(...)` 三种用法
- 详见：`docs/02-core-concepts/FLEXIBLE_DECORATOR_PATTERN.md`

### 2. 装饰器属性丢失

**问题**：使用 `@wraps(func)` 导致自定义属性（`__pyspring_bean__`）丢失。

**解决**：

- 直接在原函数上设置属性
- 不使用 wrapper 函数

### 3. Bean方法未被扫描

**问题**：所有 `@Bean` 方法显示 `@Bean=False`，导致 bean_methods 列表为空。

**解决**：

- 修复所有配置类中的 `@Bean` 为 `@Bean()`
- 现在支持两种写法

### 4. Bean覆盖Component

**问题**：`SecurityConfigManager` 同时被识别为 Component（实现 IManaged）和 Bean。

**解决**：

- Registry 支持 Bean 覆盖 Component 注册
- 优先级：Bean > Primary > Component

## 架构改进对比

| 方面          | 旧模式              | 新模式               |
|-------------|------------------|-------------------|
| 服务创建        | 手动创建             | IOC 容器管理          |
| 配置注入        | 手动参数             | 构造函数注入            |
| Manager 初始化 | set_provider()   | @property 延迟初始化   |
| API 层使用     | provider 可能 None | provider 永远非 None |
| 可测试性        | 难以模拟             | 易于依赖注入测试          |

## 运行测试

### 单个测试

```bash
# 分别运行
python tests/ioc/test_bean_decorator_flexible.py
python tests/ioc/test_authentication_ioc.py
python tests/ioc/test_cache_ioc.py
python tests/ioc/test_db_ioc.py
python tests/ioc/test_repositories_ioc.py
```

### 批量运行

```bash
python tests/ioc/run_all_tests.py
```

## 预期输出

所有测试应该显示：

```
✅ 所有测试通过！
✅✅✅ XXX 模块 IOC 架构验证通过 ✅✅✅
```

## 环境要求

测试需要设置以下环境变量（测试会自动设置）：

```bash
JWT_SECRET_KEY=test-secret
DATABASE_TYPE=sqlite
CACHE_TYPE=memory
```

