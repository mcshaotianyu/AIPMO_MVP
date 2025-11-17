"""主Agent核心逻辑模块"""

import os
import json
import re
from openai import OpenAI
from prompts import SYSTEM_PROMPT
from tools import ToolManager, get_tools_definitions
from conversation_manager import conversation_manager


def init_client():
    """初始化OpenAI客户端"""
    api_key = os.environ.get('DEEPSEEK_API_KEY', "sk-1e6a5099e785466789ea6243ef517aac")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )


def process_user_query(user_query: str, conversation_history: list = None, user_id: str = "user_a") -> dict:
    """
    处理用户查询（支持多轮对话）
    
    Args:
        user_query: 用户查询
        conversation_history: 对话历史（可选）
        user_id: 用户标识（可选）
        
    Returns:
        dict: 处理结果
    """
    client = init_client()
    tool_manager = ToolManager(user_id=user_id)
    
    # 获取工具定义（新格式）
    tools = get_tools_definitions()
    
    # 初始化或使用现有对话历史
    # 优先使用conversation_manager中的最新历史（包含SubAgent回调结果）
    # 如果用户提供了conversation_history，则更新到conversation_manager并合并
    stored_history = conversation_manager.get_conversation(user_id)
    
    if stored_history:
        # 如果conversation_manager中有历史，优先使用（包含最新的SubAgent结果）
        messages = stored_history.copy()
        print(f"[INFO] 从conversation_manager加载用户 {user_id} 的对话历史（包含最新SubAgent结果）")
        
        # 如果用户也提供了conversation_history，可能需要合并（暂时忽略用户提供的，使用最新的）
        if conversation_history is not None:
            print(f"[INFO] 用户提供了conversation_history，但已使用conversation_manager中的最新历史")
    elif conversation_history is not None:
        # 如果conversation_manager中没有，但用户提供了，使用用户提供的
        messages = conversation_history.copy()
        conversation_manager.set_conversation(user_id, messages)
        print(f"[INFO] 使用用户提供的对话历史，并保存到conversation_manager")
    else:
        # 都没有，创建新对话
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        print(f"[INFO] 用户 {user_id} 没有历史对话，创建新对话")
        # 保存system消息到数据库
        conversation_manager.set_conversation(user_id, messages)
    
    # 添加用户查询
    messages.append({"role": "user", "content": user_query})
    
    try:
        print(f"[INFO] 处理查询: {user_query}")
        
        max_iterations = 5  # 最大迭代次数，防止无限循环
        iteration = 0
        called_functions = []  # 记录调用过的函数
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n[INFO] === ReAct 迭代 {iteration} ===")
            
            # 调用LLM with Tools
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=tools,
                stream=False
            )
            
            # 打印原始响应
            print(f"[DEBUG] 原始大模型响应: {response}")
            print(f"[DEBUG] 响应对象类型: {type(response)}")
            
            message = response.choices[0].message
            print(f"[DEBUG] 消息对象: {message}")
            print(f"[DEBUG] 消息内容: {message.content}")
            print(f"[DEBUG] 工具调用: {message.tool_calls}")
            
            # 检查是否有工具调用
            if message.tool_calls:
                print(f"[INFO] LLM决定调用工具，共 {len(message.tool_calls)} 个工具调用")
                # 添加助手消息到历史（转换为字典格式）
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in message.tool_calls
                    ]
                })
                
                # 处理所有工具调用（确保每个tool_call都有对应的tool响应）
                has_contact_employee = False
                contact_employee_result = None
                contact_employee_session_id = None
                contact_employee_tool_call_id = None
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args_str = tool_call.function.arguments
                    tool_call_id = tool_call.id
                    
                    print(f"[INFO] 处理工具调用: {function_name} (ID: {tool_call_id})")
                    called_functions.append(function_name)
                    
                    # 特殊处理：如果是contact_employee工具，记录信息但不立即返回
                    if function_name == "contact_employee":
                        has_contact_employee = True
                        contact_employee_tool_call_id = tool_call_id
                        
                        try:
                            function_args = json.loads(function_args_str)
                            print(f"[INFO] contact_employee工具参数: {function_args}")
                            
                            # 并行执行工具（不等待完成）
                            contact_employee_result = tool_manager.execute_tool(function_name, function_args)
                            print(f"[INFO] contact_employee工具已启动")
                            
                            # 从function_result中提取所有session_id（格式：会话ID: xxx-xxx-xxx 或 所有会话ID: xxx, xxx, xxx）
                            # 先尝试提取"所有会话ID"格式
                            all_session_ids_match = re.search(r'所有会话ID:\s*([a-f0-9\-\s,]+)', contact_employee_result)
                            if all_session_ids_match:
                                # 提取所有session_id
                                session_ids_str = all_session_ids_match.group(1)
                                session_ids = [s.strip() for s in session_ids_str.split(',') if s.strip()]
                                print(f"[INFO] 提取到 {len(session_ids)} 个session_id: {session_ids}")
                                # 注册每个session_id到tool_call_id和user_id的映射
                                for session_id in session_ids:
                                    conversation_manager.register_session(session_id, tool_call_id, user_id)
                                    print(f"[INFO] 已注册session_id映射: {session_id} -> tool_call_id={tool_call_id}, user_id={user_id}")
                            else:
                                # 如果没有"所有会话ID"格式，尝试提取单个会话ID（向后兼容）
                                session_id_match = re.search(r'会话ID:\s*([a-f0-9\-]+)', contact_employee_result)
                                if session_id_match:
                                    contact_employee_session_id = session_id_match.group(1)
                                    print(f"[INFO] 提取到session_id: {contact_employee_session_id}")
                                    # 注册session_id到tool_call_id和user_id的映射
                                    conversation_manager.register_session(contact_employee_session_id, tool_call_id, user_id)
                                    print(f"[INFO] 已注册session_id映射: {contact_employee_session_id} -> tool_call_id={tool_call_id}, user_id={user_id}")
                            
                            # 添加工具调用结果到消息历史
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": contact_employee_result
                            })
                            
                        except json.JSONDecodeError as e:
                            contact_employee_result = f"错误：函数参数解析失败: {str(e)}"
                            print(f"[ERROR] contact_employee参数解析失败: {str(e)}")
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": contact_employee_result
                            })
                    else:
                        # 普通工具处理
                        function_result = None
                        try:
                            function_args = json.loads(function_args_str)
                            print(f"[INFO] 工具参数: {function_args}")
                            # 执行函数
                            function_result = tool_manager.execute_tool(function_name, function_args)
                            print(f"[INFO] 工具执行完成: {function_name}")
                            print(f"[INFO] 工具结果预览: {function_result[:200]}{'...' if len(function_result) > 200 else ''}")
                        except json.JSONDecodeError as e:
                            function_result = f"错误：函数参数解析失败: {str(e)}"
                            print(f"[ERROR] 参数解析失败: {str(e)}")
                        except Exception as e:
                            function_result = f"错误：工具执行异常: {str(e)}"
                            print(f"[ERROR] 工具执行异常: {str(e)}")
                        
                        # 添加工具调用结果到消息历史
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": function_result
                        })
                
                # 如果调用了contact_employee工具，需要特殊处理（立即返回）
                if has_contact_employee:
                    print(f"[INFO] 检测到contact_employee工具，执行特殊处理")
                    # 立即返回LLM的content作为最终回复
                    final_answer = message.content or "好的，我已联系相关员工，有结果后我会通知您。"
                    
                    # 添加助手回复到历史
                    messages.append({
                        "role": "assistant", 
                        "content": final_answer
                    })
                    
                    # 保存对话历史到conversation_manager
                    conversation_manager.set_conversation(user_id, messages)
                    print(f"[INFO] 已保存用户 {user_id} 的对话历史")
                    
                    print(f"[INFO] contact_employee特殊处理完成，直接返回回复")
                    print(f"[INFO] 最终回复内容: {final_answer}")
                    print(f"[INFO] 总共进行了 {iteration} 轮ReAct，调用了工具: {called_functions}")
                    
                    return {
                        "status": "completed",
                        "answer": final_answer,
                        "function_called": called_functions,
                        "function_result": contact_employee_result,
                        "iterations": iteration,
                        "conversation_history": messages
                    }
                
                print(f"[INFO] 所有工具调用完成，继续下一轮判断...")
                
            else:
                # 没有工具调用，LLM给出最终回复
                final_answer = message.content
                messages.append({
                    "role": "assistant",
                    "content": final_answer
                })
                
                # 保存对话历史到conversation_manager
                conversation_manager.set_conversation(user_id, messages)
                
                print(f"[INFO] LLM决定给出最终回复")
                print(f"[INFO] 最终回复内容: {final_answer}")
                print(f"[INFO] 总共进行了 {iteration} 轮ReAct，调用了工具: {called_functions}")
                
                return {
                    "status": "completed",
                    "answer": final_answer,
                    "function_called": called_functions,
                    "function_result": function_result if called_functions else None,
                    "iterations": iteration,
                    "conversation_history": messages
                }
        
        # 达到最大迭代次数
        print(f"[WARNING] 达到最大迭代次数 {max_iterations}，强制结束")
        
        # 尝试获取一个总结回复
        messages.append({
            "role": "user", 
            "content": "请基于以上信息给出最终回复"
        })
        
        print(f"[INFO] 调用LLM进行最终回复，检查这里是否存在问题：{messages}")
        final_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools,
            stream=False
        )
        
        final_message = final_response.choices[0].message
        final_answer = final_message.content or "抱歉，经过多轮分析后仍无法给出明确答案。"
        
        messages.append({
            "role": "assistant",
            "content": final_answer
        })
        
        # 保存对话历史到conversation_manager
        conversation_manager.set_conversation(user_id, messages)
        
        return {
            "status": "max_iterations_reached",
            "answer": final_answer,
            "function_called": called_functions,
            "iterations": max_iterations,
            "conversation_history": messages
        }
            
    except Exception as e:
        print(f"[ERROR] 处理异常: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "conversation_history": messages
        }


def call_llm(client, conversation_history):
    """调用LLM（兼容性函数）"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=conversation_history,
        stream=False
    )
    return response.choices[0].message.content
