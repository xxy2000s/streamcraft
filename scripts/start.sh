#!/bin/bash

# StreamCraft 启动脚本

echo "🚀 启动 StreamCraft 系统..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 请先安装 Docker Compose"
    exit 1
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "📝 创建环境配置文件..."
    cp .env.example .env
    
    echo "⚠️  请编辑 .env 文件配置必要的环境变量"
    echo "   特别注意修改以下配置："
    echo "   - MYSQL_ROOT_PASSWORD"
    echo "   - MYSQL_PASSWORD" 
    echo "   - SECRET_KEY"
    echo ""
    echo "编辑完成后重新运行此脚本"
    exit 1
fi

# 构建并启动服务
echo "🐳 构建并启动Docker容器..."
docker-compose up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "📋 检查服务状态..."
docker-compose ps

echo ""
echo "✅ StreamCraft 启动完成！"
echo ""
echo "应用查看地址："
echo "  前端界面: http://localhost"
echo "  API文档: http://localhost/docs" 
echo "  后端API: http://localhost:8000"
echo ""
echo "🔧 管理命令："
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"