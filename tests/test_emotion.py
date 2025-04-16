"""
测试情绪识别模块的功能

此模块包含对情绪识别相关功能的测试，包括：
- 中文情绪文本识别
- 情绪类型匹配
- 情绪强度计算
"""

import pytest
from typing import Dict, List, Tuple

from utils.types import EmotionType
from components.emotion_response import detect_emotion

# 情绪关键词映射
EMOTION_KEYWORDS: Dict[EmotionType, List[str]] = {
    EmotionType.HAPPY: ["开心", "快乐", "高兴", "愉快", "兴奋"],
    EmotionType.EXCITED: ["兴奋", "激动", "活跃", "精力充沛"],
    EmotionType.CALM: ["平静", "安静", "放松", "舒适"],
    EmotionType.ANXIOUS: ["焦虑", "紧张", "担心", "不安"],
    EmotionType.SAD: ["伤心", "难过", "沮丧", "失望"],
    EmotionType.ANGRY: ["生气", "愤怒", "烦躁", "不满"],
    EmotionType.NEUTRAL: ["一般", "普通", "正常", "还行"]
}

# 测试用例
TEST_CASES: List[Tuple[str, EmotionType, float]] = [
    ("我好累，最近压力好大", EmotionType.ANXIOUS, -0.6),
    ("今天天气真好，心情愉快", EmotionType.HAPPY, 0.8),
    ("小白今天特别活跃，一直在玩", EmotionType.EXCITED, 0.7),
    ("它看起来很平静，在晒太阳", EmotionType.CALM, 0.3),
    ("不知道为什么，它今天很烦躁", EmotionType.ANGRY, -0.5),
    ("它看起来有点难过，不知道怎么了", EmotionType.SAD, -0.4),
    ("今天状态一般，没什么特别的", EmotionType.NEUTRAL, 0.0)
]

@pytest.mark.asyncio
async def test_detect_emotion_by_keywords():
    """
    测试中文情绪文本识别功能
    
    验证：
    1. 能正确识别中文情绪关键词
    2. 返回正确的情绪类型
    3. 情绪强度值在合理范围内
    """
    for text, expected_emotion, expected_sentiment in TEST_CASES:
        emotion, sentiment = await detect_emotion(text)
        assert emotion == expected_emotion, f"文本 '{text}' 的情绪识别错误"
        assert -1.0 <= sentiment <= 1.0, f"情绪强度值 {sentiment} 超出范围"
        assert abs(sentiment - expected_sentiment) < 0.3, f"情绪强度值 {sentiment} 与预期 {expected_sentiment} 差异过大"

@pytest.mark.asyncio
async def test_detect_emotion_edge_cases():
    """
    测试情绪识别的边界情况
    
    验证：
    1. 空字符串处理
    2. 无情绪关键词的文本
    3. 混合情绪文本
    """
    # 测试空字符串
    emotion, sentiment = await detect_emotion("")
    assert emotion == EmotionType.NEUTRAL
    assert sentiment == 0.0
    
    # 测试无情绪关键词的文本
    emotion, sentiment = await detect_emotion("今天天气是晴天")
    assert emotion == EmotionType.NEUTRAL
    assert abs(sentiment) < 0.1
    
    # 测试混合情绪文本
    emotion, sentiment = await detect_emotion("虽然有点累，但是很开心")
    assert emotion in [EmotionType.HAPPY, EmotionType.ANXIOUS]
    assert -0.5 <= sentiment <= 0.5 