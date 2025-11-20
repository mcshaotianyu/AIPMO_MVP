#!/usr/bin/env python3
"""
更新 user_info.xlsx 文件
从员工台账表读取员工数据，生成包含姓名、分数、手机号的Excel文件
"""

import sys
import os
import random
import pandas as pd

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import db

def update_user_info_xlsx():
    """更新user_info.xlsx文件"""
    print("正在从数据库读取员工数据...")
    
    # 从数据库获取所有员工
    employees = db.get_all_employees()
    
    if not employees:
        print("❌ 数据库中没有员工数据，请先运行初始化脚本：")
        print("   python database/init_employee_data.py")
        return False
    
    print(f"找到 {len(employees)} 个员工")
    
    # 准备数据
    data = []
    for emp in employees:
        name = emp.get('name', '')
        phone = emp.get('phone', '')
        department = emp.get('department', '')
        
        # 随机生成分数（40-100）
        score = random.randint(40, 100)
        
        # 随机决定是否有手机号（70%概率有手机号，30%概率没有）
        if random.random() < 0.3:
            phone = ''  # 30%概率没有手机号
        else:
            # 确保手机号是字符串格式，避免Excel显示为科学计数法
            phone = str(phone) if phone else ''
        
        data.append({
            '姓名': name,
            '分数': score,
            '手机号': phone,
            '部门': department
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 保存到Excel文件
    excel_path = '/Users/shaotianyu/Desktop/teleai/aipmo/tianyu/myserver/codeagent/data/user_info.xlsx'
    
    print(f"正在保存到 {excel_path}...")
    
    # 确保手机号列是字符串类型，空值保持为空字符串
    # 使用replace将NaN替换为空字符串，然后转换为字符串类型
    df['手机号'] = df['手机号'].fillna('').astype(str).replace('nan', '')
    
    # 使用ExcelWriter来设置列格式
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        # 获取工作表
        worksheet = writer.sheets['Sheet1']
        
        # 找到手机号列的索引
        phone_col_idx = None
        for idx, col_name in enumerate(df.columns, start=1):
            if col_name == '手机号':
                phone_col_idx = idx
                break
        
        if phone_col_idx:
            # 设置手机号列为文本格式，避免科学计数法
            for row in range(2, len(df) + 2):  # 从第2行开始（第1行是标题）
                cell = worksheet.cell(row=row, column=phone_col_idx)
                if cell.value and str(cell.value).strip():  # 如果有值且不为空
                    # 设置为文本格式
                    cell.number_format = '@'
                    # 确保值是字符串，如果是数字则转换为字符串
                    if isinstance(cell.value, (int, float)):
                        cell.value = str(int(cell.value))
                    else:
                        cell.value = str(cell.value)
    
    # 统计信息
    total = len(df)
    with_phone = len(df[df['手机号'] != ''])
    without_phone = total - with_phone
    
    print(f"✅ Excel文件已更新！")
    print(f"   总员工数: {total}")
    print(f"   有手机号: {with_phone} ({with_phone/total*100:.1f}%)")
    print(f"   无手机号: {without_phone} ({without_phone/total*100:.1f}%)")
    print(f"   分数范围: {df['分数'].min()} - {df['分数'].max()}")
    print(f"   平均分数: {df['分数'].mean():.1f}")
    
    return True

if __name__ == "__main__":
    try:
        success = update_user_info_xlsx()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ 更新失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

