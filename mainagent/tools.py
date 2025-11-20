"""工具模块"""

import json
import sys
import os
import requests
from typing import Dict, Any, List

# 添加database目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import db
from utils.logger import mainagent_logger as logger


class SearchPhoneTool:
    """根据姓名查询手机号工具"""
    
    def __init__(self):
        self.name = "search_phone"
        self.description = "根据员工姓名列表查询对应的手机号"
    
    def execute(self, names: List[str]) -> str:
        """
        根据员工姓名列表查询手机号
        
        Args:
            names: 员工姓名列表
            
        Returns:
            str: JSON格式的查询结果，包含name和phone的列表
        """
        try:
            logger.info(f"执行search_phone工具，输入姓名列表: {names}")
            
            if not names or not isinstance(names, list):
                logger.warning(f"search_phone工具收到无效输入: {names}")
                return json.dumps([])
            
            # 过滤空字符串
            original_count = len(names)
            names = [name.strip() for name in names if name and name.strip()]
            filtered_count = len(names)
            
            if original_count != filtered_count:
                logger.debug(f"过滤了 {original_count - filtered_count} 个空姓名")
            
            if not names:
                logger.warning("search_phone工具：过滤后姓名列表为空")
                return json.dumps([])
            
            logger.info(f"查询 {len(names)} 个员工的手机号: {names}")
            
            # 从数据库查询
            results = db.search_employee_phones(names)
            
            logger.info(f"search_phone工具查询完成，找到 {len(results)} 个员工信息")
            if results:
                logger.debug(f"查询结果: {json.dumps(results, ensure_ascii=False)}")
            
            # 返回JSON格式的结果
            return json.dumps(results, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"search_phone工具执行异常: {str(e)}", exc_info=True)
            return json.dumps([], ensure_ascii=False)


class ContactEmployeeTool:
    """联系员工工具"""
    
    def __init__(self):
        self.name = "contact_employee"
        self.description = "通知员工相关信息"
    
    def execute(self, employee_info: List[Dict[str, str]], user_a: str = "user_a") -> str:
        """
        通知员工
        
        Args:
            employee_info: 员工信息列表，每个元素是一个字典，包含：
                - phone: 员工手机号
                - name: 员工姓名
                - question: 通知内容
            user_a: 用户A的标识
            
        Returns:
            str: 通知结果
        """
        logger.info(f"执行contact_employee工具，用户: {user_a}，员工数量: {len(employee_info) if employee_info else 0}")
        
        if not employee_info or not isinstance(employee_info, list):
            logger.error("contact_employee工具：employee_info 必须是一个非空列表")
            return "错误：employee_info 必须是一个非空列表"
        
        results = []
        success_count = 0
        error_count = 0
        
        for idx, emp in enumerate(employee_info):
            if not isinstance(emp, dict):
                error_msg = f"错误：第 {idx+1} 个员工信息格式不正确，必须是字典"
                logger.error(f"contact_employee工具：{error_msg}")
                results.append(error_msg)
                error_count += 1
                continue
            
            employee_id = emp.get("phone") or emp.get("employee_phone")
            employee_name = emp.get("name") or emp.get("employee_name")
            question = emp.get("question")
            
            if not all([employee_id, employee_name, question]):
                error_msg = f"错误：第 {idx+1} 个员工信息不完整，需要 phone、name、question"
                logger.warning(f"contact_employee工具：{error_msg}，员工信息: {emp}")
                results.append(error_msg)
                error_count += 1
                continue
            
            # 直接通知员工（这里可以集成企业微信API或其他通知方式）
            # 目前只是返回通知信息
            logger.info(f"通知员工 [{idx+1}/{len(employee_info)}]: {employee_name} (手机号: {employee_id})")
            logger.debug(f"通知内容: {question[:100]}{'...' if len(question) > 100 else ''}")
            results.append(f"已成功通知{employee_name}（手机号: {employee_id}）\n通知内容: {question}")
            success_count += 1
        
        # 组合所有结果
        result_text = "\n\n".join(results)
        logger.info(f"contact_employee工具执行完成，成功: {success_count}，失败: {error_count}")
        return result_text


class SelectEmployeeTool:
    """筛选员工工具"""
    
    def __init__(self):
        self.name = "select_employee"
        self.description = "根据用户输入从本地员工信息文件中筛选符合条件的员工"
        self.codeagent_url = os.environ.get('CODEAGENT_URL', 'http://localhost:5004')
        # 默认文件路径：使用相对于项目根目录的路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.default_file_path = os.path.join(base_dir, "codeagent", "data", "user_info.xlsx")
    
    def execute(self, query: str, file_path: str = None, max_iterations: int = 10) -> str:
        """
        执行员工筛选
        
        Args:
            query: 筛选条件描述（例如："筛选出分数在80分以上的员工"）
            file_path: 文件路径（可选，但会被忽略，始终使用默认的user_info.xlsx文件）
            max_iterations: 最大迭代次数（可选，默认10）
            
        Returns:
            str: 筛选结果
        """
        try:
            # 始终使用默认的user_info.xlsx文件，忽略用户提供的file_path
            file_path = self.default_file_path
            logger.info(f"执行select_employee工具，查询: {query}, 使用默认文件: {file_path}, 最大迭代: {max_iterations}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                error_msg = f"错误：员工信息文件不存在: {file_path}"
                logger.error(error_msg)
                return error_msg
            
            # 构造请求数据
            request_data = {
                "query": query,
                "file_path": file_path,
                "max_iterations": max_iterations
            }
            
            logger.debug(f"调用codeagent接口: {self.codeagent_url}/query")
            logger.debug(f"请求数据: {json.dumps(request_data, ensure_ascii=False)}")
            
            # 调用codeagent的query接口
            response = requests.post(
                f"{self.codeagent_url}/query",
                json=request_data,
                timeout=60
            )
            
            logger.info(f"codeagent响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                iterations = result.get("iterations", 0)
                function_called = result.get("function_called", [])
                
                logger.info(f"codeagent返回状态: {status}, 迭代次数: {iterations}, 调用工具: {function_called}")
                
                if status == "completed":
                    final_answer = result.get("final_answer", "")
                    logger.info(f"select_employee工具执行成功，结果长度: {len(final_answer)} 字符")
                    logger.debug(f"筛选结果预览: {final_answer[:300]}{'...' if len(final_answer) > 300 else ''}")
                    return final_answer
                elif status == "max_iterations_reached":
                    final_answer = result.get("final_answer", "")
                    logger.warning(f"select_employee工具达到最大迭代次数 {iterations}")
                    return f"筛选完成（达到最大迭代次数{iterations}次）：\n{final_answer}"
                elif status == "error":
                    error_msg = result.get("error", "未知错误")
                    logger.error(f"select_employee工具执行失败: {error_msg}")
                    return f"筛选员工失败：{error_msg}"
                else:
                    logger.warning(f"select_employee工具返回未知状态: {status}")
                    return f"筛选员工返回未知状态：{status}"
            else:
                error_msg = f"筛选员工服务返回错误码 {response.status_code}，响应: {response.text}"
                logger.error(error_msg)
                return error_msg
            
        except requests.exceptions.Timeout:
            logger.error(f"select_employee工具：请求超时（60秒）")
            return f"筛选员工服务超时"
        except requests.exceptions.ConnectionError:
            logger.error(f"select_employee工具：无法连接到代码Agent服务（{self.codeagent_url}）")
            return f"筛选员工服务连接失败：无法连接到代码Agent服务（{self.codeagent_url}）"
        except Exception as e:
            logger.error(f"select_employee工具执行异常: {str(e)}", exc_info=True)
            return f"筛选员工执行异常：{str(e)}"


def get_tools_definitions() -> List[Dict]:
    """获取新格式的tools定义"""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_phone",
                "description": "根据员工姓名列表查询对应的手机号。当你知道员工姓名但缺少手机号时，使用此工具查询",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "names": {
                            "type": "array",
                            "description": "员工姓名列表，每个元素是一个员工姓名",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["names"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "contact_employee",
                "description": "当用户同意通知员工时，调用此工具通知相关员工。可以一次通知多个员工，也可以一次通知一个员工。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_info": {
                            "type": "array",
                            "description": "员工信息列表，每个元素包含一个员工的联系信息",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "phone": {
                                        "type": "string",
                                        "description": "员工手机号"
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "员工姓名"
                                    },
                                    "question": {
                                        "type": "string",
                                        "description": "要发送给该员工的通知内容"
                                    }
                                },
                                "required": ["phone", "name", "question"]
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
                "description": "从本地员工信息文件（user_info.xlsx）中筛选符合条件的员工。该工具会自动读取项目中的user_info.xlsx文件，无需指定文件路径。当用户需要根据文件内容（如Excel文件）筛选员工时，使用此工具。例如：筛选出分数在80分以上的员工、筛选出不及格的员工等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "筛选条件描述，例如：'筛选出分数在80分以上的员工'、'筛选出不及格的员工'、'筛选出得分在85-90分之间的员工'等"
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
            "search_phone": SearchPhoneTool(),
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
        logger.info(f"ToolManager执行工具: {tool_name}，用户ID: {self.user_id}")
        logger.debug(f"工具输入参数: {json.dumps(tool_input, ensure_ascii=False)}")
        
        if tool_name not in self.tools:
            logger.error(f"未知工具: {tool_name}，可用工具: {list(self.tools.keys())}")
            return f"错误：未知工具 {tool_name}"
        
        tool = self.tools[tool_name]
        
        try:
            if tool_name == "search_phone":
                names = tool_input.get("names", [])
                if not names or not isinstance(names, list):
                    logger.error(f"search_phone工具：names参数无效: {names}")
                    return f"错误：{tool_name} 需要 names 参数（员工姓名列表）"
                if len(names) == 0:
                    logger.error(f"search_phone工具：names列表为空")
                    return f"错误：names 列表不能为空"
                return tool.execute(names)
            elif tool_name == "contact_employee":
                employee_info = tool_input.get("employee_info")
                if not employee_info:
                    logger.error(f"contact_employee工具：employee_info参数缺失")
                    return f"错误：contact_employee 需要 employee_info 参数（员工信息列表）"
                if not isinstance(employee_info, list):
                    logger.error(f"contact_employee工具：employee_info不是列表类型: {type(employee_info)}")
                    return f"错误：employee_info 必须是一个列表"
                if len(employee_info) == 0:
                    logger.error(f"contact_employee工具：employee_info列表为空")
                    return f"错误：employee_info 列表不能为空"
                return tool.execute(employee_info, user_a=self.user_id)
            elif tool_name == "select_employee":
                query = tool_input.get("query", "")
                if not query:
                    logger.error(f"select_employee工具：query参数缺失")
                    return f"错误：select_employee 需要 query 参数"
                # file_path参数会被忽略，始终使用默认的user_info.xlsx文件
                max_iterations = tool_input.get("max_iterations", 10)
                logger.info(f"select_employee工具：忽略用户提供的file_path参数，使用默认文件")
                return tool.execute(query, None, max_iterations)
            else:
                logger.error(f"工具 {tool_name} 执行逻辑未实现")
                return f"错误：工具 {tool_name} 执行逻辑未实现"
                
        except Exception as e:
            logger.error(f"工具 {tool_name} 执行异常: {str(e)}", exc_info=True)
            return f"工具执行异常：{str(e)}"
    
    def get_available_tools(self) -> Dict[str, str]:
        """获取可用工具列表"""
        return {name: tool.description for name, tool in self.tools.items()}
