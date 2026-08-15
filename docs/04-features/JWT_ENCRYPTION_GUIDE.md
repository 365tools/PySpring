# JWT Token 加密功能指南

## 📖 概述

PySpring 认证系统支持对 JWT Token 进行加密，防止 Token 被轻易 base64 解码查看 payload 内容。

### 问题背景

**JWT 默认安全性**：

- ✅ JWT 使用签名（HMAC/RSA）防止篡改
- ❌ JWT payload 是 base64 编码的，任何人都可以解码查看
- ⚠️ 如果 payload 包含敏感信息（如权限、角色），可能存在信息泄露风险

**示例**：未加密的 JWT Token

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwicm9sZXMiOlsiYWRtaW4iXX0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

使用 base64 解码即可查看：

```json
{
  "sub": "1234567890",
  "name": "John Doe",
  "roles": ["admin"]  // 敏感信息泄露
}
```

### 解决方案

**JWT 加密（推荐）**：

- 🔐 对整个 JWT Token 进行 AES 加密
- ✅ 外部无法查看 payload 内容
- ✅ 保持 JWT 无状态特性
- ✅ 性能开销小

**加密后的 Token**：

```
gAAAAABmX8Y5k3J2... (随机密文，无法解码)
```

---

## 🔧 加密方案

### 支持的算法

#### 1. **Fernet（推荐）**

- 基于 **AES-128-CBC + HMAC-SHA256**
- Python `cryptography` 库标准实现
- 自动处理 IV 生成和认证
- 密钥固定 32 字节（base64 编码）

**优点**：

- ✅ 简单易用
- ✅ 安全性高
- ✅ 工业标准
- ✅ 自动处理细节

**缺点**：

- ⚠️ AES-128（128位密钥，足够安全）

#### 2. **AES-GCM（高级选项）**

- 基于 **AES-256-GCM**
- 提供更强的加密（256位密钥）
- 需要手动管理 nonce

**优点**：

- ✅ 更强的加密（256位）
- ✅ 认证加密（AEAD）

**缺点**：

- ⚠️ 实现复杂度稍高
- ⚠️ 需要正确管理 nonce

### 架构设计

```
┌─────────────────────────────────────────────────────┐
│                  用户请求登录                         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          1. 生成 JWT Token (签名)                     │
│          {sub: "123", email: "...", roles: [...]}   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          2. 加密 JWT Token (Fernet/AES-GCM)         │
│          eyJhbGc... → gAAAAABmX8Y5k3J2...           │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          3. 返回加密后的 Token                        │
│          {"access_token": "gAAAAABmX8Y5..."}       │
└─────────────────────────────────────────────────────┘

                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          用户携带 Token 访问受保护路径                 │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          1. 解密 Token (Fernet/AES-GCM)             │
│          gAAAAABmX8Y5... → eyJhbGc...               │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          2. 验证 JWT Token (签名、过期时间)           │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          3. 提取用户信息，继续处理请求                 │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 生成加密密钥

```bash
# 使用工具脚本生成
python tools/generate_encryption_key.py
```

输出示例：

```
============================================================
🔐 JWT 加密密钥生成成功
============================================================

密钥: vQ8eZ7J_Xk2mN9pL0oR6uY4tH1sA3bC5dF7gE8iW9jK=

请将此密钥保存到环境变量中：
------------------------------------------------------------
# Linux/Mac
export JWT_ENCRYPTION_KEY="vQ8eZ7J_Xk2mN9pL0oR6uY4tH1sA3bC5dF7gE8iW9jK="

# Windows PowerShell
$env:JWT_ENCRYPTION_KEY="vQ8eZ7J_Xk2mN9pL0oR6uY4tH1sA3bC5dF7gE8iW9jK="
------------------------------------------------------------
```

或者使用 Python 代码：

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())
```

### 2. 配置加密

编辑 `config/security.yaml`：

```yaml
authentication:
  jwt:
    secret_key: null  # JWT 签名密钥
    algorithm: "HS256"
    access_token_expire: 3600
    refresh_token_expire: 2592000
    
    # JWT 加密配置
    encryption:
      enabled: true  # 启用加密
      encryption_key: null  # 通过环境变量设置
      algorithm: "Fernet"  # 使用 Fernet 算法
```

### 3. 设置环境变量

```bash
# Linux/Mac
export JWT_SECRET_KEY="your-jwt-secret-key"
export JWT_ENCRYPTION_KEY="vQ8eZ7J_Xk2mN9pL0oR6uY4tH1sA3bC5dF7gE8iW9jK="
export JWT_ENCRYPTION_ENABLED="true"

# Windows PowerShell
$env:JWT_SECRET_KEY="your-jwt-secret-key"
$env:JWT_ENCRYPTION_KEY="vQ8eZ7J_Xk2mN9pL0oR6uY4tH1sA3bC5dF7gE8iW9jK="
$env:JWT_ENCRYPTION_ENABLED="true"
```

### 4. 启动应用

```bash
python main.py
```

查看日志确认加密已启用：

```
🔐 JWT 加密已启用 - 算法: Fernet
🔒 全局认证中间件已启动 (基于认证链)
🔐 JWT 加密已启用 - Token 将被加密返回
```

### 5. 测试

**登录获取加密 Token**：

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```

响应（加密后）：

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "gAAAAABmX8Y5k3J2h7LmP9qN0oR5tU3vB6cA1dE4fI7jK8lM...",
    "refresh_token": "gAAAAABmX8Y6n4K3i8MnQ0pO6rS4uU5wC7dB2eF5gJ8kL9mN...",
    "token_type": "bearer"
  }
}
```

**使用加密 Token 访问**：

```bash
curl -H "Authorization: Bearer gAAAAABmX8Y5k3J2..." \
  http://localhost:8000/api/user/profile
```

---

## ⚙️ 配置详解

### 完整配置

```yaml
authentication:
  jwt:
    # JWT 签名配置
    secret_key: null  # 必须通过环境变量 JWT_SECRET_KEY 设置
    algorithm: "HS256"
    access_token_expire: 3600
    refresh_token_expire: 2592000
    
    # JWT 加密配置
    encryption:
      # 是否启用加密
      enabled: false  # 开发环境：false，生产环境：true
      
      # 加密密钥（必须通过环境变量 JWT_ENCRYPTION_KEY 设置）
      encryption_key: null
      
      # 加密算法
      # - Fernet: AES-128-CBC + HMAC (推荐)
      # - AES-GCM: AES-256-GCM (高级)
      algorithm: "Fernet"
```

### 环境变量

| 变量名                      | 必填 | 说明            | 示例                |
|--------------------------|----|---------------|-------------------|
| `JWT_SECRET_KEY`         | ✅  | JWT 签名密钥      | `your-secret-key` |
| `JWT_ENCRYPTION_KEY`     | ⚠️ | 加密密钥（启用加密时必填） | `vQ8eZ7J_Xk2...`  |
| `JWT_ENCRYPTION_ENABLED` | ❌  | 是否启用加密        | `true` / `false`  |

### 不同环境配置

#### 开发环境

```yaml
encryption:
  enabled: false  # 禁用加密，方便调试
```

#### 测试环境

```yaml
encryption:
  enabled: true
  encryption_key: null  # 使用临时密钥（自动生成）
```

#### 生产环境

```yaml
encryption:
  enabled: true
  encryption_key: null  # 必须通过环境变量设置
```

```bash
# .env 文件
JWT_SECRET_KEY="your-production-secret-key-32-chars-min"
JWT_ENCRYPTION_KEY="vQ8eZ7J_Xk2mN9pL0oR6uY4tH1sA3bC5dF7gE8iW9jK="
JWT_ENCRYPTION_ENABLED="true"
```

---

## 🔒 安全最佳实践

### 1. 密钥管理

**✅ 推荐做法**：

- 使用环境变量存储密钥
- 不同环境使用不同密钥（开发、测试、生产）
- 定期轮换密钥（每 3-6 个月）
- 使用密钥管理服务（AWS KMS、Azure Key Vault）

**❌ 错误做法**：

- 不要在代码中硬编码密钥
- 不要将密钥提交到 Git 仓库
- 不要在日志中打印密钥
- 不要在多个环境共用密钥

### 2. 密钥生成

```bash
# 推荐：使用加密库生成随机密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 推荐：使用工具脚本
python tools/generate_encryption_key.py

# ❌ 不推荐：使用简单字符串
encryption_key: "my-simple-password"  # 不安全！
```

### 3. 密钥轮换

**步骤**：

1. **生成新密钥**：
   ```bash
   NEW_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
   ```

2. **更新环境变量**：
   ```bash
   export JWT_ENCRYPTION_KEY_NEW="$NEW_KEY"
   ```

3. **支持双密钥解密**（过渡期）：
   ```python
   # 先尝试新密钥，失败则用旧密钥
   try:
       return decrypt_with_new_key(token)
   except:
       return decrypt_with_old_key(token)
   ```

4. **强制用户重新登录**（简单方案）：
    - 更新密钥后，所有旧 Token 失效
    - 用户需要重新登录获取新 Token

### 4. 监控和审计

```python
# 记录加密/解密失败
logger.warning(f"Token 解密失败: {e}")

# 监控异常解密尝试
if decryption_failures > THRESHOLD:
    alert("可能存在密钥泄露或攻击")
```

---

## 🧪 测试验证

### 1. 验证加密是否生效

```python
# test_encryption.py
from pyspring.security.auth.encryption import jwt_encryption_manager

# 检查是否启用
print(f"加密已启用: {jwt_encryption_manager.is_enabled()}")

# 测试加密/解密
original = "test-jwt-token"
encrypted = jwt_encryption_manager.encrypt(original)
decrypted = jwt_encryption_manager.decrypt(encrypted)

print(f"原始: {original}")
print(f"加密: {encrypted}")
print(f"解密: {decrypted}")
assert original == decrypted, "解密失败！"
```

### 2. 对比加密前后

**未加密**：

```bash
# Token 结构明显（三段式，用点分隔）
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

# 可以 base64 解码查看 payload
echo "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0" | base64 -d
# 输出: {"sub":"1234567890","name":"John Doe"}
```

**加密后**：

```bash
# Token 是随机密文（无法解码）
gAAAAABmX8Y5k3J2h7LmP9qN0oR5tU3vB6cA1dE4fI7jK8lM2nO3pQ4rS5tU6vW7xY8zA9bC0dD1eE2fF3gG4hH5iI6jJ7kK8lL9mM0nN1oO2pP3qQ4rR5sS6t

# 无法解码，只能通过正确的密钥解密
```

### 3. 性能测试

```python
import time
from pyspring.security.auth.impl.token import TokenManagerService

# 测试 1000 次加密/解密
token_manager = TokenManagerService(...)

start = time.time()
for _ in range(1000):
    token = token_manager.create_access_token({"sub": "123"})
    payload = await token_manager.verify_token(token)
end = time.time()

print(f"1000 次加密+解密: {end - start:.2f} 秒")
print(f"平均每次: {(end - start) / 1000 * 1000:.2f} 毫秒")
```

**性能参考**（Fernet）：

- 加密：~0.1-0.3ms
- 解密：~0.1-0.3ms
- **总开销**：~0.2-0.6ms（可接受）

---

## 🐛 故障排查

### 问题 1: "JWT 加密器初始化失败"

**错误信息**：

```
❌ Fernet 加密器初始化失败: Fernet key must be 32 url-safe base64-encoded bytes
```

**原因**：

- 加密密钥格式不正确
- 密钥长度不是 32 字节

**解决**：

```bash
# 使用工具生成正确的密钥
python tools/generate_encryption_key.py

# 或使用 Python
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 问题 2: "Token 解密失败"

**错误信息**：

```
⚠️ Token 解密失败: Invalid token
```

**原因**：

1. 加密密钥不匹配（密钥被更换）
2. Token 被篡改
3. Token 不是加密的（可能是旧 Token）

**解决**：

```python
# 检查密钥是否正确
echo $JWT_ENCRYPTION_KEY

# 检查是否启用加密
cat config/security.yaml | grep -A 5 encryption

# 清除旧 Token，重新登录
```

### 问题 3: 性能下降

**症状**：

- 响应时间明显增加
- CPU 使用率升高

**排查**：

```python
# 使用性能分析工具
import cProfile
cProfile.run('token_manager.create_access_token(...)')

# 检查是否使用了 AES-GCM（比 Fernet 慢）
# 建议使用 Fernet
```

**优化**：

- 使用 Fernet 而非 AES-GCM
- 考虑使用缓存（已加密的 Token 缓存）
- 异步处理加密操作

### 问题 4: 密钥未生效

**症状**：

- 设置了环境变量，但仍使用临时密钥

**检查**：

```bash
# 确认环境变量已设置
echo $JWT_ENCRYPTION_KEY

# 检查应用启动日志
# 应该看到: [SecurityConfigManager] JWT_ENCRYPTION_KEY 已从环境变量加载
```

---

## 🆚 加密方案对比

### JWT 加密 vs JWE

| 特性   | 本方案（JWT + AES） | JWE (RFC 7516)      |
|------|----------------|---------------------|
| 标准化  | ❌ 非标准          | ✅ JWT 官方标准          |
| 实现难度 | ✅ 简单           | ⚠️ 复杂               |
| 库支持  | ✅ cryptography | ⚠️ python-jose 支持有限 |
| 性能   | ✅ 高            | ⚠️ 较低               |
| 互操作性 | ❌ 限于 Python    | ✅ 跨语言               |
| 安全性  | ✅ 足够           | ✅ 足够                |

**推荐**：

- 如果只使用 Python：本方案（简单高效）
- 如果需要跨语言：考虑 JWE

### Fernet vs AES-GCM

| 特性   | Fernet            | AES-GCM        |
|------|-------------------|----------------|
| 密钥长度 | 128位              | 256位           |
| 安全性  | ✅ 高               | ✅ 更高           |
| 性能   | ✅ 快               | ⚠️ 稍慢          |
| 易用性  | ✅ 简单              | ⚠️ 需手动管理 nonce |
| 标准化  | ✅ cryptography 标准 | ✅ NIST 标准      |

**推荐**：

- 一般场景：Fernet（简单高效）
- 高安全场景：AES-GCM（更强加密）

---

## 📚 相关文档

- [认证系统配置指南](./SECURITY_CONFIG_GUIDE.md)
- [Cryptography 库文档](https://cryptography.io/)
- [Fernet 规范](https://github.com/fernet/spec/blob/master/Spec.md)

---

## 🔍 常见问题

### Q1: 加密会影响性能吗？

**A**: 影响很小。Fernet 加密/解密只需 0.1-0.3ms，对整体请求时间（通常 10-100ms）影响不大。

### Q2: 是否需要同时加密 Access Token 和 Refresh Token？

**A**: 是的。两者都包含用户信息，都应加密。系统会自动处理。

### Q3: 加密后 Token 长度会增加吗？

**A**: 会稍微增加（约 30-50%）。这是加密算法的特性，但不会影响传输。

### Q4: 可以在不停机的情况下更换密钥吗？

**A**: 可以，但需要实现双密钥解密机制（过渡期支持新旧密钥）。简单方案是更换密钥后强制用户重新登录。

### Q5: 加密密钥和签名密钥有什么区别？

**A**:

- **签名密钥** (JWT_SECRET_KEY): 用于 JWT 签名，防止篡改
- **加密密钥** (JWT_ENCRYPTION_KEY): 用于加密整个 JWT，防止被解码查看

两者都很重要，都需要妥善保管。

---

**版本**: PySpring 0.1.0
