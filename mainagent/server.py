"""主Agent服务API"""

import os
import sys
import requests
from flask import Flask, request, jsonify
from core import execute_function_call_agent, process_user_query
from conversation_manager import conversation_manager

# 添加当前目录到路径以导入session_manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# 用于存储回调通知（实际生产中应该使用数据库或消息队列）
callback_notifications = {}

# SubAgent服务URL
SUBAGENT_URL = os.environ.get('SUBAGENT_URL', 'http://localhost:5000')


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
        "max_iterations": 10  // 可选，最大迭代次数，默认10
    }
    
    返回格式:
    {
        "status": "completed" | "max_iterations_reached" | "error",
        "final_answer": "最终答案",
        "iterations": 执行迭代次数,
        "execution_log": ["执行日志..."],
        "error": "错误信息"  // 仅在出错时返回
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "error": "请求体不能为空"}), 400
        
        query = data.get('query')
        if not query:
            return jsonify({"status": "error", "error": "query 参数必填"}), 400
        
        max_iterations = data.get('max_iterations', 10)
        
        # 执行Function Call Agent
        result = execute_function_call_agent(query, max_iterations)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    """
    多轮对话接口（向后兼容，内部转发到/message统一入口）
    
    请求格式:
    {
        "query": "用户查询内容",
        "conversation_history": [...]  // 可选，对话历史
        "user_id": "用户标识"  // 可选，用户ID
    }
    
    返回格式:
    {
        "status": "completed" | "max_iterations_reached" | "error",
        "answer": "回答内容",
        "function_called": ["调用的函数名列表"] | null,
        "function_result": "最后一个函数执行结果" | null,
        "iterations": "ReAct迭代次数",
        "conversation_history": [...],
        "error": "错误信息"  // 仅在出错时返回
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "error": "请求体不能为空"}), 400
        
        query = data.get('query')
        if not query:
            return jsonify({"status": "error", "error": "query 参数必填"}), 400
        
        conversation_history = data.get('conversation_history')
        user_id = data.get('user_id', 'user_a')
        
        # 【向后兼容】内部转发到统一入口/message的处理逻辑
        # 保持/chat接口不变，但内部使用统一处理
        result = process_user_query(query, conversation_history, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/tools', methods=['GET'])
def get_tools():
    """
    获取可用工具列表
    
    返回格式:
    {
        "tools": {
            "tool_name": "tool_description",
            ...
        }
    }
    """
    try:
        from tools import ToolManager
        tool_manager = ToolManager()
        tools = tool_manager.get_available_tools()
        
        return jsonify({"tools": tools})
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/functions', methods=['GET'])
def get_functions():
    """
    获取Function Call函数定义
    
    返回格式:
    {
        "functions": [...]
    }
    """
    try:
        from tools import get_tools_definitions
        tools = get_tools_definitions()
        
        return jsonify({"tools": tools})
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/session_callback', methods=['POST'])
def session_callback():
    """
    子agent会话完成回调接口
    
    请求格式:
    {
        "session_id": "会话ID",
        "result": "子agent获取的结果",
        "user_a": "用户A标识",
        "question": "原始问题"
    }
    
    返回格式:
    {
        "status": "success" | "error",
        "message": "..."
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "请求体不能为空"}), 400
        
        session_id = data.get('session_id')
        result = data.get('result')
        user_a = data.get('user_a')
        question = data.get('question')
        
        print(f"\n[CALLBACK] 收到子agent回调通知")
        print(f"  会话ID: {session_id}")
        print(f"  用户A: {user_a}")
        print(f"  原始问题: {question}")
        print(f"  子agent结果: {result}")
        
        # 【关键步骤】更新对话历史，将SubAgent的结果添加到tool消息中
        updated = conversation_manager.update_tool_result(session_id, result)
        if updated:
            print(f"[INFO] 已更新用户 {user_a} 的对话历史，添加SubAgent结果")
        else:
            print(f"[WARNING] 未能更新对话历史，可能session_id未注册或用户对话历史不存在")
        
        # 存储回调通知（实际生产中应该推送给用户A）
        callback_notifications[session_id] = {
            "result": result,
            "user_a": user_a,
            "question": question,
            "timestamp": os.popen('date +%Y-%m-%d_%H:%M:%S').read().strip()
        }
        
        # TODO: 这里应该实际推送给用户A（通过企业微信API等）
        print("\n" + "🔔" + "═" * 68 + "🔔")
        print("                   ✨ 准备推送通知给用户A ✨")
        print("═" * 70)
        print(f"📌 目标用户: {user_a}")
        print(f"📌 关于问题: {question}")
        print(f"\n💡 推送内容:")
        print(f"{result}")
        print("═" * 70)
        print(f"✅ 通知已记录到系统，用户A的终端会自动接收\n")
        
        return jsonify({"status": "success", "message": "回调接收成功"})
        
    except Exception as e:
        print(f"[ERROR] 回调处理失败: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_notifications', methods=['GET'])
def get_notifications():
    """
    查询所有回调通知（用于测试）
    
    返回格式:
    {
        "notifications": {...}
    }
    """
    return jsonify({"notifications": callback_notifications})


@app.route('/message', methods=['POST'])
def unified_message():
    """
    统一消息入口 - 用于企业微信集成
    
    根据消息内容自动路由（不依赖type字段）：
    1. 如果消息包含 session_id + user_b_id + message → 路由到subagent（用户B回复）
    2. 如果消息包含 session_id → 路由到subagent（查询会话状态）
    3. 如果消息包含 user_b_id（无session_id） → 路由到subagent（查询待处理会话）
    4. 如果消息包含 query → 路由到mainagent（用户A查询）
    
    请求格式:
    {
        "query": "...",  // 用户A查询时使用
        "session_id": "...",  // 用户B回复或查询会话时使用
        "user_b_id": "...",  // 用户B回复或查询会话时使用
        "message": "...",  // 用户B回复内容
        "conversation_history": [...],  // 用户A查询时可选
        "user_id": "...",  // 用户A标识，可选
        ...
    }
    
    返回格式:
    根据路由类型返回相应的结果
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "error": "请求体不能为空"}), 400
        
        # 自动识别消息类型（根据实际字段判断，不依赖type字段）
        # 优先级：session_id > user_b_id > query
        # 1. 如果有session_id，说明是subagent相关的请求
        if data.get('session_id'):
            # 如果有user_b_id和message，说明是用户B的回复
            if data.get('user_b_id') and data.get('message'):
                message_type = "user_b_reply"
            # 否则是查询会话状态
            else:
                message_type = "get_session_status"
        # 2. 如果没有session_id但有user_b_id，说明是查询待处理会话
        elif data.get('user_b_id'):
            message_type = "get_pending_sessions"
        # 3. 如果有query，说明是用户A的查询
        elif data.get('query'):
            message_type = "user_query"
        # 4. 无法识别
        else:
            return jsonify({"status": "error", "error": "无法识别消息类型，请提供必要的参数字段（query、session_id或user_b_id）"}), 400
        
        # 根据消息类型路由
        if message_type == "user_query":
            # 用户A的查询 - 使用mainagent处理
            query = data.get('query')
            if not query:
                return jsonify({"status": "error", "error": "query 参数必填"}), 400
            
            conversation_history = data.get('conversation_history')
            user_id = data.get('user_id', 'user_a')
            
            result = process_user_query(query, conversation_history, user_id)
            return jsonify(result)
            
        elif message_type == "user_b_reply":
            # 用户B的回复 - 转发到subagent
            session_id = data.get('session_id')
            user_b_id = data.get('user_b_id')
            message = data.get('message')
            
            if not all([session_id, user_b_id, message]):
                return jsonify({"status": "error", "error": "session_id, user_b_id, message 参数必填"}), 400
            
            try:
                response = requests.post(
                    f"{SUBAGENT_URL}/reply",
                    json={
                        "session_id": session_id,
                        "user_b_id": user_b_id,
                        "message": message
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    return jsonify(response.json())
                else:
                    return jsonify({"status": "error", "error": f"SubAgent返回错误: {response.status_code}"}), response.status_code
                    
            except requests.exceptions.ConnectionError:
                return jsonify({"status": "error", "error": f"无法连接到SubAgent服务 ({SUBAGENT_URL})"}), 503
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 500
                
        elif message_type == "get_session_status":
            # 查询会话状态 - 转发到subagent
            session_id = data.get('session_id')
            if not session_id:
                return jsonify({"status": "error", "error": "session_id 参数必填"}), 400
            
            try:
                response = requests.get(
                    f"{SUBAGENT_URL}/get_status",
                    params={"session_id": session_id},
                    timeout=5
                )
                
                if response.status_code == 200:
                    return jsonify(response.json())
                else:
                    return jsonify({"status": "error", "error": f"SubAgent返回错误: {response.status_code}"}), response.status_code
                    
            except requests.exceptions.ConnectionError:
                return jsonify({"status": "error", "error": f"无法连接到SubAgent服务 ({SUBAGENT_URL})"}), 503
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 500
                
        elif message_type == "get_pending_sessions":
            # 查询待处理会话 - 转发到subagent
            user_b_id = data.get('user_b_id')
            if not user_b_id:
                return jsonify({"status": "error", "error": "user_b_id 参数必填"}), 400
            
            try:
                response = requests.get(
                    f"{SUBAGENT_URL}/get_pending_sessions",
                    params={"user_b_id": user_b_id},
                    timeout=5
                )
                
                if response.status_code == 200:
                    return jsonify(response.json())
                else:
                    return jsonify({"status": "error", "error": f"SubAgent返回错误: {response.status_code}"}), response.status_code
                    
            except requests.exceptions.ConnectionError:
                return jsonify({"status": "error", "error": f"无法连接到SubAgent服务 ({SUBAGENT_URL})"}), 503
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 500
        else:
            return jsonify({"status": "error", "error": f"未知的消息类型: {message_type}"}), 400
            
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == '__main__':
    # 运行服务
    port = int(os.environ.get('MAINAGENT_PORT', 5001))
    print(f"\n主Agent服务启动在端口 {port}")
    print(f"回调URL: http://localhost:{port}/session_callback\n")
    app.run(host='0.0.0.0', port=port, debug=False)
