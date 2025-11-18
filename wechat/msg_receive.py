#!/usr/bin/env python3
"""
企业微信消息接收工具
该模块提供通过 Webhook 回调接收来自企业微信的消息的功能。
它处理 URL 验证和消息解密以实现安全通信。
配置：
- 令牌：验证令牌 （uahVGvONDc7cUx）
- ENCODING_AES_KEY：用于消息加密的 AES 密钥 （eF0rmkgB8rtBUGvXVOF5NnV0v5MoVquJQY45wUdXTax）
- CORP_ID：企业 ID （ww33e8813b380a21b9）
"""

import hashlib
import base64
import xml.etree.ElementTree as ET

import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import time
import os
from typing import Optional, Dict, Any
from flask import Flask, request, make_response

# 兼容从项目根目录与从 mainagent 目录两种运行方式
try:
    from wechat.msg_send import send_text_message  # 当项目根目录在 sys.path 时
except ModuleNotFoundError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 加入项目根目录
    from wechat.msg_send import send_text_message

TOKEN = "eU8eazR4xwO7XD1ZPXOm0pDAGvvlqCOk"
ENCODING_AES_KEY = "MBTHULJAlzkhQAglYL0SIqdWCqMPU01bBE3CfLnWRua"
CORP_ID = "ww33e8813b380a21b9"
MAINAGENT_URL = "http://localhost:5001"

app = Flask(__name__)


def verify_url(msg_signature: str, timestamp: str, nonce: str, echo_str: str) -> str:
    """
    在微信网址验证期间验证回传网址。
    参数：
    msg_signature （str）：来自微信的签名
    timestamp （str）：来自微信的时间戳
    nonce （str）：来自微信的 nonce
    echo_str （str）：来自微信的加密回声字符串
    返回：
    str：如果验证成功，则解密的回声字符串
    """
    # Sort parameters and compute signature
    signature = compute_signature(TOKEN, timestamp, nonce, echo_str)

    if signature != msg_signature:
        raise ValueError("Signature verification failed")

    # Decrypt echo string
    return decrypt_message(echo_str, ENCODING_AES_KEY, CORP_ID)


def compute_signature(token: str, timestamp: str, nonce: str, encrypt: str) -> str:
    """
    计算微信回调验证的签名。

    参数：
        token （str）：验证令牌
        timestamp （str）：时间戳
        nonce （str）：随机数
        encrypt （str）：加密消息

    返回：
        str：计算签名
    """
    # Sort parameters lexicographically
    params = [token, timestamp, nonce, encrypt]
    params.sort()

    # Concatenate parameters
    raw_string = ''.join(params)

    # Compute SHA1 hash
    sha1 = hashlib.sha1()
    sha1.update(raw_string.encode('utf-8'))
    return sha1.hexdigest()


def decrypt_message(encrypt_str: str, encoding_aes_key: str, corp_id: str) -> str:
    """
    解密来自微信的消息。

    参数：
        encrypt_str （str）：Base64 编码的加密消息
        encoding_aes_key （str）：AES 密钥
        corp_id （str）：企业 ID

    返回：
        str：解密消息
    """
    # Decode base64
    aes_key = base64.b64decode(encoding_aes_key + '=')
    encrypt_bytes = base64.b64decode(encrypt_str)

    # Extract IV (first 16 bytes)
    iv = aes_key[:16]

    # Decrypt
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypt_bytes) + decryptor.finalize()

    # Remove padding
    pad = decrypted[-1]
    if isinstance(pad, int):
        decrypted = decrypted[:-pad]
    else:
        decrypted = decrypted[:-ord(pad)]

    # Extract message length (4 bytes after 16-byte random string)
    msg_len = int.from_bytes(decrypted[16:20], byteorder='big')

    # Extract message content
    msg = decrypted[20:20 + msg_len].decode('utf-8')

    # Extract CorpID and verify
    received_corp_id = decrypted[20 + msg_len:20 + msg_len + len(corp_id)].decode('utf-8')
    if received_corp_id != corp_id:
        raise ValueError("CorpID mismatch")

    return msg


def parse_message(xml_content: str) -> Dict[str, Any]:
    """
    解析来自企业微信的 XML 消息。

    参数：
        xml_content （str）：来自微信的 XML 内容

    返回：
        dict：解析的消息数据
    """
    root = ET.fromstring(xml_content)
    message = {}

    for child in root:
        message[child.tag] = child.text

    return message


@app.route('/yxg/wechat/callback', methods=['GET', 'POST'])
def wechat_callback():
    """
    WeCom 回调端点。

    对于 GET 请求：处理 URL 验证
    对于 POST 请求：处理传入邮件
    """
    if request.method == 'GET':
        # URL verification
        msg_signature = request.args.get('msg_signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        echo_str = request.args.get('echostr')

        # If any required parameters are missing, return a helpful message
        if not all([msg_signature, timestamp, nonce, echo_str]):
            return "This endpoint is for WeCom callback verification only. Please configure your WeCom app with the correct parameters.", 400

        try:
            decrypted_echo = verify_url(msg_signature, timestamp, nonce, echo_str)
            response = make_response(decrypted_echo)
            response.headers['Content-Type'] = 'text/plain'
            return response
        except Exception as e:
            return f"Verification failed: {str(e)}", 400

    elif request.method == 'POST':
        # Message reception from WeCom
        print(f"DEBUG: Received POST request at {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Log the request to a file for debugging
        try:
            with open("/tmp/yxg_debug.log", "a", encoding="utf-8") as f:
                f.write(f"\n=== POST Request {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                f.write(f"Headers: {dict(request.headers)}\n")
                f.write(f"Remote Addr: {request.remote_addr}\n")
                f.write(f"URL Args: {dict(request.args)}\n")
        except Exception as e:
            print(f"Error writing debug log: {e}")

        # Get encrypted message data from POST request
        # WeCom sends: msg_signature, timestamp, nonce, and encrypted XML
        msg_signature = request.args.get('msg_signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')

        try:
            # Get the XML content
            xml_content = request.data.decode('utf-8')
            print(f"DEBUG: XML content length={len(xml_content)}")

            # Log raw content
            try:
                with open("/tmp/yxg_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"Raw XML (first 500 chars): {xml_content[:500]}\n")
            except:
                pass

            # Parse the encrypted XML structure
            root = ET.fromstring(xml_content)
            encrypt_tag = root.find('Encrypt')

            if encrypt_tag is None:
                # Not encrypted - parse directly
                print("DEBUG: Message not encrypted, parsing directly")
                message_data = {
                    'ToUserName': root.find('ToUserName').text if root.find('ToUserName') is not None else '',
                    'FromUserName': root.find('FromUserName').text if root.find('FromUserName') is not None else '',
                    'CreateTime': root.find('CreateTime').text if root.find('CreateTime') is not None else '',
                    'MsgType': root.find('MsgType').text if root.find('MsgType') is not None else '',
                    'Content': root.find('Content').text if root.find('Content') is not None else '',
                    'MsgId': root.find('MsgId').text if root.find('MsgId') is not None else '',
                    'AgentID': root.find('AgentID').text if root.find('AgentID') is not None else ''
                }
            else:
                # Encrypted - need to decrypt
                print("DEBUG: Message is encrypted, decrypting...")
                encrypted_msg = encrypt_tag.text

                # Verify signature
                computed_signature = compute_signature(TOKEN, timestamp, nonce, encrypted_msg)
                if computed_signature != msg_signature:
                    print(f"DEBUG: Signature mismatch! Expected {msg_signature}, got {computed_signature}")
                    return "Invalid signature", 400

                # Decrypt the message
                decrypted_xml = decrypt_message(encrypted_msg, ENCODING_AES_KEY, CORP_ID)
                print(f"DEBUG: Decrypted XML: {decrypted_xml[:200]}...")

                # Parse the decrypted XML
                decrypted_root = ET.fromstring(decrypted_xml)
                message_data = {
                    'ToUserName': decrypted_root.find('ToUserName').text if decrypted_root.find(
                        'ToUserName') is not None else '',
                    'FromUserName': decrypted_root.find('FromUserName').text if decrypted_root.find(
                        'FromUserName') is not None else '',
                    'CreateTime': decrypted_root.find('CreateTime').text if decrypted_root.find(
                        'CreateTime') is not None else '',
                    'MsgType': decrypted_root.find('MsgType').text if decrypted_root.find(
                        'MsgType') is not None else '',
                    'Content': decrypted_root.find('Content').text if decrypted_root.find(
                        'Content') is not None else '',
                    'MsgId': decrypted_root.find('MsgId').text if decrypted_root.find('MsgId') is not None else '',
                    'AgentID': decrypted_root.find('AgentID').text if decrypted_root.find('AgentID') is not None else ''
                }

            print(f"DEBUG: Parsed message: {message_data}")

            # Check if we have valid content
            if not message_data.get('Content') or not message_data.get('FromUserName'):
                print(f"DEBUG: Invalid message data, skipping processing")
                print(
                    f"DEBUG: Content='{message_data.get('Content')}', FromUserName='{message_data.get('FromUserName')}'")
                try:
                    with open("/tmp/yxg_debug.log", "a", encoding="utf-8") as f:
                        f.write(
                            f"ERROR: Invalid message data - Content='{message_data.get('Content')}', FromUserName='{message_data.get('FromUserName')}'\n")
                except:
                    pass
                response = make_response("success")
                response.headers['Content-Type'] = 'text/plain'
                return response

            # Process message
            print(f"DEBUG: About to call process_incoming_message()")
            try:
                with open("/tmp/yxg_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"About to call process_incoming_message() with content='{message_data.get('Content')}'\n")
            except:
                pass
            process_incoming_message(message_data)
            print(f"DEBUG: Message processed successfully")
            try:
                with open("/tmp/yxg_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"Message processed successfully\n")
            except:
                pass

            # Return success response
            response = make_response("success")
            response.headers['Content-Type'] = 'text/plain'
            return response

        except Exception as e:
            print(f"ERROR in webhook: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Message processing failed: {str(e)}", 500


# File to track processed message IDs to prevent duplicates across restarts
PROCESSED_IDS_FILE = "/tmp/yxg_processed_msg_ids.txt"


def load_processed_ids():
    """Load processed message IDs from file."""
    try:
        if os.path.exists(PROCESSED_IDS_FILE):
            with open(PROCESSED_IDS_FILE, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()
    except:
        return set()


def save_processed_id(msg_id):
    """Save processed message ID to file."""
    try:
        with open(PROCESSED_IDS_FILE, 'a') as f:
            f.write(f"{msg_id}\n")
    except:
        pass


# Load existing processed IDs
_processed_message_ids = load_processed_ids()


def process_incoming_message(message_data: Dict[str, Any]) -> None:
    """
    Process incoming message from WeCom.
    
    Args:
        message_data (dict): Parsed message data
    """
    import json
    import sys
    from datetime import datetime

    # Get message ID to prevent duplicate processing
    message_id = message_data.get('MsgId', '')

    # Check if we've already processed this message
    if message_id in _processed_message_ids:
        print(f"DEBUG: Message {message_id} already processed, skipping duplicate")
        return

    # Add to processed set
    _processed_message_ids.add(message_id)
    save_processed_id(message_id)

    # Log entry to debug file
    try:
        with open("/tmp/yxg_debug.log", "a", encoding="utf-8") as f:
            f.write(f"\nprocess_incoming_message() called with message_data keys: {list(message_data.keys())}\n")
    except:
        pass

    # Example implementation - log the message
    print(f"Received message: {message_data}")

    # Save message to a file
    try:
        # Create a timestamp for the message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Prepare message record
        message_record = {
            "timestamp": timestamp,
            "received_data": message_data
        }

        # Append to messages log file
        with open("/home/AI_HR_backup/wechat_messages.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(message_record, ensure_ascii=False) + "\n")

        print(f"Message saved to log file")
    except Exception as e:
        print(f"Error saving message to log: {e}")

    # Process different message types
    message_type = message_data.get('MsgType', 'unknown')
    from_user = message_data.get('FromUserName', 'unknown')
    create_time = message_data.get('CreateTime', 'unknown')

    print(f"[{create_time}] {from_user}: {message_type} message received")

    # Handle different message types
    if message_type == "text":
        content = message_data.get('Content', '')
        sender_id = message_data.get('FromUserName')

        # 1. 主动问问题 没有过往问题
        # 2. 回答别人的问题

        """发送查询到主agent（使用统一入口/message）"""
        try:
            response = requests.post(
                f"{MAINAGENT_URL}/message",
                json={
                    # 不指定type，由服务端根据字段自动路由
                    "query": content,
                    "user_id": sender_id  # 传递用户ID
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()

                # 更新对话历史
                # self.conversation_history = result.get("conversation_history")

                status = result.get("status")
                answer = result.get("answer")
                error = result.get("error")
                function_called = result.get("function_called")

                if error:
                    print(f"❌ 错误: {error}")
                elif answer:
                    print(f"🤖 助手回复:\n")
                    print(f"  {answer}")

                    if function_called:
                        print(
                            f"\n📋 调用的工具: {', '.join(function_called) if isinstance(function_called, list) else function_called}")
                else:
                    print(f"状态: {status}")

                # 拿问题发送的用户b的企微 需要用户b的手机号
                send_res = send_text_message(sender_id, answer)
                # {
                #   "errcode" : 0,
                #   "errmsg" : "ok",
                #   "invaliduser" : "userid1|userid2",
                #   "invalidparty" : "partyid1|partyid2",
                #   "invalidtag": "tagid1|tagid2",
                #   "unlicenseduser" : "userid3|userid4",
                #   "msgid": "xxxx",
                #   "response_code": "xyzxyz"
                # }
                # 如果部分接收人无权限或不存在，发送仍然执行，
                # 但会返回无效的部分（即invaliduser或invalidparty或invalidtag或unlicenseduser），
                # 常见的原因是接收人不在应用的可见范围内。

                if send_res.get("errcode") != 0:
                    print(f"联系员工失败: errcode={send_res.get('errcode')}，errmsg={send_res.get('errmsg', '未知错误')}")
                    print("\n排查建议:")
                    print("1. errcode=60020：确认服务器公网IP已加入企业微信应用 IP 白名单")
                    print("2. errcode=40001：检查 CORP_ID 与 SECRET 是否正确")
                    print("3. errcode=40002：检查 AGENT_ID 是否正确")
                    print("4. 检查到 qyapi.weixin.qq.com 的网络连通性")
            else:
                print(f"请求失败: HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            print("请求超时")
        except requests.exceptions.ConnectionError:
            print("无法连接到主agent服务")
        except Exception as e:
            print(str(e))

        print(f"Text message content: {content}")

        # Example: Handle specific commands
        if content.lower() == "help":
            # In a real implementation, you might send a response back
            print("Help command received")
        elif content.lower() == "status":
            print("Status request received")

    elif message_type == "image":
        media_id = message_data.get('MediaId', '')
        print(f"Image message with media ID: {media_id}")

    elif message_type == "voice":
        media_id = message_data.get('MediaId', '')
        format_type = message_data.get('Format', '')
        print(f"Voice message with media ID: {media_id}, format: {format_type}")

    elif message_type == "video":
        media_id = message_data.get('MediaId', '')
        thumb_media_id = message_data.get('ThumbMediaId', '')
        print(f"Video message with media ID: {media_id}, thumb media ID: {thumb_media_id}")

    elif message_type == "location":
        location_x = message_data.get('Location_X', '')
        location_y = message_data.get('Location_Y', '')
        scale = message_data.get('Scale', '')
        label = message_data.get('Label', '')
        print(f"Location message: {label} ({location_x}, {location_y}), scale: {scale}")

    elif message_type == "link":
        title = message_data.get('Title', '')
        description = message_data.get('Description', '')
        url = message_data.get('Url', '')
        print(f"Link message: {title} - {description}, URL: {url}")

    else:
        print(f"Unhandled message type: {message_type}")


if __name__ == '__main__':
    # Run the Flask app for testing
    app.run(host='0.0.0.0', port=8081, debug=True)
