#!/usr/bin/env python3
"""为XLSX文件添加score列"""

import pandas as pd
import numpy as np
import os

def add_score_column(file_path: str):
    """
    在XLSX文件的第五列位置添加score列，值为45-100的随机整数
    
    Args:
        file_path: XLSX文件路径
    """
    try:
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return False
        
        print(f"📁 读取文件: {file_path}")
        
        # 读取完整文件
        df = pd.read_excel(file_path)
        
        print(f"✅ 文件读取成功")
        print(f"   当前行数: {len(df)}")
        print(f"   当前列数: {len(df.columns)}")
        print(f"   当前列名: {list(df.columns)}")
        
        # 检查是否已经有score列
        if 'score' in df.columns or 'Score' in df.columns or 'SCORE' in df.columns:
            print(f"\n⚠️  文件中已存在score列，将覆盖")
            # 删除现有的score列
            score_cols = [col for col in df.columns if col.lower() == 'score']
            df = df.drop(columns=score_cols)
        
        # 生成45-100的随机整数
        np.random.seed()  # 使用当前时间作为随机种子
        scores = np.random.randint(45, 101, size=len(df))  # 101是上限（不包含）
        
        # 在第5列位置插入score列（如果当前列数少于5，就追加到末尾）
        if len(df.columns) >= 5:
            # 在第5列位置插入
            df.insert(4, 'score', scores)  # 索引从0开始，第5列是索引4
            print(f"\n✅ 在第5列位置插入score列")
        else:
            # 如果列数少于5，追加到末尾
            df['score'] = scores
            print(f"\n✅ 添加score列到末尾（当前列数少于5）")
        
        print(f"   新列数: {len(df.columns)}")
        print(f"   新列名: {list(df.columns)}")
        print(f"   Score范围: {scores.min()} - {scores.max()}")
        print(f"   Score平均值: {scores.mean():.2f}")
        
        # 保存文件
        print(f"\n💾 保存文件...")
        df.to_excel(file_path, index=False, engine='openpyxl')
        
        print(f"✅ 文件保存成功！")
        print(f"\n前5行数据预览:")
        print(df.head().to_string())
        
        return True
        
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    file_path = "/Users/shaotianyu/Desktop/teleai/aipmo/tianyu/myserver/codeagent/data/user_info.xlsx"
    
    print("=" * 70)
    print("为XLSX文件添加score列（45-100随机值）")
    print("=" * 70)
    
    success = add_score_column(file_path)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ 完成！")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ 失败！")
        print("=" * 70)

