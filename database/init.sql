-- PostgreSQL数据库初始化脚本
-- 用于存储Multi-Agent系统的会话和对话历史

-- 创建数据库（如果不存在，需要在外部创建）
-- CREATE DATABASE myserver_db;

-- 会话表：存储主agent和子agent之间的会话信息
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_a VARCHAR(255) NOT NULL,  -- 任务发起方（用户A的ID）
    user_b_id VARCHAR(255) NOT NULL,  -- 任务接收方（用户B的ID）
    user_b_name VARCHAR(255) NOT NULL,  -- 用户B的姓名
    question TEXT NOT NULL,  -- 原始问题
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending/in_progress/completed/failed
    result TEXT,  -- 最终结果
    callback_url TEXT,  -- 回调URL
    callback_triggered BOOLEAN DEFAULT FALSE,  -- 是否已触发回调
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 会话消息表：存储子agent与用户B的对话历史（子任务对话）
CREATE TABLE IF NOT EXISTS session_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- user/assistant
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_session_messages_session_id ON session_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_session_messages_created ON session_messages(session_id, created_at);

-- 用户对话历史表：存储用户A与mainagent的对话历史（初始对话）
CREATE TABLE IF NOT EXISTS user_conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- 用户ID（用于数据隔离）
    role VARCHAR(50) NOT NULL,  -- system/user/assistant/tool
    content TEXT,
    tool_call_id VARCHAR(255),  -- 如果是tool消息，记录tool_call_id
    tool_calls JSONB,  -- 如果是assistant消息且包含tool_calls，存储tool_calls
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_conversations_user_id ON user_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_conversations_created ON user_conversations(user_id, created_at);

-- 会话映射表：存储session_id到tool_call_id和user_id的映射
CREATE TABLE IF NOT EXISTS session_mappings (
    session_id VARCHAR(255) PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
    tool_call_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,  -- 用户A的ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_session_mappings_user_id ON session_mappings(user_id);
CREATE INDEX IF NOT EXISTS idx_session_mappings_tool_call_id ON session_mappings(tool_call_id);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为sessions表创建更新时间触发器
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

