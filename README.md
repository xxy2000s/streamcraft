# StreamCraft - 多平台媒体聚合系统

## 项目概述

StreamCraft是一个现代化的多平台媒体内容聚合系统，支持小红书、微信、B站等多个平台的内容收藏、分类和管理。系统采用前后端分离架构，具有美观的用户界面和完善的后台管理系统。

## 核心功能

✅ **多平台内容聚合** - 支持小红书、微信、B站等主流平台内容收集  
✅ **AI智能分类** - 利用AI技术自动对内容进行分类和标签化  
✅ **机器人助手** - 通过聊天机器人快速添加收藏内容  
✅ **实时热点追踪** - 每日抓取各平台热门内容  
✅ **用户管理系统** - 完善的用户注册、登录和权限控制  
✅ **现代化前端** - 响应式设计，支持移动端访问  
✅ **Docker部署** - 一键部署，支持生产环境  

## 技术架构

### 后端技术栈
- **FastAPI** - 高性能Python Web框架
- **MySQL** - 关系型数据库存储
- **Redis** - 缓存和会话管理
- **JWT** - 用户认证和授权
- **OpenAI API** - AI内容分类
- **BeautifulSoup/Selenium** - 网页内容爬取
- **Prometheus** - 系统监控和指标收集

### 前端技术栈
- **React 18** + **TypeScript** - 现代化前端框架
- **TailwindCSS** - 实用优先的CSS框架
- **React Query** - 数据获取和状态管理
- **Zustand** - 轻量级状态管理
- **Framer Motion** - 动画和过渡效果
- **Lucide Icons** - 美观的图标库

### 部署架构
- **Docker** - 容器化部署
- **Docker Compose** - 多容器编排
- **Nginx** - 反向代理和负载均衡
- **MySQL** - 主数据库
- **Redis** - 缓存服务

## 项目结构

```
streamcraft/
├── backend/                 # 后端服务
│   ├── app/                # 主应用目录
│   ├── models/             # 数据模型
│   ├── schemas/            # Pydantic模型
│   ├── services/           # 业务逻辑层
│   ├── routers/            # API路由
│   ├── utils/              # 工具函数
│   ├── config/             # 配置文件
│   ├── main.py             # 应用入口
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端应用
│   ├── src/                # 源代码
│   │   ├── components/     # React组件
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API服务
│   │   ├── stores/         # 状态管理
│   │   └── types/          # TypeScript类型
│   ├── package.json        # Node依赖
│   └── vite.config.ts      # 构建配置
├── docker/                 # Docker配置
│   ├── nginx/             # Nginx配置
│   ├── mysql/             # MySQL初始化脚本
│   └── redis/             # Redis配置
├── docs/                  # 项目文档
│   ├── deployment.md      # 部署指南
│   └── api.md            # API文档
├── tests/                 # 测试代码
└── docker-compose.yml     # Docker编排文件
```

## 快速开始

### 开发环境启动

```bash
# 克隆项目
git clone <repository-url>
cd streamcraft

# 复制环境配置
cp .env.example .env

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 访问应用
# 前端: http://localhost
# API文档: http://localhost/docs
```

### 本地开发

**后端开发:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**前端开发:**
```bash
cd frontend
npm install
npm run dev
```

## 功能演示

### 1. 用户注册和登录
- 支持邮箱注册和登录
- JWT Token认证机制
- 用户信息管理

### 2. 内容收藏管理
- 通过机器人助手快速添加链接
- 手动创建和编辑收藏
- 分类和标签管理
- 搜索和筛选功能

### 3. AI智能分类
- 自动识别内容类型
- 智能分配分类标签
- 内容摘要生成

### 4. 热门内容追踪
- 实时抓取各平台热点
- 热度排序和展示
- 定时更新机制

## 部署说明

详细部署指南请参考 [部署文档](./docs/deployment.md)

## API文档

完整的API接口文档请参考 [API文档](./docs/api.md)

## 监控和运维

系统内置完善的监控体系：
- **健康检查**: `/health` 端点
- **性能指标**: Prometheus指标收集
- **日志管理**: 结构化日志输出
- **错误追踪**: 异常捕获和报告

## 测试

```bash
# 运行后端测试
cd backend && pytest

# 运行前端测试
cd frontend && npm test
```

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License

---

**StreamCraft** - 让内容收藏变得更简单！ 🚀