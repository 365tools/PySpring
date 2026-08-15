# PySpring 认证系统配置指南

## 📖 目录

1. [架构概述](#架构概述)
2. [快速开始](#快速开始)
3. [配置文件详解](#配置文件详解)
4. [认证提供者](#认证提供者)
5. [白名单配置](#白名单配置)
6. [角色权限配置](#角色权限配置)
7. [自定义认证提供者](#自定义认证提供者)
8. [最佳实践](#最佳实践)
9. [故障排查](#故障排查)

---

## 架构概述

### 新架构特性

PySpring 认证系统基于 **责任链模式（Chain of Responsibility Pattern）** 重构，具有以下特性：

1. **配置驱动**：所有配置通过 YAML 文件管理，无需修改代码
2. **可扩展**：支持多种认证方式（JWT、API Key、OAuth2 等）
3. **优先级控制**：认证提供者按优先级顺序执行
4. **灵活白名单**：支持精确匹配、前缀匹配、正则匹配
5. **统一接口**：所有认证提供者继承统一的基类

### 核心组件

```
┌──────────────────────────────────────────────────────────┐
│                   FastAPI Application                     │
└─────────────────────┬────────────────────────────────────┘
                      │
         ┌────────────▼───────────────┐
         │  AuthenticationMiddleware  │  (拦截所有请求)
         └────────────┬───────────────┘
                      │
         ┌────────────▼───────────────┐
         │   AuthenticationChain      │  (责任链管理器)
         └────────────┬───────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
┌─────▼────┐   ┌─────▼────┐   ┌─────▼────┐
│   JWT    │   │ API Key  │   │ OAuth2   │  (认证提供者)
│ Provider │   │ Provider │   │ Provider │
└──────────┘   └──────────┘   └──────────┘
```

### 工作流程

1. **请求拦截**：`AuthenticationMiddleware` 拦截所有 HTTP 请求
2. **白名单检查**：检查请求路径是否在白名单中
3. **认证链执行**：按优先级顺序执行所有启用的认证提供者
4. **角色验证**（可选）：验证用户角色权限
5. **注入用户信息**：将认证信息注入到 `request.state`
7. **继续处理**：交给业务逻辑处理

---

## 快速开始

### 1. 配置文件

复制示例配置文件：

```bash
cp config/security.example.yaml config/security.yaml
```

### 2. 最小配置

编辑 `config/security.yaml`：

```yaml
authentication:
  enabled: true
  
  jwt:
    secret_key: null  # 通过环境变量 JWT_SECRET_KEY 设置
    algorithm: "HS256"
    access_token_expire: 3600
  
  providers:
    - name: "jwt"
      type: "JWTAuthProvider"
      enabled: true
      priority: 1
      config:
        token_sources: ["header", "cookie", "query"]
        token_prefix: "Bearer"
  
  whitelist:
    exact_paths:
      - "/api/auth/login"
      - "/api/auth/register"
      - "/docs"
```

### 3. 环境变量

设置 JWT 密钥（生产环境**必须**）：

```bash
# Linux/Mac
export JWT_SECRET_KEY="your-super-secret-key-change-in-production"

# Windows
set JWT_SECRET_KEY=your-super-secret-key-change-in-production
```

### 4. 初始化认证系统

在应用启动时初始化：

```python
from pyspring.security.auth.factory import AuthenticationInitializer
from pyspring.security.auth.impl.token import TokenManagerService

# 获取 TokenManagerService 实例（通过 IoC 容器）
token_manager = app_container.service(TokenManagerService)

# 初始化认证系统
AuthenticationInitializer.initialize(token_manager)
```

### 5. 注册中间件

在 FastAPI 应用中注册：

```python
from fastapi import FastAPI
from pyspring.security.auth.middleware.auth import AuthenticationMiddleware

app = FastAPI()

# 注册认证中间件
app.add_middleware(AuthenticationMiddleware)
```

### 6. 测试

```bash
# 访问公开路径（无需认证）
curl http://localhost:8000/docs

# 访问受保护路径（需要认证）
curl -H "Authorization: Bearer <your-token>" http://localhost:8000/api/user/profile
```

---

## 配置文件详解

### 认证配置 (authentication)

```yaml
authentication:
  # 是否启用认证（false 则所有请求放行）
  enabled: true
  
  # JWT 配置
  jwt:
    secret_key: null           # JWT 密钥（必须通过环境变量设置）
    algorithm: "HS256"         # 签名算法
    access_token_expire: 3600  # Access Token 过期时间（秒）
    refresh_token_expire: 2592000  # Refresh Token 过期时间（秒）
```

**⚠️ 安全提示**：

- `secret_key` 在生产环境**必须**通过环境变量 `JWT_SECRET_KEY` 设置
- 密钥长度建议 **32 字符以上**
- 定期更换密钥（旧 Token 会失效）

### 认证提供者 (providers)

```yaml
providers:
  - name: "jwt"              # 提供者名称（唯一标识）
    type: "JWTAuthProvider"  # 提供者类型
    enabled: true            # 是否启用
    priority: 1              # 优先级（数字越小优先级越高）
    config:                  # 提供者特定配置
      token_sources:         # Token 来源优先级
        - "header"           # 1. Authorization Header
        - "cookie"           # 2. Cookie
        - "query"            # 3. URL 参数
      token_prefix: "Bearer" # Token 前缀
```

**多提供者示例**：

```yaml
providers:
  # 主要认证方式：JWT
  - name: "jwt"
    type: "JWTAuthProvider"
    enabled: true
    priority: 1
  
  # 备用认证方式：API Key（服务间调用）
  - name: "api_key"
    type: "APIKeyAuthProvider"
    enabled: true
    priority: 2
    config:
      header_name: "X-API-Key"
  
  # 第三方认证：OAuth2
  - name: "oauth2"
    type: "OAuth2AuthProvider"
    enabled: false
    priority: 3
```

### 白名单配置 (whitelist)

```yaml
whitelist:
  # 精确匹配（路径必须完全一致）
  exact_paths:
    - "/"
    - "/health"
    - "/api/auth/login"
    - "/api/auth/register"
  
  # 前缀匹配（以这些前缀开头的所有路径）
  prefix_paths:
    - "/static/"
    - "/api/public/"
  
  # 正则表达式匹配（高级模式）
  regex_patterns:
    - "^/api/v[0-9]+/public/.*"  # 所有版本的 public API
    - "^/download/[a-z0-9]+$"    # 下载链接
```

**匹配优先级**：

1. **精确匹配** (exact_paths)
2. **前缀匹配** (prefix_paths)
3. **正则匹配** (regex_patterns)

任一匹配成功，即视为白名单路径。

### 授权配置 (authorization)

```yaml
authorization:
  enabled: true  # 是否启用角色验证
  
  # 路径-角色映射
  role_mappings:
    # 精确路径
    "/api/admin/users":
      - "admin"
    
    # 通配符路径
    "/api/admin/*":
      - "admin"
    "/api/user/*":
      - "user"
      - "admin"  # admin 也可以访问 user 路径
  
  # 角色继承
  role_hierarchy:
    super_admin:
      inherits: ["admin"]  # 超级管理员继承管理员权限
    admin:
      inherits: ["user"]   # 管理员继承用户权限
    user:
      inherits: []
```

**角色继承示例**：

- `super_admin` 可以访问：`admin` 权限 + `user` 权限 + `super_admin` 权限
- `admin` 可以访问：`user` 权限 + `admin` 权限
- `user` 可以访问：`user` 权限

### 安全配置 (security)

```yaml
security:
  # 限流配置
  rate_limit:
    enabled: false
    default_limit: 60  # 每分钟 60 次
    path_limits:
      "/api/auth/login": 5  # 登录接口：每分钟 5 次
  
  # CORS 配置
  cors:
    enabled: true
    allow_origins:
      - "http://localhost:3000"
      - "https://yourdomain.com"
    allow_credentials: true
```

---

## 认证提供者

### JWT 认证提供者

**特性**：

- 支持多种 Token 来源（Header、Cookie、URL 参数）
- 自动验证 Token 有效性和过期时间
- 黑名单机制（已撤销的 Token）
- 两级存储（Redis + 数据库）

**Token 提取优先级**：

1. **Authorization Header**: `Authorization: Bearer <token>`
2. **Cookie**: `access_token=<token>`
3. **URL 参数**: `?token=<token>`

**示例**：

```python
# 方式 1: Authorization Header（推荐）
curl -H "Authorization: Bearer eyJhbGc..." http://localhost:8000/api/user/profile

# 方式 2: Cookie
curl -b "access_token=eyJhbGc..." http://localhost:8000/api/user/profile

# 方式 3: URL 参数（仅用于特殊场景，如 WebSocket）
curl http://localhost:8000/api/user/profile?token=eyJhbGc...
```

### API Key 认证提供者（示例）

**配置**：

```yaml
providers:
  - name: "api_key"
    type: "APIKeyAuthProvider"
    enabled: true
    priority: 2
    config:
      header_name: "X-API-Key"
      verify_ip: true  # 是否验证 IP 白名单
```

**使用**：

```python
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/service/action
```

### OAuth2 认证提供者（示例）

**配置**：

```yaml
providers:
  - name: "oauth2"
    type: "OAuth2AuthProvider"
    enabled: true
    priority: 3
    config:
      providers:
        - google
        - github
        - wechat
```

---

## 白名单配置

### 精确匹配

路径必须完全一致：

```yaml
exact_paths:
  - "/"                        # 根路径
  - "/api/auth/login"          # 登录接口
  - "/docs"                    # 文档页面
```

**示例**：

- ✅ `/api/auth/login` → 匹配
- ❌ `/api/auth/login/` → 不匹配（尾部斜杠）
- ❌ `/api/auth/login?code=123` → 不匹配（有参数）

### 前缀匹配

以指定前缀开头的所有路径：

```yaml
prefix_paths:
  - "/static/"                 # 所有静态文件
  - "/api/public/"             # 所有公开 API
  - "/download/"               # 所有下载路径
```

**示例**：

- ✅ `/static/css/style.css` → 匹配
- ✅ `/api/public/announcement` → 匹配
- ❌ `/api/private/data` → 不匹配

### 正则匹配

支持完整的正则表达式：

```yaml
regex_patterns:
  - "^/api/v[0-9]+/public/.*"  # 所有版本的 public API
  - "^/download/[a-f0-9-]{36}$"  # UUID 格式的下载链接
  - "^/share/[a-z0-9]+$"       # 分享链接
```

**示例**：

- ✅ `/api/v1/public/users` → 匹配
- ✅ `/api/v2/public/posts` → 匹配
- ✅ `/download/550e8400-e29b-41d4-a716-446655440000` → 匹配
- ❌ `/api/v1/private/users` → 不匹配

### 通配符匹配（在 role_mappings 中支持）

使用 `*` 匹配任意字符：

```yaml
role_mappings:
  "/api/admin/*":              # 所有 admin 路径
    - "admin"
  "/api/user/*/profile":       # 用户个人资料路径
    - "user"
```

---

## 角色权限配置

### 路径-角色映射

定义哪些路径需要哪些角色才能访问：

```yaml
role_mappings:
  # 精确路径匹配
  "/api/admin/users":
    - "admin"              # 仅 admin 角色可访问
  
  "/api/admin/settings":
    - "admin"
    - "super_admin"        # admin 或 super_admin 可访问
  
  # 通配符匹配
  "/api/admin/*":
    - "admin"              # 所有 admin 路径需要 admin 角色
  
  "/api/user/*":
    - "user"
    - "admin"              # user 或 admin 可访问
```

**匹配规则**：

- 用户角色 **包含在** 所需角色列表中，即可访问
- 支持多个角色（OR 关系）

### 角色继承

子角色自动继承父角色的所有权限：

```yaml
role_hierarchy:
  super_admin:
    inherits: ["admin"]    # 继承 admin 的所有权限
  admin:
    inherits: ["user"]     # 继承 user 的所有权限
  user:
    inherits: []           # 无继承
```

**继承示例**：

假设路径 `/api/user/profile` 需要 `user` 角色：

- ✅ `user` 角色 → 可访问
- ✅ `admin` 角色 → 可访问（继承了 `user`）
- ✅ `super_admin` 角色 → 可访问（继承了 `admin`，`admin` 继承了 `user`）
- ❌ `guest` 角色 → 无法访问

---

## 自定义认证提供者

### 1. 创建提供者类

继承 `BaseAuthProvider` 或 `AuthProvider`：

```python
from typing import Optional, Any
from fastapi import Request
from pyspring.security.auth.providers.base import BaseAuthProvider, AuthenticationResult

class CustomAuthProvider(BaseAuthProvider):
    """自定义认证提供者"""
    
    async def extract_credentials(self, request: Request) -> Optional[Any]:
        """从请求中提取凭证"""
        # 例如：从自定义 Header 提取
        custom_token = request.headers.get("X-Custom-Auth")
        return custom_token
    
    async def validate_credentials(self, credentials: Any) -> AuthenticationResult:
        """验证凭证"""
        # 实现自定义验证逻辑
        if self.verify_custom_token(credentials):
            return AuthenticationResult(
                success=True,
                user_id="user123",
                username="custom_user",
                roles=["custom_role"],
                provider_name=self.name
            )
        else:
            return AuthenticationResult(
                success=False,
                error_message="自定义认证失败",
                provider_name=self.name
            )
    
    def verify_custom_token(self, token: str) -> bool:
        """自定义 Token 验证逻辑"""
        # 实现您的验证逻辑
        return token == "valid-token"
```

### 2. 注册提供者类型

```python
from src.pyspring.security.auth.factory import AuthenticationInitializer

# 注册自定义提供者类型
AuthenticationInitializer.register_custom_provider(
    provider_type="CustomAuthProvider",
    provider_class=CustomAuthProvider
)
```

### 3. 配置文件

在 `security.yaml` 中添加配置：

```yaml
providers:
  - name: "custom"
    type: "CustomAuthProvider"
    enabled: true
    priority: 10
    config:
      # 自定义配置参数
      custom_param: "value"
```

### 4. 初始化

```python
from src.pyspring.security.auth.factory import AuthenticationInitializer

# 注册自定义提供者
AuthenticationInitializer.register_custom_provider(
    "CustomAuthProvider", CustomAuthProvider
)

# 初始化认证系统
AuthenticationInitializer.initialize(token_manager)
```

---

## 最佳实践

### 1. 环境分离

**开发环境** (`config/security.dev.yaml`):

```yaml
authentication:
  enabled: true
  providers:
    - name: "jwt"
  
authorization:
  enabled: false  # 开发时禁用角色验证

security:
  rate_limit:
    enabled: false  # 开发时禁用限流
```

**生产环境** (`config/security.prod.yaml`):

```yaml
authentication:
  enabled: true
  jwt:
    access_token_expire: 1800  # 30 分钟
  providers:
    - name: "jwt"

authorization:
  enabled: true

security:
  rate_limit:
    enabled: true
    default_limit: 30  # 更严格的限流
```

### 2. JWT 密钥管理

```bash
# 生成安全的随机密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 环境变量设置（Linux/Mac）
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"

# Docker 环境
docker run -e JWT_SECRET_KEY="your-secret-key" your-app
```

### 3. Token 有效期

**推荐配置**：

| Token 类型      | 开发环境 | 生产环境  | 高安全场景 |
|---------------|------|-------|-------|
| Access Token  | 1 小时 | 30 分钟 | 15 分钟 |
| Refresh Token | 30 天 | 7 天   | 3 天   |

```yaml
jwt:
  access_token_expire: 1800   # 30 分钟
  refresh_token_expire: 604800  # 7 天
```

### 4. 白名单最小化原则

只添加真正需要公开访问的路径：

```yaml
whitelist:
  exact_paths:
    - "/api/auth/login"      # ✅ 必须公开
    - "/api/auth/register"   # ✅ 必须公开
    - "/health"              # ✅ 健康检查
    - "/docs"                # ⚠️ 生产环境建议移除
    # - "/api/user/profile"  # ❌ 不应公开
```

### 5. 角色最小权限原则

```yaml
role_mappings:
  # ✅ 好的实践：明确指定角色
  "/api/admin/users":
    - "admin"
  
  "/api/user/profile":
    - "user"
  
  # ⚠️ 避免：过度开放
  # "/api/*":
  #   - "user"  # 所有路径都允许 user 访问
```

### 6. 日志记录

启用详细的认证日志：

```python
from pyspring.log.loguru.logger import logger

# 在认证失败时记录
logger.warning(f"认证失败: {path} - {error_message}")

# 在认证成功时记录
logger.info(f"认证成功: {path} - 用户: {username}")
```

---

## 故障排查

### 问题 1: "未提供认证凭证"

**错误信息**：

```json
{
  "code": 401,
  "message": "认证失败",
  "detail": "jwt: 未找到认证凭证"
}
```

**原因**：

- 没有在请求中包含 Token
- Token 格式不正确

**解决方案**：

```bash
# 检查 Token 格式
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/user/profile

# 检查 Token 来源配置
cat config/security.yaml | grep token_sources
```

### 问题 2: "Token 无效或已过期"

**错误信息**：

```json
{
  "code": 401,
  "message": "认证失败",
  "detail": "jwt: Token 验证失败: Signature verification failed"
}
```

**原因**：

- Token 已过期
- JWT 密钥不匹配
- Token 被篡改

**解决方案**：

```bash
# 检查 Token 是否过期
python -c "import jwt; print(jwt.decode('your-token', options={'verify_signature': False}))"

# 检查 JWT 密钥
echo $JWT_SECRET_KEY

# 重新登录获取新 Token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```

### 问题 3: "权限不足"

**错误信息**：

```json
{
  "code": 403,
  "message": "权限不足",
  "detail": "您没有访问此资源的权限"
}
```

**原因**：

- 用户角色不足
- 角色映射配置错误

**解决方案**：

```bash
# 检查用户角色
python -c "import jwt; print(jwt.decode('your-token', options={'verify_signature': False})['roles'])"

# 检查角色映射
cat config/security.yaml | grep -A 10 role_mappings
```

### 问题 4: 白名单不生效

**症状**：

- 公开路径仍然要求认证

**解决方案**：

```python
# 测试白名单匹配
from pyspring.security.auth.providers.base import PathMatcher
from pyspring.security.auth.config_manager import security_config

whitelist = security_config.get_whitelist_config()
path = "/api/auth/login"

print(PathMatcher.is_match(path, whitelist))  # 应该返回 True
```

### 问题 5: 认证提供者未加载

**症状**：

- 日志显示 "没有可用的认证提供者"

**解决方案**：

```python
# 检查认证链
from src.pyspring.security.auth.chain import auth_chain_manager

chain = auth_chain_manager.get_chain()
print(f"提供者数量: {chain.get_provider_count()}")
print(f"提供者列表: {[p.get_name() for p in chain.get_providers()]}")
```

### 问题 6: 配置文件未生效

**症状**：

- 修改配置后无变化

**解决方案**：

```python
# 重新加载配置
from src.pyspring.security.auth.config_manager import security_config

security_config.reload()

# 重新加载白名单
from src.pyspring.security.auth.chain import auth_chain_manager

auth_chain_manager.get_chain().reload_whitelist()
```

---

## 高级用法

### 动态添加认证提供者

```python
from src.pyspring.security.auth.chain import auth_chain_manager
from pyspring.security.auth.providers.jwt_provider import JWTAuthProvider

# 动态添加提供者
custom_provider = JWTAuthProvider("custom_jwt", {...}, token_manager)
auth_chain_manager.get_chain().register_provider(custom_provider)
```

### 运行时修改白名单

```python
from src.pyspring.security.auth.config_manager import security_config

# 动态添加白名单路径
whitelist = security_config.get_whitelist_config()
whitelist["exact_paths"].append("/api/temp/public")

# 重新加载
auth_chain_manager.get_chain().reload_whitelist()
```

### 自定义错误响应

```python
class CustomAuthenticationMiddleware(AuthenticationMiddleware):
    """自定义错误响应"""
    
    @staticmethod
    def create_error_response(status_code: int, message: str, detail: str = None):
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error_code": f"AUTH_{status_code}",
                "message": message,
                "detail": detail,
                "timestamp": datetime.now().isoformat()
            }
        )
```

---

## 附录

### 完整配置示例

查看 [`config/security.example.yaml`](../config/security.example.yaml)

### 相关文档

- [IoC 容器配置指南](./IOC_CONFIG_GUIDE.md)
- [日志配置指南](./LOGGING_CONFIG_GUIDE.md)
- [数据库配置指南](./REPOSITORIES_CONFIG_GUIDE.md)

### API 参考

- `AuthProvider`: 认证提供者基类
- `AuthenticationChain`: 认证链管理器
- `SecurityConfigManager`: 配置管理器
- `PathMatcher`: 路径匹配工具

---

**最后更新**: 2024-01-XX  
**版本**: PySpring 0.1.0
