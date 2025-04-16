"""
记忆管理组件

提供记忆管理的用户界面，包括记忆的查看、编辑和删除功能。
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Optional, Dict, Any

from utils.types import (
    MemoryFragment,
    ConversationMemory,
    MemoryContext,
    EmotionType
)
from utils.memory_client import (
    get_memories,
    get_conversation_memories,
    create_memory,
    update_memory,
    delete_memory,
    create_conversation_memory,
    update_conversation_memory,
    delete_conversation_memory
)

def render_memory_timeline(pet_id: str, days: int = 7) -> None:
    """
    渲染记忆时间线
    
    Args:
        pet_id: 宠物ID
        days: 显示天数
    """
    st.subheader("记忆时间线")
    
    # 获取时间范围内的记忆
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    memories = get_memories(pet_id, start_date, end_date)
    
    if not memories:
        st.info("暂无记忆记录")
        return
    
    # 转换为DataFrame
    df = pd.DataFrame([
        {
            "时间": memory.timestamp,
            "内容": memory.content,
            "情绪": memory.emotion.value,
            "重要性": memory.importance,
            "上下文": memory.context.value
        }
        for memory in memories
    ])
    
    # 创建时间线图表
    fig = px.timeline(
        df,
        x_start="时间",
        y="情绪",
        color="上下文",
        size="重要性",
        hover_data=["内容"],
        title=f"最近{days}天的记忆时间线"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_emotion_analysis(pet_id: str, days: int = 30) -> None:
    """
    渲染情绪分析图表
    
    Args:
        pet_id: 宠物ID
        days: 显示天数
    """
    st.subheader("情绪分析")
    
    # 获取时间范围内的记忆
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    memories = get_memories(pet_id, start_date, end_date)
    
    if not memories:
        st.info("暂无情绪记录")
        return
    
    # 转换为DataFrame
    df = pd.DataFrame([
        {
            "日期": memory.timestamp.date(),
            "情绪": memory.emotion.value,
            "重要性": memory.importance
        }
        for memory in memories
    ])
    
    # 创建情绪分布饼图
    emotion_counts = df["情绪"].value_counts()
    fig1 = px.pie(
        values=emotion_counts.values,
        names=emotion_counts.index,
        title="情绪分布"
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # 创建情绪趋势折线图
    daily_emotions = df.groupby("日期")["情绪"].value_counts().unstack(fill_value=0)
    fig2 = go.Figure()
    for emotion in daily_emotions.columns:
        fig2.add_trace(go.Scatter(
            x=daily_emotions.index,
            y=daily_emotions[emotion],
            name=emotion,
            mode="lines+markers"
        ))
    fig2.update_layout(title="情绪趋势")
    st.plotly_chart(fig2, use_container_width=True)

def render_memory_search(pet_id: str) -> None:
    """
    渲染记忆搜索界面
    
    Args:
        pet_id: 宠物ID
    """
    st.subheader("记忆搜索")
    
    # 搜索条件
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("关键词")
        context = st.selectbox(
            "上下文类型",
            [c.value for c in MemoryContext],
            format_func=lambda x: x
        )
    with col2:
        start_date = st.date_input("开始日期")
        end_date = st.date_input("结束日期")
    
    # 搜索按钮
    if st.button("搜索"):
        # 获取记忆
        memories = get_memories(
            pet_id,
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time())
        )
        
        # 过滤结果
        if keyword:
            memories = [
                m for m in memories
                if keyword.lower() in m.content.lower()
            ]
        if context:
            memories = [
                m for m in memories
                if m.context.value == context
            ]
        
        # 显示结果
        if not memories:
            st.info("未找到相关记忆")
            return
        
        for memory in memories:
            with st.expander(
                f"{memory.timestamp.strftime('%Y-%m-%d %H:%M')} - {memory.content[:50]}..."
            ):
                st.write(f"内容: {memory.content}")
                st.write(f"情绪: {memory.emotion.value}")
                st.write(f"重要性: {memory.importance}")
                st.write(f"上下文: {memory.context.value}")
                
                # 编辑和删除按钮
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("编辑", key=f"edit_{memory.id}"):
                        st.session_state.editing_memory = memory
                with col2:
                    if st.button("删除", key=f"delete_{memory.id}"):
                        if delete_memory(memory.id):
                            st.success("删除成功")
                            st.experimental_rerun()
                        else:
                            st.error("删除失败")

def render_memory_editor(pet_id: str) -> None:
    """
    渲染记忆编辑器
    
    Args:
        pet_id: 宠物ID
    """
    st.subheader("记忆编辑器")
    
    # 编辑现有记忆
    if "editing_memory" in st.session_state:
        memory = st.session_state.editing_memory
        st.write("编辑记忆")
        
        content = st.text_area("内容", memory.content)
        emotion = st.selectbox(
            "情绪",
            [e.value for e in EmotionType],
            index=[e.value for e in EmotionType].index(memory.emotion.value),
            format_func=lambda x: x
        )
        importance = st.slider("重要性", 0.0, 1.0, memory.importance)
        context = st.selectbox(
            "上下文",
            [c.value for c in MemoryContext],
            index=[c.value for c in MemoryContext].index(memory.context.value),
            format_func=lambda x: x
        )
        
        if st.button("保存"):
            updated_memory = update_memory(
                memory.id,
                content=content,
                emotion=EmotionType(emotion),
                importance=importance,
                context=MemoryContext(context)
            )
            if updated_memory:
                st.success("更新成功")
                del st.session_state.editing_memory
                st.experimental_rerun()
            else:
                st.error("更新失败")
    
    # 创建新记忆
    else:
        st.write("创建新记忆")
        
        content = st.text_area("内容")
        emotion = st.selectbox(
            "情绪",
            [e.value for e in EmotionType],
            format_func=lambda x: x
        )
        importance = st.slider("重要性", 0.0, 1.0, 0.5)
        context = st.selectbox(
            "上下文",
            [c.value for c in MemoryContext],
            format_func=lambda x: x
        )
        
        if st.button("创建"):
            if not content:
                st.error("请输入记忆内容")
                return
            
            new_memory = create_memory(
                pet_id=pet_id,
                content=content,
                emotion=EmotionType(emotion),
                importance=importance,
                context=MemoryContext(context)
            )
            if new_memory:
                st.success("创建成功")
                st.experimental_rerun()
            else:
                st.error("创建失败")

def render_conversation_memory(pet_id: str) -> None:
    """
    渲染对话记忆界面
    
    Args:
        pet_id: 宠物ID
    """
    st.subheader("对话记忆")
    
    # 获取最近的对话记忆
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    conversations = get_conversation_memories(pet_id, start_date, end_date)
    
    if not conversations:
        st.info("暂无对话记忆")
        return
    
    # 显示对话记忆列表
    for conversation in conversations:
        with st.expander(
            f"{conversation.start_time.strftime('%Y-%m-%d %H:%M')} - {conversation.topic}"
        ):
            st.write(f"主题: {conversation.topic}")
            st.write(f"摘要: {conversation.summary}")
            st.write("关键点:")
            for point in conversation.key_points:
                st.write(f"- {point}")
            st.write("情绪:")
            for emotion in conversation.emotions:
                st.write(f"- {emotion.value}")
            
            # 显示对话内容
            st.write("对话内容:")
            for message in conversation.messages:
                st.write(f"{message['role']}: {message['content']}")
            
            # 编辑和删除按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("编辑", key=f"edit_conv_{conversation.id}"):
                    st.session_state.editing_conversation = conversation
            with col2:
                if st.button("删除", key=f"delete_conv_{conversation.id}"):
                    if delete_conversation_memory(conversation.id):
                        st.success("删除成功")
                        st.experimental_rerun()
                    else:
                        st.error("删除失败")

def render_memory_manager(pet_id: str) -> None:
    """
    渲染记忆管理主界面
    
    Args:
        pet_id: 宠物ID
    """
    st.title("记忆管理")
    
    # 侧边栏导航
    page = st.sidebar.selectbox(
        "功能选择",
        ["记忆时间线", "情绪分析", "记忆搜索", "记忆编辑器", "对话记忆"]
    )
    
    # 根据选择渲染不同页面
    if page == "记忆时间线":
        days = st.sidebar.slider("显示天数", 1, 30, 7)
        render_memory_timeline(pet_id, days)
    elif page == "情绪分析":
        days = st.sidebar.slider("显示天数", 1, 90, 30)
        render_emotion_analysis(pet_id, days)
    elif page == "记忆搜索":
        render_memory_search(pet_id)
    elif page == "记忆编辑器":
        render_memory_editor(pet_id)
    elif page == "对话记忆":
        render_conversation_memory(pet_id) 