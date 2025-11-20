#!/bin/bash
# 检查系统状态脚本

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Multi-Agent 系统状态检查                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 检查端口占用
echo "📡 检查端口占用..."
echo ""

PORT_5001=$(lsof -ti:5001)
PORT_5004=$(lsof -ti:5004)

if [ -z "$PORT_5001" ]; then
    echo "  ✓ 端口 5001 (主Agent)   : 空闲"
else
    echo "  ⚠️  端口 5001 (主Agent)   : 被占用 (PID: $PORT_5001)"
    echo "     执行: kill -9 $PORT_5001"
fi

if [ -z "$PORT_5004" ]; then
    echo "  ✓ 端口 5004 (代码Agent) : 空闲"
else
    echo "  ⚠️  端口 5004 (代码Agent) : 被占用 (PID: $PORT_5004)"
    echo "     执行: kill -9 $PORT_5004"
fi

echo ""

# 检查服务健康
echo "🏥 检查服务健康..."
echo ""

# 检查主Agent
if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "  ✓ 主Agent服务 (5001)    : 正常运行"
else
    echo "  ✗ 主Agent服务 (5001)    : 未运行"
    echo "     启动: cd mainagent && python server.py"
fi

# 检查代码Agent
if curl -s http://localhost:5004/health > /dev/null 2>&1; then
    echo "  ✓ 代码Agent服务 (5004)  : 正常运行"
else
    echo "  ✗ 代码Agent服务 (5004)  : 未运行"
    echo "     启动: cd codeagent && python server.py"
fi

echo ""

# 检查文件
echo "📁 检查关键文件..."
echo ""

FILES=(
    "user_a_terminal.py"
    "mainagent/server.py"
    "mainagent/core.py"
    "codeagent/server.py"
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
if [ -z "$PORT_5001" ] && [ -z "$PORT_5004" ]; then
    if ! curl -s http://localhost:5001/health > /dev/null 2>&1; then
        echo "💡 建议: 服务未运行，请按以下顺序启动："
        echo ""
        echo "   终端1: cd mainagent && python server.py"
        echo "   终端2: cd codeagent && python server.py"
        echo "   终端3: python user_a_terminal.py"
        echo ""
        echo "   或直接运行: ./start_test.sh"
        echo ""
    fi
else
    if [ ! -z "$PORT_5001" ] || [ ! -z "$PORT_5004" ]; then
        echo "💡 建议: 端口被占用，请先清理："
        echo ""
        if [ ! -z "$PORT_5001" ]; then
            echo "   kill -9 $PORT_5001"
        fi
        if [ ! -z "$PORT_5004" ]; then
            echo "   kill -9 $PORT_5004"
        fi
        echo ""
        echo "   或执行: ./stop_services.sh"
        echo ""
    fi
fi

echo "详细启动指南请查看: START_HERE.md"
echo ""

