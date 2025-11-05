#!/bin/bash
# 停止所有服务的脚本

echo "停止 Multi-Agent 服务..."

# 读取PIDs
if [ -f logs/subagent.pid ]; then
    SUBAGENT_PID=$(cat logs/subagent.pid)
    if ps -p $SUBAGENT_PID > /dev/null 2>&1; then
        kill $SUBAGENT_PID
        echo "  ✓ 子Agent服务已停止 (PID: $SUBAGENT_PID)"
    fi
    rm logs/subagent.pid
fi

if [ -f logs/mainagent.pid ]; then
    MAINAGENT_PID=$(cat logs/mainagent.pid)
    if ps -p $MAINAGENT_PID > /dev/null 2>&1; then
        kill $MAINAGENT_PID
        echo "  ✓ 主Agent服务已停止 (PID: $MAINAGENT_PID)"
    fi
    rm logs/mainagent.pid
fi

# 备用方案：按端口查找并停止
pkill -f "python.*server.py" 2>/dev/null

echo "所有服务已停止"

