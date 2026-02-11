# StreamCraft API 文档

## 认证

所有需要认证的API都需要在请求头中包含JWT Token：

```
Authorization: Bearer <your-access-token>
```

## 用户认证

### 用户注册
**POST** `/api/v1/register`

请求体：
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

响应：
```json
{
  "success": true,
  "message": "User registered successfully"
}
```

### 用户登录
**POST** `/api/v1/login`

请求体：
```json
{
  "username": "testuser",
  "password": "password123"
}
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 获取当前用户信息
**GET** `/api/v1/users/me`

响应：
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

## 收藏管理

### 创建收藏
**POST** `/api/v1/collections`

请求体：
```json
{
  "platform": "xiaohongshu",
  "content_id": "abcdef123456",
  "title": "有趣的分享内容",
  "content": "这是内容的简要描述...",
  "url": "https://www.xiaohongshu.com/discovery/item/abcdef123456",
  "author": "用户名",
  "cover_image": "https://example.com/image.jpg",
  "content_type": "post",
  "category": "生活日常",
  "tags": ["分享", "日常"]
}
```

### 获取收藏列表
**GET** `/api/v1/collections`

查询参数：
- `skip`: 偏移量 (默认: 0)
- `limit`: 限制数量 (默认: 20, 最大: 100)
- `platform`: 平台过滤
- `category`: 分类过滤

响应：
```json
[
  {
    "id": 1,
    "user_id": 1,
    "platform": "xiaohongshu",
    "content_id": "abcdef123456",
    "title": "有趣的分享内容",
    "content": "这是内容的简要描述...",
    "url": "https://www.xiaohongshu.com/discovery/item/abcdef123456",
    "author": "用户名",
    "cover_image": "https://example.com/image.jpg",
    "content_type": "post",
    "category": "生活日常",
    "tags": ["分享", "日常"],
    "collected_at": "2024-01-01T10:00:00Z",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z",
    "like_count": 5
  }
]
```

### 获取单个收藏
**GET** `/api/v1/collections/{id}`

### 更新收藏
**PUT** `/api/v1/collections/{id}`

### 删除收藏
**DELETE** `/api/v1/collections/{id}`

## 分类管理

### 创建分类
**POST** `/api/v1/categories`

请求体：
```json
{
  "name": "科技数码",
  "description": "科技和数码产品相关内容",
  "color": "#3B82F6"
}
```

### 获取所有分类
**GET** `/api/v1/categories`

### 获取单个分类
**GET** `/api/v1/categories/{id}`

### 删除分类
**DELETE** `/api/v1/categories/{id}`

## 标签管理

### 创建标签
**POST** `/api/v1/tags`

请求体：
```json
{
  "name": "教程"
}
```

### 获取所有标签
**GET** `/api/v1/tags`

### 获取单个标签
**GET** `/api/v1/tags/{id}`

### 删除标签
**DELETE** `/api/v1/tags/{id}`

## 热门内容

### 获取热门内容
**GET** `/api/v1/hot-content`

查询参数：
- `platform`: 平台过滤
- `limit`: 限制数量 (默认: 20)

### 手动触发爬取
**POST** `/api/v1/hot-content/crawl`

### 获取支持的平台
**GET** `/api/v1/hot-content/platforms`

## 机器人助手

### 发送消息给机器人
**POST** `/api/v1/bot/message`

请求体：
```json
{
  "message": "请帮我收藏这个链接: https://www.xiaohongshu.com/discovery/item/abcdef123456",
  "user_id": 1
}
```

响应：
```json
{
  "success": true,
  "message": "成功接收到1个链接，正在后台处理...",
  "data": {
    "urls_processed": 1,
    "urls": ["https://www.xiaohongshu.com/discovery/item/abcdef123456"]
  }
}
```

### 获取机器人状态
**GET** `/api/v1/bot/status`

## 系统监控

### 健康检查
**GET** `/health`

响应：
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Prometheus指标
**GET** `/metrics`

## 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "success": false,
  "message": "错误描述信息",
  "error_code": "ERROR_CODE"
}
```

## 状态码说明

- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未授权
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

## 速率限制

API有以下速率限制：
- 普通用户: 100次/分钟
- 认证用户: 1000次/分钟
- 管理员: 无限制

超过限制时会返回429状态码。