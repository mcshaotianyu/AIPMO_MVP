#!/bin/bash
# 检查系统状态脚本

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Multi-Agent 系统状态检查                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 检查端口占用
echo "📡 检查端口占用..."
echo ""

PORT_5000=$(lsof -ti:5000)
PORT_5001=$(lsof -ti:5001)

if [ -z "$PORT_5000" ]; then
    echo "  ✓ 端口 5000 (子Agent)   : 空闲"
else
    echo "  ⚠️  端口 5000 (子Agent)   : 被占用 (PID: $PORT_5000)"
    echo "     执行: kill -9 $PORT_5000"
fi

if [ -z "$PORT_5001" ]; then
    echo "  ✓ 端口 5001 (主Agent)   : 空闲"
else
    echo "  ⚠️  端口 5001 (主Agent)   : 被占用 (PID: $PORT_5001)"
    echo "     执行: kill -9 $PORT_5001"
fi

echo ""

# 检查服务健康
echo "🏥 检查服务健康..."
echo ""

# 检查子Agent
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "  ✓ 子Agent服务 (5000)    : 正常运行"
else
    echo "  ✗ 子Agent服务 (5000)    : 未运行"
    echo "     启动: cd subagent && python server.py"
fi

# 检查主Agent
if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "  ✓ 主Agent服务 (5001)    : 正常运行"
else
    echo "  ✗ 主Agent服务 (5001)    : 未运行"
    echo "     启动: cd mainagent && python server.py"
fi

echo ""

# 检查文件
echo "📁 检查关键文件..."
echo ""

FILES=(
    "user_a_terminal.py"
    "user_b_terminal.py"
    "session_manager.py"
    "mainagent/server.py"
    "mainagent/core.py"
    "subagent/server.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (缺失)"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# 给出建议
if [ -z "$PORT_5000" ] && [ -z "$PORT_5001" ]; then
    if ! curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo "💡 建议: 服务未运行，请按以下顺序启动："
        echo ""
        echo "   终端1: cd subagent && python server.py"
        echo "   终端2: cd mainagent && python server.py"
        echo "   终端3: python user_a_terminal.py"
        echo "   终端4: python user_b_terminal.py"
        echo ""
    fi
else
    if [ ! -z "$PORT_5000" ] || [ ! -z "$PORT_5001" ]; then
        echo "💡 建议: 端口被占用，请先清理："
        echo ""
        if [ ! -z "$PORT_5000" ]; then
            echo "   kill -9 $PORT_5000"
        fi
        if [ ! -z "$PORT_5001" ]; then
            echo "   kill -9 $PORT_5001"
        fi
        echo ""
        echo "   或执行: ./stop_services.sh"
        echo ""
    fi
fi

echo "详细启动指南请查看: START_HERE.md"
echo ""

