# 统一消息入口说明

## 📋 修改概述

为了支持企业微信集成，我们在mainagent中添加了统一消息入口 `/message`，使得用户A和用户B都可以通过同一个服务端点进行交互。

## 🎯 解决的问题

**之前的问题：**
- 用户A → mainagent (端口5001)
- 用户B → subagent (端口5000)
- 两个独立的服务端点，企业微信集成时无法统一路由

**现在的解决方案：**
- 用户A → mainagent `/message` 或 `/chat`（向后兼容）
- 用户B → mainagent `/message`（统一入口，内部转发到subagent）
- 所有用户消息都通过mainagent统一入口，便于企业微信集成

## 🔧 修改内容

### 1. mainagent/server.py
- ✅ 添加了 `/message` 统一消息入口接口
- ✅ 支持自动识别消息类型（用户A查询、用户B回复、查询会话状态等）
- ✅ 内部转发用户B的消息到subagent
- ✅ 保持向后兼容，所有原有接口不变

### 2. user_b_terminal.py
- ✅ 支持通过环境变量 `USE_UNIFIED_ENTRY=true` 启用统一入口模式
- ✅ 默认使用直接连接subagent模式（向后兼容）
- ✅ 统一入口模式下，所有请求都通过mainagent的 `/message` 接口

## 📝 使用方法

### 方式1：使用统一入口（推荐用于企业微信集成）

```bash
# 设置环境变量启用统一入口
export USE_UNIFIED_ENTRY=true

# 启动用户B终端（将使用mainagent的统一入口）
python user_b_terminal.py
```

### 方式2：使用原有方式（向后兼容，默认）

```bash
# 不设置环境变量，使用默认模式（直接连接subagent）
python user_b_terminal.py
```

## 🔌 API接口说明

### 统一消息入口 `/message`

**请求格式：**
```json
{
  "type": "user_query" | "user_b_reply" | "get_session_status" | "get_pending_sessions",
  // 用户A查询
  "query": "...",
  "conversation_history": [...],
  "user_id": "...",
  // 用户B回复
  "session_id": "...",
  "user_b_id": "...",
  "message": "..."
}
```

**自动识别（无需指定type）：**
- 如果包含 `session_id` 和 `user_b_id` → 识别为 `user_b_reply`
- 如果包含 `query` → 识别为 `user_query`
- 如果只包含 `session_id` → 识别为 `get_session_status`
- 如果只包含 `user_b_id` → 识别为 `get_pending_sessions`

**示例1：用户A查询**
```bash
curl -X POST http://localhost:5001/message \
  -H "Content-Type: application/json" \
  -d '{
    "type": "user_query",
    "query": "健身房周末开门吗？",
    "user_id": "user_a_张三"
  }'
```

**示例2：用户B回复**
```bash
curl -X POST http://localhost:5001/message \
  -H "Content-Type: application/json" \
  -d '{
    "type": "user_b_reply",
    "session_id": "xxx-xxx-xxx",
    "user_b_id": "1234567890",
    "message": "周末8:00-20:00开放"
  }'
```

**示例3：查询会话状态**
```bash
curl -X POST http://localhost:5001/message \
  -H "Content-Type: application/json" \
  -d '{
    "type": "get_session_status",
    "session_id": "xxx-xxx-xxx"
  }'
```

## ✅ 向后兼容性

- ✅ 所有原有接口保持不变（`/chat`, `/query`, `/tools`, `/functions` 等）
- ✅ subagent的所有接口保持不变（`/reply`, `/get_status`, `/get_pending_sessions` 等）
- ✅ user_b_terminal.py 默认使用原有模式（直接连接subagent）
- ✅ 测试流程完全不受影响，可以继续使用原有方式

## 🧪 测试验证

### 测试原有方式（向后兼容）
```bash
# 1. 启动服务
./start_test.sh

# 2. 启动用户B（使用默认模式，直接连接subagent）
python user_b_terminal.py

# 3. 启动用户A
python user_a_terminal.py
```

### 测试统一入口模式
```bash
# 1. 启动服务
./start_test.sh

# 2. 启动用户B（使用统一入口）
USE_UNIFIED_ENTRY=true python user_b_terminal.py

# 3. 启动用户A（可以继续使用原有方式，或也使用/message）
python user_a_terminal.py
```

## 🚀 企业微信集成建议

在企业微信集成时，建议：

1. **统一使用 `/message` 接口**
   - 所有用户消息（用户A和用户B）都发送到 `http://your-mainagent-url/message`
   - 系统会自动识别消息类型并路由

2. **消息格式**
   ```json
   {
     "type": "user_query",  // 或 "user_b_reply" 等
     "user_id": "企业微信用户ID",
     "query": "用户消息内容",
     // ... 其他参数
   }
   ```

3. **会话管理**
   - 用户B的回复需要包含 `session_id` 和 `user_b_id`
   - 可以从企业微信的上下文或消息中获取这些信息

## 📊 架构对比

### 修改前
```
用户A → mainagent:5001/chat
用户B → subagent:5000/reply
```

### 修改后（统一入口模式）
```
用户A → mainagent:5001/message  → 内部处理
用户B → mainagent:5001/message  → 转发到 subagent:5000/reply
```

### 修改后（向后兼容模式，默认）
```
用户A → mainagent:5001/chat
用户B → subagent:5000/reply
```

## ⚠️ 注意事项

1. 统一入口模式下，需要确保mainagent能够连接到subagent
2. 环境变量 `SUBAGENT_URL` 可以配置subagent的地址（默认：http://localhost:5000）
3. 企业微信集成时，建议使用统一入口模式，便于统一管理和路由

