"""
测试 chat 模块的功能

此模块包含对 chat 相关功能的测试，包括：
- AI 回复生成
- 情绪识别
- 对话上下文管理
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from utils.types import PetProfile, EmotionType, AIContext, ChatMessage
from utils.openai_client import get_chat_response

# 模拟宠物档案数据
MOCK_PET_PROFILE: PetProfile = {
    "id": "pet_001",
    "user_id": "user_001",
    "name": "小白",
    "species": "cat",
    "breed": "英短",
    "age": 2.5,
    "weight": 4.2,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00",
    "avatar_url": "https://example.com/avatar.jpg",
    "description": "一只活泼可爱的英短猫咪"
}

# 模拟聊天消息
MOCK_MESSAGES: List[Dict[str, str]] = [
    {"role": "user", "content": "小白今天心情怎么样？"},
    {"role": "assistant", "content": "小白今天看起来很开心，一直在玩毛线球。"},
    {"role": "user", "content": "太好了！它最近有什么变化吗？"}
]

# 模拟 AI 上下文
MOCK_AI_CONTEXT: AIContext = {
    "pet_profile": MOCK_PET_PROFILE,
    "recent_logs": [],
    "chat_history": [],
    "current_emotion": EmotionType.HAPPY
}

@pytest.mark.asyncio
async def test_generate_ai_response():
    """
    测试 AI 回复生成功能
    
    验证：
    1. 函数能正常生成非空回复
    2. 回复内容与输入上下文相关
    3. 异常处理正常工作
    """
    # 模拟 OpenAI API 响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "小白今天看起来很开心，一直在玩毛线球。它最近体重增加了一点，但整体状态很好。"
    
    with patch("utils.openai_client.get_openai_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_response
        
        # 测试正常情况
        response = await get_chat_response(MOCK_MESSAGES, MOCK_AI_CONTEXT)
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "小白" in response
        
        # 测试异常情况
        mock_client.return_value.chat.completions.create.side_effect = Exception("API 请求失败")
        with pytest.raises(Exception):
            await get_chat_response(MOCK_MESSAGES, MOCK_AI_CONTEXT)

@pytest.mark.asyncio
async def test_generate_ai_response_without_context():
    """
    测试无上下文时的 AI 回复生成
    
    验证：
    1. 函数在没有上下文时也能正常工作
    2. 生成的回复符合基本要求
    """
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "作为宠物助手，我很乐意帮助你。"
    
    with patch("utils.openai_client.get_openai_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_response
        
        response = await get_chat_response(MOCK_MESSAGES)
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0 