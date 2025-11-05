#!/bin/bash
# 启动所有服务的脚本

echo "=================================="
echo "  启动 Multi-Agent 服务系统"
echo "=================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 启动子agent服务
echo "[1/2] 启动子Agent服务 (端口 5000)..."
cd subagent
nohup python3 server.py > ../logs/subagent.log 2>&1 &
SUBAGENT_PID=$!
echo "  子Agent PID: $SUBAGENT_PID"
cd ..

sleep 2

# 启动主agent服务
echo "[2/2] 启动主Agent服务 (端口 5001)..."
cd mainagent
nohup python3 server.py > ../logs/mainagent.log 2>&1 &
MAINAGENT_PID=$!
echo "  主Agent PID: $MAINAGENT_PID"
cd ..

sleep 2

# 检查服务是否启动成功
echo ""
echo "检查服务状态..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "  ✓ 子Agent服务启动成功 (http://localhost:5000)"
else
    echo "  ✗ 子Agent服务启动失败"
fi

if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "  ✓ 主Agent服务启动成功 (http://localhost:5001)"
else
    echo "  ✗ 主Agent服务启动失败"
fi

echo ""
echo "=================================="
echo "服务已启动！"
echo "=================================="
echo ""
echo "查看日志:"
echo "  子Agent: tail -f logs/subagent.log"
echo "  主Agent: tail -f logs/mainagent.log"
echo ""
echo "停止服务:"
echo "  ./stop_services.sh"
echo ""
echo "开始测试:"
echo "  python3 test_full_flow.py"
echo ""

# 保存PIDs
echo "$SUBAGENT_PID" > logs/subagent.pid
echo "$MAINAGENT_PID" > logs/mainagent.pid

