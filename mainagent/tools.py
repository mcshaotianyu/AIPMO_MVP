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
            # 这里可以接入真实的检索系统，如Elasticsearch、向量数据库等
            # 目前返回模拟结果
            mock_docs = {
                "二次报销": "二次报销是指员工在首次报销被拒绝或需要补充材料后，重新提交报销申请的流程。通常需要提供完整的发票、申请表和相关证明材料。审批流程：1.重新填写报销单 2.补充缺失材料 3.部门主管审批 4.财务审核 5.出纳付款。",
                "项目进度": "项目进度管理包括计划制定、执行监控、风险评估等环节。需要定期更新进度报告，确保项目按时完成。关键节点：需求分析->设计->开发->测试->上线->维护。",
                "人力资源": "人力资源部门负责员工招聘、培训、绩效管理、薪酬福利等工作。是企业人才管理的核心部门。联系方式：HR@company.com，电话：400-123-4567。",
                "财务流程": "财务流程包括预算编制、费用审批、报销管理、财务分析等环节。需要严格按照公司制度执行。财务部门工作时间：周一至周五 9:00-18:00。",
                "请假": "请假流程：1.填写请假申请单 2.直属主管审批 3.人力资源部备案 4.超过3天需总监审批。病假需提供医院证明，年假需提前一周申请。",
                "加班": "加班申请流程：1.填写加班申请单 2.部门主管审批 3.人力资源部确认 4.财务部计算加班费。加班费标准：工作日1.5倍，周末2倍，法定节假日3倍。"
            }
            
            # 关键词匹配
            for keyword, info in mock_docs.items():
                if keyword in query:
                    return info
            
            return "未找到相关文档信息"
            
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
        return "id:1234567890, name:雷总"
        try:
            # 模拟员工数据库
            mock_employees = {
                "人力资源": [
                    {"id": "hr001", "name": "张小华", "department": "人力资源部", "position": "HR专员", "expertise": "招聘、培训"},
                    {"id": "hr002", "name": "李明", "department": "人力资源部", "position": "HR主管", "expertise": "绩效管理、薪酬"}
                ],
                "财务": [
                    {"id": "fin001", "name": "王会计", "department": "财务部", "position": "会计", "expertise": "报销审核、账务处理"},
                    {"id": "fin002", "name": "陈出纳", "department": "财务部", "position": "出纳", "expertise": "资金管理、付款"}
                ],
                "技术": [
                    {"id": "tech001", "name": "刘工程师", "department": "技术部", "position": "高级工程师", "expertise": "系统开发、架构设计"},
                    {"id": "tech002", "name": "赵程序员", "department": "技术部", "position": "程序员", "expertise": "前端开发、UI设计"}
                ],
                "项目": [
                    {"id": "pm001", "name": "孙项目", "department": "项目管理部", "position": "项目经理", "expertise": "项目管理、进度控制"},
                    {"id": "pm002", "name": "周助理", "department": "项目管理部", "position": "项目助理", "expertise": "项目协调、文档管理"}
                ]
            }
            
            # 关键词匹配员工
            found_employees = []
            for keyword, employees in mock_employees.items():
                if keyword in query:
                    found_employees.extend(employees)
            
            # 也可以按姓名搜索
            for dept_employees in mock_employees.values():
                for emp in dept_employees:
                    if emp["name"] in query:
                        found_employees.append(emp)
            
            if found_employees:
                result = "找到以下相关员工：\n"
                for emp in found_employees:
                    result += f"- {emp['name']} (ID: {emp['id']}) - {emp['department']} {emp['position']} - 专长: {emp['expertise']}\n"
                return result.strip()
            else:
                return "未找到相关员工"
            
        except Exception as e:
            return f"员工检索失败：{str(e)}"


class ContactEmployeeTool:
    """联系员工工具"""
    
    def __init__(self):
        self.name = "contact_employee"
        self.description = "联系员工获取问题答案"
        self.subagent_url = os.environ.get('SUBAGENT_URL', 'http://localhost:5000')
        self.mainagent_url = os.environ.get('MAINAGENT_URL', 'http://localhost:5001')
    
    def execute(self, employee_id: str, employee_name: str, question: str, user_a: str = "user_a") -> str:
        """
        联系员工
        
        Args:
            employee_id: 员工ID
            employee_name: 员工姓名
            question: 问询问题
            user_a: 用户A的标识
            
        Returns:
            str: 问询结果
        """
        try:
            # 生成唯一会话ID
            session_id = str(uuid.uuid4())
            
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
                    return f"已成功联系{employee_name}（ID: {employee_id}），子agent已向其提问：{first_question}\n\n会话ID: {session_id}\n我会在收到完整回复后通知您。"
                else:
                    return f"联系员工失败：{result.get('error', '未知错误')}"
            else:
                return f"联系员工失败：子agent服务返回错误码 {response.status_code}"
            
        except requests.exceptions.Timeout:
            return f"联系员工失败：子agent服务超时"
        except requests.exceptions.ConnectionError:
            return f"联系员工失败：无法连接到子agent服务（{self.subagent_url}）"
        except Exception as e:
            return f"联系员工失败：{str(e)}"


def get_function_definitions() -> List[Dict]:
    """获取Function Call的函数定义（旧格式，兼容性）"""
    return [
        {
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
        },
        {
            "name": "search_employee",
            "description": "当知识库文档中不存在用户问题的相关答案时，调用此工具从员工台账中找到可能能解决用户问题的员工",
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
        },
        {
            "name": "contact_employee",
            "description": "当用户同意联系员工时，调用此工具联系员工问询相关问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "员工ID"
                    },
                    "employee_name": {
                        "type": "string",
                        "description": "员工姓名"
                    },
                    "question": {
                        "type": "string",
                        "description": "要问询的问题"
                    }
                },
                "required": ["employee_id", "employee_name", "question"]
            }
        }
    ]


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
                "description": "根据查询内容从员工台账中检索相关员工信息",
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
                "description": "当用户同意联系员工时，调用此工具联系员工问询相关问题",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "string",
                            "description": "员工ID"
                        },
                        "employee_name": {
                            "type": "string",
                            "description": "员工姓名"
                        },
                        "question": {
                            "type": "string",
                            "description": "要问询的问题"
                        }
                    },
                    "required": ["employee_id", "employee_name", "question"]
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
            "contact_employee": ContactEmployeeTool()
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
                employee_id = tool_input.get("employee_id", "")
                employee_name = tool_input.get("employee_name", "")
                question = tool_input.get("question", "")
                if not all([employee_id, employee_name, question]):
                    return f"错误：contact_employee 需要 employee_id, employee_name, question 参数"
                return tool.execute(employee_id, employee_name, question, user_a=self.user_id)
            else:
                return f"错误：工具 {tool_name} 执行逻辑未实现"
                
        except Exception as e:
            return f"工具执行异常：{str(e)}"
    
    def get_available_tools(self) -> Dict[str, str]:
        """获取可用工具列表"""
        return {name: tool.description for name, tool in self.tools.items()}
