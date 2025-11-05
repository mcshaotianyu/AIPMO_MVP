"""主Agent命令行交互版本"""

from core import process_user_query


def main():
    print("\n" + "="*60)
    print("主Agent Function Call系统启动")
    print("支持工具：search_doc（文档检索）、search_employee（员工检索）、contact_employee（联系员工）")
    print("输入 'quit' 或 'exit' 退出")
    print("="*60)
    
    conversation_history = None
    
    while True:
        try:
            # 获取用户输入
            user_query = input("\n请输入您的查询: ").strip()
            
            if user_query.lower() in ['quit', 'exit', '退出']:
                print("\n再见！")
                break
            
            if not user_query:
                continue
            
            print(f"\n处理查询: {user_query}")
            print("-" * 50)
            
            # 处理用户查询
            result = process_user_query(user_query, conversation_history)
            
            # 更新对话历史
            conversation_history = result.get("conversation_history")
            
            print("\n执行结果:")
            print(f"状态: {result['status']}")
            
            if result.get("iterations"):
                print(f"ReAct迭代次数: {result['iterations']}")
            
            if result.get("function_called"):
                if isinstance(result['function_called'], list):
                    print(f"调用的工具: {', '.join(result['function_called'])}")
                else:
                    print(f"调用的工具: {result['function_called']}")
            
            if result.get("answer"):
                print(f"\n助手回复: {result['answer']}")
            
            if result.get("error"):
                print(f"错误: {result['error']}")
            
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
        except Exception as e:
            print(f"\n发生错误: {str(e)}")


if __name__ == "__main__":
    main()
