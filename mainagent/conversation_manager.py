"""对话历史管理模块 - 用于管理用户A的对话历史"""

import threading
from typing import Dict, List, Optional
from datetime import datetime


class ConversationManager:
    """对话历史管理器 - 单例模式"""
    
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
        # 存储每个用户的对话历史: {user_id: conversation_history}
        self.conversations: Dict[str, List[Dict]] = {}
        # 存储session_id到tool_call_id和user_id的映射: {session_id: {"tool_call_id": ..., "user_id": ...}}
        self.session_to_tool_call: Dict[str, Dict[str, str]] = {}
        self._lock = threading.Lock()
        self._initialized = True
    
    def get_conversation(self, user_id: str) -> Optional[List[Dict]]:
        """获取用户的对话历史"""
        with self._lock:
            return self.conversations.get(user_id)
    
    def set_conversation(self, user_id: str, conversation_history: List[Dict]):
        """设置用户的对话历史"""
        with self._lock:
            self.conversations[user_id] = conversation_history
    
    def update_conversation(self, user_id: str, conversation_history: List[Dict]):
        """更新用户的对话历史（如果已存在则更新，否则创建）"""
        with self._lock:
            self.conversations[user_id] = conversation_history
    
    def register_session(self, session_id: str, tool_call_id: str, user_id: str):
        """注册session_id到tool_call_id和user_id的映射"""
        with self._lock:
            self.session_to_tool_call[session_id] = {
                "tool_call_id": tool_call_id,
                "user_id": user_id
            }
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, str]]:
        """获取session_id对应的tool_call_id和user_id"""
        with self._lock:
            return self.session_to_tool_call.get(session_id)
    
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
        
        conversation = self.get_conversation(user_id)
        if not conversation:
            return False
        
        # 查找对应的tool消息并更新
        with self._lock:
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
                            msg["content"] = f"{base_content}\n\n【已收到回复】\n{result}"
                        else:
                            msg["content"] = f"{original_content}\n\n【最新回复】\n{result}"
                    else:
                        # 第一次更新，追加结果
                        msg["content"] = f"{original_content}\n\n【已收到回复】\n{result}"
                    
                    updated = True
                    print(f"[DEBUG] 更新tool消息内容，tool_call_id={tool_call_id}")
                    print(f"[DEBUG] 更新后的内容预览: {msg['content'][:200]}...")
                    break
            
            if updated:
                self.conversations[user_id] = conversation
                print(f"[INFO] 已更新用户 {user_id} 的对话历史，tool消息已包含SubAgent结果")
            
            return updated


# 全局对话管理器实例
conversation_manager = ConversationManager()

