"""数据库连接和操作模块"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
import json
import threading


class Database:
    """数据库操作类 - 单例模式"""
    
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
        
        # 从环境变量获取数据库配置
        self.db_config = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': os.environ.get('DB_PORT', '5432'),
            'database': os.environ.get('DB_NAME', 'myserver_db'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD', 'postgres')
        }
        
        # 创建连接池
        self.pool = None
        self._init_pool()
        
        self._initialized = True
    
    def _init_pool(self):
        """初始化连接池"""
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **self.db_config
            )
            print(f"[INFO] 数据库连接池初始化成功: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
        except Exception as e:
            print(f"[ERROR] 数据库连接池初始化失败: {str(e)}")
            print(f"[WARNING] 请确保PostgreSQL数据库已启动，可以使用 ./start_database.sh 启动数据库")
            # 不抛出异常，允许程序继续运行（但数据库操作会失败）
            self.pool = None
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        if self.pool is None:
            raise Exception("数据库连接池未初始化，请确保PostgreSQL数据库已启动")
        
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.pool.putconn(conn)
    
    # ==================== 会话（Session）相关操作 ====================
    
    def create_session(self, session_id: str, user_a: str, user_b_id: str, 
                     user_b_name: str, question: str, callback_url: Optional[str] = None) -> Dict:
        """创建新会话"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO sessions (session_id, user_a, user_b_id, user_b_name, question, callback_url)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (session_id, user_a, user_b_id, user_b_name, question, callback_url))
                return dict(cur.fetchone())
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM sessions WHERE session_id = %s", (session_id,))
                row = cur.fetchone()
                return dict(row) if row else None
    
    def update_session_status(self, session_id: str, status: str):
        """更新会话状态"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE sessions SET status = %s WHERE session_id = %s",
                    (status, session_id)
                )
    
    def set_session_result(self, session_id: str, result: str):
        """设置会话结果"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE sessions SET result = %s, status = 'completed' WHERE session_id = %s",
                    (result, session_id)
                )
    
    def mark_callback_triggered(self, session_id: str):
        """标记回调已触发"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE sessions SET callback_triggered = TRUE WHERE session_id = %s",
                    (session_id,)
                )
    
    def get_pending_sessions(self, user_b_id: str) -> List[Dict]:
        """获取特定用户B的待处理会话"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT s.*, 
                           (SELECT content FROM session_messages 
                            WHERE session_id = s.session_id AND role = 'assistant' 
                            ORDER BY created_at DESC LIMIT 1) as latest_question,
                           (SELECT COUNT(*) FROM session_messages WHERE session_id = s.session_id) / 2 as conversation_turns
                    FROM sessions s
                    WHERE s.user_b_id = %s AND s.status IN ('pending', 'in_progress')
                    ORDER BY s.created_at DESC
                """, (user_b_id,))
                return [dict(row) for row in cur.fetchall()]
    
    def get_all_sessions(self) -> List[Dict]:
        """获取所有会话（用于调试）"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT s.*,
                           (SELECT content FROM session_messages 
                            WHERE session_id = s.session_id AND role = 'assistant' 
                            ORDER BY created_at DESC LIMIT 1) as latest_question,
                           (SELECT COUNT(*) FROM session_messages WHERE session_id = s.session_id) / 2 as conversation_turns
                    FROM sessions s
                    ORDER BY s.created_at DESC
                """)
                return [dict(row) for row in cur.fetchall()]
    
    # ==================== 会话消息（Session Messages）相关操作 ====================
    
    def add_session_message(self, session_id: str, role: str, content: str):
        """添加会话消息"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO session_messages (session_id, role, content)
                    VALUES (%s, %s, %s)
                """, (session_id, role, content))
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        """获取会话的所有消息"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT role, content, created_at
                    FROM session_messages
                    WHERE session_id = %s
                    ORDER BY created_at ASC
                """, (session_id,))
                rows = cur.fetchall()
                return [
                    {
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["created_at"].isoformat() if row["created_at"] else None
                    }
                    for row in rows
                ]
    
    # ==================== 用户对话历史（User Conversations）相关操作 ====================
    
    def save_user_message(self, user_id: str, role: str, content: Optional[str] = None,
                         tool_call_id: Optional[str] = None, tool_calls: Optional[List[Dict]] = None):
        """保存用户消息"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                tool_calls_json = json.dumps(tool_calls) if tool_calls else None
                cur.execute("""
                    INSERT INTO user_conversations (user_id, role, content, tool_call_id, tool_calls)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, role, content, tool_call_id, tool_calls_json))
    
    def get_user_conversation(self, user_id: str) -> List[Dict]:
        """获取用户的对话历史"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT role, content, tool_call_id, tool_calls
                    FROM user_conversations
                    WHERE user_id = %s
                    ORDER BY created_at ASC
                """, (user_id,))
                rows = cur.fetchall()
                result = []
                for row in rows:
                    msg = {
                        "role": row["role"],
                        "content": row["content"] if row["content"] is not None else ""
                    }
                    if row["tool_call_id"]:
                        msg["tool_call_id"] = row["tool_call_id"]
                    if row["tool_calls"]:
                        # tool_calls已经是JSONB，直接使用
                        msg["tool_calls"] = row["tool_calls"]
                    result.append(msg)
                return result
    
    def update_user_message(self, user_id: str, tool_call_id: str, new_content: str):
        """更新用户消息（用于更新tool消息的内容）"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_conversations
                    SET content = %s
                    WHERE user_id = %s AND tool_call_id = %s AND role = 'tool'
                """, (new_content, user_id, tool_call_id))
    
    def clear_user_conversation(self, user_id: str):
        """清空用户的对话历史"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_conversations WHERE user_id = %s", (user_id,))
    
    # ==================== 会话映射（Session Mappings）相关操作 ====================
    
    def register_session_mapping(self, session_id: str, tool_call_id: str, user_id: str):
        """注册session_id到tool_call_id和user_id的映射"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO session_mappings (session_id, tool_call_id, user_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE
                    SET tool_call_id = EXCLUDED.tool_call_id, user_id = EXCLUDED.user_id
                """, (session_id, tool_call_id, user_id))
    
    def get_session_mapping(self, session_id: str) -> Optional[Dict]:
        """获取session_id对应的tool_call_id和user_id"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT tool_call_id, user_id
                    FROM session_mappings
                    WHERE session_id = %s
                """, (session_id,))
                row = cur.fetchone()
                return dict(row) if row else None


# 全局数据库实例
db = Database()

