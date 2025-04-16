"""
OpenAI 客户端模块

此模块提供了与 OpenAI API 交互的功能。
包括聊天生成、情绪分析和日志分析。
"""

from typing import Optional, List, Dict, Any
from openai import OpenAI
from datetime import datetime

from .config import OPENAI_API_KEY, OPENAI_MODEL
from .errors import OpenAIRequestError
from .types import ChatMessage, AIContext, EmotionType, LogType

# 全局 OpenAI 客户端实例
_openai_client: Optional[OpenAI] = None

def get_openai_client() -> OpenAI:
    """
    获取 OpenAI 客户端实例
    
    Returns:
        OpenAI: OpenAI 客户端实例
        
    Raises:
        OpenAIRequestError: 当无法初始化客户端时抛出
    """
    global _openai_client
    
    if _openai_client is None:
        try:
            if not OPENAI_API_KEY:
                raise OpenAIRequestError("缺少 OpenAI API 密钥")
                
            _openai_client = OpenAI(api_key=OPENAI_API_KEY)
            
        except Exception as e:
            raise OpenAIRequestError(details=str(e))
            
    return _openai_client

def get_chat_response(messages: List[Dict[str, str]], context: Optional[AIContext] = None) -> str:
    """
    生成聊天回复
    
    Args:
        messages: 聊天消息历史
        context: 可选的 AI 上下文信息
        
    Returns:
        str: 生成的回复内容
        
    Raises:
        OpenAIRequestError: 当请求失败时抛出
    """
    try:
        # 构建系统提示
        system_prompt = build_system_prompt(context) if context else "你是一个温柔、专业的宠物助手。"
        
        # 添加系统消息
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        # 调用 API
        response = get_openai_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=full_messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        raise OpenAIRequestError("生成回复失败", str(e))

def analyze_emotion(text: str) -> tuple[float, EmotionType]:
    """
    分析文本情感
    
    Args:
        text: 待分析的文本
        
    Returns:
        tuple[float, EmotionType]: (情感值, 情绪类型)
        
    Raises:
        OpenAIRequestError: 当分析失败时抛出
    """
    try:
        prompt = f"""
        分析以下文本的情感倾向和情绪类型：
        
        文本：{text}
        
        请以 JSON 格式返回：
        {{
            "sentiment": -1到1之间的浮点数,
            "emotion": "happy/excited/calm/anxious/sad/angry/neutral"
        }}
        """
        
        response = get_openai_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        
        # 解析响应
        result = eval(response.choices[0].message.content)
        return result["sentiment"], EmotionType(result["emotion"])
        
    except Exception as e:
        raise OpenAIRequestError("情感分析失败", str(e))

def analyze_log(log_type: LogType, content: str) -> str:
    """
    分析日志内容
    
    Args:
        log_type: 日志类型
        content: 日志内容
        
    Returns:
        str: AI 分析结果
        
    Raises:
        OpenAIRequestError: 当分析失败时抛出
    """
    try:
        prompt = f"""
        作为宠物健康顾问，请分析以下{log_type.value}记录：
        
        内容：{content}
        
        请提供：
        1. 简要分析
        2. 可能的原因
        3. 建议采取的措施
        """
        
        response = get_openai_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        raise OpenAIRequestError("日志分析失败", str(e))

def build_system_prompt(context: AIContext) -> str:
    """
    构建系统提示
    
    Args:
        context: AI 上下文信息
        
    Returns:
        str: 构建的系统提示
    """
    pet = context["pet_profile"]
    recent_logs = context["recent_logs"]
    current_emotion = context["current_emotion"]
    
    prompt = f"""
    你是 Koda，一个温柔、专业的宠物助手。你正在与{pet['name']}的主人对话。
    
    宠物信息：
    - 名字：{pet['name']}
    - 品种：{pet['breed']}
    - 年龄：{pet['age']}岁
    - 体重：{pet['weight']}kg
    
    最近状态：
    """
    
    if recent_logs:
        prompt += "\n最近的记录："
        for log in recent_logs[:3]:  # 只显示最近3条
            prompt += f"\n- {log['date']}: {log['content']}"
            
    if current_emotion:
        prompt += f"\n\n当前情绪：{current_emotion.value}"
        
    prompt += """
    
    请以温柔、专业的语气与主人交流，提供有价值的建议和关心。
    """
    
    return prompt 