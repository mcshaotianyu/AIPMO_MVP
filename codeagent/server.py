"""代码Agent服务API"""

import os
import sys
from flask import Flask, request, jsonify
from core import execute_code_agent, process_user_query

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})


@app.route('/query', methods=['POST'])
def query():
    """
    处理用户查询接口（单次查询）
    
    请求格式:
    {
        "query": "用户查询内容",
        "file_path": "XLSX文件路径（可选）",
        "max_iterations": 10  // 可选，最大迭代次数，默认10
    }
    
    返回格式:
    {
        "status": "completed" | "max_iterations_reached" | "error",
        "final_answer": "最终答案",
        "iterations": 执行迭代次数,
        "execution_log": ["执行日志..."],
        "function_called": ["调用的工具列表"],
        "error": "错误信息"  // 仅在出错时返回
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "error": "请求体不能为空"}), 400
        
        query_text = data.get('query')
        if not query_text:
            return jsonify({"status": "error", "error": "query 参数必填"}), 400
        
        file_path = data.get('file_path')
        max_iterations = data.get('max_iterations', 10)
        
        # 执行代码Agent
        result = execute_code_agent(query_text, file_path, max_iterations)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    """
    多轮对话接口
    
    请求格式:
    {
        "query": "用户查询内容",
        "file_path": "XLSX文件路径（可选）",
        "conversation_history": [...]  // 可选，对话历史
    }
    
    返回格式:
    {
        "status": "completed" | "max_iterations_reached" | "error",
        "answer": "回答内容",
        "function_called": ["调用的函数名列表"] | null,
        "iterations": "ReAct迭代次数",
        "conversation_history": [...],
        "error": "错误信息"  // 仅在出错时返回
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "error": "请求体不能为空"}), 400
        
        query_text = data.get('query')
        if not query_text:
            return jsonify({"status": "error", "error": "query 参数必填"}), 400
        
        file_path = data.get('file_path')
        conversation_history = data.get('conversation_history')
        
        result = process_user_query(query_text, file_path, conversation_history)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == '__main__':
    # 运行服务
    port = int(os.environ.get('CODEAGENT_PORT', 5004))
    print(f"\n代码Agent服务启动在端口 {port}\n")
    app.run(host='0.0.0.0', port=port, debug=True)

