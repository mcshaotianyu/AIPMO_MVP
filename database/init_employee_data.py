#!/usr/bin/env python3
"""
初始化员工台账数据脚本
生成随机员工数据并插入到数据库
"""

import random
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import db

# 常见姓氏
SURNAMES = ['张', '王', '李', '赵', '刘', '陈', '杨', '黄', '周', '吴', '徐', '孙', '马', '朱', '胡', '郭', '何', '高', '林', '罗', '郑', '梁', '谢', '宋', '唐', '许', '韩', '冯', '邓', '曹', '彭', '曾', '肖', '田', '董', '袁', '潘', '于', '蒋', '蔡', '余', '杜', '叶', '程', '魏', '苏', '吕', '丁', '任', '沈', '姚', '卢', '姜', '崔', '钟', '谭', '陆', '汪', '范', '金', '石', '廖', '贾', '夏', '韦', '付', '方', '白', '邹', '孟', '熊', '秦', '邱', '江', '尹', '薛', '闫', '段', '雷', '侯', '龙', '史', '陶', '黎', '贺', '顾', '毛', '郝', '龚', '邵', '万', '钱', '严', '覃', '武', '戴', '莫', '孔', '向', '汤']

# 常见名字
GIVEN_NAMES = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '娟', '涛', '明', '超', '秀兰', '霞', '平', '刚', '桂英', '建华', '文', '华', '建国', '红', '建国', '玉', '秀', '英', '梅', '兰', '菊', '竹', '松', '柏', '柳', '杨', '桃', '李', '杏', '梨', '花', '草', '树', '木', '山', '水', '火', '土', '金', '银', '铜', '铁', '钢', '石', '玉', '珠', '宝', '珍', '珠', '贝', '壳', '海', '洋', '江', '河', '湖', '海', '天', '地', '日', '月', '星', '辰', '光', '明', '亮', '暗', '黑', '白', '红', '黄', '蓝', '绿', '紫', '青', '橙', '粉', '灰', '棕', '褐', '金', '银', '铜', '铁', '钢', '石', '玉', '珠', '宝', '珍', '珠', '贝', '壳']

# 部门列表
DEPARTMENTS = ['技术部', '市场部', '人事部', '财务部', '运营部', '产品部', '设计部', '销售部', '客服部', '综合中心', '平台业务部', '研发部', '测试部', '运维部', '行政部']

def generate_phone():
    """生成随机手机号"""
    return f"1{random.randint(3, 9)}{random.randint(100000000, 999999999)}"

def generate_name():
    """生成随机姓名"""
    surname = random.choice(SURNAMES)
    given_name = random.choice(GIVEN_NAMES)
    # 30%概率生成两个字的名字
    if random.random() < 0.3:
        given_name += random.choice(GIVEN_NAMES)
    return surname + given_name

def init_employee_data(num_employees=50):
    """初始化员工数据"""
    print(f"正在生成 {num_employees} 个随机员工数据...")
    
    employees = []
    used_names = set()
    
    # 先添加一些固定的员工（从之前的测试中）
    fixed_employees = [
        ('徐雨婷', '13800138016', '财务部'),
        ('孙铭', '13800138017', '人事部'),
        ('邵天宇', '18210126508', '平台业务部'),
        ('古乐', '13800138019', '综合中心'),
        ('张伟', '13800138000', '综合中心'),
    ]
    
    for name, phone, dept in fixed_employees:
        employees.append((name, phone, dept))
        used_names.add(name)
    
    # 生成随机员工
    while len(employees) < num_employees:
        name = generate_name()
        if name not in used_names:
            phone = generate_phone()
            department = random.choice(DEPARTMENTS)
            employees.append((name, phone, department))
            used_names.add(name)
    
    # 插入数据库
    print("正在插入数据到数据库...")
    success_count = 0
    for name, phone, department in employees:
        try:
            db.add_employee(name, phone, department)
            success_count += 1
        except Exception as e:
            print(f"插入 {name} 失败: {str(e)}")
    
    print(f"成功插入 {success_count} 个员工数据")
    
    # 验证数据
    all_employees = db.get_all_employees()
    print(f"数据库中现有 {len(all_employees)} 个员工")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='初始化员工台账数据')
    parser.add_argument('-n', '--num', type=int, default=50, help='要生成的员工数量（默认50）')
    args = parser.parse_args()
    
    try:
        init_employee_data(args.num)
        print("✅ 员工数据初始化完成！")
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        sys.exit(1)

