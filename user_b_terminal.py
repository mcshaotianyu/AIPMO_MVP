#!/usr/bin/env python3
"""
用户B交互终端

此脚本模拟用户B（被联系的员工）的交互界面：
1. 通过统一接口发送消息（与user_a_terminal.py完全一致）
2. 后台轮询检查新的问询会话
3. 多轮对话直到任务完成

使用方法：
1. 确保主agent和子agent服务已启动
2. 运行此脚本: python user_b_terminal.py [user_id]
"""

import requests
import json
import time
import threading
import sys

MAINAGENT_URL = "http://localhost:5002"


class UserBTerminal:
    """用户B终端"""

    def __init__(self, user_id="*"):  # 默认员工ID
        self.user_id = user_id
        self.monitoring = True
        self.known_sessions = set()  # 已处理的会话ID
        self.in_conversation = False  # 是否正在处理会话
        self.current_session_id = None  # 当前会话ID

    def print_banner(self):
        """打印横幅"""
        print("\n" + "╔" + "═" * 68 + "╗")
        print("║" + " " * 20 + "用户B (被咨询员工) 交互终端" + " " * 19 + "║")
        print("╚" + "═" * 68 + "╝")
        print(f"\n当前用户: {self.user_id}")
        print("=" * 70)
        print("提示:")
        print("  - 直接输入消息回复（服务端会自动路由到相应会话）")
        print("  - 输入 'quit' 或 'exit' 退出")
        print("  - 后台会自动检测新的问询请求")
        print("=" * 70)

    def send_message(self, message):
        """
        发送消息到主agent（使用统一入口/message，与user_a_terminal.py完全一致）

        Args:
            message: 消息内容（如果为空字符串，用于查询pending sessions）

        Returns:
            dict: 服务端返回的结果
        """
        try:
            response = requests.post(
                f"{MAINAGENT_URL}/message",
                json={
                    "user_id": self.user_id,  # 统一使用user_id
                    "message": message  # 统一使用message字段（也支持query）
                },
                timeout=600
            )

            if response.status_code == 200:
                result = response.json()
                return result
            else:
                return {
                    "status": "error",
                    "error": f"请求失败: HTTP {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {"status": "error", "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "error": "无法连接到主agent服务"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def display_result(self, result):
        """显示结果"""
        print("\n" + "─" * 70)

        status = result.get("status")
        error = result.get("error")

        # 处理subagent的回复（用户B的对话）
        if result.get("session_status") == "completed":
            print("✓ 会话已完成！")
            print(f"\n子Agent总结的信息:")
            print(result.get("result", ""))
            print("✅ 此结果已自动回调给主agent，将推送给用户A。")
        elif result.get("next_question"):
            print(f"💬 子Agent: {result['next_question']}")
        elif result.get("answer"):
            print(f"🤖 助手回复:\n  {result['answer']}")
        elif error:
            print(f"❌ 错误: {error}")
        else:
            print(f"状态: {status}")

        print("─" * 70)
    
    def check_new_sessions(self):
        """
        检查是否有新的问询（通过发送空消息触发服务端返回pending sessions）

        Returns:
            list: 新的会话列表
        """
        result = self.send_message("")  # 空消息触发服务端返回pending sessions

        new_sessions = []
        if result.get("status") == "success" and result.get("sessions"):
            sessions = result.get("sessions", [])
            for session in sessions:
                session_id = session.get("session_id")
                if session_id and session_id not in self.known_sessions:
                    new_sessions.append(session)

        return new_sessions

    def handle_new_session(self, session):
        """处理新会话"""
        session_id = session.get("session_id")
        self.known_sessions.add(session_id)
        self.current_session_id = session_id
        self.in_conversation = True  # 进入对话模式
        
        print("\n")
        print("🔔" + "═" * 68 + "🔔")
        print("                   ✨ 收到新的问询请求 ✨")
        print("═" * 70)
        print(f"📌 来自用户: {session.get('user_a', '未知')}")
        print(f"📌 原始问题: {session.get('question', '未知')}")
        print(f"📌 模拟员工: {session.get('user_b_name', '未知')} (ID: {self.user_id})")
        print("═" * 70)
        
        # 显示子agent的第一个问题
        if session.get('latest_question'):
            print(f"\n💬 子Agent: {session['latest_question']}\n")

    def run(self):
        """运行交互终端"""
        self.print_banner()

        # 检查服务是否可用
        try:
            response = requests.get(f"{MAINAGENT_URL}/health", timeout=5)
            if response.status_code != 200:
                print(f"\n❌ 主Agent服务不可用")
                print("   请先启动主agent服务: cd mainagent && python server.py")
                return
            print(f"✓ 主Agent服务正常\n")
        except Exception as e:
            print(f"\n❌ 无法连接到主Agent服务: {e}")
            print("   请先启动主agent服务: cd mainagent && python server.py")
            return
        
        # 启动后台监控线程，定期检查新会话
        def monitor_new_sessions():
            while self.monitoring:
                try:
                    time.sleep(3)  # 每3秒检查一次

                    # 如果正在对话中，跳过检查
                    if self.in_conversation:
                        continue

                    new_sessions = self.check_new_sessions()
                    if new_sessions:
                        for session in new_sessions:
                            self.handle_new_session(session)
                except Exception as e:
                    pass  # 静默失败

        monitor_thread = threading.Thread(target=monitor_new_sessions)
        monitor_thread.daemon = True
        monitor_thread.start()

        # 显示等待提示
        print("\n💡 等待新的问询请求...")
        print("   (收到问询时会自动开始对话)")
        print("   输入 'quit' 退出\n")

        # 主循环
        while True:
            try:
                # 如果不在对话中，等待新会话
                if not self.in_conversation:
                    time.sleep(1)  # 避免CPU占用过高
                    continue

                # 获取用户输入
                user_input = input(f"\n[{self.user_id}] 您的回复: ").strip()

                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("\n👋 再见！")
                    self.monitoring = False
                    break

                if not user_input:
                    continue

                print(f"\n⏳ 处理中...")

                # 发送消息（服务端会自动路由）
                result = self.send_message(user_input)

                # 显示结果
                self.display_result(result)

                # 如果会话完成，退出对话模式
                if result.get("session_status") == "completed":
                    self.in_conversation = False
                    self.current_session_id = None
                    print("\n💡 继续等待新的问询请求...")
                    print("   输入 'quit' 退出\n")

            except KeyboardInterrupt:
                print("\n\n👋 程序被用户中断")
                self.monitoring = False
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {str(e)}")


def main():
    """主函数"""
    # 默认
    user_id = "*"
    terminal = UserBTerminal(user_id)
    terminal.run()


if __name__ == "__main__":
    main()
