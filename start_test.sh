#!/bin/bash

# Multi-Agent 系统测试脚本
# 使用方法: ./start_test.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════"
echo "           Multi-Agent 系统测试 - 启动脚本"
echo "════════════════════════════════════════════════════════════"
echo ""

# 停止旧服务
echo "🧹 清理旧服务..."
./stop_services.sh > /dev/null 2>&1
sleep 1

# 清理Python缓存
rm -rf __pycache__ mainagent/__pycache__ subagent/__pycache__ 2>/dev/null

# 启动主Agent
echo "🚀 启动主Agent服务 (端口5001)..."
cd mainagent
python server.py > ../logs/mainagent.log 2>&1 &
MAIN_PID=$!
cd ..
sleep 2

# 启动子Agent  
echo "🚀 启动子Agent服务 (端口5000)..."
cd subagent
python server.py > ../logs/subagent.log 2>&1 &
SUB_PID=$!
cd ..
sleep 2

# 检查服务
echo "🔍 检查服务状态..."
MAIN_HEALTH=$(curl -s http://127.0.0.1:5001/health 2>/dev/null)
SUB_HEALTH=$(curl -s http://127.0.0.1:5000/health 2>/dev/null)

if [[ "$MAIN_HEALTH" != *"ok"* ]]; then
    echo "❌ 主Agent启动失败！"
    echo "   查看日志: tail -f logs/mainagent.log"
    exit 1
fi

if [[ "$SUB_HEALTH" != *"ok"* ]]; then
    echo "❌ 子Agent启动失败！"
    echo "   查看日志: tail -f logs/subagent.log"
    exit 1
fi

echo "✅ 主Agent运行中 (PID: $MAIN_PID)"
echo "✅ 子Agent运行中 (PID: $SUB_PID)"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "                  服务已就绪，开始测试"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 接下来的步骤："
echo ""
echo "【步骤1】打开新终端，启动用户B（员工端）："
echo "  cd $SCRIPT_DIR"
echo "  python user_b_terminal.py"
echo ""
echo "【步骤2】再打开一个新终端，启动用户A（提问端）："
echo "  cd $SCRIPT_DIR"
echo "  python user_a_terminal.py"
echo ""
echo "【步骤3】在用户A终端输入测试问题："
echo "  健身房周末开门吗？"
echo "  需要（确认联系员工）"
echo ""
echo "【步骤4】观察用户B终端："
echo "  ⏱️ 3-5秒后会自动收到问询"
echo "  💬 显示子Agent的问题"
echo "  ✍️ 直接回复即可（无需输入会话ID）"
echo ""
echo "【步骤5】观察用户A终端："
echo "  ⏱️ 对话完成后3-5秒"
echo "  🔔 自动收到最终答案"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "💡 提示:"
echo "  - 停止服务: ./stop_services.sh"
echo "  - 查看状态: ./check_status.sh"
echo "  - 主Agent日志: tail -f logs/mainagent.log"
echo "  - 子Agent日志: tail -f logs/subagent.log"
echo ""

