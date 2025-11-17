# 📖 使用说明 - 企业微信集成版本

## 前置准备

### 1. 配置企业微信环境变量（必需）

```bash
export WECHAT_CORP_ID="your_corp_id"           # 企业ID（必需）
export WECHAT_CORP_SECRET="your_corp_secret"   # 应用Secret（必需）
export WECHAT_AGENT_ID="your_agent_id"         # 应用AgentID（必需）
export WECHAT_TOKEN="your_token"               # 回调验证token（可选）
export WECHAT_ENCODING_AES_KEY="your_key"      # 回调加密key（可选）
export DEEPSEEK_API_KEY="your-api-key"         # DeepSeek API Key（必需）
```

### 2. 进入项目目录

```bash
cd /Users/shaotianyu/Desktop/teleai/aipmo/tianyu/myserver
```

### 3. 清理Python缓存（可选）

```bash
rm -rf __pycache__ mainagent/__pycache__ subagent/__pycache__ codeagent/__pycache__
```

---

## 启动步骤

### 1. 启动数据库

```bash
./start_database.sh
```

### 2. 启动服务

```bash
./start_test.sh
```

看到以下提示说明服务启动成功：
```
✅ 主Agent运行中 (PID: xxxxx)
✅ 子Agent运行中 (PID: xxxxx)
✅ 代码Agent运行中 (PID: xxxxx)
```

### 3. 配置企业微信回调URL

在企业微信管理后台：
1. 进入应用管理 → 选择应用
2. 配置回调URL: `https://your-domain.com/wechat/callback`
3. 设置Token和EncodingAESKey（如果使用加密模式）

---

## 💬 使用流程

### 用户A发送消息

在企业微信中，用户A发送消息：
```
健身房周末开门吗？
```

系统会自动：
1. 接收消息（通过 `/wechat/callback`）
2. 路由到MainAgent处理
3. 可能调用工具（search_doc, contact_employee等）
4. 推送给用户A

### 如果触发联系员工

当MainAgent决定联系员工时：
1. 创建session并调用SubAgent
2. SubAgent生成first_question
3. **自动推送给用户B（被联系的员工）**

### 用户B回复消息

在企业微信中，用户B收到推送后回复：
```
周末8:00-20:00开放
```

系统会自动：
1. 接收消息（通过 `/wechat/callback`）
2. 路由到SubAgent（因为有pending session）
3. 处理回复，生成next_question或result
4. **推送给用户B**

### 会话完成

当SubAgent完成任务后：
1. 异步回调MainAgent（`/session_callback`）
2. 更新对话历史
3. **自动推送给用户A（最终结果）**

---

## 🛑 停止服务

```bash
./stop_services.sh
```

---

## 🔍 调试

### 查看日志

```bash
# 主Agent日志
tail -f logs/mainagent.log

# 子Agent日志
tail -f logs/subagent.log

# 代码Agent日志
tail -f logs/codeagent.log
```

### 检查服务状态

```bash
./check_status.sh
```

### 常见问题

**Q: 服务启动失败？**
A: 检查必需的环境变量是否配置：
```bash
echo $WECHAT_CORP_ID
echo $WECHAT_CORP_SECRET
echo $WECHAT_AGENT_ID
```

**Q: 消息未推送？**
A: 检查：
1. 环境变量是否正确配置
2. 查看日志确认access_token是否获取成功
3. 检查企业微信应用配置是否正确

**Q: 回调验证失败？**
A: 检查 `WECHAT_TOKEN` 是否正确，确认签名验证逻辑已实现

---

## 📚 相关文档

- [企业微信集成说明](./WECHAT_INTEGRATION.md)
- [README](./README.md)

---

**立即开始 → 配置环境变量并运行 `./start_test.sh`** 🚀
