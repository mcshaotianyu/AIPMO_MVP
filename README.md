# Multi-Agent 异步协作系统

企业微信多Agent聊天机器人 - 支持RAG检索和异步员工咨询

---

## 🚀 快速测试（3步）

### 第1步：启动服务
```bash
./start_test.sh
```

### 第2步：打开新终端 - 启动用户B（员工）
```bash
cd /Users/shaotianyu/Desktop/teleai/aipmo/tianyu/myserver
python user_b_terminal.py
```
按回车使用默认ID（1234567890）

### 第3步：再打开一个新终端 - 启动用户A（提问者）
```bash
cd /Users/shaotianyu/Desktop/teleai/aipmo/tianyu/myserver
python user_a_terminal.py
```

---

## 💬 测试对话流程

### 在用户A终端输入：
```
健身房周末开门吗？
```

主Agent会回复并询问是否联系员工，继续输入：
```
需要
```

### 观察用户B终端：
⏱️ **3-5秒后自动收到问询**，显示：
```
🔔════════════════════════════════════════════════════════════════════🔔
                   ✨ 收到新的问询请求 ✨
══════════════════════════════════════════════════════════════════════
📌 来自用户: user_a_张三
📌 原始问题: 健身房周末开门吗？
══════════════════════════════════════════════════════════════════════

💬 子Agent: [自动显示问题]

您的回复: [直接输入回复]
```

**直接输入回复**，无需任何菜单操作：
```
您的回复: 周末8:00-20:00开放

💬 子Agent: [继续提问]

您的回复: 对的
```

### 观察用户A终端：
⏱️ **对话完成后3-5秒自动收到推送**：
```
🔔════════════════════════════════════════════════════════════════════🔔
                   ✨ 收到来自主Agent的推送通知 ✨
══════════════════════════════════════════════════════════════════════
💡 最新答复:
健身房周末8:00-20:00开放
══════════════════════════════════════════════════════════════════════
```

---

## 🎯 核心特性

✅ **用户A提问** → 主Agent处理  
✅ **RAG检索** → 搜索文档/员工  
✅ **触发联系** → 启动子Agent  
✅ **用户B自动收到通知** → 3-5秒内，自动进入对话  
✅ **直接对话** → 无需菜单、无需输入会话ID  
✅ **自动完成** → 子Agent自动回调主Agent  
✅ **用户A自动收到推送** → 3-5秒内显示最终答案  
✅ **完全异步** → 互不阻塞  

---

## 🛠️ 工具命令

```bash
# 停止所有服务
./stop_services.sh

# 检查服务状态
./check_status.sh

# 查看日志
tail -f logs/mainagent.log
tail -f logs/subagent.log
```

---

## 🐛 故障排查

### 问题1：端口被占用
```bash
# 杀死占用端口的进程
kill -9 $(lsof -ti:5000)  # 子Agent
kill -9 $(lsof -ti:5001)  # 主Agent
```

### 问题2：用户B没收到通知
**原因：** Python缓存问题

**解决：**
```bash
# 清理缓存后重启
rm -rf __pycache__ mainagent/__pycache__ subagent/__pycache__
./start_test.sh
```

### 问题3：服务启动失败
```bash
# 查看具体错误
cat logs/mainagent.log
cat logs/subagent.log

# 检查OpenAI API Key
echo $OPENAI_API_KEY
```

---

## 📁 核心文件

```
myserver/
├── mainagent/              # 主Agent服务
│   ├── server.py          # Flask服务
│   ├── core.py            # 核心逻辑
│   ├── tools.py           # 工具定义
│   └── prompts.py         # 提示词
├── subagent/              # 子Agent服务
│   ├── server.py          # Flask服务
│   ├── core.py            # 对话逻辑
│   └── prompts.py         # 提示词
├── session_manager.py     # 会话管理
├── user_a_terminal.py     # 用户A终端
├── user_b_terminal.py     # 用户B终端
├── start_test.sh          # ⭐ 测试启动脚本
├── stop_services.sh       # 停止服务
└── check_status.sh        # 状态检查
```

---

## 🏗️ 系统架构

```
用户A终端
    ↓
主Agent (端口5001)
    ├→ search_doc       # RAG文档检索
    ├→ search_employee  # 查找员工
    └→ contact_employee # 联系员工
         ↓
    子Agent (端口5000)
         ↓
    用户B终端 ← 🔔 自动通知
         ↓
    多轮对话
         ↓
    完成 → 回调主Agent
         ↓
    用户A终端 ← 🔔 自动推送
```

---

## ⚙️ 环境要求

```bash
# Python 3.8+
pip install -r mainagent/requirements.txt

# 设置OpenAI API Key
export OPENAI_API_KEY="your-api-key"
```

---

**立即开始测试 → 运行 `./start_test.sh`** 🚀
