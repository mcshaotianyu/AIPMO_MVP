"""主Agent服务API"""

import os
import sys
import requests
from flask import Flask, request, jsonify
from core import process_user_query
from conversation_manager import conversation_manager

# 添加当前目录到路径以导入session_manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from session_manager import session_manager

app = Flask(__name__)

# 用于存储回调通知（实际生产中应该使用数据库或消息队列）
callback_notifications = {}

# SubAgent服务URL
SUBAGENT_URL = os.environ.get('SUBAGENT_URL', 'http://localhost:5002')


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})


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
    
    新的路由逻辑（基于user_id自动判断）：
    1. 如果提供了session_id，使用明确路由（向后兼容）
    2. 如果提供了user_id，查询该用户是否在sessions表中作为user_b_id存在且有未完成会话
       - 如果有未完成会话 → 路由到subagent（用户B回复）
       - 如果没有 → 路由到mainagent（用户A查询）
    3. 如果没有user_id，使用原有字段组合方式（向后兼容）
    
    请求格式:
    {
        "user_id": "...",  // 发送消息的用户ID（必需，用于路由判断）
        "query": "...",  // 消息内容（可选，也支持message字段）
        "message": "...",  // 消息内容（可选，与query等价）
        "session_id": "...",  // 明确指定会话ID（向后兼容）
        ...
    }
    
    注意：
    - conversation_history不应由客户端传递，服务端会根据路由自动获取：
      * 路由到mainagent → 从conversation_manager自动获取
      * 路由到subagent → 从session自动获取
    - 路由判断仅基于user_id查询pending sessions，不依赖message内容
    
    返回格式:
    根据路由类型返回相应的结果
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "error": "请求体不能为空"}), 400
        
        # 【新路由逻辑】优先使用基于user_id的自动路由
        user_id = data.get('user_id')
        message_content = data.get('message') or data.get('query')  # 支持message和query字段
        
        # 路由判断有且仅有一个依据：根据user_id查询是否有pending session
        if user_id:
            # 查询该用户是否在sessions表中作为user_b_id存在，且有未完成会话
            try:
                # 支持"*"查询所有待处理会话（用于测试，模拟所有用户）
                if user_id == "*":
                    pending_sessions = session_manager.get_all_pending_sessions()
                else:
                    pending_sessions = session_manager.get_pending_sessions(user_id)
            except Exception as e:
                print(f"[ERROR] 查询待处理会话失败: {str(e)}")
                # 查询失败，默认路由到mainagent
                pending_sessions = []
            
            # 如果没有message_content，返回pending sessions列表（用于轮询查询）
            if not message_content:
                return jsonify({
                    "status": "success",
                    "sessions": pending_sessions
                })
            
            # 根据pending_sessions决定路由（不依赖message_content）
            if len(pending_sessions) > 0:
                # 用户B：有未完成的会话 → 路由到subagent
                # 判断条件：
                # - 如果user_id是"*"（模拟所有用户），选择最新的会话（第一个）
                # - 否则，如果有多个pending会话，取最先create的那一条（最旧的）
                # TODO:如果有多个session，应该基于query用模型判断最相关的session
                if len(pending_sessions) > 1:
                    if user_id == "*":
                        # 模拟所有用户时，优先选择最新的会话（用户通常想回复最新的问询）
                        selected_session = pending_sessions[0]  # 第一个是最新的（按created_at DESC排序）
                        session_id = selected_session['session_id']
                        print(f"[INFO] 用户 {user_id} 有 {len(pending_sessions)} 个待处理会话，自动使用最新的: {session_id}")
                    else:
                        # 特定用户时，取最先create的（最旧的，即列表最后一个）
                        selected_session = pending_sessions[-1]
                        session_id = selected_session['session_id']
                        print(f"[INFO] 用户 {user_id} 有 {len(pending_sessions)} 个待处理会话，自动使用最先创建的: {session_id}")
                else:
                    # 只有一个会话，直接使用
                    selected_session = pending_sessions[0]
                    session_id = selected_session['session_id']
                    print(f"[INFO] 用户 {user_id} 有1个待处理会话，自动使用: {session_id}")
                
                # 如果user_id是"*"，使用选中session的真实user_b_id
                actual_user_b_id = selected_session.get('user_b_id', user_id) if user_id == "*" else user_id
                
                # 转发到subagent的reply接口（subagent会自动从session获取对话历史）
                try:
                    response = requests.post(
                        f"{SUBAGENT_URL}/reply",
                        json={
                            "session_id": session_id,
                            "user_b_id": actual_user_b_id,
                            "message": message_content
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
            else:
                # 自动从conversation_manager获取对话历史，不依赖客户端传递
                query = message_content
                
                # 不传递conversation_history，让process_user_query自动从conversation_manager获取
                result = process_user_query(query, conversation_history=None, user_id=user_id)
                return jsonify(result)
        
        # 无法识别
        return jsonify({
            "status": "error",
            "error": "无法识别消息类型，请提供 user_id（推荐）或必要的参数字段（query、session_id或user_b_id）"
        }), 400
            
    except Exception as e:
        print(f"[ERROR] 统一消息入口处理异常: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == '__main__':
    # 运行服务
    port = int(os.environ.get('MAINAGENT_PORT', 5001))
    print(f"\n主Agent服务启动在端口 {port}")
    print(f"回调URL: http://localhost:{port}/session_callback\n")
    app.run(host='0.0.0.0', port=port, debug=False)
