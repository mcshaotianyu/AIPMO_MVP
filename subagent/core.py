"""核心对话逻辑模块"""

import os
import re
from openai import OpenAI
from prompts import SYSTEM_PROMPT_TEMPLATE


def init_client():
    """初始化OpenAI客户端"""
    api_key = os.environ.get('DEEPSEEK_API_KEY', "sk-1e6a5099e785466789ea6243ef517aac")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )


def extract_completed_info(response_text):
    """提取任务完成信息"""
    if '[TASK_COMPLETED]' not in response_text:
        return None
    
    pattern = r'\[TASK_COMPLETED\]\s*(.*?)\s*\[TASK_COMPLETED\]'
    match = re.search(pattern, response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def create_conversation_history(task, person):
    """创建初始对话历史"""
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(task=task, person=person)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "您好，请问想问什么"}  # 模拟问询对象的开场白
    ]


def call_llm(client, conversation_history):
    """调用LLM"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=conversation_history,
        stream=False
    )
    return response.choices[0].message.content

