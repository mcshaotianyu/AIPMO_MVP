# Multi-Agent 异步协作系统

企业微信多Agent聊天机器人 - 支持RAG检索和异步员工咨询

---

## 🚀 快速开始

### 1. 配置企业微信环境变量（必需）

```bash
export WECHAT_CORP_ID="your_corp_id"           # 企业ID（必需）
export WECHAT_CORP_SECRET="your_corp_secret"   # 应用Secret（必需）
export WECHAT_AGENT_ID="your_agent_id"         # 应用AgentID（必需）
export WECHAT_TOKEN="your_token"               # 回调验证token（可选）
export WECHAT_ENCODING_AES_KEY="your_key"      # 回调加密key（可选）
export DEEPSEEK_API_KEY="your-api-key"         # DeepSeek API Key（必需）
```

### 2. 启动数据库

```bash
./start_database.sh
```

### 3. 启动服务

```bash
./start_test.sh
```

### 4. 配置企业微信回调URL

在企业微信管理后台配置回调URL: `https://your-domain.com/wechat/callback`

---

## 🎯 核心特性

✅ **企业微信集成** → 通过 `/wechat/callback` 统一接收消息  
✅ **自动路由** → 根据 `user_id` 自动判断路由到 MainAgent 或 SubAgent  
✅ **RAG检索** → 搜索文档/员工  
✅ **异步咨询** → 启动子Agent联系员工  
✅ **自动推送** → 所有消息自动推送给正确的用户  
✅ **完全异步** → 互不阻塞  

---

## 🏗️ 系统架构

```
企业微信用户A
    ↓ (POST /wechat/callback)
主Agent (端口5001)
    ├→ process_user_query
    ├→ search_doc       # RAG文档检索
    ├→ search_employee  # 查找员工
    └→ contact_employee # 联系员工
         ↓
    子Agent (端口5000)
         ├→ /start_session → 推送给User B
         └→ /reply
         ↓
    企业微信用户B ← 🔔 自动推送
         ↓ (POST /wechat/callback)
    主Agent自动路由到SubAgent
         ↓
    多轮对话
         ↓
    完成 → 回调主Agent
         ↓
    企业微信用户A ← 🔔 自动推送
```

---

## 🌐 接口说明

### 企业微信回调接口

**URL**: `POST /wechat/callback`

**功能**: 接收企业微信推送的消息（统一入口）

**说明**:
- 企业微信会通过此接口推送用户消息
- 系统会自动处理消息并推送给正确的用户
- 支持GET请求用于URL验证（企业微信要求）

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

## ⚙️ 环境要求

```bash
# Python 3.8+
pip install -r requirements.txt

# 必需环境变量
export WECHAT_CORP_ID="your_corp_id"
export WECHAT_CORP_SECRET="your_corp_secret"
export WECHAT_AGENT_ID="your_agent_id"
export DEEPSEEK_API_KEY="your-api-key"
```

---

## 📁 核心文件

```
myserver/
├── mainagent/              # 主Agent服务
│   ├── server.py          # Flask服务（企业微信回调接口）
│   ├── core.py            # 核心逻辑（process_user_query）
│   ├── tools.py           # 工具定义
│   ├── wechat_adapter.py  # 企业微信适配层
│   └── prompts.py         # 提示词
├── subagent/              # 子Agent服务
│   ├── server.py          # Flask服务（/start_session, /reply）
│   ├── core.py            # 对话逻辑
│   └── prompts.py         # 提示词
├── codeagent/             # 代码Agent服务（员工筛选）
│   ├── server.py          # Flask服务
│   └── core.py            # 代码执行逻辑
├── database/              # 数据库
│   ├── db.py              # 数据库操作
│   └── init.sql           # 初始化脚本
├── session_manager.py     # 会话管理
├── start_test.sh          # 启动脚本
├── stop_services.sh       # 停止服务
└── check_status.sh        # 状态检查
```

---

## 📖 详细文档

- [企业微信集成说明](./WECHAT_INTEGRATION.md)

---

## ⚠️ 重要提示

1. **必须配置企业微信环境变量**: 未配置必需环境变量时，服务无法启动
2. **回调URL配置**: 在企业微信管理后台配置回调URL: `https://your-domain.com/wechat/callback`
3. **HTTPS要求**: 回调URL必须支持HTTPS协议
4. **签名验证**: 需要根据企业微信文档实现完整的签名验证逻辑

---

**立即开始 → 配置环境变量并运行 `./start_test.sh`** 🚀
