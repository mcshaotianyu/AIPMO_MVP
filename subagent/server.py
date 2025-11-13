"""SubAgent对话服务API"""

import os
import sys
import requests
import threading
from flask import Flask, request, jsonify
from core import init_client, extract_completed_info, create_conversation_history, call_llm

# 添加父目录到路径以导入session_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from session_manager import session_manager

app = Flask(__name__)


def execute_task(task, person, user_replies=None, max_turns=20):
    """
    执行问询任务
    
    Args:
        task: 子任务
        person: 问询对象
        user_replies: 用户回复列表（可选），如果提供则使用这些回复，否则返回第一个问题
        max_turns: 最大对话轮数
    
    Returns:
        dict: {"status": "completed"/"waiting"/"error", "completed_info"/"question"/"error": "..."}
    """
    client = init_client()
    conversation_history = create_conversation_history(task, person)
    
    try:
        # 获取LLM的第一条回复（开场问题）
        assistant_response = call_llm(client, conversation_history)
        
        # 检测是否已经完成任务
        completed_info = extract_completed_info(assistant_response)
        if completed_info:
            return {"status": "completed", "completed_info": completed_info}
        
        # 添加助手的第一条回复到历史
        conversation_history.append({"role": "assistant", "content": assistant_response})
        
        # 如果没有提供用户回复，返回第一个问题
        if not user_replies:
            return {"status": "waiting", "question": assistant_response}
        
        # 使用提供的用户回复继续对话
        for turn, user_reply in enumerate(user_replies):
            if turn >= max_turns:
                break
            
            conversation_history.append({"role": "user", "content": user_reply})
            assistant_response = call_llm(client, conversation_history)
            
            # 检测任务完成
            completed_info = extract_completed_info(assistant_response)
            if completed_info:
                return {"status": "completed", "completed_info": completed_info}
            
            conversation_history.append({"role": "assistant", "content": assistant_response})
        
        # 如果所有回复都用完了还没完成任务，返回当前的问题
        return {"status": "waiting", "question": assistant_response}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})


@app.route('/start_session', methods=['POST'])
def start_session():
    """
    启动新会话接口
    
    请求格式:
    {
        "session_id": "唯一会话ID",
        "user_a": "用户A标识",
        "user_b_id": "用户B的ID",
        "user_b_name": "用户B的姓名",
        "question": "原始问题",
        "callback_url": "完成时的回调URL（可选）"
    }
    
    返回格式:
    {
        "status": "success" | "error",
        "session_id": "...",
        "first_question": "...",  // 子agent的第一个问题
        "error": "..."
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "error": "请求体不能为空"}), 400
        
        session_id = data.get('session_id')
        user_a = data.get('user_a')
        user_b_id = data.get('user_b_id')
        user_b_name = data.get('user_b_name')
        question = data.get('question')
        callback_url = data.get('callback_url')
        
        if not all([session_id, user_a, user_b_id, user_b_name, question]):
            return jsonify({"status": "error", "error": "缺少必要参数"}), 400
        
        # 创建会话
        session = session_manager.create_session(
            session_id, user_a, user_b_id, user_b_name, question, callback_url
        )
        
        # 生成第一个问题
        client = init_client()
        task = f"帮用户询问：{question}"
        conversation_history = create_conversation_history(task, user_b_name)
        
        # 【修复】保存system prompt和开场白到数据库
        for msg in conversation_history:
            session_manager.add_conversation_turn(session_id, msg["role"], msg["content"])
        
        # 获取LLM的第一条回复
        assistant_response = call_llm(client, conversation_history)  # 其实是问询，向用户B问询相关信息
        
        # 检测是否直接完成（不太可能）
        completed_info = extract_completed_info(assistant_response)
        if completed_info:
            # 保存assistant回复
            session_manager.add_conversation_turn(session_id, "assistant", assistant_response)
            session_manager.set_session_result(session_id, completed_info)
            trigger_callback_if_needed(session_id)
            return jsonify({
                "status": "success",
                "session_id": session_id,
                "session_status": "completed",
                "result": completed_info
            })
        
        # 记录assistant回复到对话历史
        session_manager.add_conversation_turn(session_id, "assistant", assistant_response)
        session_manager.update_session_status(session_id, "in_progress")
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "first_question": assistant_response
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/reply', methods=['POST'])
def reply():
    """
    用户B回复接口
    
    请求格式:
    {
        "session_id": "会话ID",
        "user_b_id": "用户B的ID（验证用）",
        "message": "用户B的回复内容"
    }
    
    返回格式:
    {
        "status": "success" | "error",
        "session_status": "in_progress" | "completed",
        "next_question": "...",  // 继续进行时返回
        "result": "...",  // 完成时返回
        "error": "..."
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "error": "请求体不能为空"}), 400
        
        session_id = data.get('session_id')
        user_b_id = data.get('user_b_id')
        message = data.get('message')
        
        if not all([session_id, user_b_id, message]):
            return jsonify({"status": "error", "error": "缺少必要参数"}), 400
        
        # 先获取会话用于验证（不加载完整历史）
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({"status": "error", "error": "会话不存在"}), 404
        
        # 验证用户B
        if session.user_b_id != user_b_id:
            return jsonify({"status": "error", "error": "无权限访问此会话"}), 403
        
        # 检查会话状态
        if session.status == "completed":
            return jsonify({"status": "error", "error": "会话已完成"}), 400
        
        # 【关键修复1】先保存用户回复到数据库
        session_manager.add_conversation_turn(session_id, "user", message)
        
        # 【关键修复2】然后从数据库重新加载完整历史（包含刚保存的user消息）
        from database.db import db
        conversation_history = []
        for turn in db.get_session_messages(session_id):
            conversation_history.append({
                "role": turn["role"],
                "content": turn["content"]
            })
        
        # 调用LLM获取下一个问题或结论
        client = init_client()
        assistant_response = call_llm(client, conversation_history)
        
        # 检测是否完成
        completed_info = extract_completed_info(assistant_response)
        if completed_info:
            session_manager.add_conversation_turn(session_id, "assistant", assistant_response)
            session_manager.set_session_result(session_id, completed_info)
            
            # 触发回调
            trigger_callback_if_needed(session_id)
            
            return jsonify({
                "status": "success",
                "session_status": "completed",
                "result": completed_info
            })
        else:
            # 继续对话
            session_manager.add_conversation_turn(session_id, "assistant", assistant_response)
            
            return jsonify({
                "status": "success",
                "session_status": "in_progress",
                "next_question": assistant_response
            })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


def trigger_callback_if_needed(session_id: str):
    """触发回调（如果配置了callback_url）"""
    session = session_manager.get_session(session_id)
    if not session or not session.callback_url or session.callback_triggered:
        return
    
    # 在后台线程中触发回调
    def do_callback():
        try:
            print(f"[INFO] 触发回调: {session.callback_url}")  # /session_callback
            response = requests.post(
                session.callback_url,
                json={
                    "session_id": session_id,
                    "result": session.result,
                    "user_a": session.user_a,
                    "question": session.question
                },
                timeout=10
            )
            print(f"[INFO] 回调响应: {response.status_code}")
            session_manager.mark_callback_triggered(session_id)
        except Exception as e:
            print(f"[ERROR] 回调失败: {str(e)}")
    
    thread = threading.Thread(target=do_callback)
    thread.daemon = True
    thread.start()


if __name__ == '__main__':
    # 运行服务
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

