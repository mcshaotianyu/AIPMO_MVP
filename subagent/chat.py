"""ReAct多轮对话主程序（命令行交互版本）"""

from core import init_client, extract_completed_info, create_conversation_history, call_llm


def main():
    # 写死的子任务和问询对象（可以后续改为从配置或输入获取）
    task = "询问二次报销具体流程"
    person = "人力资源部 孙铭"
    
    client = init_client()
    conversation_history = create_conversation_history(task, person)
    
    print(f"\n当前子任务：{task}")
    print(f"问询对象：{person}")
    print("\n开始对话...\n")
    
    # 获取LLM的第一条回复（开场问题）
    try:
        print("助手: ", end="", flush=True)
        assistant_response = call_llm(client, conversation_history)
        print(assistant_response)
        
        # 检测是否已经完成任务
        completed_info = extract_completed_info(assistant_response)
        if completed_info:
            print("\n" + "="*50)
            print("任务完成！归纳整理的信息：")
            print("="*50)
            print(completed_info)
            print("="*50)
            print("\n任务已完成。")
            return
        
        conversation_history.append({"role": "assistant", "content": assistant_response})
    except Exception as e:
        print(f"\n错误: {e}")
        return
    
    # 主循环
    while True:
        user_input = input("\n问询对象回复: ").strip()
        
        if user_input.lower() in ['quit', 'exit', '退出']:
            print("\n再见！")
            break
        
        if not user_input:
            continue
        
        conversation_history.append({"role": "user", "content": user_input})
        
        try:
            assistant_response = call_llm(client, conversation_history)
            completed_info = extract_completed_info(assistant_response)
            
            if completed_info:
                print(f"\n助手: {assistant_response}")
                print("\n" + "="*50)
                print("任务完成！归纳整理的信息：")
                print("="*50)
                print(completed_info)
                print("="*50)
                print("\n任务已完成。")
                break
            else:
                print(f"\n助手: {assistant_response}")
                conversation_history.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            print(f"\n错误: {e}")
            if conversation_history and conversation_history[-1]["role"] == "user":
                conversation_history.pop()


if __name__ == "__main__":
    main()

