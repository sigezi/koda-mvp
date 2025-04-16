"""
对话记忆管理模块

此模块负责管理对话记忆，包括：
- 长期记忆存储
- 短期记忆缓存
- 记忆检索与关联
- 记忆生成与更新
"""

from typing import List, Dict, Any, Optional, TypedDict, Set
from datetime import datetime, timedelta
import json
from collections import defaultdict
import numpy as np
from scipy import stats

from .types import PetProfile, LogEntry, EmotionType, ChatMessage
from .errors import handle_error

class MemoryFragment(TypedDict):
    """记忆片段数据结构"""
    content: str           # 记忆内容
    timestamp: str        # 创建时间
    emotion: Optional[str] # 关联情绪
    importance: float     # 重要性分数
    context: Dict[str, Any]  # 上下文信息
    references: Set[str]   # 关联引用

class ConversationMemory(TypedDict):
    """对话记忆数据结构"""
    topic: str            # 对话主题
    start_time: str       # 开始时间
    end_time: Optional[str]  # 结束时间
    messages: List[Dict[str, Any]]  # 消息列表
    summary: str          # 对话摘要
    key_points: List[str]  # 关键点
    emotions: Dict[str, Any]  # 情绪统计
    fragments: List[MemoryFragment]  # 记忆片段

class MemoryIndex(TypedDict):
    """记忆索引数据结构"""
    timestamp: str        # 索引时间
    keywords: Set[str]    # 关键词集合
    emotion_tags: Set[str]  # 情绪标签
    importance: float     # 重要性分数
    memory_id: str        # 记忆ID

def create_memory_fragment(
    content: str,
    context: Dict[str, Any],
    emotion: Optional[EmotionType] = None,
    references: Optional[Set[str]] = None
) -> MemoryFragment:
    """
    创建记忆片段
    
    Args:
        content: 记忆内容
        context: 上下文信息
        emotion: 关联情绪
        references: 关联引用
        
    Returns:
        MemoryFragment: 记忆片段
    """
    try:
        # 计算重要性分数
        importance = calculate_importance(content, context, emotion)
        
        return {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "emotion": emotion.value if emotion else None,
            "importance": importance,
            "context": context,
            "references": references or set()
        }
    except Exception as e:
        handle_error(e)
        return {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "emotion": None,
            "importance": 0.5,
            "context": {},
            "references": set()
        }

def create_conversation_memory(
    messages: List[Dict[str, Any]],
    topic: str,
    start_time: str,
    end_time: Optional[str] = None
) -> ConversationMemory:
    """
    创建对话记忆
    
    Args:
        messages: 消息列表
        topic: 对话主题
        start_time: 开始时间
        end_time: 结束时间
        
    Returns:
        ConversationMemory: 对话记忆
    """
    try:
        # 生成对话摘要
        summary = generate_conversation_summary(messages)
        
        # 提取关键点
        key_points = extract_key_points(messages)
        
        # 分析情绪
        emotions = analyze_conversation_emotions(messages)
        
        # 生成记忆片段
        fragments = generate_memory_fragments(messages, topic)
        
        return {
            "topic": topic,
            "start_time": start_time,
            "end_time": end_time,
            "messages": messages,
            "summary": summary,
            "key_points": key_points,
            "emotions": emotions,
            "fragments": fragments
        }
    except Exception as e:
        handle_error(e)
        return {
            "topic": topic,
            "start_time": start_time,
            "end_time": end_time,
            "messages": messages,
            "summary": "对话记录",
            "key_points": [],
            "emotions": {},
            "fragments": []
        }

def calculate_importance(
    content: str,
    context: Dict[str, Any],
    emotion: Optional[EmotionType]
) -> float:
    """
    计算记忆重要性分数
    
    Args:
        content: 记忆内容
        context: 上下文信息
        emotion: 关联情绪
        
    Returns:
        float: 重要性分数 (0-1)
    """
    try:
        score = 0.5  # 基础分数
        
        # 情感强度影响
        if emotion:
            sentiment = context.get("sentiment", 0)
            score += abs(sentiment) * 0.2  # 情感越强烈越重要
        
        # 关键词影响
        important_keywords = {
            "第一次", "生病", "手术", "事故", "成长",
            "里程碑", "变化", "异常", "重要", "特殊"
        }
        keyword_matches = sum(1 for word in important_keywords if word in content)
        score += keyword_matches * 0.1  # 每个关键词增加0.1分
        
        # 时间衰减
        days_passed = (
            datetime.now() - 
            datetime.fromisoformat(context.get("timestamp", datetime.now().isoformat()))
        ).days
        time_decay = np.exp(-days_passed / 365)  # 一年的指数衰减
        score *= time_decay
        
        return min(1.0, max(0.0, score))  # 确保分数在0-1之间
        
    except Exception as e:
        handle_error(e)
        return 0.5

def generate_conversation_summary(messages: List[Dict[str, Any]]) -> str:
    """
    生成对话摘要
    
    Args:
        messages: 消息列表
        
    Returns:
        str: 对话摘要
    """
    try:
        # 提取所有消息内容
        content = "\n".join([msg["content"] for msg in messages])
        
        # 构建摘要提示
        summary_prompt = f"""
        请用一句话总结以下对话的主要内容（不超过50个字）：
        
        {content}
        
        只返回总结，不要有其他文字。
        """
        
        # 调用OpenAI API
        response = st.session_state.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.5,
            max_tokens=100
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        handle_error(e)
        return "对话记录"

def extract_key_points(messages: List[Dict[str, Any]]) -> List[str]:
    """
    提取对话关键点
    
    Args:
        messages: 消息列表
        
    Returns:
        List[str]: 关键点列表
    """
    try:
        # 提取所有消息内容
        content = "\n".join([msg["content"] for msg in messages])
        
        # 构建关键点提取提示
        key_points_prompt = f"""
        请从以下对话中提取3-5个关键信息点（每点不超过20字）：
        
        {content}
        
        请用JSON数组格式返回，只包含关键点文本，不要有其他内容。
        """
        
        # 调用OpenAI API
        response = st.session_state.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": key_points_prompt}],
            temperature=0.5,
            max_tokens=200
        )
        
        # 解析JSON响应
        key_points = json.loads(response.choices[0].message.content.strip())
        return key_points
        
    except Exception as e:
        handle_error(e)
        return []

def analyze_conversation_emotions(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析对话情绪
    
    Args:
        messages: 消息列表
        
    Returns:
        Dict[str, Any]: 情绪分析结果
    """
    try:
        emotions = []
        sentiments = []
        
        # 收集情绪数据
        for msg in messages:
            if "emotion" in msg:
                emotions.append(msg["emotion"])
            if "sentiment" in msg:
                sentiments.append(msg["sentiment"])
        
        # 计算情绪统计
        emotion_stats = {
            "main_emotion": max(set(emotions), key=emotions.count) if emotions else None,
            "avg_sentiment": sum(sentiments) / len(sentiments) if sentiments else 0.0,
            "emotion_counts": {e: emotions.count(e) for e in set(emotions)} if emotions else {},
            "sentiment_range": (min(sentiments), max(sentiments)) if sentiments else (0.0, 0.0),
            "sentiment_std": np.std(sentiments) if sentiments else 0.0
        }
        
        return emotion_stats
        
    except Exception as e:
        handle_error(e)
        return {
            "main_emotion": None,
            "avg_sentiment": 0.0,
            "emotion_counts": {},
            "sentiment_range": (0.0, 0.0),
            "sentiment_std": 0.0
        }

def generate_memory_fragments(
    messages: List[Dict[str, Any]],
    topic: str
) -> List[MemoryFragment]:
    """
    从对话生成记忆片段
    
    Args:
        messages: 消息列表
        topic: 对话主题
        
    Returns:
        List[MemoryFragment]: 记忆片段列表
    """
    try:
        fragments = []
        
        # 按时间顺序处理消息
        for i, msg in enumerate(messages):
            # 获取上下文
            context = {
                "topic": topic,
                "timestamp": msg.get("timestamp", datetime.now().isoformat()),
                "position": i,
                "total_messages": len(messages),
                "sentiment": msg.get("sentiment", 0.0)
            }
            
            # 创建记忆片段
            fragment = create_memory_fragment(
                content=msg["content"],
                context=context,
                emotion=msg.get("emotion"),
                references=set([msg.get("id", str(i))])
            )
            
            fragments.append(fragment)
        
        # 按重要性排序
        fragments.sort(key=lambda x: x["importance"], reverse=True)
        
        return fragments[:5]  # 只保留最重要的5个片段
        
    except Exception as e:
        handle_error(e)
        return []

def create_memory_index(memory: MemoryFragment) -> MemoryIndex:
    """
    创建记忆索引
    
    Args:
        memory: 记忆片段
        
    Returns:
        MemoryIndex: 记忆索引
    """
    try:
        # 提取关键词
        keywords = extract_keywords(memory["content"])
        
        # 提取情绪标签
        emotion_tags = set()
        if memory["emotion"]:
            emotion_tags.add(memory["emotion"])
        
        return {
            "timestamp": memory["timestamp"],
            "keywords": keywords,
            "emotion_tags": emotion_tags,
            "importance": memory["importance"],
            "memory_id": str(hash(memory["content"]))
        }
        
    except Exception as e:
        handle_error(e)
        return {
            "timestamp": datetime.now().isoformat(),
            "keywords": set(),
            "emotion_tags": set(),
            "importance": 0.0,
            "memory_id": ""
        }

def extract_keywords(text: str) -> Set[str]:
    """
    提取文本关键词
    
    Args:
        text: 输入文本
        
    Returns:
        Set[str]: 关键词集合
    """
    try:
        # 构建关键词提取提示
        keyword_prompt = f"""
        请从以下文本中提取3-5个关键词（每个词不超过4个字）：
        
        {text}
        
        请用JSON数组格式返回，只包含关键词，不要有其他内容。
        """
        
        # 调用OpenAI API
        response = st.session_state.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": keyword_prompt}],
            temperature=0.5,
            max_tokens=100
        )
        
        # 解析JSON响应
        keywords = set(json.loads(response.choices[0].message.content.strip()))
        return keywords
        
    except Exception as e:
        handle_error(e)
        return set()

def retrieve_relevant_memories(
    query: str,
    memories: List[MemoryFragment],
    top_k: int = 3
) -> List[MemoryFragment]:
    """
    检索相关记忆
    
    Args:
        query: 查询文本
        memories: 记忆片段列表
        top_k: 返回数量
        
    Returns:
        List[MemoryFragment]: 相关记忆列表
    """
    try:
        # 提取查询关键词
        query_keywords = extract_keywords(query)
        
        # 计算相关性分数
        scored_memories = []
        for memory in memories:
            # 关键词匹配分数
            memory_keywords = extract_keywords(memory["content"])
            keyword_score = len(query_keywords & memory_keywords) / max(len(query_keywords), 1)
            
            # 时间衰减
            days_passed = (
                datetime.now() - 
                datetime.fromisoformat(memory["timestamp"])
            ).days
            time_score = np.exp(-days_passed / 365)
            
            # 重要性加权
            final_score = (
                keyword_score * 0.4 +  # 关键词匹配权重
                time_score * 0.3 +    # 时间衰减权重
                memory["importance"] * 0.3  # 重要性权重
            )
            
            scored_memories.append((memory, final_score))
        
        # 按分数排序
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # 返回top_k个记忆
        return [memory for memory, _ in scored_memories[:top_k]]
        
    except Exception as e:
        handle_error(e)
        return []

def merge_memory_fragments(
    fragments: List[MemoryFragment],
    max_length: int = 500
) -> str:
    """
    合并记忆片段
    
    Args:
        fragments: 记忆片段列表
        max_length: 最大长度
        
    Returns:
        str: 合并后的记忆文本
    """
    try:
        if not fragments:
            return ""
        
        # 按时间排序
        sorted_fragments = sorted(fragments, key=lambda x: x["timestamp"])
        
        # 构建合并提示
        merge_prompt = f"""
        请将以下记忆片段合并为一段连贯的叙述（不超过{max_length}字）：
        
        {chr(10).join(f'- {f["content"]}' for f in sorted_fragments)}
        
        只返回合并后的文本，不要有其他内容。
        """
        
        # 调用OpenAI API
        response = st.session_state.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": merge_prompt}],
            temperature=0.7,
            max_tokens=max_length
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        handle_error(e)
        return "记忆合并失败"

def update_memory_importance(
    memory: MemoryFragment,
    interaction_count: int,
    emotional_impact: float
) -> MemoryFragment:
    """
    更新记忆重要性
    
    Args:
        memory: 记忆片段
        interaction_count: 交互次数
        emotional_impact: 情感影响强度
        
    Returns:
        MemoryFragment: 更新后的记忆片段
    """
    try:
        # 基础重要性
        base_importance = memory["importance"]
        
        # 交互频率影响
        interaction_factor = min(interaction_count / 10, 1.0)  # 最多提升0.2
        
        # 情感影响
        emotion_factor = min(abs(emotional_impact), 1.0)  # 最多提升0.3
        
        # 计算新的重要性分数
        new_importance = base_importance * 0.5 + interaction_factor * 0.2 + emotion_factor * 0.3
        
        # 更新记忆片段
        updated_memory = memory.copy()
        updated_memory["importance"] = min(1.0, max(0.0, new_importance))
        
        return updated_memory
        
    except Exception as e:
        handle_error(e)
        return memory

def cleanup_old_memories(
    memories: List[MemoryFragment],
    max_age_days: int = 365,
    min_importance: float = 0.3
) -> List[MemoryFragment]:
    """
    清理旧记忆
    
    Args:
        memories: 记忆片段列表
        max_age_days: 最大保留天数
        min_importance: 最小重要性阈值
        
    Returns:
        List[MemoryFragment]: 清理后的记忆列表
    """
    try:
        current_time = datetime.now()
        cleaned_memories = []
        
        for memory in memories:
            # 计算记忆年龄
            memory_time = datetime.fromisoformat(memory["timestamp"])
            age_days = (current_time - memory_time).days
            
            # 检查是否保留
            if age_days <= max_age_days or memory["importance"] >= min_importance:
                cleaned_memories.append(memory)
        
        return cleaned_memories
        
    except Exception as e:
        handle_error(e)
        return memories 