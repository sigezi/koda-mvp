"""
记忆客户端模块

提供与Supabase数据库交互的功能，包括记忆的CRUD操作。
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from supabase import Client

from utils.types import MemoryFragment, MemoryContext, ConversationMemory, EmotionType
from utils.errors import handle_error, DatabaseError
from utils.connection import initialize_clients

# 获取 Supabase 客户端
supabase: Client = initialize_clients()

def get_memories(
    pet_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[MemoryFragment]:
    """
    获取宠物的记忆列表
    
    Args:
        pet_id: 宠物ID
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        记忆列表
    """
    try:
        query = supabase.table("memories").select("*").eq("pet_id", pet_id)
        
        if start_date:
            query = query.gte("timestamp", start_date.isoformat())
        if end_date:
            query = query.lte("timestamp", end_date.isoformat())
        
        response = query.execute()
        
        if response.error:
            raise DatabaseError(f"获取记忆失败: {response.error.message}")
        
        return [
            MemoryFragment(
                id=record["id"],
                pet_id=record["pet_id"],
                content=record["content"],
                timestamp=datetime.fromisoformat(record["timestamp"]),
                emotion=EmotionType(record["emotion"]),
                importance=record["importance"],
                context=MemoryContext(record["context"]),
                references=record.get("references", [])
            )
            for record in response.data
        ]
    except Exception as e:
        raise DatabaseError(f"获取记忆失败: {str(e)}")

def get_conversation_memories(
    pet_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[ConversationMemory]:
    """
    获取宠物的对话记忆列表
    
    Args:
        pet_id: 宠物ID
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        对话记忆列表
    """
    try:
        query = supabase.table("conversation_memories").select("*").eq("pet_id", pet_id)
        
        if start_date:
            query = query.gte("start_time", start_date.isoformat())
        if end_date:
            query = query.lte("end_time", end_date.isoformat())
        
        response = query.execute()
        
        if response.error:
            raise DatabaseError(f"获取对话记忆失败: {response.error.message}")
        
        return [
            ConversationMemory(
                id=record["id"],
                pet_id=record["pet_id"],
                topic=record["topic"],
                start_time=datetime.fromisoformat(record["start_time"]),
                end_time=datetime.fromisoformat(record["end_time"]),
                messages=record["messages"],
                summary=record["summary"],
                key_points=record["key_points"],
                emotions=[EmotionType(e) for e in record["emotions"]],
                fragments=record.get("fragments", [])
            )
            for record in response.data
        ]
    except Exception as e:
        raise DatabaseError(f"获取对话记忆失败: {str(e)}")

def create_memory(
    pet_id: str,
    content: str,
    context: MemoryContext,
    emotion: EmotionType,
    importance: float,
    references: Optional[List[str]] = None
) -> Optional[MemoryFragment]:
    """
    创建新的记忆片段
    
    Args:
        pet_id: 宠物ID
        content: 记忆内容
        context: 记忆上下文
        emotion: 情绪类型
        importance: 重要性
        references: 相关记忆ID列表
    
    Returns:
        创建的记忆片段
    """
    try:
        data = {
            "pet_id": pet_id,
            "content": content,
            "context": context.value,
            "emotion": emotion.value,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
            "references": references or []
        }
        
        response = supabase.table("memories").insert(data).execute()
        
        if response.error:
            raise DatabaseError(f"创建记忆失败: {response.error.message}")
        
        if not response.data:
            return None
        
        record = response.data[0]
        return MemoryFragment(
            id=record["id"],
            pet_id=record["pet_id"],
            content=record["content"],
            timestamp=datetime.fromisoformat(record["timestamp"]),
            emotion=EmotionType(record["emotion"]),
            importance=record["importance"],
            context=MemoryContext(record["context"]),
            references=record.get("references", [])
        )
    except Exception as e:
        raise DatabaseError(f"创建记忆失败: {str(e)}")

def update_memory(
    memory_id: str,
    content: Optional[str] = None,
    context: Optional[MemoryContext] = None,
    emotion: Optional[EmotionType] = None,
    importance: Optional[float] = None,
    references: Optional[List[str]] = None
) -> Optional[MemoryFragment]:
    """
    更新记忆片段
    
    Args:
        memory_id: 记忆ID
        content: 记忆内容
        context: 记忆上下文
        emotion: 情绪类型
        importance: 重要性
        references: 相关记忆ID列表
    
    Returns:
        更新后的记忆片段
    """
    try:
        data = {}
        if content is not None:
            data["content"] = content
        if context is not None:
            data["context"] = context.value
        if emotion is not None:
            data["emotion"] = emotion.value
        if importance is not None:
            data["importance"] = importance
        if references is not None:
            data["references"] = references
        
        if not data:
            return None
        
        response = supabase.table("memories").update(data).eq("id", memory_id).execute()
        
        if response.error:
            raise DatabaseError(f"更新记忆失败: {response.error.message}")
        
        if not response.data:
            return None
        
        record = response.data[0]
        return MemoryFragment(
            id=record["id"],
            pet_id=record["pet_id"],
            content=record["content"],
            timestamp=datetime.fromisoformat(record["timestamp"]),
            emotion=EmotionType(record["emotion"]),
            importance=record["importance"],
            context=MemoryContext(record["context"]),
            references=record.get("references", [])
        )
    except Exception as e:
        raise DatabaseError(f"更新记忆失败: {str(e)}")

def delete_memory(memory_id: str) -> bool:
    """
    删除记忆片段
    
    Args:
        memory_id: 记忆ID
    
    Returns:
        是否删除成功
    """
    try:
        response = supabase.table("memories").delete().eq("id", memory_id).execute()
        
        if response.error:
            raise DatabaseError(f"删除记忆失败: {response.error.message}")
        
        return bool(response.data)
    except Exception as e:
        raise DatabaseError(f"删除记忆失败: {str(e)}")

def create_conversation_memory(
    pet_id: str,
    topic: str,
    messages: List[Dict[str, str]],
    summary: str,
    key_points: List[str],
    emotions: List[EmotionType],
    fragments: Optional[List[str]] = None
) -> Optional[ConversationMemory]:
    """
    创建新的对话记忆
    
    Args:
        pet_id: 宠物ID
        topic: 对话主题
        messages: 对话消息列表
        summary: 对话摘要
        key_points: 关键点列表
        emotions: 情绪类型列表
        fragments: 相关记忆片段ID列表
    
    Returns:
        创建的对话记忆
    """
    try:
        data = {
            "pet_id": pet_id,
            "topic": topic,
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "messages": messages,
            "summary": summary,
            "key_points": key_points,
            "emotions": [e.value for e in emotions],
            "fragments": fragments or []
        }
        
        response = supabase.table("conversation_memories").insert(data).execute()
        
        if response.error:
            raise DatabaseError(f"创建对话记忆失败: {response.error.message}")
        
        if not response.data:
            return None
        
        record = response.data[0]
        return ConversationMemory(
            id=record["id"],
            pet_id=record["pet_id"],
            topic=record["topic"],
            start_time=datetime.fromisoformat(record["start_time"]),
            end_time=datetime.fromisoformat(record["end_time"]),
            messages=record["messages"],
            summary=record["summary"],
            key_points=record["key_points"],
            emotions=[EmotionType(e) for e in record["emotions"]],
            fragments=record.get("fragments", [])
        )
    except Exception as e:
        raise DatabaseError(f"创建对话记忆失败: {str(e)}")

def update_conversation_memory(
    memory_id: str,
    topic: Optional[str] = None,
    messages: Optional[List[Dict[str, str]]] = None,
    summary: Optional[str] = None,
    key_points: Optional[List[str]] = None,
    emotions: Optional[List[EmotionType]] = None,
    fragments: Optional[List[str]] = None
) -> Optional[ConversationMemory]:
    """
    更新对话记忆
    
    Args:
        memory_id: 记忆ID
        topic: 对话主题
        messages: 对话消息列表
        summary: 对话摘要
        key_points: 关键点列表
        emotions: 情绪类型列表
        fragments: 相关记忆片段ID列表
    
    Returns:
        更新后的对话记忆
    """
    try:
        data = {}
        if topic is not None:
            data["topic"] = topic
        if messages is not None:
            data["messages"] = messages
        if summary is not None:
            data["summary"] = summary
        if key_points is not None:
            data["key_points"] = key_points
        if emotions is not None:
            data["emotions"] = [e.value for e in emotions]
        if fragments is not None:
            data["fragments"] = fragments
        
        if not data:
            return None
        
        response = supabase.table("conversation_memories").update(data).eq("id", memory_id).execute()
        
        if response.error:
            raise DatabaseError(f"更新对话记忆失败: {response.error.message}")
        
        if not response.data:
            return None
        
        record = response.data[0]
        return ConversationMemory(
            id=record["id"],
            pet_id=record["pet_id"],
            topic=record["topic"],
            start_time=datetime.fromisoformat(record["start_time"]),
            end_time=datetime.fromisoformat(record["end_time"]),
            messages=record["messages"],
            summary=record["summary"],
            key_points=record["key_points"],
            emotions=[EmotionType(e) for e in record["emotions"]],
            fragments=record.get("fragments", [])
        )
    except Exception as e:
        raise DatabaseError(f"更新对话记忆失败: {str(e)}")

def delete_conversation_memory(memory_id: str) -> bool:
    """
    删除对话记忆
    
    Args:
        memory_id: 记忆ID
    
    Returns:
        是否删除成功
    """
    try:
        response = supabase.table("conversation_memories").delete().eq("id", memory_id).execute()
        
        if response.error:
            raise DatabaseError(f"删除对话记忆失败: {response.error.message}")
        
        return bool(response.data)
    except Exception as e:
        raise DatabaseError(f"删除对话记忆失败: {str(e)}") 