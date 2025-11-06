#!/usr/bin/env python3
"""
用户B交互终端

此脚本模拟用户B（被联系的员工）的交互界面：
1. 查看待处理的问询会话
2. 回复子agent的问题
3. 多轮对话直到任务完成

使用方法：
1. 确保主agent和子agent服务已启动
2. 确保已通过test_full_flow.py触发了联系员工流程
3. 运行此脚本: python user_b_terminal.py
"""

import requests
import json
import sys
import os

# 支持使用统一入口（mainagent）或直接连接subagent
# 通过环境变量 USE_UNIFIED_ENTRY=true 启用统一入口
# USE_UNIFIED_ENTRY = os.environ.get('USE_UNIFIED_ENTRY', 'false').lower() == 'true'
# USE_UNIFIED_ENTRY = os.environ.get('USE_UNIFIED_ENTRY', 'true')
USE_UNIFIED_ENTRY = 'true'
SUBAGENT_URL = "http://localhost:5000"
MAINAGENT_URL = "http://localhost:5001"


def print_banner():
    """打印横幅"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "用户B (被咨询员工) 交互终端" + " " * 19 + "║")
    print("╚" + "═" * 68 + "╝\n")


def get_pending_sessions(user_b_id):
    """获取用户B的待处理会话"""
    try:
        if USE_UNIFIED_ENTRY:
            # 使用统一入口（不指定type，由服务端根据user_b_id自动路由）
            response = requests.post(
                f"{MAINAGENT_URL}/message",
                json={
                    "user_b_id": user_b_id
                },
                timeout=5
            )
        else:
            # 直接连接subagent（向后兼容）
            response = requests.get(
                f"{SUBAGENT_URL}/get_pending_sessions",
                params={"user_b_id": user_b_id},
                timeout=5
            )
        
        result = response.json()
        
        if result.get("status") == "success":
            return result.get("sessions", [])
        else:
            print(f"获取会话失败: {result.get('error')}")
            return []
            
    except Exception as e:
        print(f"请求失败: {e}")
        return []


def get_session_status(session_id):
    """获取会话详情"""
    try:
        if USE_UNIFIED_ENTRY:
            # 使用统一入口（不指定type，由服务端根据session_id自动路由）
            response = requests.post(
                f"{MAINAGENT_URL}/message",
                json={
                    "session_id": session_id
                },
                timeout=5
            )
        else:
            # 直接连接subagent（向后兼容）
            response = requests.get(
                f"{SUBAGENT_URL}/get_status",
                params={"session_id": session_id},
                timeout=5
            )
        
        result = response.json()
        
        if result.get("status") == "success":
            return result.get("session")
        else:
            print(f"获取会话状态失败: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def reply_to_session(session_id, user_b_id, message):
    """回复会话"""
    try:
        if USE_UNIFIED_ENTRY:
            # 使用统一入口（不指定type，由服务端根据session_id+user_b_id+message自动路由）
            response = requests.post(
                f"{MAINAGENT_URL}/message",
                json={
                    "session_id": session_id,
                    "user_b_id": user_b_id,
                    "message": message
                },
                timeout=30
            )
        else:
            # 直接连接subagent（向后兼容）
            response = requests.post(
                f"{SUBAGENT_URL}/reply",
                json={
                    "session_id": session_id,
                    "user_b_id": user_b_id,
                    "message": message
                },
                timeout=30
            )
        
        result = response.json()
        
        if result.get("status") == "success":
            return result
        else:
            print(f"回复失败: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def interactive_mode():
    """交互模式"""
    print_banner()
    
    # 检查服务
    try:
        if USE_UNIFIED_ENTRY:
            # 使用统一入口时，检查mainagent服务
            response = requests.get(f"{MAINAGENT_URL}/health", timeout=5)
            if response.status_code != 200:
                print(f"\n❌ 主Agent服务不可用（统一入口模式）")
                print("   请先启动主agent服务: cd mainagent && python server.py")
                return
            print(f"✓ 主Agent服务正常（统一入口模式）\n")
        else:
            # 向后兼容模式，检查subagent服务
            response = requests.get(f"{SUBAGENT_URL}/health", timeout=5)
            if response.status_code != 200:
                print(f"\n❌ 子Agent服务不可用")
                print("   请先启动子agent服务: cd subagent && python server.py")
                return
            print(f"✓ 子Agent服务正常（直接连接模式）\n")
    except Exception as e:
        if USE_UNIFIED_ENTRY:
            print(f"\n❌ 无法连接到主Agent服务: {e}")
            print("   请先启动主agent服务: cd mainagent && python server.py")
        else:
            print(f"\n❌ 无法连接到子Agent服务: {e}")
            print("   请先启动子agent服务: cd subagent && python server.py")
        return
    
    # 输入用户B的ID（支持"*"或"all"来接收所有员工的会话）
    print("请输入您的员工ID:")
    print("  - 输入具体员工ID: 只接收该员工的问询")
    print("  - 输入 '*' 或 'all': 接收所有员工的问询（测试模式）")
    print("  - 直接回车: 使用默认ID 1234567890")
    user_b_id_input = input("> ").strip()
    
    if not user_b_id_input:
        user_b_id = "1234567890"
        print(f"\n当前用户: 员工ID {user_b_id} (默认)")
    elif user_b_id_input.lower() in ["*", "all"]:
        user_b_id = "*"
        print(f"\n当前模式: 测试模式 - 接收所有员工的问询")
    else:
        user_b_id = user_b_id_input
        print(f"\n当前用户: 员工ID {user_b_id}")
    
    print("\n💡 等待新的问询请求...")
    print("   (收到问询时会自动开始对话)")
    print("   输入 'quit' 退出\n")
    
    # 启动后台监控线程，自动处理新会话
    import threading
    import time
    monitoring = {"active": True, "known_sessions": set(), "in_conversation": False}
    
    def handle_new_session(session_id, session):
        """自动处理新会话"""
        monitoring["in_conversation"] = True
        
        # 【关键修复】使用会话中的实际user_b_id，而不是外部的user_b_id变量
        actual_user_b_id = session.get('user_b_id', user_b_id)
        
        print("\n")
        print("🔔" + "═" * 68 + "🔔")
        print("                   ✨ 收到新的问询请求 ✨")
        print("═" * 70)
        print(f"📌 来自用户: {session['user_a']}")
        print(f"📌 原始问题: {session['question']}")
        if user_b_id == "*":
            print(f"📌 模拟员工: {session.get('user_b_name', '未知')} (ID: {actual_user_b_id})")
        print("═" * 70)
        
        # 显示子agent的第一个问题
        if session.get('latest_question'):
            print(f"\n💬 子Agent: {session['latest_question']}\n")
        
        # 进入对话循环
        while monitoring["active"]:
            try:
                user_input = input("您的回复: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    monitoring["active"] = False
                    break
                
                # 【关键修复】使用会话中的实际user_b_id来回复
                result = reply_to_session(session_id, actual_user_b_id, user_input)
                
                if result:
                    if result.get('session_status') == 'completed':
                        print("\n" + "═" * 70)
                        print("✓ 会话已完成！")
                        print("\n子Agent总结的信息:")
                        print(result['result'])
                        print("═" * 70)
                        print("✅ 此结果已自动回调给主agent，将推送给用户A。\n")
                        break
                    elif result.get('next_question'):
                        print(f"\n💬 子Agent: {result['next_question']}\n")
                else:
                    print("❌ 回复失败，请重试")
                    
            except KeyboardInterrupt:
                monitoring["active"] = False
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
        
        monitoring["in_conversation"] = False
        print("\n💡 继续等待新的问询请求...")
        print("   输入 'quit' 退出\n")
    
    def monitor_new_sessions():
        """后台监控新会话"""
        while monitoring["active"]:
            try:
                time.sleep(3)  # 每3秒检查一次
                
                # 如果正在对话中，跳过检查
                if monitoring["in_conversation"]:
                    continue
                
                sessions = get_pending_sessions(user_b_id)
                if sessions:
                    for session in sessions:
                        session_id = session['session_id']
                        # 如果是新会话，自动进入对话
                        if session_id not in monitoring["known_sessions"]:
                            monitoring["known_sessions"].add(session_id)
                            handle_new_session(session_id, session)
                            
            except Exception as e:
                pass  # 静默失败
    
    monitor_thread = threading.Thread(target=monitor_new_sessions)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # 主循环 - 等待用户输入quit退出
    try:
        while monitoring["active"]:
            user_input = input("").strip()
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n👋 再见！")
                monitoring["active"] = False
                break
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
        monitoring["active"] = False


def quick_reply_mode():
    """快速回复模式（通过命令行参数）"""
    if len(sys.argv) < 4:
        print("用法: python user_b_terminal.py quick <session_id> <user_b_id> <message>")
        return
    
    session_id = sys.argv[2]
    user_b_id = sys.argv[3]
    message = " ".join(sys.argv[4:])
    
    print(f"\n回复会话 {session_id}...")
    result = reply_to_session(session_id, user_b_id, message)
    
    if result:
        if result.get('session_status') == 'completed':
            print("\n✓ 会话已完成！")
            print(f"\n结果: {result['result']}")
        elif result.get('next_question'):
            print(f"\n下一个问题: {result['next_question']}")


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_reply_mode()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()

