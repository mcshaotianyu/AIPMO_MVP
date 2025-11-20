-- PostgreSQL数据库初始化脚本
-- 用于存储员工筛选与通知系统的数据

-- 创建数据库（如果不存在，需要在外部创建）
-- CREATE DATABASE myserver_db;

-- MainAgent对话历史表：专门存储mainagent和用户的对话信息
CREATE TABLE IF NOT EXISTS mainagent_conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- 用户ID（用于数据隔离）
    role VARCHAR(50) NOT NULL,  -- system/user/assistant/tool
    content TEXT,
    tool_call_id VARCHAR(255),  -- 如果是tool消息，记录tool_call_id
    tool_calls JSONB,  -- 如果是assistant消息且包含tool_calls，存储tool_calls
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mainagent_conversations_user_id ON mainagent_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_mainagent_conversations_created ON mainagent_conversations(user_id, created_at);

-- 员工台账表：存储员工基本信息
CREATE TABLE IF NOT EXISTS employee_directory (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,  -- 员工姓名
    phone VARCHAR(50) NOT NULL,  -- 员工手机号
    department VARCHAR(255),  -- 部门
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name)  -- 确保姓名唯一
);

CREATE INDEX IF NOT EXISTS idx_employee_directory_name ON employee_directory(name);
CREATE INDEX IF NOT EXISTS idx_employee_directory_phone ON employee_directory(phone);
