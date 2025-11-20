#!/bin/bash

# 数据库初始化脚本
# 功能：创建所有表、初始化员工数据、更新Excel文件

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "════════════════════════════════════════════════════════════"
echo "           数据库初始化脚本"
echo "════════════════════════════════════════════════════════════"
echo ""

# 检查数据库是否运行
if ! docker ps | grep -q myserver_postgres; then
    echo "❌ 数据库未运行，请先启动数据库："
    echo "   ./start_database.sh"
    exit 1
fi

echo "✅ 数据库正在运行"
echo ""

# 步骤1：创建所有表
echo "📋 步骤1: 创建数据库表..."
docker exec -i myserver_postgres psql -U postgres -d myserver_db < database/init.sql
if [ $? -eq 0 ]; then
    echo "✅ 数据库表创建成功"
else
    echo "❌ 数据库表创建失败"
    exit 1
fi
echo ""

# 步骤2：检查员工数据是否存在
echo "📋 步骤2: 检查员工数据..."
EMPLOYEE_COUNT=$(docker exec -i myserver_postgres psql -U postgres -d myserver_db -t -c "SELECT COUNT(*) FROM employee_directory;" | tr -d ' ')

if [ "$EMPLOYEE_COUNT" = "0" ] || [ -z "$EMPLOYEE_COUNT" ]; then
    echo "   员工数据为空，正在初始化..."
    python database/init_employee_data.py -n 50
    if [ $? -eq 0 ]; then
        echo "✅ 员工数据初始化成功"
    else
        echo "❌ 员工数据初始化失败"
        exit 1
    fi
else
    echo "✅ 员工数据已存在（共 $EMPLOYEE_COUNT 条）"
fi
echo ""

# 步骤3：更新Excel文件
echo "📋 步骤3: 更新Excel文件..."
python database/update_user_info_xlsx.py
if [ $? -eq 0 ]; then
    echo "✅ Excel文件更新成功"
else
    echo "❌ Excel文件更新失败"
    exit 1
fi
echo ""

echo "════════════════════════════════════════════════════════════"
echo "           数据库初始化完成！"
echo "════════════════════════════════════════════════════════════"
echo ""

