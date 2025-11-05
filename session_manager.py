"""会话管理模块 - 用于管理主agent和子agent之间的异步会话"""

import json
import time
import threading
import sys
import os
from typing import Dict, List, Optional
from datetime import datetime

# 添加database目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import db


class Session:
    """会话对象（用于兼容性，实际数据存储在数据库中）"""
    
    def __init__(self, session_id: str, user_a: str, user_b_id: str, user_b_name: str, question: str):
        self.session_id = session_id
        self.user_a = user_a  # 用户A的标识
        self.user_b_id = user_b_id  # 用户B的ID
        self.user_b_name = user_b_name  # 用户B的姓名
        self.question = question  # 原始问题
        self.status = "pending"  # pending/in_progress/completed/failed
        self.conversation_history = []  # 子agent与用户B的对话历史（从数据库加载）
        self.result = None  # 最终结果
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.callback_url = None  # 回调URL
        self.callback_triggered = False  # 是否已触发回调
    
    def to_dict(self):
        """转换为字典"""
        # 从数据库加载最新的对话历史
        conversation_history = db.get_session_messages(self.session_id)
        
        # 获取最新的assistant消息（子agent的问题）
        latest_question = None
        for msg in reversed(conversation_history):
            if msg.get("role") == "assistant":
                latest_question = msg.get("content")
                break
        
        # 从数据库获取最新的会话信息
        session_data = db.get_session(self.session_id)
        if session_data:
            self.status = session_data.get("status", self.status)
            self.result = session_data.get("result", self.result)
            self.callback_triggered = session_data.get("callback_triggered", False)
            self.created_at = session_data.get("created_at").isoformat() if session_data.get("created_at") else self.created_at
            self.updated_at = session_data.get("updated_at").isoformat() if session_data.get("updated_at") else self.updated_at
        
        return {
            "session_id": self.session_id,
            "user_a": self.user_a,
            "user_b_id": self.user_b_id,
            "user_b_name": self.user_b_name,
            "question": self.question,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "callback_triggered": self.callback_triggered,
            "conversation_turns": len(conversation_history) // 2,  # 对话轮数
            "latest_question": latest_question  # 子agent的最新问题
        }


class SessionManager:
    """会话管理器 - 单例模式（使用PostgreSQL存储）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.Lock()
        self._initialized = True
    
    def create_session(self, session_id: str, user_a: str, user_b_id: str, 
                      user_b_name: str, question: str, callback_url: Optional[str] = None) -> Session:
        """
        创建新会话
        
        Args:
            session_id: 会话ID
            user_a: 用户A的标识
            user_b_id: 用户B的ID
            user_b_name: 用户B的姓名
            question: 原始问题
            callback_url: 完成时的回调URL
            
        Returns:
            Session: 创建的会话对象
        """
        # 存储到数据库
        db.create_session(session_id, user_a, user_b_id, user_b_name, question, callback_url)
        
        # 创建Session对象（用于兼容性）
        session = Session(session_id, user_a, user_b_id, user_b_name, question)
        session.callback_url = callback_url
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        session_data = db.get_session(session_id)
        if not session_data:
            return None
        
        # 创建Session对象
        session = Session(
            session_id,
            session_data["user_a"],
            session_data["user_b_id"],
            session_data["user_b_name"],
            session_data["question"]
        )
        session.status = session_data.get("status", "pending")
        session.result = session_data.get("result")
        session.callback_url = session_data.get("callback_url")
        session.callback_triggered = session_data.get("callback_triggered", False)
        session.created_at = session_data.get("created_at").isoformat() if session_data.get("created_at") else datetime.now().isoformat()
        session.updated_at = session_data.get("updated_at").isoformat() if session_data.get("updated_at") else datetime.now().isoformat()
        
        # 加载对话历史
        session.conversation_history = db.get_session_messages(session_id)
        
        return session
    
    def update_session_status(self, session_id: str, status: str):
        """更新会话状态"""
        db.update_session_status(session_id, status)
    
    def add_conversation_turn(self, session_id: str, role: str, content: str):
        """添加对话记录"""
        db.add_session_message(session_id, role, content)
    
    def set_session_result(self, session_id: str, result: str):
        """设置会话结果"""
        db.set_session_result(session_id, result)
    
    def get_all_sessions(self) -> List[Dict]:
        """获取所有会话（用于调试）"""
        return db.get_all_sessions()
    
    def get_pending_sessions(self, user_b_id: str) -> List[Dict]:
        """获取特定用户B的待处理会话"""
        return db.get_pending_sessions(user_b_id)
    
    def get_all_pending_sessions(self) -> List[Dict]:
        """获取所有待处理会话（用于测试，模拟所有用户）"""
        return db.get_all_pending_sessions()
    
    def mark_callback_triggered(self, session_id: str):
        """标记回调已触发"""
        db.mark_callback_triggered(session_id)


# 全局会话管理器实例
session_manager = SessionManager()

