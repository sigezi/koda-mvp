"""
Koda AI 类型定义模块

定义系统中使用的各种数据类型。
"""

from typing import TypedDict, List, Optional, Dict, Union
from datetime import datetime
from enum import Enum

class PetProfile(TypedDict):
    """宠物档案类型"""
    id: str
    name: str
    type: str  # 宠物类型（猫/狗等）
    breed: str  # 品种
    gender: str  # 性别
    age: int  # 年龄
    size: str  # 体型
    avatar: str  # 头像URL
    behavior: str  # 行为特征
    diet: str  # 饮食习惯
    created_at: datetime
    updated_at: datetime

class LogType(str, Enum):
    """日志类型枚举"""
    CHAT = "chat"  # 对话日志
    EMOTION = "emotion"  # 情绪日志
    BEHAVIOR = "behavior"  # 行为日志
    HEALTH = "health"  # 健康日志
    DIET = "diet"  # 饮食日志

class EmotionType(Enum):
    """情绪类型"""
    HAPPY = "happy"  # 开心
    SAD = "sad"  # 伤心
    ANGRY = "angry"  # 生气
    FEAR = "fear"  # 害怕
    NEUTRAL = "neutral"  # 平静
    EXCITED = "excited"  # 兴奋
    ANXIOUS = "anxious"  # 焦虑
    RELAXED = "relaxed"  # 放松
    OTHER = "other"  # 其他

class LogEntry(TypedDict):
    """日志条目类型"""
    id: str
    user_id: str
    pet_id: str
    log_type: LogType
    summary: str  # 日志摘要
    content: str  # 详细内容
    date: datetime
    sentiment: float  # 情感值（-1到1）
    emotion_type: str  # 情绪类型
    ai_analysis: str  # AI分析结果
    created_at: datetime
    updated_at: datetime

class ChatMessage(TypedDict):
    """聊天消息类型"""
    id: str  # 消息ID
    user_id: str  # 用户ID
    pet_id: str  # 宠物ID
    role: str  # 角色（user/assistant）
    content: str  # 消息内容
    timestamp: datetime  # 时间戳
    emotion: Optional[EmotionType]  # 情绪类型（可选）
    sentiment: Optional[float]  # 情感值（可选，-1到1）
    ai_analysis: Optional[str]  # AI分析结果（可选）

class MemoryContext(Enum):
    """记忆上下文类型"""
    CHAT = "chat"  # 对话记忆
    BEHAVIOR = "behavior"  # 行为记忆
    EMOTION = "emotion"  # 情绪记忆
    HEALTH = "health"  # 健康记忆
    DIET = "diet"  # 饮食记忆
    OTHER = "other"  # 其他记忆

class MemoryFragment(TypedDict):
    """记忆片段"""
    id: str  # 记忆ID
    pet_id: str  # 宠物ID
    content: str  # 记忆内容
    timestamp: datetime  # 时间戳
    emotion: EmotionType  # 情绪类型
    importance: float  # 重要性（0-1）
    context: MemoryContext  # 上下文类型
    references: List[str]  # 相关记忆引用

class ConversationMemory(TypedDict):
    """对话记忆"""
    id: str  # 记忆ID
    pet_id: str  # 宠物ID
    topic: str  # 对话主题
    start_time: datetime  # 开始时间
    end_time: datetime  # 结束时间
    messages: List[Dict[str, str]]  # 对话消息列表
    summary: str  # 对话摘要
    key_points: List[str]  # 关键点
    emotions: List[EmotionType]  # 情绪变化

class MemoryIndex(TypedDict):
    """记忆索引"""
    id: str  # 索引ID
    memory_id: str  # 记忆ID
    timestamp: datetime  # 时间戳
    keywords: List[str]  # 关键词
    emotion_tags: List[EmotionType]  # 情绪标签
    importance: float  # 重要性
    context: MemoryContext  # 上下文类型

class BehaviorRecommendation(TypedDict):
    """行为建议"""
    id: str  # 建议ID
    pet_id: str  # 宠物ID
    title: str  # 建议标题
    content: str  # 建议内容
    reason: str  # 建议原因
    priority: int  # 优先级（1-5）
    created_at: datetime  # 创建时间
    updated_at: datetime  # 更新时间
    status: str  # 状态（pending/accepted/rejected）
    feedback: Optional[str]  # 反馈 