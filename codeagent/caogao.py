#!/usr/bin/env python3
"""测试脚本：测试 read_xlsx 和 execute_code 两个函数"""

import os
import json
import pandas as pd
import subprocess
import tempfile


def execute(code: str, file_path: str) -> str:
    """
    执行Python代码
    
    Args:
        code: 要执行的Python代码
        file_path: XLSX文件路径（代码中可能需要使用）
        
    Returns:
        str: 执行结果
    """
    try:
        if not file_path:
            return "错误：file_path 参数不能为空"
        
        if not os.path.exists(file_path):
            return f"错误：文件不存在: {file_path}"
        
        # 创建临时文件保存代码
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
        
        try:
            # 执行代码，工作目录设置为文件所在目录
            work_dir = os.path.dirname(os.path.abspath(file_path)) if file_path else None
            result = subprocess.run(
                ['python', temp_code_file],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=work_dir
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    return f"执行成功：\n{output}"
                else:
                    return "执行成功，但无输出"
            else:
                error = result.stderr.strip()
                return f"执行失败：\n{error}"
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_code_file):
                os.unlink(temp_code_file)
                
    except subprocess.TimeoutExpired:
        return "执行超时：代码执行时间超过30秒"
    except Exception as e:
        return f"执行代码失败：{str(e)}"


def execute2(file_path: str) -> str:
    """
    读取XLSX文件的前20行
    
    Args:
        file_path: XLSX文件路径
        
    Returns:
        str: JSON格式的前20行数据和列信息
    """
    try:
        if not os.path.exists(file_path):
            return f"错误：文件不存在: {file_path}"
        
        if not file_path.endswith(('.xlsx', '.xls')):
            return f"错误：文件格式不支持，需要.xlsx或.xls格式"
        
        # 读取前20行
        df = pd.read_excel(file_path, nrows=20)
        
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
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"读取XLSX文件失败：{str(e)}"


def test_functions():
    """测试两个函数的串联使用"""
    print("=" * 70)
    print("测试 read_xlsx 和 execute_code 函数")
    print("=" * 70)
    
    # 测试文件路径（可以根据实际情况修改）
    test_file = "/Users/shaotianyu/Desktop/teleai/aipmo/tianyu/myserver/codeagent/data/user_info.xlsx"
    
    # 如果文件不存在，尝试其他路径
    if not os.path.exists(test_file):
        # 尝试查找项目中的xlsx文件
        possible_paths = [
            "./data/user_info.xlsx",
            "../data/user_info.xlsx",
            "user_info.xlsx",
            "data.xlsx"
        ]
        test_file = None
        for path in possible_paths:
            if os.path.exists(path):
                test_file = path
                break
        
        if not test_file:
            print(f"❌ 未找到测试文件，请确保存在XLSX文件")
            print(f"   尝试的路径: {possible_paths}")
            return
    
    print(f"\n📁 测试文件: {test_file}\n")
    
    # 第一步：读取文件前20行
    print("=" * 70)
    print("步骤1: 读取XLSX文件前20行")
    print("=" * 70)
    result_json = execute2(test_file)
    
    if result_json.startswith("错误"):
        print(f"❌ {result_json}")
        return
    
    print("✅ 文件读取成功")
    print(f"\n文件信息（前200字符）:\n{result_json[:200]}...\n")
    
    # 解析结果
    try:
        file_info = json.loads(result_json)
        columns = file_info.get("columns", [])
        file_path = file_info.get("file_path", test_file)
        
        print(f"📊 列信息:")
        for col in columns[:5]:  # 只显示前5列
            print(f"  - {col['column_name']}: {col['data_type']}")
        if len(columns) > 5:
            print(f"  ... 还有 {len(columns) - 5} 列")
        
        # 识别姓名列
        name_column = None
        for col in columns:
            col_name = col['column_name'].lower()
            if '姓名' in col_name or '名字' in col_name or col_name == 'name':
                name_column = col['column_name']
                break
        
        if name_column:
            print(f"\n✅ 识别到姓名列: {name_column}")
        else:
            print(f"\n⚠️  未识别到姓名列，使用第一列作为示例")
            if columns:
                name_column = columns[0]['column_name']
        
    except json.JSONDecodeError as e:
        print(f"❌ 解析JSON失败: {e}")
        return
    
    # 第二步：生成测试代码
    print("\n" + "=" * 70)
    print("步骤2: 生成测试代码")
    print("=" * 70)
    
    # 生成一个简单的测试代码：读取文件并显示前5行
    test_code = f"""import pandas as pd
import json

# 读取完整数据
df = pd.read_excel(FILE_PATH)

# 显示基本信息
print(f"总行数: {{len(df)}}")
print(f"列名: {{list(df.columns)}}")

# 选择姓名列和前几列（如果存在）
if '{name_column}' in df.columns:
    selected_cols = ['{name_column}']
    # 添加前3个列（如果姓名列不在前3个）
    for col in df.columns[:3]:
        if col not in selected_cols:
            selected_cols.append(col)
            if len(selected_cols) >= 4:
                break
    
    result = df[selected_cols].head(10)  # 取前10行
else:
    # 如果没有姓名列，取前5列的前10行
    result = df[df.columns[:5]].head(10)

# 输出JSON格式结果
print(json.dumps(result.to_dict('records'), ensure_ascii=False, indent=2))
"""
    
    print("生成的测试代码:")
    print("-" * 70)
    print(test_code)
    print("-" * 70)
    
    # 第三步：执行代码
    print("\n" + "=" * 70)
    print("步骤3: 执行生成的代码")
    print("=" * 70)
    
    execution_result = execute(test_code, file_path)
    
    print("\n执行结果:")
    print("-" * 70)
    print(execution_result)
    print("-" * 70)
    
    # 判断执行是否成功
    if execution_result.startswith("执行成功"):
        print("\n✅ 测试完成！两个函数串联工作正常。")
    else:
        print("\n❌ 代码执行失败，请检查错误信息。")
    
    print("=" * 70)


if __name__ == "__main__":
    test_functions()