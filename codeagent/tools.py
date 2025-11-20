"""代码Agent工具模块"""

import os
import sys
import json
import pandas as pd
import subprocess
import tempfile
from typing import Dict, Any, List

# 添加utils目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import codeagent_logger as logger


class ReadXlsxTool:
    """读取XLSX文件前20行工具"""
    
    def __init__(self):
        self.name = "read_xlsx"
        self.description = "读取XLSX文件的前20行数据，用于分析列结构和内容"
    
    def execute(self, file_path: str) -> str:
        """
        读取XLSX文件的前20行
        
        Args:
            file_path: XLSX文件路径
            
        Returns:
            str: JSON格式的前20行数据和列信息
        """
        try:
            logger.info(f"执行read_xlsx工具，文件路径: {file_path}")
            
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return f"错误：文件不存在: {file_path}"
            
            if not file_path.endswith(('.xlsx', '.xls')):
                logger.error(f"文件格式不支持: {file_path}")
                return f"错误：文件格式不支持，需要.xlsx或.xls格式"
            
            # 读取前20行
            logger.debug("开始读取Excel文件前20行")
            df = pd.read_excel(file_path, nrows=20)
            logger.info(f"成功读取 {len(df)} 行数据，列数: {len(df.columns)}")
            
            # 获取列信息
            columns_info = []
            for col in df.columns:
                # 分析列的数据类型和示例值
                sample_values = df[col].dropna().head(5).tolist()
                dtype = str(df[col].dtype)
                
                columns_info.append({
                    "column_name": str(col),
                    "data_type": dtype,
                    "sample_values": [str(v) for v in sample_values],
                    "non_null_count": int(df[col].notna().sum())
                })
            
            # 将前20行转换为字典列表（只包含非空值）
            data_rows = []
            for idx, row in df.iterrows():
                row_dict = {}
                for col in df.columns:
                    value = row[col]
                    if pd.notna(value):
                        row_dict[str(col)] = str(value)
                if row_dict:  # 只添加非空行
                    data_rows.append(row_dict)
            
            result = {
                "file_path": file_path,
                "total_rows_read": len(data_rows),
                "columns": columns_info,
                "data": data_rows
            }
            
            logger.info(f"read_xlsx工具执行成功，读取 {len(data_rows)} 行，{len(columns_info)} 列")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"read_xlsx工具执行异常: {str(e)}", exc_info=True)
            return f"读取XLSX文件失败：{str(e)}"


class ExecuteCodeTool:
    """执行Python代码工具"""
    
    def __init__(self):
        self.name = "execute_code"
        self.description = "执行Python代码并返回结果"
    
    def execute(self, code: str, file_path: str) -> str:
        """
        执行Python代码
        
        Args:
            code: 要执行的Python代码
            file_path: XLSX文件路径（代码中可能需要使用）
            
        Returns:
            str: 执行结果
        """
        try:
            logger.info(f"执行execute_code工具，代码长度: {len(code)} 字符，文件路径: {file_path}")
            
            if not file_path:
                logger.error("file_path参数为空")
                return "错误：file_path 参数不能为空"
            
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return f"错误：文件不存在: {file_path}"
            
            # 创建临时文件保存代码
            logger.debug("创建临时Python文件")
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                # 在代码开头添加文件路径变量
                # 转义文件路径中的反斜杠
                escaped_path = file_path.replace('\\', '\\\\')
                modified_code = f"""import os
import sys

# 设置文件路径
FILE_PATH = r'{escaped_path}'

{code}
"""
                f.write(modified_code)
                temp_code_file = f.name
                logger.debug(f"临时文件已创建: {temp_code_file}")
            
            try:
                # 执行代码，工作目录设置为文件所在目录
                work_dir = os.path.dirname(os.path.abspath(file_path)) if file_path else None
                logger.info(f"开始执行Python代码，工作目录: {work_dir}")
                result = subprocess.run(
                    ['python', temp_code_file],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=work_dir
                )
                
                logger.info(f"代码执行完成，返回码: {result.returncode}")
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    logger.info(f"代码执行成功，输出长度: {len(output)} 字符")
                    logger.debug(f"代码输出预览: {output[:300]}{'...' if len(output) > 300 else ''}")
                    if output:
                        return f"执行成功：\n{output}"
                    else:
                        logger.warning("代码执行成功但无输出")
                        return "执行成功，但无输出"
                else:
                    error = result.stderr.strip()
                    logger.error(f"代码执行失败，返回码: {result.returncode}")
                    logger.error(f"错误信息: {error}")
                    return f"执行失败：\n{error}"
                    
            finally:
                # 清理临时文件
                if os.path.exists(temp_code_file):
                    os.unlink(temp_code_file)
                    logger.debug(f"临时文件已删除: {temp_code_file}")
                    
        except subprocess.TimeoutExpired:
            logger.error("代码执行超时（30秒）")
            return "执行超时：代码执行时间超过30秒"
        except Exception as e:
            logger.error(f"execute_code工具执行异常: {str(e)}", exc_info=True)
            return f"执行代码失败：{str(e)}"


def get_tools_definitions() -> List[Dict]:
    """获取工具定义（新格式）"""
    return [
        {
            "type": "function",
            "function": {
                "name": "read_xlsx",
                "description": "读取XLSX文件的前20行数据，用于分析列结构和内容。这是第一步，必须先调用此工具了解文件结构。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "XLSX文件的完整路径"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_code",
                "description": "执行Python代码并返回结果。代码应该能够处理XLSX文件并输出JSON格式的结果。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要执行的Python代码"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "XLSX文件的完整路径，代码中会通过FILE_PATH变量访问"
                        }
                    },
                    "required": ["code", "file_path"]
                }
            }
        }
    ]


class ToolManager:
    """工具管理器"""
    
    def __init__(self):
        self.tools = {
            "read_xlsx": ReadXlsxTool(),
            "execute_code": ExecuteCodeTool()
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
            if tool_name == "read_xlsx":
                file_path = tool_input.get("file_path", "./data/user_info.xlsx")
                if not file_path:
                    return f"错误：read_xlsx 需要 file_path 参数"
                return tool.execute(file_path)
            
            elif tool_name == "execute_code":
                code = tool_input.get("code", "")
                file_path = tool_input.get("file_path", "")
                if not code or not file_path:
                    return f"错误：execute_code 需要 code 和 file_path 参数"
                return tool.execute(code, file_path)
            
            else:
                return f"错误：工具 {tool_name} 执行逻辑未实现"
                
        except Exception as e:
            return f"工具执行异常：{str(e)}"
    
    def get_available_tools(self) -> Dict[str, str]:
        """获取可用工具列表"""
        return {name: tool.description for name, tool in self.tools.items()}

