#!/bin/bash

# 员工筛选与通知系统 - 启动脚本
# 使用方法: ./start_test.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════"
echo "           员工筛选与通知系统 - 启动脚本"
echo "════════════════════════════════════════════════════════════"
echo ""

# 检查数据库是否运行
echo "🔍 检查数据库状态..."
if ! docker ps | grep -q myserver_postgres; then
    echo "❌ 数据库未运行"
    echo "   正在启动数据库..."
    ./start_database.sh
    sleep 3
fi

# 检查数据库表是否存在
echo "🔍 检查数据库表..."
MAINAGENT_TABLE=$(docker exec -i myserver_postgres psql -U postgres -d myserver_db -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'mainagent_conversations');" 2>/dev/null | tr -d ' ')
EMPLOYEE_TABLE=$(docker exec -i myserver_postgres psql -U postgres -d myserver_db -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'employee_directory');" 2>/dev/null | tr -d ' ')

if [ "$MAINAGENT_TABLE" != "t" ] || [ "$EMPLOYEE_TABLE" != "t" ]; then
    echo "⚠️  数据库表未初始化"
    echo "   正在初始化数据库..."
    ./database/setup.sh
    if [ $? -ne 0 ]; then
        echo "❌ 数据库初始化失败"
        exit 1
    fi
else
    echo "✅ 数据库表已存在"
fi
echo ""

# 停止旧服务
echo "🧹 清理旧服务..."
./stop_services.sh > /dev/null 2>&1
sleep 1

# 清理Python缓存
rm -rf __pycache__ mainagent/__pycache__ codeagent/__pycache__ 2>/dev/null

# 启动主Agent
echo "🚀 启动主Agent服务 (端口5001)..."
cd mainagent
python server.py > ../logs/mainagent.log 2>&1 &
MAIN_PID=$!
cd ..
sleep 2

# 启动代码Agent
echo "🚀 启动代码Agent服务 (端口5004)..."
cd codeagent
python server.py > ../logs/codeagent.log 2>&1 &
CODE_PID=$!
cd ..
sleep 2

# 检查服务
echo "🔍 检查服务状态..."
MAIN_HEALTH=$(curl -s http://127.0.0.1:5001/health 2>/dev/null)
CODE_HEALTH=$(curl -s http://127.0.0.1:5004/health 2>/dev/null)

if [[ "$MAIN_HEALTH" != *"ok"* ]]; then
    echo "❌ 主Agent启动失败！"
    echo "   查看日志: tail -f logs/mainagent.log"
    exit 1
fi

if [[ "$CODE_HEALTH" != *"ok"* ]]; then
    echo "❌ 代码Agent启动失败！"
    echo "   查看日志: tail -f logs/codeagent.log"
    exit 1
fi

echo "✅ 主Agent运行中 (PID: $MAIN_PID)"
echo "✅ 代码Agent运行中 (PID: $CODE_PID)"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "                  服务已就绪，开始测试"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 接下来的步骤："
echo ""
echo "【步骤1】打开新终端，启动用户A（提问端）："
echo "  cd $SCRIPT_DIR"
echo "  python user_a_terminal.py"
echo ""
echo "【步骤2】在用户A终端输入测试问题："
echo "  筛选出分数在80分以上的员工"
echo "  需要（确认通知员工）"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "💡 提示:"
echo "  - 停止服务: ./stop_services.sh"
echo "  - 查看状态: ./check_status.sh"
echo "  - 初始化数据库: ./database/setup.sh"
echo "  - 主Agent日志: tail -f logs/mainagent.log"
echo "  - 代码Agent日志: tail -f logs/codeagent.log"
echo ""

