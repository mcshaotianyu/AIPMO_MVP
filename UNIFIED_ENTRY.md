# 统一消息入口说明

## 📋 概述

系统采用统一消息入口 `/message`，所有用户（用户A和用户B）都通过同一个服务端点进行交互，便于企业微信集成和统一管理。

## 🎯 核心特性

- ✅ **统一入口**：所有用户消息都通过 `mainagent:5001/message` 统一入口
- ✅ **自动路由**：根据 `user_id` 自动判断路由到 mainagent 或 subagent
- ✅ **自动获取历史**：对话历史由服务端自动管理，客户端无需传递
- ✅ **完全扁平化**：客户端接口完全统一，只传递 `user_id` 和 `message`/`query`

## 🔧 路由逻辑

### 路由判断依据

**唯一依据：根据 `user_id` 查询是否有 pending session**

1. **如果 `user_id` 有 pending sessions** → 路由到 subagent（用户B回复）
2. **如果 `user_id` 没有 pending sessions** → 路由到 mainagent（用户A查询）
3. **如果 `message_content` 为空** → 返回 pending sessions 列表（用于轮询）

### 特殊支持

- **`user_id="*"`**：查询所有待处理会话（用于测试，模拟所有用户）
  - 查询时返回所有 pending sessions
  - 回复时自动选择最新的会话

## 📝 API接口说明

### 统一消息入口 `/message`

**请求格式：**
```json
{
  "user_id": "...",      // 必需，发送消息的用户ID（用于路由判断）
  "query": "...",         // 可选，消息内容（与message等价）
  "message": "..."        // 可选，消息内容（与query等价）
}
```

**重要说明：**
- `conversation_history` **不应由客户端传递**，服务端会根据路由自动获取：
  - 路由到 mainagent → 从 `conversation_manager` 自动获取
  - 路由到 subagent → 从 `session` 自动获取
- 路由判断**仅基于 `user_id` 查询 pending sessions**，不依赖 message 内容

**返回格式：**

1. **查询 pending sessions（message 为空）**：
```json
{
  "status": "success",
  "sessions": [
    {
      "session_id": "...",
      "user_a": "...",
      "user_b_id": "...",
      "user_b_name": "...",
      "question": "...",
      "latest_question": "...",
      "conversation_turns": 1,
      "status": "in_progress"
    }
  ]
}
```

2. **用户A查询（路由到 mainagent）**：
```json
{
  "status": "completed",
  "answer": "...",
  "function_called": ["search_doc", "contact_employee"],
  "conversation_history": [...]
}
```

3. **用户B回复（路由到 subagent）**：
```json
{
  "status": "success",
  "session_status": "in_progress" | "completed",
  "next_question": "...",  // 继续进行时返回
  "result": "..."          // 完成时返回
}
```

## 💻 客户端使用

### user_a_terminal.py

```python
# 发送查询
response = requests.post(
    f"{MAINAGENT_URL}/message",
    json={
        "user_id": self.user_id,
        "query": query  # 也支持message字段
    }
)
```

### user_b_terminal.py

```python
# 查询 pending sessions（发送空消息）
response = requests.post(
    f"{MAINAGENT_URL}/message",
    json={
        "user_id": self.user_id,  # 支持"*"查询所有
        "message": ""  # 空消息触发返回pending sessions
    }
)

# 发送回复
response = requests.post(
    f"{MAINAGENT_URL}/message",
    json={
        "user_id": self.user_id,
        "message": message
    }
)
```

## 📊 架构流程

### 用户A查询流程
```
用户A终端
  ↓ (user_id + query)
mainagent:5001/message
  ↓ (查询pending sessions = [])
mainagent内部处理
  ↓ (调用process_user_query)
返回结果
```

### 用户B回复流程
```
用户B终端
  ↓ (user_id + message)
mainagent:5001/message
  ↓ (查询pending sessions = [session1, session2, ...])
自动选择会话
  ↓ (转发到subagent)
subagent:5000/reply
  ↓ (处理回复)
返回结果
```

### 用户B查询待处理会话
```
用户B终端
  ↓ (user_id + ""空消息)
mainagent:5001/message
  ↓ (查询pending sessions)
返回sessions列表
```

## 🚀 企业微信集成建议

1. **统一使用 `/message` 接口**
   - 所有用户消息都发送到 `http://your-mainagent-url/message`
   - 系统会自动识别消息类型并路由

2. **消息格式**
   ```json
   {
     "user_id": "企业微信用户ID",
     "message": "用户消息内容"
   }
   ```

3. **会话管理**
   - 用户B的回复会自动路由到对应的会话
   - 无需手动传递 `session_id`，系统会自动选择

## ⚠️ 注意事项

1. **必须提供 `user_id`**：路由判断的唯一依据
2. **不要传递 `conversation_history`**：由服务端自动管理
3. **`user_id="*"`**：仅用于测试，模拟所有用户
4. **环境变量**：`SUBAGENT_URL` 可配置 subagent 地址（默认：http://localhost:5000）

## 🔌 其他接口

### mainagent 接口

- `/health`：健康检查
- `/session_callback`：子agent回调接口（内部使用）
- `/get_notifications`：查询通知（用于测试）

### subagent 接口（内部使用）

- `/health`：健康检查
- `/start_session`：启动新会话（被 mainagent 调用）
- `/reply`：用户B回复（被 mainagent 调用）
