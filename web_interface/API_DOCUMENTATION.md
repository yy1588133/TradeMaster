# TradeMaster 认证系统 API 文档

## 概述

TradeMaster 认证系统提供完整的RESTful API，支持用户认证、授权、会话管理和API密钥管理等功能。

**基础URL**: `http://localhost:8000/api/v1`

**认证方式**: Bearer Token (JWT)

**内容类型**: `application/json`

## 🔐 认证端点

### 用户注册

**POST** `/auth/register`

注册新用户账户。

**请求体**:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**响应**:
```json
{
  "message": "注册成功，请查收验证邮件",
  "user": {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": false,
    "role": "user",
    "created_at": "2025-08-15T14:30:00Z"
  }
}
```

### 用户登录

**POST** `/auth/login`

用户身份验证并获取访问令牌。

**请求体**:
```json
{
  "username": "john_doe",
  "password": "SecurePass123!",
  "remember_me": false
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "last_login_at": "2025-08-15T14:30:00Z"
  }
}
```

### 刷新令牌

**POST** `/auth/refresh`

使用刷新令牌获取新的访问令牌。

**请求体**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800
}
```

### 用户登出

**POST** `/auth/logout`

登出当前用户会话。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "all_devices": false
}
```

**响应**:
```json
{
  "message": "登出成功"
}
```

### 获取个人资料

**GET** `/auth/profile`

获取当前用户的详细信息。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "id": 1,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "avatar_url": "https://example.com/avatar.jpg",
  "is_active": true,
  "is_verified": true,
  "role": "user",
  "last_login_at": "2025-08-15T14:30:00Z",
  "login_count": 15,
  "created_at": "2025-08-01T10:00:00Z",
  "updated_at": "2025-08-15T14:30:00Z",
  "settings": {
    "theme": "light",
    "language": "zh-CN",
    "timezone": "Asia/Shanghai"
  }
}
```

### 更新个人资料

**PUT** `/auth/profile`

更新用户个人信息。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "full_name": "John Smith",
  "avatar_url": "https://example.com/new-avatar.jpg",
  "settings": {
    "theme": "dark",
    "language": "en-US"
  }
}
```

**响应**: 与获取个人资料相同

### 修改密码

**PUT** `/auth/password`

修改用户密码。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "current_password": "SecurePass123!",
  "new_password": "NewSecurePass456!",
  "confirm_new_password": "NewSecurePass456!"
}
```

**响应**:
```json
{
  "message": "密码修改成功"
}
```

## 🔑 API密钥管理

### 创建API密钥

**POST** `/api-keys`

为当前用户创建新的API密钥。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "name": "My API Key",
  "permissions": ["read", "write"],
  "ip_whitelist": ["192.168.1.100", "10.0.0.1"],
  "rate_limit": 1000,
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**响应**:
```json
{
  "id": 1,
  "name": "My API Key",
  "key_prefix": "tm_live_",
  "display_key": "tm_live_...xyzw1234",
  "full_key": "tm_live_abcd1234567890efghijklmnopqrstuvwxyzw1234",
  "user_id": 1,
  "permissions": ["read", "write"],
  "ip_whitelist": ["192.168.1.100", "10.0.0.1"],
  "rate_limit": 1000,
  "usage_count": 0,
  "is_active": true,
  "expires_at": "2025-12-31T23:59:59Z",
  "created_at": "2025-08-15T14:30:00Z"
}
```

### 获取API密钥列表

**GET** `/api-keys`

获取当前用户的所有API密钥。

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `skip`: 跳过数量 (默认: 0)
- `limit`: 限制数量 (默认: 100)
- `active_only`: 仅显示激活的密钥 (默认: true)

**响应**:
```json
[
  {
    "id": 1,
    "name": "My API Key",
    "key_prefix": "tm_live_",
    "display_key": "tm_live_...xyzw1234",
    "user_id": 1,
    "permissions": ["read", "write"],
    "rate_limit": 1000,
    "usage_count": 42,
    "last_used_at": "2025-08-15T12:00:00Z",
    "is_active": true,
    "expires_at": "2025-12-31T23:59:59Z",
    "created_at": "2025-08-15T14:30:00Z"
  }
]
```

### 获取API密钥详情

**GET** `/api-keys/{api_key_id}`

获取指定API密钥的详细信息。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**: 与创建API密钥响应相同（不包含full_key）

### 更新API密钥

**PUT** `/api-keys/{api_key_id}`

更新API密钥配置。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "name": "Updated API Key",
  "permissions": ["read"],
  "rate_limit": 500,
  "is_active": true
}
```

**响应**: 与获取API密钥详情相同

### 删除API密钥

**DELETE** `/api-keys/{api_key_id}`

删除指定的API密钥。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**: `204 No Content`

### 停用/激活API密钥

**POST** `/api-keys/{api_key_id}/deactivate`
**POST** `/api-keys/{api_key_id}/activate`

停用或激活API密钥。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**: 与获取API密钥详情相同

### 获取API密钥使用统计

**GET** `/api-keys/{api_key_id}/stats`

获取API密钥的使用统计信息。

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `days`: 统计天数 (默认: 30)

**响应**:
```json
{
  "total_requests": 1000,
  "success_requests": 950,
  "error_requests": 50,
  "success_rate": 95.0,
  "avg_response_time": 150.5,
  "daily_stats": [
    {
      "date": "2025-08-15",
      "count": 50
    }
  ],
  "endpoint_stats": [
    {
      "endpoint": "/api/v1/strategies",
      "count": 200
    }
  ]
}
```

### 获取API密钥使用日志

**GET** `/api-keys/{api_key_id}/usage`

获取API密钥的使用日志。

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `skip`: 跳过数量 (默认: 0)
- `limit`: 限制数量 (默认: 100)
- `days`: 查询天数 (默认: 7)

**响应**:
```json
[
  {
    "id": 1,
    "api_key_id": 1,
    "endpoint": "/api/v1/strategies",
    "method": "GET",
    "ip_address": "192.168.1.100",
    "user_agent": "TradeMaster-Client/1.0",
    "status_code": 200,
    "response_time": 120,
    "created_at": "2025-08-15T14:30:00Z"
  }
]
```

### 获取API密钥速率限制状态

**GET** `/api-keys/{api_key_id}/rate-limit`

获取API密钥当前的速率限制状态。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "limit": 1000,
  "current_usage": 150,
  "remaining": 850,
  "reset_time": "2025-08-15T15:00:00Z",
  "is_exceeded": false
}
```

## 📱 会话管理

### 获取用户会话列表

**GET** `/sessions`

获取当前用户的所有活跃会话。

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `include_inactive`: 是否包含非活跃会话 (默认: false)

**响应**:
```json
[
  {
    "id": 1,
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "is_active": true,
    "is_current": true,
    "expires_at": "2025-08-16T14:30:00Z",
    "last_activity_at": "2025-08-15T14:30:00Z",
    "created_at": "2025-08-15T10:00:00Z",
    "is_expired": false,
    "location": "北京, 中国"
  }
]
```

### 终止指定会话

**DELETE** `/sessions/{session_id}`

终止指定的用户会话。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**: `204 No Content`

### 终止所有会话

**DELETE** `/sessions`

终止用户的所有会话。

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `keep_current`: 是否保留当前会话 (默认: true)

**响应**: `204 No Content`

### 获取当前会话信息

**GET** `/sessions/current`

获取当前会话的详细信息。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**: 与会话列表中的单个会话对象相同

### 获取会话统计信息

**GET** `/sessions/stats`

获取用户会话的统计信息。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "active_sessions": 3,
  "max_sessions": 5,
  "is_over_limit": false,
  "session_timeout_hours": 24
}
```

### 清理过期会话

**POST** `/sessions/cleanup`

清理用户的过期会话。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**: `204 No Content`

### 刷新会话活动时间

**POST** `/sessions/refresh-activity`

更新当前会话的最后活动时间。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**: `204 No Content`

## 🔧 系统端点

### 健康检查

**GET** `/health`

检查系统健康状态。

**响应**:
```json
{
  "status": "healthy",
  "timestamp": 1692115800.123,
  "version": "1.0.0",
  "database": "connected",
  "environment": "development"
}
```

### 系统信息

**GET** `/info`

获取系统基本信息。

**响应**:
```json
{
  "application": {
    "name": "TradeMaster Web Interface",
    "version": "1.0.0",
    "environment": "development"
  },
  "database": {
    "status": "connected",
    "active_connections": 5
  },
  "timestamp": 1692115800.123
}
```

### API状态

**GET** `/api/v1/status`

获取API服务状态。

**响应**:
```json
{
  "status": "正常运行",
  "version": "v1",
  "message": "TradeMaster Web Interface API v1",
  "endpoints": {
    "auth": "认证相关接口",
    "api-keys": "API密钥管理接口",
    "sessions": "会话管理接口"
  }
}
```

## 📝 错误响应

所有API端点在出现错误时返回统一的错误格式：

```json
{
  "detail": "错误详细信息",
  "status_code": 400,
  "timestamp": 1692115800.123
}
```

### 常见HTTP状态码

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `204 No Content`: 请求成功，无返回内容
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证或令牌无效
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `422 Unprocessable Entity`: 请求数据验证失败
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 服务器内部错误

## 🔐 认证说明

### JWT令牌格式

访问令牌包含以下信息：
```json
{
  "sub": 1,           // 用户ID
  "username": "john_doe",
  "role": "user",
  "exp": 1692117600,  // 过期时间戳
  "iat": 1692115800,  // 签发时间戳
  "type": "access"    // 令牌类型
}
```

### API密钥认证

对于API密钥认证，使用以下请求头：
```
Authorization: Bearer <api_key>
```

API密钥格式：`tm_live_<32字符随机字符串>`

### 权限级别

- `admin`: 管理员权限，可以管理所有用户和系统设置
- `user`: 普通用户权限，可以使用基本功能
- `analyst`: 分析师权限，可以进行数据分析和策略开发
- `viewer`: 观察者权限，只能查看数据，不能修改

## 📊 使用示例

### Python示例

```python
import requests

# 用户登录
login_data = {
    "username": "john_doe",
    "password": "SecurePass123!"
}

response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json=login_data
)

tokens = response.json()
access_token = tokens["access_token"]

# 使用访问令牌调用API
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

profile = requests.get(
    "http://localhost:8000/api/v1/auth/profile",
    headers=headers
).json()

print(f"Welcome, {profile['full_name']}!")
```

### JavaScript示例

```javascript
// 用户登录
const loginData = {
  username: 'john_doe',
  password: 'SecurePass123!'
};

const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(loginData),
});

const tokens = await loginResponse.json();

// 使用访问令牌
const profileResponse = await fetch('http://localhost:8000/api/v1/auth/profile', {
  headers: {
    'Authorization': `Bearer ${tokens.access_token}`,
  },
});

const profile = await profileResponse.json();
console.log(`Welcome, ${profile.full_name}!`);
```

### cURL示例

```bash
# 用户登录
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123!"
  }'

# 使用返回的令牌获取个人资料
curl -X GET "http://localhost:8000/api/v1/auth/profile" \
  -H "Authorization: Bearer <access_token>"
```

## 🔄 变更日志

### v1.0.0 (2025-08-15)
- ✨ 初始API版本发布
- 🔐 完整的认证和授权系统
- 🔑 API密钥管理功能
- 📱 会话管理和监控
- 📊 使用统计和日志记录
- 🛡️ 安全增强特性

---

**联系支持**: 如有API使用问题，请联系 [support@trademaster.com](mailto:support@trademaster.com)