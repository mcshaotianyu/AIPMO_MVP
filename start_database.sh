#!/bin/bash

# 启动PostgreSQL数据库的脚本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════"
echo "           启动 PostgreSQL 数据库"
echo "════════════════════════════════════════════════════════════"
echo ""

# 检查docker是否运行
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未找到 docker 命令"
    echo "   请先安装 Docker"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ 错误: Docker 未运行"
    echo "   请先启动 Docker"
    exit 1
fi

# 检查docker-compose是否运行
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ 错误: 未找到 docker-compose 命令"
    exit 1
fi

# 启动数据库
echo "🚀 启动 PostgreSQL 数据库..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

# 等待数据库就绪
echo "⏳ 等待数据库就绪..."
sleep 5

# 检查数据库是否运行
if docker ps | grep -q myserver_postgres; then
    echo "✅ PostgreSQL 数据库已启动"
    echo ""
    echo "数据库配置:"
    echo "  - Host: localhost"
    echo "  - Port: 5432"
    echo "  - Database: myserver_db"
    echo "  - User: postgres"
    echo "  - Password: postgres"
    echo ""
    echo "查看日志: docker logs -f myserver_postgres"
    echo "停止数据库: docker-compose down (或 docker compose down)"
else
    echo "❌ 数据库启动失败"
    echo "   查看日志: docker logs myserver_postgres"
    exit 1
fi

