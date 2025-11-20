#!/usr/bin/env python3
"""
用户A交互终端

此脚本模拟用户A（提问的用户）的交互界面：
1. 向主agent提问
2. 接收主agent的回复
3. 多轮对话

使用方法：
1. 确保主agent服务已启动
2. 运行此脚本: python user_a_terminal.py
"""

import requests
import sys

MAINAGENT_URL = "http://localhost:5001"


class UserATerminal:
    """用户A终端"""
    
    def __init__(self, user_id="user_a_张三"):
        self.user_id = user_id
        self.conversation_history = None
        
    def print_banner(self):
        """打印横幅"""
        print("\n" + "╔" + "═" * 68 + "╗")
        print("║" + " " * 20 + "用户A (提问者) 交互终端" + " " * 22 + "║")
        print("╚" + "═" * 68 + "╝")
        print(f"\n当前用户: {self.user_id}")
        print("=" * 70)
        print("提示:")
        print("  - 直接输入问题向主agent提问")
        print("  - 输入 'quit' 或 'exit' 退出")
        print("=" * 70)
    
    def send_query(self, query):
        """发送查询到主agent（使用统一入口/message）"""
        try:
            response = requests.post(
                f"{MAINAGENT_URL}/message",
                json={
                    # 统一接口：只传递user_id和query/message，服务端自动路由和获取对话历史
                    "user_id": self.user_id,
                    "query": query  # 也支持message字段
                },
                timeout=600
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 更新对话历史（从服务端返回的结果中获取）
                self.conversation_history = result.get("conversation_history")
                
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
        answer = result.get("answer")
        error = result.get("error")
        function_called = result.get("function_called")
        
        if error:
            print(f"❌ 错误: {error}")
        elif answer:
            print(f"🤖 助手回复:\n")
            print(f"  {answer}")
            
            if function_called:
                print(f"\n📋 调用的工具: {', '.join(function_called) if isinstance(function_called, list) else function_called}")
        else:
            print(f"状态: {status}")
        
        print("─" * 70)
    
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
        
        # 主循环
        while True:
            try:
                # 获取用户输入
                user_input = input(f"\n[{self.user_id}] 您的问题: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("\n👋 再见！")
                    break
                
                if not user_input:
                    continue
                
                print(f"\n⏳ 处理中...")
                
                # 发送查询
                result = self.send_query(user_input)
                
                # 显示结果
                self.display_result(result)
                
            except KeyboardInterrupt:
                print("\n\n👋 程序被用户中断")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {str(e)}")


def main():
    """主函数"""
    # 可以通过命令行参数指定用户ID
    user_id = sys.argv[1] if len(sys.argv) > 1 else "user_a_张三"
    
    terminal = UserATerminal(user_id)
    terminal.run()


if __name__ == "__main__":
    main()

