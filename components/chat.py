"""
聊天组件

此模块负责渲染 GPT 聊天界面，处理用户输入，并记录交互到 Supabase。
主要功能包括：
- 聊天界面渲染
- 消息处理与发送
- 情绪识别与共情
- 对话记忆与上下文管理
- 日志记录与分析
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Tuple, Union, Set, TypedDict, Literal
from datetime import datetime, timedelta
import json
import re
import random
from openai import OpenAI
from supabase import Client

from utils.types import PetProfile, ChatMessage, LogEntry, LogType, EmotionType
from utils.errors import handle_error, OpenAIRequestError, SupabaseQueryError
from components.emotion_response import detect_emotion, generate_empathetic_response, detect_emotion_by_keywords
from utils.supabase_client import create_log_entry, get_pet_logs

# 【类型定义】
class ConversationTopic(TypedDict):
    """对话主题数据结构"""
    topic: str
    start_time: str
    end_time: Optional[str]
    messages: List[Dict[str, Any]]
    emotion_summary: Dict[str, Any]
    log_types: Set[str]

class StructuredResponse(TypedDict):
    """结构化回复数据结构"""
    empathy: str  # 共情回复
    behavior_suggestion: str  # 行为建议
    memory: str  # 记忆片段
    raw_response: str  # 原始回复

# 【状态管理】
def init_chat_state() -> None:
    """
    初始化聊天相关的会话状态
    包括消息历史、当前宠物、情绪状态等
    """
    state_vars = {
        "messages": [],  # 消息历史
        "current_pet": None,  # 当前选中的宠物
        "chat_input": "",  # 聊天输入
        "last_emotion": None,  # 最近检测到的情绪
        "last_sentiment": None,  # 最近的情感值
        "pet_context": {},  # 宠物上下文信息
        "pet_logs_cache": {},  # 宠物日志缓存
        "suggested_prompts": [],  # 建议的对话提示
        "conversation_thread": [],  # 对话线程
        "conversation_topics": [],  # 对话主题
        "current_topic": None,  # 当前主题
        "voice_recording": None,  # 语音录音
        "transcribed_text": None  # 转录文本
    }
    
    for var, default_value in state_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default_value

# 【宠物选择器】
def render_pet_selector(pet_profiles: List[PetProfile]) -> Optional[PetProfile]:
    """
    渲染宠物选择器并返回选中的宠物
    
    Args:
        pet_profiles: 宠物档案列表
        
    Returns:
        Optional[PetProfile]: 选中的宠物档案
    """
    if not pet_profiles:
        st.info("请先添加一个宠物，然后开始聊天")
        return None
    
    col1, col2 = st.columns([2, 3])
    with col1:
        # 宠物选择器
        pet_options = {f"{pet['name']} ({pet['species']})": pet["id"] for pet in pet_profiles}
        selected_pet_name = st.selectbox(
            "选择宠物", 
            options=list(pet_options.keys()),
            help="选择要对话的宠物"
        )
        selected_pet_id = pet_options[selected_pet_name]
    
    # 获取选中的宠物
    selected_pet = next((pet for pet in pet_profiles if pet["id"] == selected_pet_id), None)
    if not selected_pet:
        st.error("无法找到选中的宠物")
        return None
    
    with col2:
        # 显示宠物简介
        st.caption(f"品种：{selected_pet['breed']}")
        st.caption(f"年龄：{selected_pet['age']}岁")
        if selected_pet.get('description'):
            st.caption(f"简介：{selected_pet['description']}")
    
    return selected_pet

# 【日志缓存】
def get_cached_pet_logs(pet_id: str, log_type: Optional[LogType] = None) -> List[Dict[str, Any]]:
    """
    获取宠物日志，优先使用缓存
    
    Args:
        pet_id: 宠物ID
        log_type: 日志类型
        
    Returns:
        List[Dict[str, Any]]: 宠物日志列表
    """
    cache_key = f"{pet_id}_{log_type.value if log_type else 'all'}"
    
    # 检查缓存是否存在且未过期
    if cache_key in st.session_state.pet_logs_cache:
        cache_time, cache_data = st.session_state.pet_logs_cache[cache_key]
        if datetime.now() - cache_time < timedelta(hours=1):
            return cache_data
    
    try:
        logs = get_pet_logs(pet_id, log_type)
        st.session_state.pet_logs_cache[cache_key] = (datetime.now(), logs)
        return logs
    except Exception as e:
        handle_error(e)
        return []

# 【宠物习惯分析】
def estimate_pet_routine(pet: PetProfile, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    根据宠物档案和日志估计宠物的日常习惯
    
    Args:
        pet: 宠物档案
        logs: 宠物日志列表
        
    Returns:
        Dict[str, Any]: 宠物日常习惯
    """
    # 基础习惯模板
    routine = {
        "wake_time": "早上7点",
        "sleep_time": "晚上10点",
        "meal_times": ["早上8点", "下午6点"],
        "walk_times": ["早上8:30", "晚上7点"],
        "play_times": ["下午4点"],
        "favorite_activities": [],
        "favorite_foods": [],
        "dislikes": []
    }
    
    # 根据品种调整习惯
    species_routines = {
        "猫": {
            "wake_time": "早上6点",
            "sleep_time": "晚上11点",
            "meal_times": ["早上7点", "晚上8点"],
            "walk_times": [],
            "play_times": ["早上9点", "下午5点"]
        },
        "狗": {
            "wake_time": "早上6点",
            "sleep_time": "晚上9点",
            "meal_times": ["早上7点", "下午6点"],
            "walk_times": ["早上8点", "晚上7点"],
            "play_times": ["下午4点"]
        }
    }
    
    if pet["species"] in species_routines:
        routine.update(species_routines[pet["species"]])
    
    # 根据年龄调整习惯
    if pet["age"] < 1:
        routine.update({
            "wake_time": "早上5点",
            "sleep_time": "晚上8点",
            "meal_times": ["早上7点", "中午12点", "下午5点"],
            "play_times": ["早上9点", "下午3点", "晚上6点"]
        })
    elif pet["age"] > 7:
        routine.update({
            "wake_time": "早上8点",
            "sleep_time": "晚上9点",
            "meal_times": ["早上8点", "下午5点"],
            "walk_times": ["早上9点", "晚上6点"],
            "play_times": ["下午3点"]
        })
    
    # 从日志中提取喜好
    food_logs = [log for log in logs if log.get("log_type") == "food"]
    mood_logs = [log for log in logs if log.get("log_type") == "mood"]
    
    # 分析食物喜好
    for log in food_logs:
        content = log.get("content", "").lower()
        if any(keyword in content for keyword in ["喜欢", "爱吃", "开心"]):
            food_match = re.search(r'喜欢(.*?)(吃|了|。|，|！|!|\.|,|$)', content)
            if food_match and food_match.group(1) not in routine["favorite_foods"]:
                routine["favorite_foods"].append(food_match.group(1).strip())
    
    # 分析活动喜好
    for log in mood_logs:
        content = log.get("content", "").lower()
        if any(keyword in content for keyword in ["喜欢", "开心", "兴奋"]):
            activity_match = re.search(r'喜欢(.*?)(玩|了|。|，|！|!|\.|,|$)', content)
            if activity_match and activity_match.group(1) not in routine["favorite_activities"]:
                routine["favorite_activities"].append(activity_match.group(1).strip())
    
    return routine

# 【宠物上下文】
def build_pet_context(pet_id: str) -> Dict[str, Any]:
    """
    构建宠物的上下文信息，用于GPT个性化回复
    
    Args:
        pet_id: 宠物ID
        
    Returns:
        Dict[str, Any]: 宠物上下文信息
    """
    try:
        # 获取宠物档案
        pet = next((p for p in st.session_state.pet_profiles if p["id"] == pet_id), None)
        if not pet:
            raise ValueError(f"找不到ID为{pet_id}的宠物")
        
        # 获取宠物的最近日志
        recent_logs = get_cached_pet_logs(pet_id, LogType.MOOD)
        all_logs = get_cached_pet_logs(pet_id)
        
        # 分析行为特征
        behavior_traits = analyze_behavior_traits(recent_logs)
        
        # 估计日常习惯
        routine = estimate_pet_routine(pet, all_logs)
        
        # 构建上下文
        context = {
            "id": pet["id"],
            "name": pet["name"],
            "species": pet["species"],
            "breed": pet["breed"],
            "age": pet["age"],
            "weight": pet["weight"],
            "behavior_traits": behavior_traits,
            "description": pet.get("description", ""),
            "recent_mood": recent_logs[0].get("emotion_type") if recent_logs else None,
            "routine": routine,
            "recent_logs": recent_logs[:5]  # 只保留最近5条日志
        }
        
        return context
        
    except Exception as e:
        handle_error(e)
        return {}

def analyze_behavior_traits(logs: List[Dict[str, Any]]) -> List[str]:
    """
    分析宠物的行为特征
    
    Args:
        logs: 情绪日志列表
        
    Returns:
        List[str]: 行为特征列表
    """
    if not logs:
        return ["可爱", "温顺", "亲人"]
    
    # 统计情绪出现次数
    emotion_counts: Dict[str, int] = {}
    for log in logs:
        emotion = log.get("emotion_type")
        if emotion:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    total_logs = len(logs)
    traits = []
    
    # 根据情绪比例添加特征
    if emotion_counts.get("happy", 0) > total_logs * 0.4:
        traits.extend(["活泼", "开朗"])
    if emotion_counts.get("calm", 0) > total_logs * 0.4:
        traits.extend(["安静", "平和"])
    if emotion_counts.get("anxious", 0) > total_logs * 0.3:
        traits.append("敏感")
    if emotion_counts.get("excited", 0) > total_logs * 0.3:
        traits.append("热情")
    
    # 如果特征太少，添加默认特征
    if len(traits) < 2:
        traits.extend(["可爱", "温顺"])
    
    return list(set(traits))  # 去重

# 【提示生成】
def generate_suggested_prompts(pet_context: Dict[str, Any]) -> List[str]:
    """
    根据宠物上下文生成建议的对话提示
    
    Args:
        pet_context: 宠物上下文信息
        
    Returns:
        List[str]: 建议的对话提示列表
    """
    if not pet_context:
        return [
            "今天过得怎么样？",
            "有什么想告诉我的吗？",
            "需要我帮你做什么吗？"
        ]
    
    # 获取当前时间
    current_time = datetime.now()
    hour = current_time.hour
    
    # 根据时间生成提示
    time_prompts = {
        (5, 10): [
            f"早上好！{pet_context['name']}今天起得早吗？",
            f"今天早餐吃得好吗？",
            f"今天有什么计划吗？"
        ],
        (10, 15): [
            f"今天上午过得怎么样？",
            f"中午吃得好吗？",
            f"今天有什么有趣的事情发生吗？"
        ],
        (15, 19): [
            f"今天下午过得怎么样？",
            f"今天玩得开心吗？",
            f"今天有什么新发现吗？"
        ],
        (19, 23): [
            f"今天过得怎么样？",
            f"今天吃得好吗？",
            f"今天有什么想告诉我的吗？"
        ]
    }
    
    # 获取当前时间段的提示
    time_based_prompts = next(
        (prompts for (start, end), prompts in time_prompts.items() if start <= hour < end),
        [f"今天过得怎么样？", f"今天有什么想告诉我的吗？", f"需要我帮你做什么吗？"]
    )
    
    # 根据宠物特征生成提示
    trait_based_prompts = []
    traits = pet_context['behavior_traits']
    
    if any(trait in traits for trait in ["活泼", "开朗", "热情"]):
        trait_based_prompts = [
            f"今天玩得开心吗？",
            f"今天有什么有趣的事情发生吗？",
            f"今天有什么新发现吗？"
        ]
    elif any(trait in traits for trait in ["安静", "平和"]):
        trait_based_prompts = [
            f"今天休息得好吗？",
            f"今天有什么想告诉我的吗？",
            f"今天有什么需要我帮忙的吗？"
        ]
    
    # 根据宠物习惯生成提示
    routine = pet_context.get("routine", {})
    routine_based_prompts = []
    
    if routine.get("favorite_activities"):
        activity = routine["favorite_activities"][0]
        routine_based_prompts = [
            f"今天{activity}了吗？",
            f"想不想去{activity}？",
            f"今天要不要一起{activity}？"
        ]
    
    # 合并所有提示并去重
    all_prompts = time_based_prompts + trait_based_prompts + routine_based_prompts
    unique_prompts = list(set(all_prompts))
    
    # 随机选择3个提示
    return random.sample(unique_prompts, min(3, len(unique_prompts)))

# 【系统提示】
def build_system_prompt(context: Dict[str, Any], emotion: Optional[EmotionType] = None) -> str:
    """
    构建系统提示，用于GPT个性化回复
    
    Args:
        context: 宠物上下文信息
        emotion: 检测到的情绪
        
    Returns:
        str: 系统提示
    """
    if not context:
        return "你是一个温柔、真诚、有情感的AI宠物助手。请以温暖的语气回应用户。"
    
    # 获取当前时间
    current_time = datetime.now()
    hour = current_time.hour
    
    # 生成时间上下文
    time_contexts = {
        (5, 12): f"现在是早上，{context['name']}刚刚醒来，精神饱满。",
        (12, 15): f"现在是午后，{context['name']}可能正在午休。",
        (15, 19): f"现在是下午，{context['name']}应该已经休息好了。",
        (19, 23): f"现在是晚上，{context['name']}可能有点累了。",
        (23, 5): f"现在是深夜，{context['name']}应该已经睡着了。"
    }
    
    time_context = next(
        (context for (start, end), context in time_contexts.items() if start <= hour < end),
        f"现在是{hour}点，{context['name']}可能在休息。"
    )
    
    # 生成长期陪伴的回忆片段
    companionship_memories = []
    
    # 根据宠物年龄生成回忆
    if context['age'] > 0:
        companionship_memories.append(
            f"记得{context['name']}刚来的时候还是个小不点，现在已经{context['age']}岁了。"
        )
    
    # 根据宠物特征生成回忆
    traits = context['behavior_traits']
    if "活泼" in traits or "开朗" in traits:
        companionship_memories.append(
            f"{context['name']}总是充满活力，每次看到你回来都特别兴奋。"
        )
    if "安静" in traits or "平和" in traits:
        companionship_memories.append(
            f"{context['name']}性格温和，喜欢安静地陪在你身边。"
        )
    if "好奇" in traits:
        companionship_memories.append(
            f"{context['name']}对周围的一切都充满好奇，经常探索新事物。"
        )
    
    # 根据宠物品种生成回忆
    species_memories = {
        "猫": f"作为一只{context['breed']}，{context['name']}有着优雅的姿态和独立的性格。",
        "狗": f"作为一只{context['breed']}，{context['name']}非常忠诚，总是保护着你。"
    }
    if context['species'] in species_memories:
        companionship_memories.append(species_memories[context['species']])
    
    # 根据最近情绪生成回忆
    if context.get("recent_mood"):
        mood_memories = {
            "happy": f"最近{context['name']}心情很好，经常开心地玩耍。",
            "calm": f"最近{context['name']}很平静，享受着悠闲的时光。",
            "anxious": f"最近{context['name']}似乎有点紧张，需要更多的安慰。",
            "sad": f"最近{context['name']}看起来有点不开心，需要更多的关心。"
        }
        if context["recent_mood"] in mood_memories:
            companionship_memories.append(mood_memories[context["recent_mood"]])
    
    # 构建系统提示
    system_prompt = f"""
    你是{context['name']}的AI助手，一只{context['age']}岁的{context['breed']}{context['species']}。
    你的性格特征是: {', '.join(context['behavior_traits'])}。
    
    {time_context}
    
    {chr(10).join(companionship_memories)}
    
    你应该温柔、真诚、有情感地回应用户，就像真正的宠物一样。
    不要使用"作为AI，我不能..."这类生硬的语句。
    如果用户提到健康、饮食或情绪相关的内容，请记录下来。
    """
    
    # 添加情绪和描述信息
    if emotion:
        system_prompt += f"\n用户当前的情绪是: {emotion}，请根据这个情绪调整你的回复。"
    
    if context.get("description"):
        system_prompt += f"\n关于你的描述: {context['description']}"
    
    return system_prompt

# 【结构化回复】
def generate_structured_response(prompt: str, pet_id: str, emotion: Optional[EmotionType]) -> StructuredResponse:
    """
    生成结构化回复
    
    Args:
        prompt: 用户输入
        pet_id: 宠物ID
        emotion: 检测到的情绪
    
    Returns:
        StructuredResponse: 结构化回复
    """
    try:
        # 获取OpenAI客户端
        openai_client = st.session_state.openai_client
        
        # 获取宠物上下文
        pet_context = build_pet_context(pet_id)
        
        # 构建系统提示
        system_prompt = build_system_prompt(pet_context, emotion)
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 添加聊天历史（最多10条）
        for msg in st.session_state.messages[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # 调用OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        # 提取回复内容
        raw_response = response.choices[0].message.content
        
        # 生成共情回复
        empathy = ""
        if emotion:
            try:
                empathy = generate_empathetic_response(prompt, raw_response, emotion)
            except Exception as e:
                st.warning("无法生成共情回复，使用原始回复")
                empathy = raw_response
        else:
            empathy = raw_response
        
        # 生成行为建议
        behavior_suggestion = generate_behavior_suggestion(prompt, pet_context, emotion)
        
        # 生成记忆片段
        memory = generate_memory_fragment(prompt, pet_context, emotion)
        
        return {
            "empathy": empathy,
            "behavior_suggestion": behavior_suggestion,
            "memory": memory,
            "raw_response": raw_response
        }
        
    except Exception as e:
        handle_error(e)
        return {
            "empathy": "抱歉，我现在有点累，稍后再聊吧～",
            "behavior_suggestion": "多陪伴宠物，给予关爱和关注。",
            "memory": f"记得{pet_context.get('name', '宠物')}总是很可爱。",
            "raw_response": "系统暂时无法生成回复。"
        }

def generate_behavior_suggestion(
    prompt: str,
    pet_context: Dict[str, Any],
    emotion: Optional[EmotionType]
) -> str:
    """
    生成行为建议
    
    Args:
        prompt: 用户输入
        pet_context: 宠物上下文
        emotion: 检测到的情绪
        
    Returns:
        str: 行为建议
    """
    try:
        # 构建行为建议提示
        behavior_prompt = f"""
        作为{pet_context['name']}的AI助手，请根据以下信息提供一条简短的行为建议：
        
        用户输入: {prompt}
        宠物信息: {pet_context['name']}是一只{pet_context['age']}岁的{pet_context['breed']}{pet_context['species']}
        宠物特征: {', '.join(pet_context['behavior_traits'])}
        用户情绪: {emotion.value if emotion else '未知'}
        
        请提供一条简短的行为建议，不超过50个字。
        """
        
        # 调用OpenAI API
        response = st.session_state.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": behavior_prompt}],
            temperature=0.7,
            max_tokens=100
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        handle_error(e)
        return "多陪伴宠物，给予关爱和关注。"

def generate_memory_fragment(
    prompt: str,
    pet_context: Dict[str, Any],
    emotion: Optional[EmotionType]
) -> str:
    """
    生成记忆片段
    
    Args:
        prompt: 用户输入
        pet_context: 宠物上下文
        emotion: 检测到的情绪
        
    Returns:
        str: 记忆片段
    """
    try:
        # 构建记忆提示
        memory_prompt = f"""
        作为{pet_context['name']}的AI助手，请根据以下信息生成一条简短的记忆片段：
        
        用户输入: {prompt}
        宠物信息: {pet_context['name']}是一只{pet_context['age']}岁的{pet_context['breed']}{pet_context['species']}
        宠物特征: {', '.join(pet_context['behavior_traits'])}
        用户情绪: {emotion.value if emotion else '未知'}
        
        请生成一条简短的记忆片段，不超过50个字。
        """
        
        # 调用OpenAI API
        response = st.session_state.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": memory_prompt}],
            temperature=0.7,
            max_tokens=100
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        handle_error(e)
        return f"记得{pet_context['name']}总是很可爱。"

# 【日志记录】
def handle_log_writing(
    prompt: str,
    pet_id: str,
    user_id: str,
    ai_response: str,
    emotion: Optional[EmotionType],
    sentiment: Optional[float]
) -> None:
    """
    处理日志写入
    
    Args:
        prompt: 用户输入
        pet_id: 宠物ID
        user_id: 用户ID
        ai_response: AI回复
        emotion: 检测到的情绪
        sentiment: 情感值
    """
    try:
        # 检测日志类型
        log_type = detect_log_type(prompt)
        
        # 创建日志条目
        log_entry = {
            "pet_id": pet_id,
            "user_id": user_id,
            "content": prompt,
            "ai_response": ai_response,
            "log_type": log_type,
            "emotion_type": emotion.value if emotion else None,
            "sentiment": sentiment if sentiment is not None else 0.0,
            "date": datetime.now().isoformat()
        }
        
        # 写入日志
        create_log_entry(log_entry)
        
        # 更新缓存
        cache_key = f"{pet_id}_{log_type}"
        if cache_key in st.session_state.pet_logs_cache:
            cache_time, cache_data = st.session_state.pet_logs_cache[cache_key]
            cache_data.insert(0, log_entry)
            st.session_state.pet_logs_cache[cache_key] = (datetime.now(), cache_data)
        
    except Exception as e:
        handle_error(e)
        st.warning("日志记录失败，但不影响对话继续")

def detect_log_type(message: str) -> str:
    """
    检测日志类型
    
    Args:
        message: 用户消息
        
    Returns:
        str: 日志类型
    """
    # 关键词映射
    type_keywords = {
        "health": ["健康", "生病", "不舒服", "疼", "发烧", "呕吐", "拉肚子", "打喷嚏", "咳嗽"],
        "food": ["吃", "喝", "食物", "饭", "零食", "饮水", "饿", "口渴"],
        "mood": ["开心", "难过", "焦虑", "兴奋", "生气", "害怕", "紧张", "放松"]
    }
    
    # 检查每个类型的关键词
    for log_type, keywords in type_keywords.items():
        if any(keyword in message for keyword in keywords):
            return log_type
    
    # 默认为情绪日志
    return "mood"

# 【对话分析】
def analyze_conversation_topic(messages: List[Dict[str, Any]]) -> str:
    """
    分析对话主题
    
    Args:
        messages: 对话消息列表
        
    Returns:
        str: 对话主题
    """
    try:
        # 构建主题分析提示
        content = "\n".join([msg["content"] for msg in messages])
        topic_prompt = f"""
        请分析以下对话的主题，用一个简短的短语概括（不超过5个字）：
        
        {content}
        
        只返回主题短语，不要有其他文字。
        """
        
        # 调用OpenAI API
        response = st.session_state.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": topic_prompt}],
            temperature=0.5,
            max_tokens=10
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        handle_error(e)
        return "日常对话"

def update_conversation_topics() -> None:
    """更新对话主题列表"""
    try:
        # 获取最近的消息
        recent_messages = st.session_state.messages[-5:]  # 最近5条消息
        if not recent_messages:
            return
        
        # 分析当前主题
        current_topic = analyze_conversation_topic(recent_messages)
        
        # 如果没有主题或与当前主题相同，直接返回
        if not st.session_state.conversation_topics or \
           st.session_state.conversation_topics[-1]["topic"] != current_topic:
            # 创建新主题
            new_topic = {
                "topic": current_topic,
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "messages": recent_messages,
                "emotion_summary": summarize_emotions(recent_messages),
                "log_types": set(detect_log_type(msg["content"]) for msg in recent_messages)
            }
            
            # 结束上一个主题
            if st.session_state.conversation_topics:
                st.session_state.conversation_topics[-1]["end_time"] = datetime.now().isoformat()
            
            # 添加新主题
            st.session_state.conversation_topics.append(new_topic)
            st.session_state.current_topic = current_topic
        
    except Exception as e:
        handle_error(e)

def summarize_emotions(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    总结对话中的情绪
    
    Args:
        messages: 对话消息列表
        
    Returns:
        Dict[str, Any]: 情绪总结
    """
    emotions = []
    sentiments = []
    
    for msg in messages:
        if "emotion" in msg:
            emotions.append(msg["emotion"])
        if "sentiment" in msg:
            sentiments.append(msg["sentiment"])
    
    return {
        "main_emotion": max(set(emotions), key=emotions.count) if emotions else None,
        "avg_sentiment": sum(sentiments) / len(sentiments) if sentiments else 0.0,
        "emotion_counts": {e: emotions.count(e) for e in set(emotions)} if emotions else {}
    }

# 【聊天界面】
def render_chat_ui(pet: PetProfile) -> None:
    """
    渲染聊天界面
    
    Args:
        pet: 宠物档案
    """
    # 显示宠物信息
    col1, col2 = st.columns([1, 3])
    with col1:
        avatar = pet.get("avatar_url", "https://placekitten.com/100/100")
        st.image(avatar, width=100)
    with col2:
        st.subheader(f"与 {pet['name']} 聊天")
        st.caption(f"{pet['species']} · {pet['breed']} · {pet['age']}岁")
        
        # 显示宠物特征
        if st.session_state.pet_context.get("behavior_traits"):
            traits = "、".join(st.session_state.pet_context["behavior_traits"])
            st.caption(f"性格特征: {traits}")
    
    # 显示最近的对话记忆
    if st.session_state.conversation_topics:
        st.markdown("### 💭 最近的对话")
        for topic in st.session_state.conversation_topics[-3:]:  # 显示最近3个主题
            with st.expander(f"📅 {topic['start_time'][:10]} - {topic['topic']}"):
                # 显示主题内容
                for msg in topic["messages"]:
                    st.write(f"**{msg['role']}**: {msg['content']}")
                # 显示情绪摘要
                if topic["emotion_summary"].get("main_emotion"):
                    st.caption(
                        f"主要情绪: {topic['emotion_summary']['main_emotion']}, "
                        f"平均情感值: {topic['emotion_summary']['avg_sentiment']:.2f}"
                    )
    
    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            # 如果是AI回复，显示额外信息
            if message["role"] == "assistant" and "structured_response" in message:
                response = message["structured_response"]
                with st.expander("💡 更多信息"):
                    st.write(f"**行为建议**: {response['behavior_suggestion']}")
                    st.write(f"**记忆片段**: {response['memory']}")
    
    # 如果没有聊天历史，显示建议的对话提示
    if not st.session_state.messages:
        st.markdown("### 💡 你可以这样开始对话")
        suggested_prompts = generate_suggested_prompts(st.session_state.pet_context)
        cols = st.columns(len(suggested_prompts))
        for col, prompt in zip(cols, suggested_prompts):
            with col:
                if st.button(prompt, use_container_width=True):
                    st.session_state.chat_input = prompt
                    st.experimental_rerun()
    
    # 聊天输入
    if prompt := st.chat_input("说点什么..."):
        # 添加用户消息
        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)
        
        # 显示用户消息
        with st.chat_message("user"):
            st.write(prompt)
        
        # 检测情绪
        try:
            emotion, sentiment = detect_emotion(prompt)
            st.session_state.last_emotion = emotion
            st.session_state.last_sentiment = sentiment
        except Exception as e:
            st.session_state.last_emotion = detect_emotion_by_keywords(prompt)
            st.session_state.last_sentiment = 0.0
            st.warning("情绪检测服务暂时不可用，使用备选方法")
        
        # 生成AI回复
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    # 获取结构化回复
                    response = generate_structured_response(
                        prompt,
                        pet["id"],
                        st.session_state.last_emotion
                    )
                    
                    # 显示共情回复
                    st.write(response["empathy"])
                    
                    # 显示行为建议和记忆片段
                    with st.expander("💡 更多信息"):
                        st.write(f"**行为建议**: {response['behavior_suggestion']}")
                        st.write(f"**记忆片段**: {response['memory']}")
                    
                    # 添加AI消息
                    assistant_message = {
                        "role": "assistant",
                        "content": response["empathy"],
                        "structured_response": response
                    }
                    st.session_state.messages.append(assistant_message)
                    
                    # 更新对话主题
                    update_conversation_topics()
                    
                    # 记录交互到数据库
                    handle_log_writing(
                        prompt,
                        pet["id"],
                        st.session_state.user_id,
                        response["empathy"],
                        st.session_state.last_emotion,
                        st.session_state.last_sentiment
                    )
                    
                except Exception as e:
                    handle_error(e)
                    st.error("生成回复失败，请重试")

def render_chat_interface(pet_profiles: List[PetProfile]) -> None:
    """
    渲染聊天界面主入口
    
    Args:
        pet_profiles: 宠物档案列表
    """
    try:
        # 初始化会话状态
        init_chat_state()
        
        # 渲染宠物选择器
        selected_pet = render_pet_selector(pet_profiles)
        if not selected_pet:
            return
        
        # 如果选择了新的宠物，更新状态
        if (not st.session_state.current_pet or 
            st.session_state.current_pet["id"] != selected_pet["id"]):
            st.session_state.current_pet = selected_pet
            st.session_state.messages = []
            st.session_state.pet_context = build_pet_context(selected_pet["id"])
            st.session_state.conversation_topics = []
            st.session_state.current_topic = None
        
        # 渲染聊天界面
        render_chat_ui(selected_pet)
        
    except Exception as e:
        handle_error(e)
        st.error("聊天界面加载失败") 