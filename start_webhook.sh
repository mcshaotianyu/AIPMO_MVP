#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 启动Webhook服务 (端口8081)..."
cd wechat
nohup python3 msg_receive.py > ../logs/webhook.log 2>&1 &
