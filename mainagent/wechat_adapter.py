"""企业微信适配层

提供企业微信API的封装，支持：
1. 接收企业微信消息回调
2. 发送消息给企业微信用户
3. 消息格式转换（企业微信格式 ↔ 系统内部格式）
"""

import os
import time
import requests
from typing import Dict, Optional


class WeChatAdapter:
    """企业微信API适配器"""
    
    def __init__(self):
        # 企业微信配置（从环境变量读取，必须配置）
        self.corp_id = os.environ.get('WECHAT_CORP_ID')
        self.corp_secret = os.environ.get('WECHAT_CORP_SECRET')
        self.agent_id = os.environ.get('WECHAT_AGENT_ID')
        self.token = os.environ.get('WECHAT_TOKEN')
        self.encoding_aes_key = os.environ.get('WECHAT_ENCODING_AES_KEY')
        
        # 验证必需配置
        if not all([self.corp_id, self.corp_secret, self.agent_id]):
            raise ValueError(
                "企业微信配置不完整，请设置以下环境变量：\n"
                "  WECHAT_CORP_ID: 企业ID\n"
                "  WECHAT_CORP_SECRET: 应用Secret\n"
                "  WECHAT_AGENT_ID: 应用AgentID"
            )
        
        # Token缓存
        self.access_token = None
        self.token_expires_at = 0
        
        print(f"[INFO] 企业微信适配器已启用 (CorpID: {self.corp_id[:10]}...)")
    
    def get_access_token(self) -> Optional[str]:
        """获取access_token（带缓存）"""
        # 检查缓存
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        try:
            url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {
                "corpid": self.corp_id,
                "corpsecret": self.corp_secret
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("errcode") == 0:
                self.access_token = data.get("access_token")
                expires_in = data.get("expires_in", 7200)
                self.token_expires_at = time.time() + expires_in - 300  # 提前5分钟刷新
                print(f"[INFO] 企业微信access_token获取成功，有效期: {expires_in}秒")
                return self.access_token
            else:
                print(f"[ERROR] 获取企业微信access_token失败: {data.get('errmsg')}")
                return None
        except Exception as e:
            print(f"[ERROR] 获取企业微信access_token异常: {str(e)}")
            return None
    
    def send_text_message(self, user_id: str, content: str) -> bool:
        """
        发送文本消息给企业微信用户
        
        Args:
            user_id: 企业微信userid
            content: 消息内容
            
        Returns:
            bool: 是否发送成功
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                print(f"[ERROR] 无法获取access_token，消息推送失败")
                return False
            
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            
            payload = {
                "touser": user_id,  # 企业微信userid
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {
                    "content": content
                }
            }
            
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            
            if data.get("errcode") == 0:
                print(f"[INFO] 企业微信消息推送成功，用户: {user_id}")
                return True
            else:
                print(f"[ERROR] 企业微信消息推送失败: {data.get('errmsg')}, 用户: {user_id}")
                return False
        except Exception as e:
            print(f"[ERROR] 企业微信消息推送异常: {str(e)}")
            return False
    
    def parse_wechat_message(self, wechat_data: Dict) -> Dict:
        """
        解析企业微信回调消息格式，转换为系统内部格式
        
        企业微信回调格式（XML或JSON，取决于配置）:
        {
            "ToUserName": "企业ID",
            "FromUserName": "企业微信userid",
            "CreateTime": 1234567890,
            "MsgType": "text",
            "Content": "消息内容",
            "MsgId": "消息ID"
        }
        
        Returns:
            dict: 系统内部格式
            {
                "user_id": "企业微信userid",
                "message": "消息内容",
                "msg_type": "text",
                "msg_id": "消息ID"
            }
        """
        # 解析企业微信消息格式（需要根据企业微信文档实现XML解析和消息解密）
        return {
            "user_id": wechat_data.get("FromUserName") or wechat_data.get("user_id"),
            "message": wechat_data.get("Content") or wechat_data.get("message", ""),
            "msg_type": wechat_data.get("MsgType") or wechat_data.get("msg_type", "text"),
            "msg_id": wechat_data.get("MsgId") or wechat_data.get("msg_id")
        }
    
    def format_response_for_wechat(self, system_response: Dict) -> str:
        """
        将系统响应格式化为企业微信消息格式（纯文本）
        
        Args:
            system_response: 系统内部响应格式
            
        Returns:
            str: 格式化后的文本消息
        """
        if system_response.get("status") == "error":
            return f"❌ 错误: {system_response.get('error', '未知错误')}"
        
        # 优先返回answer字段
        answer = system_response.get("answer", "")
        if answer:
            return answer
        
        # 处理subagent的响应
        if system_response.get("session_status") == "completed":
            result = system_response.get("result", "")
            return f"✅ 会话已完成\n\n{result}"
        elif system_response.get("next_question"):
            return system_response.get("next_question")
        
        # 默认返回
        return "处理完成"
    
    def verify_callback_url(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> Optional[str]:
        """
        验证企业微信回调URL（GET请求）
        
        Args:
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机数
            echostr: 随机字符串
            
        Returns:
            str: 验证成功返回echostr，失败返回None
        """
        # TODO: 实现真正的签名验证
        # 1. 使用token、timestamp、nonce、echostr计算签名
        # 2. 与msg_signature比较
        # 3. 如果匹配，返回echostr；否则返回None
        
        # 临时实现：需要根据企业微信文档实现完整的签名验证逻辑
        print(f"[WARNING] 企业微信回调URL验证未完全实现，需要根据企业微信文档实现签名验证")
        return echostr


# 全局实例
wechat_adapter = WeChatAdapter()

