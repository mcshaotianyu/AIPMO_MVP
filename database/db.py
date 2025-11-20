"""数据库连接和操作模块"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
import json
import threading

# 添加utils目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import database_logger as logger


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
            logger.info(f"数据库连接池初始化成功: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
        except Exception as e:
            logger.error(f"数据库连接池初始化失败: {str(e)}", exc_info=True)
            logger.warning("请确保PostgreSQL数据库已启动，可以使用 ./start_database.sh 启动数据库")
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
    
    # ==================== MainAgent对话历史（MainAgent Conversations）相关操作 ====================
    
    def save_mainagent_message(self, user_id: str, role: str, content: Optional[str] = None,
                               tool_call_id: Optional[str] = None, tool_calls: Optional[List[Dict]] = None):
        """保存MainAgent对话消息"""
        logger.debug(f"保存MainAgent消息 - 用户ID: {user_id}, 角色: {role}, 内容长度: {len(content) if content else 0}")
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                tool_calls_json = json.dumps(tool_calls) if tool_calls else None
                cur.execute("""
                    INSERT INTO mainagent_conversations (user_id, role, content, tool_call_id, tool_calls)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, role, content, tool_call_id, tool_calls_json))
                logger.debug(f"MainAgent消息已保存到数据库")
    
    def get_mainagent_conversation(self, user_id: str) -> List[Dict]:
        """获取MainAgent的对话历史"""
        logger.debug(f"获取MainAgent对话历史 - 用户ID: {user_id}")
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT role, content, tool_call_id, tool_calls
                    FROM mainagent_conversations
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
                logger.debug(f"获取到 {len(result)} 条对话历史")
                return result
    
    def update_mainagent_message(self, user_id: str, tool_call_id: str, new_content: str):
        """更新MainAgent消息（用于更新tool消息的内容）"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE mainagent_conversations
                    SET content = %s
                    WHERE user_id = %s AND tool_call_id = %s AND role = 'tool'
                """, (new_content, user_id, tool_call_id))
    
    def clear_mainagent_conversation(self, user_id: str):
        """清空MainAgent的对话历史"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM mainagent_conversations WHERE user_id = %s", (user_id,))
    
    # ==================== 员工台账（Employee Directory）相关操作 ====================
    
    def search_employee_phones(self, names: List[str]) -> List[Dict[str, str]]:
        """
        根据员工姓名列表查询手机号
        
        Args:
            names: 员工姓名列表
            
        Returns:
            List[Dict]: 查询结果列表，每个元素包含 {"name": "姓名", "phone": "手机号"}
        """
        if not names or not isinstance(names, list):
            logger.warning("search_employee_phones: 输入参数无效")
            return []
        
        logger.info(f"查询员工手机号 - 姓名列表: {names}, 数量: {len(names)}")
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 使用IN查询，匹配姓名列表
                placeholders = ','.join(['%s'] * len(names))
                cur.execute(f"""
                    SELECT name, phone
                    FROM employee_directory
                    WHERE name IN ({placeholders})
                """, tuple(names))
                
                rows = cur.fetchall()
                result = []
                for row in rows:
                    result.append({
                        "name": row["name"],
                        "phone": row["phone"]
                    })
                logger.info(f"查询完成 - 找到 {len(result)} 个员工信息")
                if result:
                    logger.debug(f"查询结果: {result}")
                return result
    
    def add_employee(self, name: str, phone: str, department: Optional[str] = None):
        """添加员工到台账"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO employee_directory (name, phone, department)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name) DO UPDATE
                    SET phone = EXCLUDED.phone, department = EXCLUDED.department
                """, (name, phone, department))
    
    def get_all_employees(self) -> List[Dict]:
        """获取所有员工（用于调试）"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT name, phone, department FROM employee_directory ORDER BY name")
                return [dict(row) for row in cur.fetchall()]


# 全局数据库实例
db = Database()
