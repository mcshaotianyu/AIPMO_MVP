"""主Agent服务API"""

import os
import sys
import requests
from flask import Flask, request, jsonify
from core import process_user_query
from conversation_manager import conversation_manager
from wechat_adapter import wechat_adapter

# 添加当前目录到路径以导入session_manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from session_manager import session_manager

app = Flask(__name__)

# SubAgent服务URL
SUBAGENT_URL = os.environ.get('SUBAGENT_URL', 'http://localhost:5000')


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})


@app.route('/wechat/callback', methods=['POST', 'GET'])
def wechat_callback():
    """
    企业微信回调接口（统一入口）
    
    GET: 验证回调URL（企业微信要求）
    POST: 接收企业微信消息并处理
    
    请求格式（POST）:
    企业微信推送的消息格式（需要根据企业微信文档实现解密）
    
    返回格式:
    {
        "status": "success" | "error"
    }
    """
    if request.method == 'GET':
        # 验证回调URL（企业微信要求）
        msg_signature = request.args.get('msg_signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        # 验证签名
        verified_echostr = wechat_adapter.verify_callback_url(msg_signature, timestamp, nonce, echostr)
        if verified_echostr:
            return verified_echostr, 200
        else:
            return jsonify({"status": "error", "message": "签名验证失败"}), 403
    
    # POST: 接收消息
    try:
        data = request.json or request.form.to_dict()
        
        # 解析企业微信消息格式（需要根据企业微信文档实现消息解密）
        message_data = wechat_adapter.parse_wechat_message(data)
        
        user_id = message_data.get("user_id")
        message_content = message_data.get("message", "")
        
        if not user_id:
            return jsonify({"status": "error", "message": "缺少user_id"}), 400
        
        print(f"\n[WECHAT] 收到企业微信消息")
        print(f"  用户ID: {user_id}")
        print(f"  消息内容: {message_content}")
        
        # 调用统一消息处理逻辑
        result = handle_unified_message_internal({
            "user_id": user_id,
            "message": message_content
        })
        
        # 【关键修改】根据路由结果决定推送给谁
        # 1. 如果路由到subagent（有user_b_id），推送给user B（被联系的员工）
        # 2. 如果路由到mainagent（没有user_b_id），推送给发送消息的人（user A）
        if result.get("user_b_id"):
            # 路由到subagent：推送给user B（被联系的员工，可能是CDEF）
            target_user_id = result.get("user_b_id")
            print(f"[INFO] 消息路由到subagent，推送给user B: {target_user_id}")
        else:
            # 路由到mainagent：推送给发送消息的人（user A）
            target_user_id = user_id
            print(f"[INFO] 消息路由到mainagent，推送给发送者: {target_user_id}")
        
        # 格式化响应并推送给正确的用户
        response_text = wechat_adapter.format_response_for_wechat(result)
        wechat_adapter.send_text_message(target_user_id, response_text)
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"[ERROR] 企业微信回调处理失败: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


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
        
        # 直接推送到企业微信
        notification_content = f"""关于您的问题：{question}

相关人员回复：
{result}"""
        
        # 推送给用户A
        success = wechat_adapter.send_text_message(user_a, notification_content)
        
        if success:
            print(f"[INFO] 已推送通知给用户 {user_a}")
        else:
            print(f"[WARNING] 推送通知失败，用户 {user_a}")
        
        return jsonify({"status": "success", "message": "回调接收成功"})
        
    except Exception as e:
        print(f"[ERROR] 回调处理失败: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


def handle_unified_message_internal(data: dict) -> dict:
    """
    统一消息处理内部逻辑（企业微信回调使用）
    
    Args:
        data: 消息数据字典，包含 user_id 和 message
        
    Returns:
        dict: 处理结果
    """
    user_id = data.get('user_id')
    message_content = data.get('message')
    
    if not user_id:
        return {"status": "error", "error": "缺少user_id"}
    
    if not message_content:
        return {"status": "error", "error": "消息内容不能为空"}
    
    # 路由判断有且仅有一个依据：根据user_id查询是否有pending session
    try:
        pending_sessions = session_manager.get_pending_sessions(user_id)
    except Exception as e:
        print(f"[ERROR] 查询待处理会话失败: {str(e)}")
        # 查询失败，默认路由到mainagent
        pending_sessions = []
    
    # 根据pending_sessions决定路由（不依赖message_content）
    if len(pending_sessions) > 0:
        # 用户B：有未完成的会话 → 路由到subagent
        # 选择最旧的session（最先创建的）
        # 因为数据库查询按created_at DESC排序，所以列表最后一个是最旧的
        if len(pending_sessions) > 1:
            # 有多个会话时，选择最旧的（列表最后一个）
            selected_session = pending_sessions[-1]
            session_id = selected_session['session_id']
            print(f"[INFO] 用户 {user_id} 有 {len(pending_sessions)} 个待处理会话，自动使用最旧的（最先创建的）: {session_id}")
        else:
            # 只有一个会话，直接使用
            selected_session = pending_sessions[0]
            session_id = selected_session['session_id']
            print(f"[INFO] 用户 {user_id} 有1个待处理会话，自动使用: {session_id}")
        
        # 使用user_id作为user_b_id（生产环境中user_id就是真实的用户ID）
        actual_user_b_id = user_id
        
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
                subagent_result = response.json()
                # 【关键修改】在返回结果中添加user_b_id信息，以便wechat_callback知道推送给谁
                subagent_result['user_b_id'] = actual_user_b_id
                subagent_result['session_id'] = session_id
                return subagent_result
            else:
                return {"status": "error", "error": f"SubAgent返回错误: {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {"status": "error", "error": f"无法连接到SubAgent服务 ({SUBAGENT_URL})"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        # 自动从conversation_manager获取对话历史，不依赖客户端传递
        query = message_content
        
        # 不传递conversation_history，让process_user_query自动从conversation_manager获取
        result = process_user_query(query, conversation_history=None, user_id=user_id)
        return result


if __name__ == '__main__':
    # 运行服务
    port = int(os.environ.get('MAINAGENT_PORT', 5001))
    print(f"\n主Agent服务启动在端口 {port}")
    print(f"回调URL: http://localhost:{port}/session_callback\n")
    app.run(host='0.0.0.0', port=port, debug=False)
