#!/usr/bin/env python3
"""
企业微信消息发送工具

本模块通过企业微信（WeCom）API 发送消息，负责获取访问令牌、
并向指定用户发送消息。

配置项：
- CORP_ID: 企业ID（ww33e8813b380a21b9）
- SECRET: 应用密钥（PjZjudyEw2GoCRppiTbtPRX0fihV3MNRWgCpht3LiZ8）
- AGENT_ID: 应用ID（1000003）
"""

import requests
import json
import time
from typing import Optional, Dict, Any

# 配置常量
CORP_ID = "ww33e8813b380a21b9"
# SECRET = "PjZjudyEw2GoCRppiTbtPRX0fihV3MNRWgCpht3LiZ8"
SECRET = "0uuOXp4w9kj9TuMUXRVw-zVw_3lBtf5ZKdSNkv7lMf8"
AGENT_ID = 1000004

# Access Token 全局缓存变量
_access_token = None
_token_expires_at = 0


def get_access_token() -> Optional[str]:
    """
    通过企业微信接口获取 Access Token。
    
    Returns:
        str: 获取成功返回 Access Token，失败返回 None
    """
    global _access_token, _token_expires_at
    
    # 若缓存中已有且未过期，直接返回
    if _access_token and time.time() < _token_expires_at:
        return _access_token
    
    # 请求新的 Access Token
    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    params = {
        "corpid": CORP_ID,
        "corpsecret": SECRET
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        result = response.json()
        
        if result.get("errcode") == 0:
            _access_token = result.get("access_token")
            # 令牌有效期为2小时，这里提前5分钟过期
            expires_in = result.get("expires_in", 7200)
            _token_expires_at = time.time() + expires_in - 300
            return _access_token
        else:
            print(f"获取 Access Token 出错: {result.get('errmsg')} (errcode: {result.get('errcode')})")
            return None
    except Exception as e:
        print(f"获取 Access Token 异常: {str(e)}")
        return None


def send_message(to_user: str, content: str, msg_type: str = "text") -> Dict[str, Any]:
    """
    通过企业微信 API 向指定用户发送消息。
    
    Args:
        to_user (str): 用户ID或邮箱（例如 'kangrz@chinatelecom.cn'）
        content (str): 消息内容
        msg_type (str): 消息类型，默认 'text'
        
    Returns:
        dict: 企业微信API返回结果
    """
    # 获取 Access Token
    access_token = get_access_token()
    if not access_token:
        return {"errcode": -1, "errmsg": "Failed to get access token"}
    
    # 组装消息体
    if msg_type == "text":
        message_data = {
            "touser": to_user,
            "msgtype": msg_type,
            "agentid": AGENT_ID,
            "text": {
                "content": content
            },
            "safe": 0
        }
    else:
        # 其他消息类型直接使用 content 字段
        message_data = {
            "touser": to_user,
            "msgtype": msg_type,
            "agentid": AGENT_ID,
            content: content,
            "safe": 0
        }
    
    # 发送消息
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
    
    try:
        response = requests.post(url, json=message_data)
        response.raise_for_status()
        result = response.json()
        
        # 常见错误码处理
        if result.get("errcode") == 60020:
            result["errmsg"] += "。通常是服务器公网IP未加入企业微信应用的IP白名单。"
        elif result.get("errcode") == 40001:
            result["errmsg"] += "。Access Token 无效，请检查 CORP_ID 与 SECRET。"
        elif result.get("errcode") == 40002:
            result["errmsg"] += "。Agent ID 无效，请检查 AGENT_ID。"
        
        return result
    except Exception as e:
        return {"errcode": -1, "errmsg": f"发送消息异常: {str(e)}"}


def send_text_message(to_user: str, content: str) -> Dict[str, Any]:
    """
    发送文本消息到指定用户。
    
    Args:
        to_user (str): 用户ID或邮箱（例如 'kangrz@chinatelecom.cn'）
        content (str): 消息内容
        
    Returns:
        dict: 企业微信API返回结果
    """
    return send_message(to_user, content, "text")


# 示例用法
if __name__ == "__main__":
    # 发送测试消息
    result = send_text_message("18731950791", "Hello from Super Agent!")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 常见问题排查
    if result.get("errcode") != 0:
        print("\n排查建议:")
        print("1. errcode=60020：确认服务器公网IP已加入企业微信应用 IP 白名单")
        print("2. errcode=40001：检查 CORP_ID 与 SECRET 是否正确")
        print("3. errcode=40002：检查 AGENT_ID 是否正确")
        print("4. 检查到 qyapi.weixin.qq.com 的网络连通性")