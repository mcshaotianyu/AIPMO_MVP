"""工具模块"""

import json
import requests
import uuid
import os
from typing import Dict, Any, List


class SearchDocTool:
    """检索文档工具"""
    
    def __init__(self):
        self.name = "search_doc"
        self.description = "根据查询内容检索相关文档信息"
    
    def execute(self, query: str) -> str:
        """
        执行文档检索
        
        Args:
            query: 查询内容
            
        Returns:
            str: 检索结果
        """
        try:
            # 从环境变量获取API密钥，如果没有则使用默认值
            api_key = os.environ.get('DOC_SEARCH_API_KEY', 'app-4xeuqrykny8i5bw9ELtlyzg4')
            url = "https://agent.teleai.com.cn/v1/chat-messages"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "input_data": {},
                "query": query,
                "mode": "streaming",
                "conversation_id": "",
                "user": "admin",
                "files": []
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            # 处理流式响应
            if response.status_code == 200:
                # 解析SSE格式的流式响应
                full_answer = ""
                
                for line in response.text.split('\n'):
                    if line.startswith('data: '):
                        data_content = line[6:]  # 移除'data: '前缀
                        if data_content.strip():
                            try:
                                event_data = json.loads(data_content)
                                
                                # 提取回答内容
                                if 'answer' in event_data:
                                    full_answer += event_data['answer']
                            except json.JSONDecodeError:
                                # 忽略非JSON数据行
                                pass
                
                # 返回完整答案
                if full_answer.strip():
                    return full_answer.strip()
                else:
                    return "未找到相关文档信息"
            else:
                return f"文档检索失败：API请求失败，状态码: {response.status_code}, 响应: {response.text[:200]}"
            
        except requests.exceptions.Timeout:
            return "文档检索失败：请求超时"
        except requests.exceptions.ConnectionError:
            return "文档检索失败：无法连接到文档检索服务"
        except Exception as e:
            return f"文档检索失败：{str(e)}"


class SearchEmployeeTool:
    """检索员工工具"""
    
    def __init__(self):
        self.name = "search_employee"
        self.description = "根据查询内容检索相关员工信息"
    
    def execute(self, query: str) -> str:
        """
        执行员工检索
        
        Args:
            query: 查询内容
            
        Returns:
            str: 检索结果
        """
        try:
            # 从环境变量获取API密钥，如果没有则使用默认值
            api_key = os.environ.get('EMPLOYEE_SEARCH_API_KEY', 'app-ZjfgBb44mO4yiK9EeYDsPfXq')
            url = "https://agent.teleai.com.cn/v1/chat-messages"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "input_data": {},
                "query": query,
                "mode": "streaming",
                "conversation_id": "",
                "user": "admin",
                "files": []
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            # 处理流式响应
            if response.status_code == 200:
                # 解析SSE格式的流式响应
                full_answer = ""
                
                for line in response.text.split('\n'):
                    if line.startswith('data: '):
                        data_content = line[6:]  # 移除'data: '前缀
                        if data_content.strip():
                            try:
                                event_data = json.loads(data_content)
                                
                                # 提取回答内容
                                if 'answer' in event_data:
                                    full_answer += event_data['answer']
                            except json.JSONDecodeError:
                                # 忽略非JSON数据行
                                pass
                
                # 返回完整答案
                if full_answer.strip():
                    return full_answer.strip()
                else:
                    return "未找到相关员工信息"
            else:
                return f"员工检索失败：API请求失败，状态码: {response.status_code}, 响应: {response.text[:200]}"
            
        except requests.exceptions.Timeout:
            return "员工检索失败：请求超时"
        except requests.exceptions.ConnectionError:
            return "员工检索失败：无法连接到员工检索服务"
        except Exception as e:
            return f"员工检索失败：{str(e)}"


class ContactEmployeeTool:
    """联系员工工具"""
    
    def __init__(self):
        self.name = "contact_employee"
        self.description = "联系员工获取问题答案"
        self.subagent_url = os.environ.get('SUBAGENT_URL', 'http://localhost:5000')
        self.mainagent_url = os.environ.get('MAINAGENT_URL', 'http://localhost:5001')
    
    def execute(self, employee_info: List[Dict[str, str]], user_a: str = "user_a") -> str:
        """
        联系员工
        
        Args:
            employee_info: 员工信息列表，每个元素是一个字典，包含：
                - id: 员工ID
                - name: 员工姓名
                - question: 问询问题
            user_a: 用户A的标识
            
        Returns:
            str: 问询结果，包含所有联系员工的会话信息
        """
        if not employee_info or not isinstance(employee_info, list):
            return "错误：employee_info 必须是一个非空列表"
        
        results = []
        session_ids = []
        
        for idx, emp in enumerate(employee_info):
            if not isinstance(emp, dict):
                results.append(f"错误：第 {idx+1} 个员工信息格式不正确，必须是字典")
                continue
            
            employee_id = emp.get("id") or emp.get("employee_id")
            employee_name = emp.get("name") or emp.get("employee_name")
            question = emp.get("question")
            
            if not all([employee_id, employee_name, question]):
                results.append(f"错误：第 {idx+1} 个员工信息不完整，需要 id、name、question")
                continue
            
            try:
                # 生成唯一会话ID
                session_id = str(uuid.uuid4())
                session_ids.append(session_id)
                
                # 构造回调URL
                callback_url = f"{self.mainagent_url}/session_callback"
                
                # 调用子agent的start_session接口
                response = requests.post(
                    f"{self.subagent_url}/start_session",
                    json={
                        "session_id": session_id,
                        "user_a": user_a,
                        "user_b_id": employee_id,
                        "user_b_name": employee_name,
                        "question": question,
                        "callback_url": callback_url
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        # 会话创建成功
                        first_question = result.get("first_question", "")
                        
                        # 【关键修改】推送给user B（employee_id），而不是user A
                        # 因为subagent的消息应该发送给被联系的员工（user B/CDEF），而不是发起问询的用户A
                        try:
                            # 导入wechat_adapter（延迟导入避免循环依赖）
                            from wechat_adapter import wechat_adapter
                            
                            # 构造推送给user B的消息
                            notification_content = f"""您收到一个新的问询请求：

来自：{user_a}
问题：{question}

{first_question}

请回复此消息继续对话。"""
                            
                            # 推送给user B（employee_id）
                            success = wechat_adapter.send_text_message(employee_id, notification_content)
                            if success:
                                print(f"[INFO] 已推送问询请求给用户B: {employee_id} ({employee_name})")
                            else:
                                print(f"[WARNING] 推送问询请求失败，用户B: {employee_id} ({employee_name})")
                        except Exception as e:
                            print(f"[ERROR] 推送消息给user B失败: {str(e)}")
                            # 即使推送失败，也继续执行，不影响主流程
                        
                        results.append(f"已成功联系{employee_name}（ID: {employee_id}），子agent已向其提问：{first_question}\n会话ID: {session_id}")
                    else:
                        results.append(f"联系{employee_name}失败：{result.get('error', '未知错误')}")
                else:
                    results.append(f"联系{employee_name}失败：子agent服务返回错误码 {response.status_code}")
                
            except requests.exceptions.Timeout:
                results.append(f"联系{employee_name}失败：子agent服务超时")
            except requests.exceptions.ConnectionError:
                results.append(f"联系{employee_name}失败：无法连接到子agent服务（{self.subagent_url}）")
            except Exception as e:
                results.append(f"联系{employee_name}失败：{str(e)}")
        
        # 组合所有结果
        result_text = "\n\n".join(results)
        if session_ids:
            result_text += f"\n\n所有会话ID: {', '.join(session_ids)}\n我会在收到完整回复后通知您。"
        
        return result_text


class SelectEmployeeTool:
    """筛选员工工具"""
    
    def __init__(self):
        self.name = "select_employee"
        self.description = "根据用户输入和相关文件筛选符合条件的员工"
        self.codeagent_url = os.environ.get('CODEAGENT_URL', 'http://localhost:5004')
    
    def execute(self, query: str, file_path: str = "/Users/shaotianyu/Desktop/teleai/aipmo/tianyu/myserver/codeagent/data/user_info.xlsx", max_iterations: int = 10) -> str:
        """
        执行员工筛选
        
        Args:
            query: 筛选条件描述（例如："筛选出分数在80分以上的员工"）
            file_path: 文件路径（可选，默认为 ./data/user_info.xlsx）
            max_iterations: 最大迭代次数（可选，默认10）
            
        Returns:
            str: 筛选结果
        """
        try:
            # 如果没有提供文件路径或为空字符串，使用默认值
            # if not file_path or file_path.strip() == "":
            #     file_path = "/Users/shaotianyu/Desktop/teleai/aipmo/tianyu/myserver/codeagent/data/user_info.xlsx"
            file_path = "/Users/shaotianyu/Desktop/teleai/aipmo/tianyu/myserver/codeagent/data/user_info.xlsx"
            # 构造请求数据
            request_data = {
                "query": query,
                "file_path": file_path,
                "max_iterations": max_iterations
            }
            
            # 调用codeagent的query接口
            response = requests.post(
                f"{self.codeagent_url}/query",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                
                if status == "completed":
                    final_answer = result.get("final_answer", "")
                    iterations = result.get("iterations", 0)
                    return final_answer
                elif status == "max_iterations_reached":
                    final_answer = result.get("final_answer", "")
                    iterations = result.get("iterations", 0)
                    return f"筛选完成（达到最大迭代次数{iterations}次）：\n{final_answer}"
                elif status == "error":
                    error_msg = result.get("error", "未知错误")
                    return f"筛选员工失败：{error_msg}"
                else:
                    return f"筛选员工返回未知状态：{status}"
            else:
                return f"筛选员工服务返回错误码 {response.status_code}，响应: {response.text[:200]}"
            
        except requests.exceptions.Timeout:
            return f"筛选员工服务超时"
        except requests.exceptions.ConnectionError:
            return f"筛选员工服务连接失败：无法连接到代码Agent服务（{self.codeagent_url}）"
        except Exception as e:
            return f"筛选员工执行异常：{str(e)}"


def get_tools_definitions() -> List[Dict]:
    """获取新格式的tools定义"""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_doc",
                "description": "根据查询内容检索相关文档信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "要检索的查询内容"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_employee",
                "description": "当search_doc工具无法检索到相关信息或检索到的结果不足以解决用户问题时，根据query内容从员工台账中检索相关员工",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "要检索的查询内容，可以是相关职责描述、部门、职位或员工姓名等"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "contact_employee",
                "description": "当用户同意联系员工时，调用此工具联系员工问询相关问题。可以一次联系多个员工",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_info": {
                            "type": "array",
                            "description": "员工信息列表，每个元素包含一个员工的联系信息",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "description": "员工ID"
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "员工姓名"
                                    },
                                    "question": {
                                        "type": "string",
                                        "description": "要问询的问题或要直接发送给该员工的消息"
                                    }
                                },
                                "required": ["id", "name", "question"]
                            }
                        }
                    },
                    "required": ["employee_info"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "select_employee",
                "description": "根据用户输入和相关文件筛选符合条件的员工。当用户需要根据文件内容（如Excel文件）筛选员工时，使用此工具。例如：筛选出分数在80分以上的员工、筛选出不及格的员工等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "筛选条件描述，例如：'筛选出分数在80分以上的员工'、'筛选出不及格的员工'、'筛选出得分在85-90分之间的员工'等"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "要处理的文件路径（可选，默认为 ./data/user_info.xlsx）"
                        },
                        "max_iterations": {
                            "type": "integer",
                            "description": "最大迭代次数（可选，默认10）"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]


class ToolManager:
    """工具管理器"""
    
    def __init__(self, user_id="user_a"):
        self.user_id = user_id
        self.tools = {
            "search_doc": SearchDocTool(),
            "search_employee": SearchEmployeeTool(),
            "contact_employee": ContactEmployeeTool(),
            "select_employee": SelectEmployeeTool()
        }
    
    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数
            
        Returns:
            str: 工具执行结果
        """
        if tool_name not in self.tools:
            return f"错误：未知工具 {tool_name}"
        
        tool = self.tools[tool_name]
        
        try:
            if tool_name in ["search_doc", "search_employee"]:
                query = tool_input.get("query", "")
                if not query:
                    return f"错误：{tool_name} 需要 query 参数"
                return tool.execute(query)
            elif tool_name == "contact_employee":
                employee_info = tool_input.get("employee_info")
                if not employee_info:
                    return f"错误：contact_employee 需要 employee_info 参数（员工信息列表）"
                if not isinstance(employee_info, list):
                    return f"错误：employee_info 必须是一个列表"
                if len(employee_info) == 0:
                    return f"错误：employee_info 列表不能为空"
                return tool.execute(employee_info, user_a=self.user_id)
            elif tool_name == "select_employee":
                query = tool_input.get("query", "")
                if not query:
                    return f"错误：select_employee 需要 query 参数"
                # 如果没有提供file_path或为空，使用默认值
                file_path = tool_input.get("file_path")
                if not file_path or file_path.strip() == "":
                    file_path = "./data/user_info.xlsx"
                max_iterations = tool_input.get("max_iterations", 10)
                return tool.execute(query, file_path, max_iterations)
            else:
                return f"错误：工具 {tool_name} 执行逻辑未实现"
                
        except Exception as e:
            return f"工具执行异常：{str(e)}"
    
    def get_available_tools(self) -> Dict[str, str]:
        """获取可用工具列表"""
        return {name: tool.description for name, tool in self.tools.items()}
