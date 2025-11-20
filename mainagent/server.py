"""主Agent服务API"""

import os
import sys
from flask import Flask, request, jsonify
from core import process_user_query

# 添加utils目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import mainagent_logger as logger

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    logger.debug("收到健康检查请求")
    return jsonify({"status": "ok"})


@app.route('/message', methods=['POST'])
def unified_message():
    """
    统一消息入口 - 用于企业微信集成
    
    请求格式:
    {
        "user_id": "...",  // 发送消息的用户ID
        "query": "...",  // 消息内容（可选，也支持message字段）
        "message": "...",  // 消息内容（可选，与query等价）
    }
    
    返回格式:
    处理结果
    """
    try:
        logger.info("收到/message请求")
        data = request.json
        if not data:
            logger.error("请求体为空")
            return jsonify({"status": "error", "error": "请求体不能为空"}), 400
        
        user_id = data.get('user_id', 'user_a')
        message_content = data.get('message') or data.get('query')
        
        logger.info(f"处理消息 - 用户ID: {user_id}, 消息长度: {len(message_content) if message_content else 0}")
        
        if not message_content:
            logger.error("消息内容为空")
            return jsonify({"status": "error", "error": "消息内容不能为空"}), 400
        
        # 处理用户查询
        logger.info(f"开始处理用户查询，用户ID: {user_id}")
        result = process_user_query(message_content, conversation_history=None, user_id=user_id)
        
        status = result.get("status", "unknown")
        logger.info(f"查询处理完成 - 用户ID: {user_id}, 状态: {status}, 迭代次数: {result.get('iterations', 0)}")
        
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"统一消息入口处理异常: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == '__main__':
    # 运行服务
    port = int(os.environ.get('MAINAGENT_PORT', 5001))
    logger.info(f"主Agent服务启动在端口 {port}")
    logger.info(f"健康检查: http://localhost:{port}/health")
    logger.info(f"消息接口: http://localhost:{port}/message")
    app.run(host='0.0.0.0', port=port, debug=True)
