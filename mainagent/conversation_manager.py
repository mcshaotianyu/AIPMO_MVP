"""对话历史管理模块 - 用于管理用户A的对话历史"""

import threading
import sys
import os
from typing import Dict, List, Optional
from datetime import datetime

# 添加database目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import db


class ConversationManager:
    """对话历史管理器 - 单例模式（使用PostgreSQL存储）"""
    
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
    
    def get_conversation(self, user_id: str) -> Optional[List[Dict]]:
        """获取用户的对话历史（使用mainagent_conversations表）"""
        conversation = db.get_mainagent_conversation(user_id)
        return conversation if conversation else None
    
    def set_conversation(self, user_id: str, conversation_history: List[Dict]):
        """设置用户的对话历史（使用mainagent_conversations表）"""
        # 先清空用户的对话历史
        db.clear_mainagent_conversation(user_id)
        
        # 然后保存新的对话历史
        for msg in conversation_history:
            role = msg.get("role")
            content = msg.get("content")
            tool_call_id = msg.get("tool_call_id")
            tool_calls = msg.get("tool_calls")
            
            # 确保content不为None（至少是空字符串）
            if content is None:
                content = ""
            
            # tool_calls如果是列表，保持原样；如果是None，保持None
            # JSON序列化会在db.save_mainagent_message中处理
            
            db.save_mainagent_message(
                user_id=user_id,
                role=role,
                content=content,
                tool_call_id=tool_call_id,
                tool_calls=tool_calls
            )
    
    def update_conversation(self, user_id: str, conversation_history: List[Dict]):
        """更新用户的对话历史（如果已存在则更新，否则创建）"""
        self.set_conversation(user_id, conversation_history)
    


# 全局对话管理器实例
conversation_manager = ConversationManager()

