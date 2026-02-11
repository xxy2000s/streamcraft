# StreamCraft 部署指南

## 系统要求

- Docker 20.10+
- Docker Compose 1.29+
- 至少 4GB RAM
- 至少 20GB 存储空间

## 快速部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd streamcraft
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要的环境变量：

```bash
# 数据库密码（必填）
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_PASSWORD=your_secure_password

# JWT密钥（必填）
SECRET_KEY=your_very_long_secret_key_here

# AI API密钥（可选，用于内容分类）
OPENAI_API_KEY=your_openai_api_key
```

### 3. 启动服务

```bash
# 后台启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 初始化数据库

首次启动后，可能需要运行数据库迁移：

```bash
docker-compose exec backend alembic upgrade head
```

### 5. 访问应用

- 前端界面: http://localhost
- API文档: http://localhost/docs
- 后端API: http://localhost:8000

## 生产环境部署

### 1. 环境准备

```bash
# 创建生产环境配置
cp .env.example .env.production
```

### 2. SSL证书配置

将SSL证书放置在 `docker/nginx/certs/` 目录下：

```bash
docker/nginx/certs/
├── fullchain.pem
└── privkey.pem
```

### 3. 启动生产环境

```bash
# 使用生产环境配置启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 服务管理

### 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启特定服务
docker-compose restart backend

# 查看服务日志
docker-compose logs backend
docker-compose logs frontend

# 进入容器
docker-compose exec backend bash
docker-compose exec mysql mysql -u streamcraft -p
```

### 数据备份

```bash
# 备份数据库
docker-compose exec mysql mysqldump -u streamcraft -p streamcraft > backup.sql

# 恢复数据库
docker-compose exec -T mysql mysql -u streamcraft -p streamcraft < backup.sql
```

## 监控和维护

### 健康检查

```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 检查前端健康状态
curl http://localhost/

# 检查Prometheus指标
curl http://localhost:8000/metrics
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 查看最近的日志
docker-compose logs --tail=100 backend
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库服务状态
   docker-compose ps mysql
   
   # 查看数据库日志
   docker-compose logs mysql
   ```

2. **前端无法访问API**
   ```bash
   # 检查网络连接
   docker-compose exec frontend ping backend
   
   # 检查Nginx配置
   docker-compose exec nginx nginx -t
   ```

3. **内存不足**
   ```bash
   # 调整Docker资源限制
   # 在Docker Desktop中调整资源分配
   ```

### 性能优化

1. **数据库优化**
   ```bash
   # 连接到MySQL进行优化
   docker-compose exec mysql mysql -u root -p
   
   # 创建索引
   CREATE INDEX idx_collections_user_id ON collections(user_id);
   CREATE INDEX idx_collections_platform ON collections(platform);
   ```

2. **缓存优化**
   ```bash
   # 调整Redis配置
   docker-compose exec redis redis-cli CONFIG SET maxmemory 512mb
   ```

## 升级部署

### 版本升级步骤

```bash
# 1. 停止当前服务
docker-compose down

# 2. 备份数据
docker-compose exec mysql mysqldump -u streamcraft -p streamcraft > backup-$(date +%Y%m%d).sql

# 3. 拉取最新代码
git pull origin main

# 4. 构建新镜像
docker-compose build

# 5. 启动服务
docker-compose up -d

# 6. 运行数据库迁移（如有需要）
docker-compose exec backend alembic upgrade head
```

## 安全建议

1. **修改默认密码**
   - 修改MySQL root密码
   - 修改应用SECRET_KEY
   - 使用强密码策略

2. **网络安全**
   - 配置防火墙规则
   - 使用HTTPS
   - 限制不必要的端口暴露

3. **定期更新**
   - 定期更新Docker镜像
   - 更新系统依赖
   - 应用安全补丁