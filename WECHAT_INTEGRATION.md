# 企业微信集成说明

## 📋 概述

系统已完全集成企业微信，通过企业微信回调接口接收和发送消息。**必须配置企业微信环境变量才能运行。**

## 🔧 配置方式

### 环境变量配置（必需）

在启动服务前必须设置以下环境变量：

```bash
export WECHAT_CORP_ID="your_corp_id"           # 企业ID（必需）
export WECHAT_CORP_SECRET="your_corp_secret"   # 应用Secret（必需）
export WECHAT_AGENT_ID="your_agent_id"         # 应用AgentID（必需）
export WECHAT_TOKEN="your_token"               # 回调验证token（可选）
export WECHAT_ENCODING_AES_KEY="your_key"      # 回调加密key（可选）
```

**注意**：如果未配置必需的环境变量，服务启动时会抛出异常。

## 🌐 接口说明

### 企业微信回调接口

**URL**: `POST /wechat/callback`

**功能**: 接收企业微信推送的消息（统一入口）

**请求格式**:
企业微信推送的消息格式（需要根据企业微信文档实现解密）

**返回格式**:
```json
{
    "status": "success"
}
```

**说明**:
- 企业微信会通过此接口推送用户消息
- 系统会自动处理消息并推送给正确的用户
- 支持GET请求用于URL验证（企业微信要求）

## 🔄 消息流转

### 用户A发送消息
```
企业微信用户A → POST /wechat/callback → MainAgent处理 → 推送给用户A
```

### 用户B回复消息
```
企业微信用户B → POST /wechat/callback → MainAgent路由到SubAgent → 处理回复 → 推送给用户B
```

### SubAgent完成回调
```
SubAgent完成任务 → POST /session_callback → 更新对话历史 → 直接推送给用户A
```

## 📝 关键特性

1. **统一入口**: `/wechat/callback` 是企业微信消息的唯一入口
2. **自动路由**: 根据 `user_id` 自动判断路由到 MainAgent 或 SubAgent
3. **自动推送**: 所有消息自动推送给正确的用户，无需轮询
4. **用户识别**: 通过 `user_id` 自动识别用户身份并路由消息

## 🔍 调试

### 查看日志

系统会输出详细的日志信息：

- `[INFO] 企业微信适配器已启用` - 企业微信模式已启用
- `[WECHAT] 收到企业微信消息` - 收到企业微信消息
- `[INFO] 消息路由到subagent，推送给user B` - 路由到SubAgent
- `[INFO] 消息路由到mainagent，推送给发送者` - 路由到MainAgent
- `[INFO] 企业微信消息推送成功` - 推送成功

### 常见问题

1. **服务启动失败**: 检查必需的环境变量是否配置（WECHAT_CORP_ID, WECHAT_CORP_SECRET, WECHAT_AGENT_ID）
2. **消息未推送**: 检查环境变量是否正确配置，查看日志确认access_token是否获取成功
3. **回调验证失败**: 检查 `WECHAT_TOKEN` 是否正确，确认签名验证逻辑已实现
4. **access_token获取失败**: 检查 `WECHAT_CORP_ID` 和 `WECHAT_CORP_SECRET` 是否正确

## 📚 相关文件

- `mainagent/wechat_adapter.py` - 企业微信适配层
- `mainagent/server.py` - 主服务，包含企业微信回调接口
- `requirements.txt` - 依赖包

## ⚠️ 注意事项

1. **必须配置环境变量**: 未配置必需环境变量时，服务无法启动
2. **回调URL配置**: 在企业微信管理后台配置回调URL: `https://your-domain.com/wechat/callback`
3. **HTTPS要求**: 回调URL必须支持HTTPS协议
4. **签名验证**: 需要根据企业微信文档实现完整的签名验证逻辑（当前为临时实现）
