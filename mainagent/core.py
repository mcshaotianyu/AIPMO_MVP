"""主Agent核心逻辑模块"""

import os
import sys
import json
from openai import OpenAI
from prompts import SYSTEM_PROMPT
from tools import ToolManager, get_tools_definitions
from conversation_manager import conversation_manager

# 添加utils目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import mainagent_logger as logger


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
    # 优先使用conversation_manager中的最新历史
    # 如果用户提供了conversation_history，则更新到conversation_manager并合并
    stored_history = conversation_manager.get_conversation(user_id)
    
    if stored_history:
        # 如果conversation_manager中有历史，优先使用
        messages = stored_history.copy()
        logger.info(f"从conversation_manager加载用户 {user_id} 的对话历史，共 {len(messages)} 条消息")
        
        # 如果用户也提供了conversation_history，可能需要合并（暂时忽略用户提供的，使用最新的）
        if conversation_history is not None:
            logger.info(f"用户提供了conversation_history，但已使用conversation_manager中的最新历史")
    elif conversation_history is not None:
        # 如果conversation_manager中没有，但用户提供了，使用用户提供的
        messages = conversation_history.copy()
        conversation_manager.set_conversation(user_id, messages)
        logger.info(f"使用用户提供的对话历史，并保存到conversation_manager，共 {len(messages)} 条消息")
    else:
        # 都没有，创建新对话
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        logger.info(f"用户 {user_id} 没有历史对话，创建新对话")
        # 保存system消息到数据库
        conversation_manager.set_conversation(user_id, messages)
    
    # 添加用户查询
    messages.append({"role": "user", "content": user_query})
    logger.info(f"收到用户查询 - 用户ID: {user_id}, 查询内容: {user_query[:100]}{'...' if len(user_query) > 100 else ''}")
    
    try:
        
        max_iterations = 5  # 最大迭代次数，防止无限循环
        iteration = 0
        called_functions = []  # 记录调用过的函数
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"=== ReAct 迭代 {iteration}/{max_iterations} ===")
            logger.debug(f"当前对话历史消息数: {len(messages)}")
            
            # 调用LLM with Tools
            logger.info("调用LLM API...")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=tools,
                stream=False
            )
            logger.debug(f"LLM API调用成功，响应ID: {response.id}")
            
            message = response.choices[0].message
            logger.debug(f"LLM响应内容: {message.content if message.content else 'None'}...")
            logger.debug(f"LLM工具调用数量: {len(message.tool_calls) if message.tool_calls else 0}")
            
            # 检查是否有工具调用
            if message.tool_calls:
                logger.info(f"LLM决定调用工具，共 {len(message.tool_calls)} 个工具调用")
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
                
                # 处理所有工具调用
                for idx, tool_call in enumerate(message.tool_calls, 1):
                    function_name = tool_call.function.name
                    function_args_str = tool_call.function.arguments
                    tool_call_id = tool_call.id
                    
                    logger.info(f"处理工具调用 [{idx}/{len(message.tool_calls)}]: {function_name} (ID: {tool_call_id})")
                    called_functions.append(function_name)
                    
                    # 执行工具
                    function_result = None
                    try:
                        function_args = json.loads(function_args_str)
                        logger.debug(f"工具 {function_name} 参数: {json.dumps(function_args, ensure_ascii=False)}")
                        
                        # 执行函数
                        logger.info(f"开始执行工具: {function_name}")
                        function_result = tool_manager.execute_tool(function_name, function_args)
                        logger.info(f"工具 {function_name} 执行完成")
                        logger.debug(f"工具 {function_name} 结果长度: {len(function_result)} 字符")
                        logger.debug(f"工具 {function_name} 结果预览: {function_result[:300]}{'...' if len(function_result) > 300 else ''}")
                    except json.JSONDecodeError as e:
                        function_result = f"错误：函数参数解析失败: {str(e)}"
                        logger.error(f"工具 {function_name} 参数解析失败: {str(e)}")
                        logger.error(f"原始参数字符串: {function_args_str}")
                    except Exception as e:
                        function_result = f"错误：工具执行异常: {str(e)}"
                        logger.error(f"工具 {function_name} 执行异常: {str(e)}", exc_info=True)
                    
                    # 添加工具调用结果到消息历史
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": function_result
                    })
                    logger.debug(f"工具 {function_name} 结果已添加到对话历史")
                
                logger.info(f"所有工具调用完成，准备进行下一轮判断...")
                
            else:
                # 没有工具调用，LLM给出最终回复
                final_answer = message.content
                messages.append({
                    "role": "assistant",
                    "content": final_answer
                })
                
                # 保存对话历史到conversation_manager
                conversation_manager.set_conversation(user_id, messages)
                
                logger.info(f"LLM决定给出最终回复（无工具调用）")
                logger.info(f"最终回复内容: {final_answer}{'...' if len(final_answer) > 200 else ''}")
                logger.info(f"查询处理完成 - 用户ID: {user_id}, 迭代次数: {iteration}, 调用工具: {called_functions}")
                
                return {
                    "status": "completed",
                    "answer": final_answer,
                    "function_called": called_functions,
                    "function_result": function_result if called_functions else None,
                    "iterations": iteration,
                    "conversation_history": messages
                }
        
        # 达到最大迭代次数
        logger.warning(f"达到最大迭代次数 {max_iterations}，强制结束")
        logger.warning(f"已调用工具: {called_functions}")
        
        # 尝试获取一个总结回复
        messages.append({
            "role": "user", 
            "content": "请基于以上信息给出最终回复"
        })
        
        logger.info("调用LLM进行最终回复（达到最大迭代次数）")
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
        
        logger.warning(f"强制结束后的最终回复: {final_answer}{'...' if len(final_answer) > 200 else ''}")
        
        return {
            "status": "max_iterations_reached",
            "answer": final_answer,
            "function_called": called_functions,
            "iterations": max_iterations,
            "conversation_history": messages
        }
            
    except Exception as e:
        logger.error(f"处理查询异常: {str(e)}", exc_info=True)
        logger.error(f"异常时的对话历史消息数: {len(messages)}")
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
