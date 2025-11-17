"""代码Agent核心逻辑模块"""

import os
import json
import re
from openai import OpenAI
from prompts import SYSTEM_PROMPT
from tools import ToolManager, get_tools_definitions


def clean_and_validate_code(code: str) -> str:
    """
    清理和验证提取的Python代码，确保可以直接执行
    
    Args:
        code: 原始代码字符串
        
    Returns:
        str: 清理后的代码，如果无效则返回None
    """
    if not code:
        return None
    
    # 移除代码块标记（如果还有残留）
    code = re.sub(r'^```python\s*', '', code, flags=re.MULTILINE)
    code = re.sub(r'^```\s*', '', code, flags=re.MULTILINE)
    code = re.sub(r'```\s*$', '', code, flags=re.MULTILINE)
    
    # 移除首尾空白
    code = code.strip()
    
    # 检查基本结构
    if not code:
        return None
    
    # 移除可能的解释性文字行（不包含Python关键字）
    lines = code.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        # 保留空行、注释和代码行
        if not stripped:
            cleaned_lines.append('')
            continue
        
        # 如果是注释或包含Python关键字的行，保留
        if (stripped.startswith('#') or 
            any(keyword in stripped for keyword in [
                'import', 'from', 'def', 'class', 'if', 'elif', 'else', 'for', 'while', 
                '=', '==', '!=', '<', '>', '<=', '>=', 'in', 'not', 'and', 'or',
                'print', 'return', 'df', 'pd', 'json', 'FILE_PATH', 'pd.read_excel',
                'pd.', 'df[', 'df.', 'filtered', 'result', 'to_dict', 'dumps'
            ])):
            cleaned_lines.append(line)
    
    code = '\n'.join(cleaned_lines).strip()
    
    if not code:
        return None
    
    # 确保包含必要的导入（在代码开头）
    has_pandas = 'import pandas' in code or 'from pandas' in code
    has_json = 'import json' in code
    
    if not has_pandas:
        code = 'import pandas as pd\n' + code
    if not has_json:
        # 在pandas导入后添加json导入
        if has_pandas:
            code = code.replace('import pandas as pd', 'import pandas as pd\nimport json', 1)
            if 'import json' not in code:
                code = code.replace('from pandas', 'import json\nfrom pandas', 1)
                if 'import json' not in code:
                    code = 'import json\n' + code
        else:
            code = 'import json\n' + code
    
    # 确保使用FILE_PATH变量（替换硬编码路径）
    if 'read_excel' in code:
        # 替换各种可能的路径格式
        code = re.sub(r"pd\.read_excel\(['\"][^'\"]+['\"]\)", 'pd.read_excel(FILE_PATH)', code)
        code = re.sub(r"read_excel\(['\"][^'\"]+['\"]\)", 'read_excel(FILE_PATH)', code)
        # 如果还是没有FILE_PATH，尝试添加
        if 'FILE_PATH' not in code and 'read_excel' in code:
            # 查找read_excel调用并替换
            code = re.sub(r'read_excel\([^)]+\)', 'read_excel(FILE_PATH)', code)
    
    # 确保有输出语句（检查是否有json.dumps输出）
    if 'json.dumps' in code and 'print(' not in code:
        # 查找json.dumps调用，如果没有被print包裹，添加print
        # 但要注意不要破坏已有的print语句
        lines = code.split('\n')
        new_lines = []
        for line in lines:
            if 'json.dumps' in line and 'print(' not in line:
                # 如果这行包含json.dumps但没有print，添加print
                if line.strip().startswith('json.dumps'):
                    line = 'print(' + line.strip() + ')'
                elif '=' in line and 'json.dumps' in line.split('=')[1]:
                    # 如果是在赋值语句中，保持原样，在后面添加print
                    new_lines.append(line)
                    var_name = line.split('=')[0].strip()
                    new_lines.append(f'print({var_name})')
                    continue
            new_lines.append(line)
        code = '\n'.join(new_lines)
    
    # 最终验证：确保包含基本结构
    if 'read_excel' not in code:
        return None
    
    if 'FILE_PATH' not in code:
        # 如果还是没有FILE_PATH，尝试添加
        code = re.sub(r'read_excel\([^)]+\)', 'read_excel(FILE_PATH)', code)
        if 'FILE_PATH' not in code:
            return None
    
    return code


def init_client():
    """初始化OpenAI客户端"""
    api_key = os.environ.get('DEEPSEEK_API_KEY', "sk-1e6a5099e785466789ea6243ef517aac")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )


def execute_code_agent(user_query: str, file_path: str = None, max_iterations: int = 10) -> dict:
    """
    执行代码Agent（ReAct方法）
    
    Args:
        user_query: 用户查询
        file_path: XLSX文件路径（可选，如果查询中包含文件路径）
        max_iterations: 最大迭代次数
        
    Returns:
        dict: 执行结果
    """
    client = init_client()
    tool_manager = ToolManager()
    
    # 获取工具定义
    tools = get_tools_definitions()
    
    # 初始化对话历史
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    
    # 如果提供了文件路径，添加到系统提示中
    if file_path:
        messages[0]["content"] += f"\n\n注意：用户提供的XLSX文件路径是：{file_path}"
    
    iteration = 0
    execution_log = []
    called_functions = []
    final_answer = None
    
    try:
        while iteration < max_iterations:
            iteration += 1
            execution_log.append(f"=== 迭代 {iteration} ===")
            print(f"\n[INFO] === ReAct 迭代 {iteration} ===")
            
            # 调用LLM with Tools
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=tools,
                stream=False
            )
            
            message = response.choices[0].message
            print(f"\n[INFO] 消息内容: {message.content}")
            print(f"\n[INFO]工具调用: {message.tool_calls}")
            
            # 检查是否有工具调用
            if message.tool_calls:
                execution_log.append("LLM决定调用工具")
                # 添加助手消息到历史
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
                
                # 处理每个工具调用
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args_str = tool_call.function.arguments
                    tool_call_id = tool_call.id
                    
                    execution_log.append(f"调用工具: {function_name}({function_args_str})")
                    called_functions.append(function_name)
                    
                    try:
                        function_args = json.loads(function_args_str)
                    except json.JSONDecodeError as e:
                        function_result = f"错误：函数参数解析失败: {str(e)}"
                    else:
                        # 执行工具
                        function_result = tool_manager.execute_tool(function_name, function_args)
                        print(f"[INFO] 工具 {function_name} 执行结果: {function_result[:200]}...")
                    
                    # 添加工具结果到消息历史
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": function_result
                    })
                    
                    execution_log.append(f"工具结果: {function_result[:100]}...")
            else:
                # 没有工具调用，检查LLM回复中是否包含代码
                assistant_content = message.content
                
                # 检查是否包含Python代码块（支持多种格式）
                code_patterns = [
                    r'```python\s*(.*?)```',  # ```python ... ```
                    r'```\s*(.*?)```',        # ``` ... ``` (没有python标记)
                ]
                
                extracted_code = None
                for pattern in code_patterns:
                    code_matches = re.findall(pattern, assistant_content, re.DOTALL)
                    if code_matches:
                        extracted_code = code_matches[0].strip()
                        break
                
                if extracted_code and file_path:
                    # 清理和验证代码
                    cleaned_code = clean_and_validate_code(extracted_code)
                    if not cleaned_code:
                        # 代码清理失败，让LLM重新生成
                        messages.append({
                            "role": "assistant",
                            "content": assistant_content
                        })
                        messages.append({
                            "role": "user",
                            "content": "代码格式不正确，请重新生成完整的、可执行的Python代码，确保代码用 ```python 和 ``` 包裹，且代码可以直接执行。"
                        })
                        continue
                    
                    print(f"[INFO] 从LLM回复中提取到代码，准备执行")
                    execution_log.append("从LLM回复中提取代码并执行")
                    
                    # 添加助手消息到历史
                    messages.append({
                        "role": "assistant",
                        "content": assistant_content
                    })
                    
                    # 执行代码
                    function_result = tool_manager.execute_tool("execute_code", {
                        "code": extracted_code,
                        "file_path": file_path
                    })
                    called_functions.append("execute_code")
                    execution_log.append(f"执行代码结果: {function_result[:200]}...")
                    
                    # 添加执行结果到消息历史
                    messages.append({
                        "role": "user",
                        "content": f"代码执行结果：\n{function_result}\n\n请解析结果，以友好的方式展示筛选出的用户信息，并询问用户是否还有其他问题。"
                    })
                    
                    # 继续循环，让LLM处理执行结果
                    continue
                else:
                    # 没有代码，LLM给出最终答案
                    final_answer = assistant_content
                    
                    # 确保最终答案包含询问用户的部分
                    if "请问您还有其他问题吗" not in final_answer and "还有其他问题" not in final_answer:
                        final_answer += "\n\n请问您还有其他问题吗？"
                    
                    messages.append({
                        "role": "assistant",
                        "content": final_answer
                    })
                    execution_log.append("LLM给出最终答案")
                    print(f"[INFO] LLM给出最终答案: {final_answer}")
                    break
        
        # 如果达到最大迭代次数
        if iteration >= max_iterations:
            return {
                "status": "max_iterations_reached",
                "final_answer": final_answer or "达到最大迭代次数，未完成处理",
                "iterations": iteration,
                "execution_log": execution_log,
                "function_called": called_functions
            }
        
        return {
            "status": "completed",
            "final_answer": final_answer or "处理完成",
            "iterations": iteration,
            "execution_log": execution_log,
            "function_called": called_functions
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "iterations": iteration,
            "execution_log": execution_log,
            "function_called": called_functions
        }


def process_user_query(user_query: str, file_path: str = None, conversation_history: list = None) -> dict:
    """
    处理用户查询（支持多轮对话）
    
    Args:
        user_query: 用户查询
        file_path: XLSX文件路径
        conversation_history: 对话历史（可选）
        
    Returns:
        dict: 处理结果
    """
    client = init_client()
    tool_manager = ToolManager()
    
    # 获取工具定义
    tools = get_tools_definitions()
    
    # 初始化或使用现有对话历史
    if conversation_history is not None:
        messages = conversation_history.copy()
    else:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    
    # 如果提供了文件路径，添加到系统提示中
    if file_path:
        if messages[0]["role"] == "system":
            messages[0]["content"] += f"\n\n注意：用户提供的XLSX文件路径是：{file_path}"
    
    # 添加用户查询
    messages.append({"role": "user", "content": user_query})
    
    try:
        print(f"[INFO] 处理查询: {user_query}")
        
        max_iterations = 10
        iteration = 0
        called_functions = []
        answer = None
        
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
            
            message = response.choices[0].message
            
            # 检查是否有工具调用
            if message.tool_calls:
                print(f"[INFO] LLM决定调用工具")
                # 添加助手消息到历史
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
                
                # 处理工具调用
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                function_args_str = tool_call.function.arguments
                tool_call_id = tool_call.id
                
                called_functions.append(function_name)
                
                try:
                    function_args = json.loads(function_args_str)
                except json.JSONDecodeError as e:
                    function_result = f"错误：函数参数解析失败: {str(e)}"
                else:
                    # 执行工具
                    function_result = tool_manager.execute_tool(function_name, function_args)
                    print(f"[INFO] 工具 {function_name} 执行结果: {function_result[:200]}...")
                
                # 添加工具结果到消息历史
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": function_result
                })
            else:
                # 没有工具调用，检查LLM回复中是否包含代码
                assistant_content = message.content
                
                # 检查是否包含Python代码块（支持多种格式）
                code_patterns = [
                    r'```python\s*(.*?)```',  # ```python ... ```
                    r'```\s*(.*?)```',        # ``` ... ``` (没有python标记)
                ]
                
                extracted_code = None
                for pattern in code_patterns:
                    code_matches = re.findall(pattern, assistant_content, re.DOTALL)
                    if code_matches:
                        extracted_code = code_matches[0].strip()
                        break
                
                if extracted_code and file_path:
                    # 清理和验证代码
                    cleaned_code = clean_and_validate_code(extracted_code)
                    if not cleaned_code:
                        # 代码清理失败，让LLM重新生成
                        messages.append({
                            "role": "assistant",
                            "content": assistant_content
                        })
                        messages.append({
                            "role": "user",
                            "content": "代码格式不正确，请重新生成完整的、可执行的Python代码，确保代码用 ```python 和 ``` 包裹，且代码可以直接执行。"
                        })
                        continue
                    
                    print(f"[INFO] 从LLM回复中提取到代码，准备执行")
                    
                    # 添加助手消息到历史
                    messages.append({
                        "role": "assistant",
                        "content": assistant_content
                    })
                    
                    # 执行代码
                    function_result = tool_manager.execute_tool("execute_code", {
                        "code": cleaned_code,
                        "file_path": file_path
                    })
                    called_functions.append("execute_code")
                    print(f"[INFO] 代码执行结果: {function_result[:200]}...")
                    
                    # 添加执行结果到消息历史
                    messages.append({
                        "role": "user",
                        "content": f"代码执行结果：\n{function_result}\n\n请解析结果，以友好的方式展示筛选出的用户信息，并询问用户是否还有其他问题。"
                    })
                    
                    # 继续循环，让LLM处理执行结果
                    continue
                else:
                    # 没有代码，LLM给出最终答案
                    answer = assistant_content
                    
                    # 确保最终答案包含询问用户的部分
                    if "请问您还有其他问题吗" not in answer and "还有其他问题" not in answer:
                        answer += "\n\n请问您还有其他问题吗？"
                    
                    messages.append({
                        "role": "assistant",
                        "content": answer
                    })
                    print(f"[INFO] LLM给出最终答案: {answer}")
                    break
        
        return {
            "status": "completed" if answer else "max_iterations_reached",
            "answer": answer or "达到最大迭代次数",
            "function_called": called_functions,
            "iterations": iteration,
            "conversation_history": messages
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "conversation_history": messages
        }

