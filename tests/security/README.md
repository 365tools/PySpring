# PySpring Security 测试套件

全方面的安全框架测试，验证认证、授权、Token管理等核心功能的逻辑闭环。

## 📁 测试文件结构

```
tests/security/
├── test_authentication_flow.py      # 认证流程测试
├── test_token_lifecycle.py          # Token生命周期测试
├── test_security_policies.py        # 安全策略测试
├── test_integration.py              # 集成测试
├── test_custom_configuration.py     # 自定义配置测试
├── test_yaml_configuration.py       # YAML配置测试
├── run_all_tests.py                 # 运行所有测试
├── run_tests.bat                    # Windows批处理运行器（推荐）
└── README.md                        # 本文件
```

## 🚀 运行测试

### ✨ 推荐方式（Windows）

直接双击运行批处理文件（自动设置UTF-8编码）：

```bash
tests\security\run_tests.bat
```

### 方式1：PowerShell（需要先设置编码）

```powershell
# 设置UTF-8编码（必须！）
$env:PYTHONIOENCODING='utf-8'
chcp 65001

# 运行所有测试
python tests/security/run_all_tests.py

# 或运行单个测试文件
python tests/security/test_authentication_flow.py
python tests/security/test_token_lifecycle.py
python tests/security/test_security_policies.py
python tests/security/test_integration.py
```

### 方式2：使用pytest

```bash
# 安装pytest
pip install pytest

# 运行所有测试
pytest tests/security/ -v --tb=short

# 运行特定测试
pytest tests/security/test_authentication_flow.py -v
```

### ⚠️ 中文显示问题

如果看到乱码，请确保：

1. **推荐**：使用 `run_tests.bat` 批处理文件（自动设置编码）
2. 或手动执行两个命令：
   ```powershell
   $env:PYTHONIOENCODING='utf-8'
   chcp 65001
   ```
3. 或在PowerShell中设置：`[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`

**关键**：必须同时设置 `PYTHONIOENCODING` 环境变量和 `chcp 65001` 代码页才能完全显示中文。

## 🧪 测试套件说明

### 1. **test_authentication_flow.py** - 认证流程测试

测试完整的用户认证流程：

- ✅ 用户注册成功
- ✅ 密码登录成功
- ✅ 时序攻击防护（用户存在vs不存在的时间应相近）
- ✅ Token生成和验证
- ✅ Refresh Token流程
- ✅ 错误消息一致性（不泄露用户存在性）

**关键验证点**：

- 时序差异 < 100ms
- 错误消息完全一致
- Token包含所有必需字段（sub, email, jti, type, exp, iat）

### 2. **test_token_lifecycle.py** - Token生命周期测试

测试Token从生成到撤销的完整生命周期：

- ✅ Token JTI生成和唯一性
- ✅ Token黑名单机制
- ✅ Refresh Token撤销加入黑名单
- ✅ 拒绝无JTI的Token
- ✅ Token过期处理
- ✅ Token类型区分（access vs refresh）
- ✅ 黑名单容错机制（Redis → DB → Reject）

**关键验证点**：

- 每个Token的JTI都是唯一UUID
- 撤销时写入数据库和Redis双重存储
- 无JTI的Token被拒绝撤销
- 黑名单查询失败时采用安全优先策略

### 3. **test_security_policies.py** - 安全策略测试

测试各种安全防护机制：

- ✅ 时序攻击防护（用户枚举）
- ✅ 登录错误消息一致性
- ✅ 注册错误消息一致性
- ✅ 用户ID输入验证
- ✅ JWT密钥强制验证
- ✅ 密码哈希安全性
- ✅ 密码并发更新保护
- ✅ Dummy Hash实现

**关键验证点**：

- 时序差异 < 100ms（防止用户枚举）
- 所有错误消息统一（不泄露用户存在性）
- 输入验证包含类型检查、边界验证、异常捕获
- 使用bcrypt安全哈希（不使用MD5/SHA1）
- 密码更新使用select_for_update锁

### 4. **test_integration.py** - 集成测试

模拟真实用户场景：

- ✅ 完整用户旅程（注册→登录→访问→刷新→登出）
- ✅ 多设备登录（同一用户在不同设备）
- ✅ Token过期和刷新流程
- ✅ 安全上下文流程

**关键验证点**：

- 不同设备的Token具有不同JTI
- 过期Token被正确拒绝
- Refresh Token可用于获取新Access Token
- 新旧Token的JTI不同

### 5. **test_custom_configuration.py** - 自定义配置测试

测试框架的可扩展性和用户自定义能力：

- ✅ 自定义用户表结构（添加额外字段）
- ✅ 自定义Token黑名单表
- ✅ 自定义@Bean - 登录提供者
- ✅ 自定义Token Payload构建器
- ✅ 自定义用户提供者（多数据源）
- ✅ 自定义响应构建器
- ✅ 集成测试 - 完整自定义配置流程
- ✅ @ConditionalOnMissingBean条件覆盖

**关键验证点**：

- 用户可以自定义数据表结构，添加业务字段
- 通过@Bean注册自定义实现
- @Configuration类被正确识别
- @ConditionalOnMissingBean实现条件注册
- 自定义实现可以覆盖框架默认实现
- 多数据源用户提供者（数据库+LDAP）
- 自定义Token Payload包含额外业务信息
- 自定义响应格式符合业务需求

### 6. **test_yaml_configuration.py** - YAML配置测试

测试YAML配置文件的加载、解析和验证：

- ✅ security.yaml配置加载
- ✅ JWT配置结构验证
- ✅ 环境变量覆盖配置
- ✅ 白名单配置验证
- ✅ 认证提供者配置
- ✅ 授权配置验证
- ✅ JWT加密配置
- ✅ 配置文件不存在时的降级策略
- ✅ 自定义YAML配置结构验证
- ✅ 配置与框架设计兼容性检查

**关键验证点**：

- YAML配置文件正确加载和解析
- JWT配置包含所有必需字段（algorithm, token_expire等）
- 环境变量可以覆盖YAML配置（优先级：ENV > YAML > 默认）
- 白名单支持三种类型（精确匹配、前缀匹配、正则匹配）
- 认证提供者配置完整（jwt, api_key, oauth2）
- 授权配置包含角色映射和层级
- JWT加密可选配置
- 配置文件缺失时使用默认配置
- 配置结构符合框架设计要求

---

## 🚀 运行测试

### 运行所有测试

```bash
# 方式1：使用总测试脚本
python tests/security/run_all_tests.py

# 方式2：从项目根目录运行
cd d:\Project\PycharmProjects\PySpring
python -m tests.security.run_all_tests
```

### 运行单个测试套件

```bash
# 认证流程测试
python tests/security/test_authentication_flow.py

# Token生命周期测试
python tests/security/test_token_lifecycle.py

# 安全策略测试
python tests/security/test_security_policies.py

# 集成测试
python tests/security/test_integration.py

# 自定义配置测试
python tests/security/test_custom_configuration.py

# YAML配置测试
python tests/security/test_yaml_configuration.py
```

### 使用pytest运行（如果已安装）

```bash
pytest tests/security/ -v
pytest tests/security/test_authentication_flow.py -v
```

## 📊 测试覆盖范围

### 认证模块

- ✅ 用户注册（DefaultRegisterService）
- ✅ 用户登录（DefaultLoginService）
- ✅ 密码验证（DefaultPasswordLoginProvider）
- ✅ 用户管理（DefaultUserManagerService）

### Token管理

- ✅ Token生成（JWTTokenGenerator）
- ✅ Token验证（TokenService）
- ✅ Token撤销（黑名单机制）
- ✅ Refresh Token流程

### 安全防护

- ✅ 时序攻击防护（Dummy Hash）
- ✅ 信息泄露防护（统一错误消息）
- ✅ 输入验证（类型检查、边界验证）
- ✅ 并发控制（select_for_update锁）
- ✅ JWT密钥验证
- ✅ 密码哈希安全性（bcrypt）

### 配置管理

- ✅ 安全配置加载（SecurityConfigManager）
- ✅ JWT加密管理（JWTEncryptionManager）
- ✅ 环境变量优先级

## 🔍 测试策略

### 单元测试

- 使用Mock对象隔离依赖
- 测试单个组件的功能
- 验证边界条件和异常处理

### 集成测试

- 测试组件间的协作
- 模拟真实用户场景
- 验证端到端流程

### 代码审查测试

- 使用inspect模块检查源代码
- 验证安全机制的实现
- 检查是否包含关键保护逻辑

### 性能测试

- 时序攻击防护（时间差异测量）
- Token生成性能
- 并发访问测试

## ✅ 验证的安全修复

根据之前的安全审计，以下Critical和High级别问题已修复并验证：

### Critical级别（4个）

1. ✅ JWT配置硬编码 - 已移至JWTTokenGenerator
2. ✅ 时序攻击漏洞 - 实现Dummy Hash，时差 < 100ms
3. ✅ Token JTI生成 - 使用uuid.uuid4()
4. ✅ 黑名单容错 - 三层降级策略（Redis → DB → Reject）

### High级别（5个）

5. ✅ IOC依赖注入 - 移除@property懒加载
6. ✅ 输入验证不足 - 添加类型检查和边界验证
7. ✅ Refresh Token黑名单 - 撤销时写入黑名单
8. ✅ token[:16]回退 - 强制要求JTI
9. ✅ 并发密码更新 - 使用select_for_update锁

### Medium级别（2个）

10. ✅ 注册消息泄露 - 统一为"用户信息已存在"
11. ✅ 登录消息泄露 - 统一为"用户名或密码错误"

## 📈 测试结果示例

```
================================================================================
PySpring Security 完整测试套件
================================================================================

================================================================================
运行测试套件: 认证流程测试
================================================================================

✅ 用户注册成功 - 通过
✅ 密码登录成功 - 通过
✅ 时序攻击防护 - 通过 (时间差: 2.6ms)
✅ Token生成和验证 - 通过
✅ Refresh Token流程 - 通过
✅ 错误消息一致性 - 通过

测试结果: 6/6 通过

================================================================================
总体结果: 4/4 测试套件通过
================================================================================
```

## 🛠️ 依赖项

测试所需的依赖（已包含在项目中）：

```python
- fastapi-users      # 密码哈希
- pyjwt             # JWT处理
- cryptography      # 加密
- sqlalchemy        # 数据库ORM
- pytest            # 测试框架（可选）
```

## 📝 注意事项

1. **环境变量**：所有测试都会设置`JWT_SECRET_KEY`环境变量
2. **Mock对象**：大部分测试使用Mock避免真实数据库操作
3. **代码审查**：部分测试通过inspect检查源代码实现
4. **异步测试**：使用asyncio.run()运行异步测试

## 🔗 相关文档

- [安全模块文档](../../docs/04-features/SECURITY_FRAMEWORK_DEEP_DIVE.md)
- [认证流程指南](../../docs/02-core-concepts/README.md)
- [Token管理指南](../../docs/04-features/JWT_ENCRYPTION_GUIDE.md)

## 📧 问题反馈

如果发现测试失败或有改进建议，请：

1. 检查环境变量是否正确设置
2. 确认依赖包已安装
3. 查看详细的错误日志
4. 提交Issue或Pull Request
