# 员工筛选与通知系统

企业微信助手 - 根据文档筛选员工并通知

---

## 🚀 快速测试（2步）

### 第1步：启动服务
```bash
./start_test.sh
```

### 第2步：打开新终端 - 启动用户A（提问者）
```bash
cd /Users/shaotianyu/Desktop/teleai/aipmo/tianyu/myserver
python user_a_terminal.py
```

---

## 💬 测试对话流程

### 在用户A终端输入：
```
筛选出分数在80分以上的员工
```

主Agent会筛选员工并询问是否通知，继续输入：
```
需要
```

主Agent会直接通知筛选出的员工。

---

## 🎯 核心特性

✅ **用户A提问** → 主Agent处理  
✅ **员工检索** → 搜索员工信息  
✅ **员工筛选** → 根据文档筛选符合条件的员工  
✅ **员工通知** → 直接通知筛选出的员工  
✅ **统一入口** → 所有消息通过 `/message` 统一接口  

---

## 🛠️ 工具命令

```bash
# 停止所有服务
./stop_services.sh

# 检查服务状态
./check_status.sh

# 查看日志
tail -f logs/mainagent.log
tail -f logs/codeagent.log
```

---

## 🐛 故障排查

### 问题1：端口被占用
```bash
# 杀死占用端口的进程
kill -9 $(lsof -ti:5001)  # 主Agent
kill -9 $(lsof -ti:5004)  # 代码Agent
```

### 问题2：服务启动失败
```bash
# 清理缓存后重启
rm -rf __pycache__ mainagent/__pycache__ codeagent/__pycache__
./start_test.sh

# 查看具体错误
cat logs/mainagent.log
cat logs/codeagent.log

# 检查API Key
echo $DEEPSEEK_API_KEY
```

---

## 📁 核心文件

```
myserver/
├── mainagent/              # 主Agent服务
│   ├── server.py          # Flask服务（统一入口/message）
│   ├── core.py            # 核心逻辑（process_user_query）
│   ├── tools.py           # 工具定义
│   └── prompts.py         # 提示词
├── codeagent/             # 代码Agent服务（员工筛选）
│   ├── server.py          # Flask服务
│   └── core.py            # 代码执行逻辑
├── database/              # 数据库
│   ├── db.py              # 数据库操作
│   └── init.sql           # 初始化脚本
├── user_a_terminal.py     # 用户A终端
├── start_test.sh          # ⭐ 测试启动脚本
├── stop_services.sh       # 停止服务
└── check_status.sh        # 状态检查
```

---

## 🏗️ 系统架构

```
用户A终端
    ↓ (user_id + query)
主Agent (端口5001)
    ├→ /message (统一入口)
    ├→ search_employee  # 检索员工
    ├→ select_employee  # 筛选员工（调用codeagent）
    └→ contact_employee # 通知员工
         ↓
    代码Agent (端口5004)
         └→ /query (筛选员工)
```

---

## ⚙️ 环境要求

```bash
# Python 3.8+
pip install -r requirements.txt

# 设置API Key
export DEEPSEEK_API_KEY="your-api-key"
```

---

## 📖 可用工具

1. **search_employee** - 根据查询内容从员工台账中检索相关员工
2. **select_employee** - 根据用户输入和相关文件筛选符合条件的员工
3. **contact_employee** - 通知相关员工

---

**立即开始测试 → 运行 `./start_test.sh`** 🚀
