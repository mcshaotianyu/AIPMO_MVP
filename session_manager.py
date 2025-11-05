"""会话管理模块 - 用于管理主agent和子agent之间的异步会话"""

import json
import time
import threading
from typing import Dict, List, Optional
from datetime import datetime


class Session:
    """会话对象"""
    
    def __init__(self, session_id: str, user_a: str, user_b_id: str, user_b_name: str, question: str):
        self.session_id = session_id
        self.user_a = user_a  # 用户A的标识
        self.user_b_id = user_b_id  # 用户B的ID
        self.user_b_name = user_b_name  # 用户B的姓名
        self.question = question  # 原始问题
        self.status = "pending"  # pending/in_progress/completed/failed
        self.conversation_history = []  # 子agent与用户B的对话历史
        self.result = None  # 最终结果
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.callback_url = None  # 回调URL
        self.callback_triggered = False  # 是否已触发回调
    
    def to_dict(self):
        """转换为字典"""
        # 获取最新的assistant消息（子agent的问题）
        latest_question = None
        for msg in reversed(self.conversation_history):
            if msg.get("role") == "assistant":
                latest_question = msg.get("content")
                break
        
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
            "conversation_turns": len(self.conversation_history) // 2,  # 对话轮数
            "latest_question": latest_question  # 子agent的最新问题
        }


class SessionManager:
    """会话管理器 - 单例模式"""
    
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
        self.sessions: Dict[str, Session] = {}
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
        with self._lock:
            session = Session(session_id, user_a, user_b_id, user_b_name, question)
            session.callback_url = callback_url
            self.sessions[session_id] = session
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def update_session_status(self, session_id: str, status: str):
        """更新会话状态"""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].status = status
                self.sessions[session_id].updated_at = datetime.now().isoformat()
    
    def add_conversation_turn(self, session_id: str, role: str, content: str):
        """添加对话记录"""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].conversation_history.append({
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
                self.sessions[session_id].updated_at = datetime.now().isoformat()
    
    def set_session_result(self, session_id: str, result: str):
        """设置会话结果"""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].result = result
                self.sessions[session_id].status = "completed"
                self.sessions[session_id].updated_at = datetime.now().isoformat()
    
    def get_all_sessions(self) -> List[Dict]:
        """获取所有会话（用于调试）"""
        return [session.to_dict() for session in self.sessions.values()]
    
    def get_pending_sessions(self, user_b_id: str) -> List[Dict]:
        """获取特定用户B的待处理会话"""
        result = []
        for session in self.sessions.values():
            if session.user_b_id == user_b_id and session.status in ["pending", "in_progress"]:
                result.append(session.to_dict())
        return result
    
    def mark_callback_triggered(self, session_id: str):
        """标记回调已触发"""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].callback_triggered = True


# 全局会话管理器实例
session_manager = SessionManager()

