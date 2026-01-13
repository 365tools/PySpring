# 认证系统迁移指南

从旧版认证系统迁移到新的基于提供者链的认证架构。

## 📋 迁移检查清单

- [ ] 
    1. 创建 `config/security.yaml` 配置文件
- [ ] 
    2. 设置环境变量 `JWT_SECRET_KEY`
- [ ] 
    3. 更新中间件初始化代码
- [ ] 
    4. 初始化认证提供者链
- [ ] 
    5. 移除旧的硬编码白名单
- [ ] 
    6. 测试认证功能
- [ ] 
    7. 验证角色权限

---

## 🔄 代码变更

### 变更 1: 配置文件

**旧版**：硬编码在 `middleware/auth.py` 中

```python
PUBLIC_PATHS: Set[str] = {
    "/",
    "/docs",
    "/api/auth/login",
    # ...
}

PUBLIC_PATH_PREFIXES: List[str] = [
    "/static/",
    "/api/docs",
]
```

**新版**：配置在 `config/security.yaml` 中

```yaml
authentication:
  whitelist:
    exact_paths:
      - "/"
      - "/docs"
      - "/api/auth/login"
    
    prefix_paths:
      - "/static/"
      - "/api/docs/"
```

### 变更 2: 中间件初始化

**旧版**：

```python
# 直接注册中间件
app.add_middleware(
    AuthenticationMiddleware,
    enable_role_check=True
)
```

**新版**：需要先初始化认证提供者链

```python
from pyspring.security.auth.factory import AuthenticationInitializer
from pyspring.security.auth.middleware.auth import AuthenticationMiddleware

# 1. 获取 TokenManagerService（通过 IoC 容器）
token_manager = app_container.service(TokenManagerService)

# 2. 初始化认证系统（加载并注册所有提供者）
AuthenticationInitializer.initialize(token_manager)

# 3. 注册中间件
app.add_middleware(AuthenticationMiddleware)
```

### 变更 3: Token 验证逻辑

**旧版**：直接调用 TokenManagerService

```python
@staticmethod
async def verify_token(token: str) -> Optional[dict]:
    token_service: TokenManagerService = AppContainerManager.service(TokenManagerService)
    payload = await token_service.verify_token(token)
    return payload
```

**新版**：通过认证提供者链

```python
# 在 dispatch 方法中
auth_result = await self.auth_chain.authenticate(request)

if auth_result.success:
    # 认证成功
    request.state.user_id = auth_result.user_id
    request.state.username = auth_result.username
    request.state.roles = auth_result.roles
```

---

## 🆕 新增功能

### 1. 多认证提供者支持

现在可以配置多个认证方式：

```yaml
providers:
  # JWT 认证（主要）
  - name: "jwt"
    type: "JWTAuthProvider"
    enabled: true
    priority: 1
  
  # API Key 认证（备用）
  - name: "api_key"
    type: "APIKeyAuthProvider"
    enabled: true
    priority: 2
```

### 2. 灵活的白名单配置

支持三种匹配方式：

```yaml
whitelist:
  # 精确匹配
  exact_paths:
    - "/api/auth/login"
  
  # 前缀匹配
  prefix_paths:
    - "/api/public/"
  
  # 正则匹配
  regex_patterns:
    - "^/api/v[0-9]+/public/.*"
```

### 3. 配置驱动的角色权限

```yaml
authorization:
  enabled: true
  
  role_mappings:
    "/api/admin/*":
      - "admin"
    
    "/api/user/*":
      - "user"
      - "admin"
  
  role_hierarchy:
    admin:
      inherits: ["user"]
```

---

## 🧪 测试迁移结果

### 1. 测试白名单

```bash
# 公开路径应该无需认证
curl http://localhost:8000/docs
curl http://localhost:8000/api/auth/login

# 应该返回 200，不需要 Token
```

### 2. 测试 JWT 认证

```bash
# 登录获取 Token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.data.access_token')

# 使用 Token 访问受保护路径
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/user/profile

# 应该返回 200，并包含用户信息
```

### 3. 测试角色权限

```bash
# 普通用户访问管理员路径
curl -H "Authorization: Bearer $USER_TOKEN" http://localhost:8000/api/admin/users

# 应该返回 403 Forbidden

# 管理员访问管理员路径
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/admin/users

# 应该返回 200
```

---

## ⚠️ 注意事项

### 1. 环境变量

**必须**设置 `JWT_SECRET_KEY` 环境变量：

```bash
export JWT_SECRET_KEY="your-super-secret-key"
```

### 2. 配置文件位置

确保 `config/security.yaml` 在正确的位置：

```
项目根目录/
├── config/
│   ├── security.yaml       ← 这里
│   ├── container.yaml
│   ├── logging.yaml
│   └── repositories.yaml
├── src/
└── docs/
```

### 3. 依赖注入顺序

认证系统初始化必须在中间件注册**之前**：

```python
# ✅ 正确顺序
AuthenticationInitializer.initialize(token_manager)  # 1. 初始化
app.add_middleware(AuthenticationMiddleware)        # 2. 注册中间件

# ❌ 错误顺序
app.add_middleware(AuthenticationMiddleware)        # 错误！
AuthenticationInitializer.initialize(token_manager)  # 此时中间件已经初始化
```

### 4. 向后兼容

旧版的 `enable_role_check` 参数仍然支持：

```python
# 仍然有效（会覆盖配置文件的设置）
app.add_middleware(
    AuthenticationMiddleware,
    enable_role_check=True
)
```

---

## 🐛 常见问题

### 问题 1: "没有可用的认证提供者"

**原因**：忘记调用 `AuthenticationInitializer.initialize()`

**解决**：

```python
# 在注册中间件之前初始化
AuthenticationInitializer.initialize(token_manager)
```

### 问题 2: 白名单不生效

**原因**：配置文件路径不正确或格式错误

**解决**：

1. 检查文件位置：`config/security.yaml`
2. 验证 YAML 格式：`python -c "import yaml; yaml.safe_load(open('config/security.yaml'))"`
3. 查看日志：`[SecurityConfigManager] 已加载配置文件`

### 问题 3: JWT 密钥错误

**错误**：`Signature verification failed`

**解决**：

1. 检查环境变量：`echo $JWT_SECRET_KEY`
2. 确保所有服务使用相同的密钥
3. 重新生成 Token

---

## 📚 更多信息

- [完整配置指南](./SECURITY_CONFIG_GUIDE.md)
- [自定义认证提供者教程](./SECURITY_CONFIG_GUIDE.md#自定义认证提供者)
- [最佳实践](./SECURITY_CONFIG_GUIDE.md#最佳实践)

---

**迁移完成后，请删除旧版中间件代码中的硬编码配置！**
