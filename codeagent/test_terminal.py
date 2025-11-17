#!/usr/bin/env python3
"""CodeAgent终端测试脚本"""

import requests
import json
import sys

CODEAGENT_URL = "http://localhost:5004"
TEST_FILE = "/Users/shaotianyu/Desktop/teleai/aipmo/tianyu/myserver/codeagent/data/user_info.xlsx"


def test_health():
    """测试健康检查"""
    print("=" * 70)
    print("测试健康检查")
    print("=" * 70)
    try:
        response = requests.get(f"{CODEAGENT_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务正常")
            print(f"响应: {response.json()}")
            return True
        else:
            print(f"❌ 服务异常: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务 ({CODEAGENT_URL})")
        print("   请先启动服务: cd codeagent && python server.py")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_query(query_text, file_path=None):
    """测试单次查询接口"""
    print("\n" + "=" * 70)
    print(f"测试查询: {query_text}")
    print("=" * 70)
    
    try:
        data = {
            "query": query_text,
            "max_iterations": 10
        }
        if file_path:
            data["file_path"] = file_path
        
        print(f"\n发送请求到: {CODEAGENT_URL}/query")
        print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(
            f"{CODEAGENT_URL}/query",
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 请求成功")
            print("\n响应结果:")
            print("-" * 70)
            print(f"状态: {result.get('status')}")
            print(f"迭代次数: {result.get('iterations')}")
            print(f"调用的工具: {result.get('function_called', [])}")
            
            if result.get('final_answer'):
                print(f"\n最终答案:")
                print(result['final_answer'])
            
            if result.get('error'):
                print(f"\n❌ 错误: {result['error']}")
            
            if result.get('execution_log'):
                print(f"\n执行日志（前5条）:")
                for log in result['execution_log'][:5]:
                    print(f"  - {log}")
            
            print("-" * 70)
            return result
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None


def test_chat(query_text, file_path=None):
    """测试多轮对话接口"""
    print("\n" + "=" * 70)
    print(f"测试对话: {query_text}")
    print("=" * 70)
    
    try:
        data = {
            "query": query_text
        }
        if file_path:
            data["file_path"] = file_path
        
        response = requests.post(
            f"{CODEAGENT_URL}/chat",
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 请求成功")
            print("\n响应结果:")
            print("-" * 70)
            print(f"状态: {result.get('status')}")
            print(f"迭代次数: {result.get('iterations')}")
            print(f"调用的工具: {result.get('function_called', [])}")
            
            if result.get('answer'):
                print(f"\n回答:")
                print(result['answer'])
            
            if result.get('error'):
                print(f"\n❌ 错误: {result['error']}")
            
            print("-" * 70)
            return result
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None


def interactive_mode():
    """交互模式"""
    print("\n" + "=" * 70)
    print("CodeAgent 交互测试模式")
    print("=" * 70)
    print(f"服务地址: {CODEAGENT_URL}")
    print(f"测试文件: {TEST_FILE}")
    print("\n提示:")
    print("  - 直接输入查询内容")
    print("  - 输入 'quit' 或 'exit' 退出")
    print("=" * 70)
    
    # 检查服务
    if not test_health():
        return
    
    conversation_history = None
    
    while True:
        try:
            query = input("\n请输入查询: ").strip()
            
            if query.lower() in ['quit', 'exit', '退出']:
                print("\n👋 再见！")
                break
            
            if not query:
                continue
            
            print(f"\n⏳ 处理中...")
            
            # 使用chat接口（支持多轮对话）
            result = test_chat(query, TEST_FILE)
            
            if result:
                # 更新对话历史
                conversation_history = result.get('conversation_history')
            
        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 命令行模式
        query = " ".join(sys.argv[1:])
        if not test_health():
            return
        test_query(query, TEST_FILE)
    else:
        # 交互模式
        interactive_mode()


if __name__ == "__main__":
    main()

