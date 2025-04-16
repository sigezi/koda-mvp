"""
情绪响应组件

此模块负责检测用户情绪并生成共情回复。
使用OpenAI API进行情绪分析和回复生成。
"""

import streamlit as st
from typing import Tuple, Optional, Dict, List
import json
from openai import OpenAI

from utils.types import EmotionType
from utils.errors import handle_error, OpenAIRequestError

# 情绪关键词映射
EMOTION_KEYWORDS: Dict[EmotionType, List[str]] = {
    "happy": ["开心", "高兴", "快乐", "愉快", "兴奋", "欢乐", "幸福", "满意", "喜欢", "好"],
    "excited": ["兴奋", "激动", "热情", "期待", "迫不及待", "充满活力", "精力充沛", "振奋"],
    "calm": ["平静", "安宁", "放松", "舒适", "安心", "稳定", "平和", "宁静"],
    "neutral": ["一般", "普通", "还行", "正常", "一般般", "还可以", "马马虎虎"],
    "anxious": ["焦虑", "担心", "不安", "紧张", "忧虑", "害怕", "恐惧", "恐慌", "忐忑"],
    "sad": ["难过", "伤心", "悲伤", "失望", "沮丧", "痛苦", "不开心", "不开心", "不开心"],
    "angry": ["生气", "愤怒", "恼火", "不满", "烦躁", "讨厌", "厌恶", "反感", "不满"]
}

# 情绪回复模板
EMOTION_RESPONSES: Dict[EmotionType, List[str]] = {
    "happy": [
        "太棒了！看到你开心我也很开心！",
        "你的快乐感染了我，我也感到非常愉快！",
        "真为你高兴！希望这种好心情能一直持续下去～",
        "你的笑容是我最大的幸福！"
    ],
    "excited": [
        "哇！我也感到非常兴奋！",
        "你的热情感染了我，我也充满活力！",
        "太棒了！让我们一起分享这份激动吧！",
        "你的兴奋让我也感到非常振奋！"
    ],
    "calm": [
        "平静的心情真好，我也感到非常安宁。",
        "这种平和的感觉很舒服，我也很放松。",
        "宁静的时光总是特别美好，我也很享受。",
        "平静的心态是最好的，我也感到很安心。"
    ],
    "neutral": [
        "嗯，我理解你的感受。",
        "保持平和的心态也很好。",
        "有时候平淡也是一种幸福。",
        "我在这里陪着你，无论你的心情如何。"
    ],
    "anxious": [
        "别担心，我在这里陪着你。",
        "深呼吸，放松一下，一切都会好起来的。",
        "我理解你的焦虑，让我们一起面对。",
        "不用担心，我会一直支持你。"
    ],
    "sad": [
        "别难过，我在这里陪着你。",
        "我理解你的感受，让我来安慰你。",
        "伤心的时候，记得我永远在你身边。",
        "别担心，一切都会好起来的，我保证。"
    ],
    "angry": [
        "我理解你的愤怒，让我们一起冷静下来。",
        "深呼吸，试着放松一下，我在这里陪着你。",
        "生气的时候，记得我永远支持你。",
        "让我们一起面对这个问题，我会一直陪着你。"
    ]
}

# 检测情绪
def detect_emotion(text: str) -> Tuple[Optional[EmotionType], Optional[float]]:
    """
    检测文本中的情绪
    
    Args:
        text: 用户输入的文本
    
    Returns:
        Tuple[Optional[EmotionType], Optional[float]]: 情绪类型和情感值
    """
    try:
        # 获取OpenAI客户端
        openai_client = st.session_state.openai_client
        
        # 构建提示
        prompt = f"""
        分析以下文本中表达的情绪，并返回JSON格式的结果：
        
        文本: "{text}"
        
        请返回以下格式的JSON:
        {{
            "emotion": "happy/excited/calm/neutral/anxious/sad/angry",
            "sentiment": -1到1之间的浮点数，表示情感强度，负值表示负面情绪，正值表示正面情绪
        }}
        
        只返回JSON，不要有其他文字。
        """
        
        # 调用OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "你是一个情绪分析专家，负责分析文本中的情绪。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        # 解析响应
        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)
        
        # 提取情绪和情感值
        emotion = result.get("emotion")
        sentiment = result.get("sentiment")
        
        # 验证情绪类型
        if emotion and emotion in EmotionType.__members__:
            return EmotionType(emotion), sentiment
        else:
            # 如果无法确定情绪，使用关键词匹配
            return detect_emotion_by_keywords(text), 0.0
            
    except Exception as e:
        # 如果API调用失败，使用关键词匹配
        return detect_emotion_by_keywords(text), 0.0

# 通过关键词检测情绪
def detect_emotion_by_keywords(text: str) -> Optional[EmotionType]:
    """
    通过关键词匹配检测情绪
    
    Args:
        text: 用户输入的文本
    
    Returns:
        Optional[EmotionType]: 检测到的情绪类型
    """
    # 统计每种情绪的关键词出现次数
    emotion_counts = {emotion: 0 for emotion in EmotionType.__members__}
    
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                emotion_counts[emotion] += 1
    
    # 找出出现次数最多的情绪
    max_count = max(emotion_counts.values())
    if max_count > 0:
        for emotion, count in emotion_counts.items():
            if count == max_count:
                return EmotionType(emotion)
    
    # 默认返回中性情绪
    return EmotionType("neutral")

# 生成共情回复
def generate_empathetic_response(user_input: str, ai_response: str, emotion: EmotionType) -> str:
    """
    生成共情回复
    
    Args:
        user_input: 用户输入
        ai_response: AI原始回复
        emotion: 检测到的情绪
    
    Returns:
        str: 共情回复
    """
    try:
        # 获取OpenAI客户端
        openai_client = st.session_state.openai_client
        
        # 构建提示
        prompt = f"""
        用户输入: "{user_input}"
        检测到的情绪: {emotion}
        AI原始回复: "{ai_response}"
        
        请根据用户的情绪，修改AI的回复，使其更加共情和温暖。
        保持宠物的语气，但增加对用户情绪的理解和安慰。
        
        只返回修改后的回复，不要有其他文字。
        """
        
        # 调用OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "你是一个共情专家，负责生成温暖、理解的回复。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        # 提取回复
        empathetic_response = response.choices[0].message.content.strip()
        
        return empathetic_response
        
    except Exception as e:
        # 如果API调用失败，使用模板回复
        return get_template_response(emotion)

# 获取模板回复
def get_template_response(emotion: EmotionType) -> str:
    """
    获取情绪对应的模板回复
    
    Args:
        emotion: 情绪类型
    
    Returns:
        str: 模板回复
    """
    import random
    
    # 获取对应情绪的回复模板
    templates = EMOTION_RESPONSES.get(emotion, EMOTION_RESPONSES["neutral"])
    
    # 随机选择一个模板
    return random.choice(templates)

# 渲染情绪响应界面
def render_emotion_response(pet_id: str, openai_client: OpenAI, supabase) -> None:
    """
    渲染情绪响应界面
    
    Args:
        pet_id: 宠物ID
        openai_client: OpenAI客户端
        supabase: Supabase客户端
    """
    st.title("情绪分析")
    
    # 获取宠物信息
    try:
        pet = supabase.table("pets").select("*").eq("id", pet_id).single().execute()
        if not pet.data:
            st.error("未找到宠物信息")
            return
    except Exception as e:
        st.error(f"获取宠物信息失败: {str(e)}")
        return
    
    # 用户输入
    user_input = st.text_area("请输入你想说的话", height=100)
    
    if st.button("分析情绪"):
        if not user_input:
            st.warning("请输入内容")
            return
            
        # 检测情绪
        emotion, sentiment = detect_emotion(user_input)
        
        if emotion:
            # 显示情绪分析结果
            st.success(f"检测到的情绪: {emotion.value}")
            st.info(f"情感强度: {sentiment:.2f}")
            
            # 生成AI回复
            ai_response = "我理解你的感受。"  # 这里可以接入更复杂的回复生成逻辑
            
            # 生成共情回复
            empathetic_response = generate_empathetic_response(user_input, ai_response, emotion)
            
            # 显示回复
            st.write("### 共情回复")
            st.write(empathetic_response)
            
            # 保存到日志
            try:
                log_entry = {
                    "pet_id": pet_id,
                    "log_type": "emotion",
                    "content": user_input,
                    "sentiment": sentiment,
                    "emotion_type": emotion.value,
                    "ai_analysis": empathetic_response
                }
                supabase.table("logs").insert(log_entry).execute()
            except Exception as e:
                st.error(f"保存日志失败: {str(e)}")
        else:
            st.error("无法检测到情绪，请重试") 