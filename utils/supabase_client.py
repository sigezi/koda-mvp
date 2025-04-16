"""
Supabase 客户端模块

此模块封装了与 Supabase 数据库的所有交互，包括：
- 宠物档案管理
- 日志记录
- 记忆存储
- 数据查询
"""

from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from datetime import datetime, timedelta
import uuid

from .config import SUPABASE_URL, SUPABASE_KEY
from .errors import SupabaseConnectionError, SupabaseQueryError, DatabaseError
from .types import PetProfile, LogEntry, MemoryFragment, ConversationMemory, MemoryIndex, LogType

# 全局 Supabase 客户端实例
_supabase_client: Optional[Client] = None

def get_supabase() -> Client:
    """
    获取 Supabase 客户端实例
    
    Returns:
        Client: Supabase 客户端实例
        
    Raises:
        SupabaseConnectionError: 当无法连接到 Supabase 时抛出
    """
    global _supabase_client
    
    if _supabase_client is None:
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                raise SupabaseConnectionError("缺少 Supabase 配置")
                
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
        except Exception as e:
            raise SupabaseConnectionError(details=str(e))
            
    return _supabase_client

def get_pet_profiles(user_id: str) -> List[PetProfile]:
    """
    获取用户的所有宠物档案
    
    Args:
        user_id: 用户ID
        
    Returns:
        List[PetProfile]: 宠物档案列表
        
    Raises:
        SupabaseQueryError: 当查询失败时抛出
    """
    try:
        response = get_supabase().table("pets").select("*").eq("user_id", user_id).execute()
        return response.data
    except Exception as e:
        raise SupabaseQueryError("获取宠物档案失败", str(e))

def get_pet_logs(pet_id: str, log_type: Optional[LogType] = None) -> List[LogEntry]:
    """
    获取宠物的日志记录
    
    Args:
        pet_id: 宠物ID
        log_type: 可选的日志类型过滤
        
    Returns:
        List[LogEntry]: 日志记录列表
        
    Raises:
        SupabaseQueryError: 当查询失败时抛出
    """
    try:
        query = get_supabase().table("logs").select("*").eq("pet_id", pet_id)
        
        if log_type:
            query = query.eq("log_type", log_type.value)
            
        response = query.order("date", desc=True).execute()
        return response.data
    except Exception as e:
        raise SupabaseQueryError("获取日志记录失败", str(e))

def create_log_entry(log_data: Dict[str, Any]) -> LogEntry:
    """
    创建新的日志记录
    
    Args:
        log_data: 日志数据字典
        
    Returns:
        LogEntry: 创建的日志记录
        
    Raises:
        SupabaseQueryError: 当创建失败时抛出
    """
    try:
        # 添加时间戳
        log_data["created_at"] = datetime.now().isoformat()
        log_data["updated_at"] = log_data["created_at"]
        
        response = get_supabase().table("logs").insert(log_data).execute()
        return response.data[0]
    except Exception as e:
        raise SupabaseQueryError("创建日志记录失败", str(e))

def update_pet_profile(pet_id: str, profile_data: Dict[str, Any]) -> PetProfile:
    """
    更新宠物档案
    
    Args:
        pet_id: 宠物ID
        profile_data: 更新的档案数据
        
    Returns:
        PetProfile: 更新后的宠物档案
        
    Raises:
        SupabaseQueryError: 当更新失败时抛出
    """
    try:
        # 添加更新时间戳
        profile_data["updated_at"] = datetime.now().isoformat()
        
        response = get_supabase().table("pets").update(profile_data).eq("id", pet_id).execute()
        return response.data[0]
    except Exception as e:
        raise SupabaseQueryError("更新宠物档案失败", str(e))

def get_emotion_logs_last_7days(pet_id: str) -> List[Dict[str, Any]]:
    """
    获取宠物过去7天的情绪日志数据
    
    Args:
        pet_id: 宠物ID
        
    Returns:
        List[Dict[str, Any]]: 情绪日志列表，按日期分组
        
    Raises:
        SupabaseQueryError: 当查询失败时抛出
    """
    try:
        # 计算7天前的日期
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        # 构建查询
        query = get_supabase().table("logs").select("*").eq("pet_id", pet_id).eq("log_type", LogType.MOOD.value)
        query = query.gte("date", seven_days_ago).order("date")
        
        # 执行查询
        response = query.execute()
        
        if not response.data:
            return []
            
        # 按日期分组
        logs_by_date = {}
        for log in response.data:
            date = log["date"][:10]  # 只取日期部分
            if date not in logs_by_date:
                logs_by_date[date] = []
            logs_by_date[date].append(log)
            
        # 转换为列表格式
        result = []
        for date, logs in logs_by_date.items():
            # 计算当天的平均情绪值
            sentiments = [log["sentiment"] for log in logs if log["sentiment"] is not None]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            
            # 统计情绪类型
            emotion_counts = {}
            for log in logs:
                if log["emotion_type"]:
                    emotion_counts[log["emotion_type"]] = emotion_counts.get(log["emotion_type"], 0) + 1
            
            # 获取主要情绪
            main_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else None
            
            result.append({
                "date": date,
                "logs": logs,
                "avg_sentiment": avg_sentiment,
                "main_emotion": main_emotion,
                "emotion_counts": emotion_counts
            })
            
        return result
        
    except Exception as e:
        raise SupabaseQueryError("获取情绪日志失败", str(e))

def create_memory_fragment(
    content: str,
    emotion: Optional[str] = None,
    importance: float = 0.5,
    context: Optional[str] = None,
    references: Optional[List[str]] = None
) -> MemoryFragment:
    """
    创建记忆片段
    
    Args:
        content: 记忆内容
        emotion: 情绪类型
        importance: 重要性（0-1）
        context: 上下文信息
        references: 相关记忆ID列表
        
    Returns:
        MemoryFragment: 创建的记忆片段
    """
    try:
        memory_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        memory = {
            "id": memory_id,
            "content": content,
            "timestamp": timestamp,
            "emotion": emotion,
            "importance": importance,
            "context": context,
            "references": references or []
        }
        
        # 插入数据库
        result = get_supabase().table("memories").insert(memory).execute()
        
        if not result.data:
            raise DatabaseError("记忆片段创建失败")
            
        return result.data[0]
        
    except Exception as e:
        raise DatabaseError("记忆片段创建失败")

def create_conversation_memory(
    topic: str,
    messages: List[Dict[str, str]],
    summary: str,
    key_points: List[str],
    emotions: List[str],
    fragments: List[MemoryFragment]
) -> ConversationMemory:
    """
    创建对话记忆
    
    Args:
        topic: 对话主题
        messages: 消息列表
        summary: 对话总结
        key_points: 关键点列表
        emotions: 情绪列表
        fragments: 记忆片段列表
        
    Returns:
        ConversationMemory: 创建的对话记忆
    """
    try:
        memory_id = str(uuid.uuid4())
        start_time = datetime.now().isoformat()
        
        memory = {
            "id": memory_id,
            "topic": topic,
            "start_time": start_time,
            "end_time": start_time,
            "messages": messages,
            "summary": summary,
            "key_points": key_points,
            "emotions": emotions,
            "fragments": [f["id"] for f in fragments]
        }
        
        # 插入数据库
        result = get_supabase().table("conversation_memories").insert(memory).execute()
        
        if not result.data:
            raise DatabaseError("对话记忆创建失败")
            
        return result.data[0]
        
    except Exception as e:
        raise DatabaseError("对话记忆创建失败")

def create_memory_index(
    memory_id: str,
    keywords: List[str],
    emotion_tags: List[str],
    importance: float
) -> MemoryIndex:
    """
    创建记忆索引
    
    Args:
        memory_id: 记忆ID
        keywords: 关键词列表
        emotion_tags: 情绪标签列表
        importance: 重要性
        
    Returns:
        MemoryIndex: 创建的记忆索引
    """
    try:
        index_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        index = {
            "id": index_id,
            "timestamp": timestamp,
            "keywords": keywords,
            "emotion_tags": emotion_tags,
            "importance": importance,
            "memory_id": memory_id
        }
        
        # 插入数据库
        result = get_supabase().table("memory_indexes").insert(index).execute()
        
        if not result.data:
            raise DatabaseError("记忆索引创建失败")
            
        return result.data[0]
        
    except Exception as e:
        raise DatabaseError("记忆索引创建失败")

def get_memories(
    pet_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_importance: float = 0.0
) -> List[MemoryFragment]:
    """
    获取记忆列表
    
    Args:
        pet_id: 宠物ID
        start_date: 开始日期
        end_date: 结束日期
        min_importance: 最小重要性
        
    Returns:
        List[MemoryFragment]: 记忆列表
    """
    try:
        query = get_supabase().table("memories").select("*")
        
        # 添加过滤条件
        if start_date:
            query = query.gte("timestamp", start_date.isoformat())
        if end_date:
            query = query.lte("timestamp", end_date.isoformat())
        if min_importance > 0:
            query = query.gte("importance", min_importance)
            
        # 执行查询
        result = query.execute()
        
        if not result.data:
            return []
            
        return result.data
        
    except Exception as e:
        raise DatabaseError("获取记忆列表失败")

def get_conversation_memories(
    pet_id: str,
    limit: int = 10
) -> List[ConversationMemory]:
    """
    获取对话记忆列表
    
    Args:
        pet_id: 宠物ID
        limit: 返回数量限制
        
    Returns:
        List[ConversationMemory]: 对话记忆列表
    """
    try:
        result = (
            get_supabase().table("conversation_memories")
            .select("*")
            .eq("pet_id", pet_id)
            .order("start_time", desc=True)
            .limit(limit)
            .execute()
        )
        
        if not result.data:
            return []
            
        return result.data
        
    except Exception as e:
        raise DatabaseError("获取对话记忆列表失败")

def search_memories(
    query: str,
    pet_id: str,
    limit: int = 5
) -> List[MemoryFragment]:
    """
    搜索记忆
    
    Args:
        query: 搜索关键词
        pet_id: 宠物ID
        limit: 返回数量限制
        
    Returns:
        List[MemoryFragment]: 匹配的记忆列表
    """
    try:
        # 先搜索索引
        index_result = (
            get_supabase().table("memory_indexes")
            .select("memory_id")
            .contains("keywords", [query])
            .eq("pet_id", pet_id)
            .order("importance", desc=True)
            .limit(limit)
            .execute()
        )
        
        if not index_result.data:
            return []
            
        # 获取记忆详情
        memory_ids = [index["memory_id"] for index in index_result.data]
        memory_result = (
            get_supabase().table("memories")
            .select("*")
            .in_("id", memory_ids)
            .execute()
        )
        
        if not memory_result.data:
            return []
            
        return memory_result.data
        
    except Exception as e:
        raise DatabaseError("搜索记忆失败")

def update_memory_importance(
    memory_id: str,
    new_importance: float
) -> None:
    """
    更新记忆重要性
    
    Args:
        memory_id: 记忆ID
        new_importance: 新的重要性值
    """
    try:
        result = (
            get_supabase().table("memories")
            .update({"importance": new_importance})
            .eq("id", memory_id)
            .execute()
        )
        
        if not result.data:
            raise DatabaseError("记忆重要性更新失败")
            
    except Exception as e:
        raise DatabaseError("记忆重要性更新失败")

def delete_old_memories(
    pet_id: str,
    max_age_days: int,
    min_importance: float
) -> None:
    """
    删除旧记忆
    
    Args:
        pet_id: 宠物ID
        max_age_days: 最大保留天数
        min_importance: 最小重要性阈值
    """
    try:
        cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
        
        result = (
            get_supabase().table("memories")
            .delete()
            .eq("pet_id", pet_id)
            .lt("timestamp", cutoff_date)
            .lt("importance", min_importance)
            .execute()
        )
        
        if not result.data:
            raise DatabaseError("旧记忆删除失败")
            
    except Exception as e:
        raise DatabaseError("旧记忆删除失败") 