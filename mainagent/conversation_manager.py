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
        """获取用户的对话历史"""
        conversation = db.get_user_conversation(user_id)
        return conversation if conversation else None
    
    def set_conversation(self, user_id: str, conversation_history: List[Dict]):
        """设置用户的对话历史"""
        # 先清空用户的对话历史
        db.clear_user_conversation(user_id)
        
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
            # JSON序列化会在db.save_user_message中处理
            
            db.save_user_message(
                user_id=user_id,
                role=role,
                content=content,
                tool_call_id=tool_call_id,
                tool_calls=tool_calls
            )
    
    def update_conversation(self, user_id: str, conversation_history: List[Dict]):
        """更新用户的对话历史（如果已存在则更新，否则创建）"""
        self.set_conversation(user_id, conversation_history)
    
    def register_session(self, session_id: str, tool_call_id: str, user_id: str):
        """注册session_id到tool_call_id和user_id的映射"""
        db.register_session_mapping(session_id, tool_call_id, user_id)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, str]]:
        """获取session_id对应的tool_call_id和user_id"""
        return db.get_session_mapping(session_id)
    
    def update_tool_result(self, session_id: str, result: str) -> bool:
        """
        更新工具调用的结果到对话历史中
        
        Args:
            session_id: 会话ID
            result: SubAgent的结果
            
        Returns:
            bool: 是否成功更新
        """
        session_info = self.get_session_info(session_id)
        if not session_info:
            return False
        
        user_id = session_info.get("user_id")
        tool_call_id = session_info.get("tool_call_id")
        
        if not user_id or not tool_call_id:
            return False
        
        # 从数据库获取对话历史
        conversation = self.get_conversation(user_id)
        if not conversation:
            return False
        
        # 查找对应的tool消息并更新
        updated = False
        for msg in conversation:
            if msg.get("role") == "tool" and msg.get("tool_call_id") == tool_call_id:
                # 更新tool消息的内容，添加SubAgent的结果
                original_content = msg.get("content", "")
                
                # 检查是否已经包含结果
                if "【已收到回复】" in original_content or "【最新回复】" in original_content:
                    # 如果已经更新过，则替换为最新结果
                    # 找到原始内容（去掉之前的回复标记）
                    lines = original_content.split("\n\n【")
                    if len(lines) > 0:
                        base_content = lines[0].strip()
                        # 保留原始联系信息，但更新为最终结果
                        new_content = f"{base_content}\n\n【已收到回复】\n{result}"
                    else:
                        new_content = f"{original_content}\n\n【最新回复】\n{result}"
                else:
                    # 第一次更新，追加结果
                    new_content = f"{original_content}\n\n【已收到回复】\n{result}"
                
                # 更新数据库中的消息
                db.update_user_message(user_id, tool_call_id, new_content)
                
                updated = True
                print(f"[DEBUG] 更新tool消息内容，tool_call_id={tool_call_id}")
                print(f"[DEBUG] 更新后的内容预览: {new_content[:200]}...")
                break
        
        if updated:
            print(f"[INFO] 已更新用户 {user_id} 的对话历史，tool消息已包含SubAgent结果")
        
        return updated


# 全局对话管理器实例
conversation_manager = ConversationManager()

