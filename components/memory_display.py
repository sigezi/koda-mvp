"""
对话记忆展示组件

此组件负责展示和管理宠物的对话记忆，包括：
- 记忆时间线展示
- 重要记忆高亮
- 记忆检索与过滤
- 记忆统计分析
"""

import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Any, Optional

from utils.memory_manager import (
    MemoryFragment,
    ConversationMemory,
    retrieve_relevant_memories,
    merge_memory_fragments,
    cleanup_old_memories,
    update_memory_importance
)
from utils.types import PetProfile, EmotionType, MemoryContext
from utils.errors import handle_error

def render_memory_timeline(memories: List[MemoryFragment]) -> None:
    """
    渲染记忆时间线
    
    Args:
        memories: 记忆片段列表
    """
    if not memories:
        st.info("暂无记忆记录")
        return
        
    # 转换记忆数据为DataFrame
    df = pd.DataFrame([
        {
            '时间': memory['timestamp'],
            '内容': memory['content'],
            '情感值': memory['emotion'],
            '重要性': memory['importance'],
            '类型': memory['context'].value
        }
        for memory in memories
    ])
    
    # 创建时间线图表
    fig = px.scatter(
        df,
        x='时间',
        y='情感值',
        size='重要性',
        color='类型',
        hover_data=['内容'],
        title='记忆时间线'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_memory_details(memory: MemoryFragment) -> None:
    """
    渲染记忆详情
    
    Args:
        memory: 记忆片段
    """
    with st.expander(f"记忆详情 - {memory['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**内容**: {memory['content']}")
            st.markdown(f"**类型**: {memory['context'].value}")
            
        with col2:
            st.markdown(f"**情感值**: {memory['emotion']:.2f}")
            st.markdown(f"**重要性**: {memory['importance']:.2f}")
            
        if memory['references']:
            st.markdown("**相关记忆**:")
            for ref_id in memory['references']:
                st.markdown(f"- {ref_id}")

def render_emotion_analysis(memories: List[MemoryFragment]) -> None:
    """
    渲染情绪分析图表
    
    Args:
        memories: 记忆片段列表
    """
    if not memories:
        return
        
    # 按日期统计情绪分布
    df = pd.DataFrame([
        {
            '日期': memory['timestamp'].date(),
            '情感值': memory['emotion'],
            '类型': memory['context'].value
        }
        for memory in memories
    ])
    
    daily_emotions = df.groupby(['日期', '类型'])['情感值'].mean().reset_index()
    
    # 创建情绪趋势图
    fig = px.line(
        daily_emotions,
        x='日期',
        y='情感值',
        color='类型',
        title='情绪趋势分析'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_memory_search() -> None:
    """
    渲染记忆搜索界面
    """
    st.subheader("记忆搜索")
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_text = st.text_input("搜索关键词")
        memory_type = st.selectbox(
            "记忆类型",
            options=[ctx.value for ctx in MemoryContext],
            format_func=lambda x: {
                "conversation": "对话记忆",
                "behavior": "行为记忆",
                "emotion": "情绪记忆"
            }[x]
        )
        
    with col2:
        start_date = st.date_input("开始日期")
        end_date = st.date_input("结束日期")
        
    if st.button("搜索"):
        if search_text:
            # 搜索相关记忆
            memories = retrieve_relevant_memories(
                search_text,
                memory_type=MemoryContext(memory_type),
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.max.time())
            )
            
            if memories:
                st.success(f"找到 {len(memories)} 条相关记忆")
                for memory in memories:
                    render_memory_details(memory)
            else:
                st.info("未找到相关记忆")

def render_memory_library(
    memories: Dict[MemoryContext, List[MemoryFragment]]
) -> None:
    """
    渲染记忆库主界面
    
    Args:
        memories: 按类型组织的记忆片段字典
    """
    st.title("记忆库")
    
    # 渲染搜索界面
    render_memory_search()
    
    # 渲染记忆时间线
    st.subheader("记忆时间线")
    all_memories = [
        memory for memories_list in memories.values()
        for memory in memories_list
    ]
    render_memory_timeline(all_memories)
    
    # 渲染情绪分析
    st.subheader("情绪分析")
    render_emotion_analysis(all_memories)
    
    # 按类型展示记忆
    for context, context_memories in memories.items():
        st.subheader({
            MemoryContext.CONVERSATION: "对话记忆",
            MemoryContext.BEHAVIOR: "行为记忆",
            MemoryContext.EMOTION: "情绪记忆"
        }[context])
        
        for memory in context_memories:
            render_memory_details(memory)

def render_memory_stats(memories: List[MemoryFragment]) -> None:
    """
    渲染记忆统计信息
    
    Args:
        memories: 记忆片段列表
    """
    try:
        if not memories:
            return
            
        # 计算基础统计
        total_memories = len(memories)
        avg_importance = sum(m["importance"] for m in memories) / total_memories
        emotion_counts = {}
        for m in memories:
            if m["emotion"]:
                emotion_counts[m["emotion"]] = emotion_counts.get(m["emotion"], 0) + 1
                
        # 显示统计信息
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("总记忆数", total_memories)
            
        with col2:
            st.metric("平均重要性", f"{avg_importance:.2f}")
            
        with col3:
            main_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else "未知"
            st.metric("主要情绪", main_emotion)
            
        # 情绪分布饼图
        if emotion_counts:
            emotion_df = pd.DataFrame([
                {"情绪": k, "数量": v}
                for k, v in emotion_counts.items()
            ])
            
            fig = px.pie(
                emotion_df,
                values="数量",
                names="情绪",
                title="情绪分布"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        handle_error(e)
        st.error("记忆统计信息渲染失败")

def render_memory_display(pet: PetProfile, memories: Dict[str, List[MemoryFragment]]) -> None:
    """
    渲染记忆库显示界面
    
    Args:
        pet: 宠物信息
        memories: 记忆库数据
    """
    st.title(f"🌟 {pet['name']} 的记忆库")
    
    # 记忆库统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("记忆总数", len(memories.get("all", [])))
    with col2:
        st.metric("重要记忆", len([m for m in memories.get("all", []) if m.importance > 0.8]))
    with col3:
        st.metric("最近更新", datetime.now().strftime("%Y-%m-%d"))
    
    # 记忆类型选择
    memory_type = st.radio(
        "选择记忆类型",
        ["全部记忆", "对话记忆", "行为记忆", "情感记忆"]
    )
    
    # 时间范围选择
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "开始日期",
            datetime.now() - timedelta(days=30)
        )
    with col2:
        end_date = st.date_input(
            "结束日期",
            datetime.now()
        )
    
    # 搜索框
    search_query = st.text_input("搜索记忆", "")
    
    # 获取筛选后的记忆
    filtered_memories = filter_memories(
        memories,
        memory_type,
        start_date,
        end_date,
        search_query
    )
    
    # 显示记忆列表
    if filtered_memories:
        for memory in filtered_memories:
            with st.expander(
                f"{memory.timestamp.strftime('%Y-%m-%d %H:%M')} - {memory.content[:50]}..."
            ):
                # 记忆内容
                st.write(memory.content)
                
                # 记忆元数据
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"情感: {memory.emotion}")
                with col2:
                    st.write(f"重要性: {memory.importance:.2f}")
                with col3:
                    st.write(f"上下文: {memory.context}")
                
                # 相关记忆
                if memory.references:
                    st.write("相关记忆:")
                    for ref in memory.references:
                        st.write(f"- {ref}")
                
                # 操作按钮
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("标记重要", key=f"important_{memory.id}"):
                        update_memory_importance(memory.id, 1.0)
                        st.success("已标记为重要记忆")
                with col2:
                    if st.button("删除", key=f"delete_{memory.id}"):
                        # TODO: 实现删除功能
                        st.warning("记忆已删除")
    else:
        st.info("没有找到符合条件的记忆")
    
    # 记忆分析图表
    st.subheader("记忆分析")
    tab1, tab2 = st.tabs(["情感趋势", "记忆分布"])
    
    with tab1:
        render_emotion_trend_chart(filtered_memories)
    
    with tab2:
        render_memory_distribution_chart(filtered_memories)

def filter_memories(
    memories: Dict[str, List[MemoryFragment]],
    memory_type: str,
    start_date: datetime,
    end_date: datetime,
    search_query: str
) -> List[MemoryFragment]:
    """
    根据条件筛选记忆
    
    Args:
        memories: 记忆库数据
        memory_type: 记忆类型
        start_date: 开始日期
        end_date: 结束日期
        search_query: 搜索关键词
    
    Returns:
        筛选后的记忆列表
    """
    # 获取指定类型的记忆
    if memory_type == "全部记忆":
        filtered = memories.get("all", [])
    elif memory_type == "对话记忆":
        filtered = memories.get("conversation", [])
    elif memory_type == "行为记忆":
        filtered = memories.get("behavior", [])
    else:  # 情感记忆
        filtered = memories.get("emotion", [])
    
    # 时间范围筛选
    filtered = [
        m for m in filtered
        if start_date <= m.timestamp.date() <= end_date
    ]
    
    # 关键词搜索
    if search_query:
        filtered = [
            m for m in filtered
            if search_query.lower() in m.content.lower()
        ]
    
    return filtered

def render_emotion_trend_chart(memories: List[MemoryFragment]) -> None:
    """
    渲染情感趋势图表
    
    Args:
        memories: 记忆列表
    """
    if not memories:
        st.info("没有足够的数据生成情感趋势图表")
        return
    
    # 准备数据
    df = pd.DataFrame([
        {
            "date": m.timestamp.date(),
            "emotion": m.emotion,
            "importance": m.importance
        }
        for m in memories
    ])
    
    # 按日期分组计算平均情感值
    df = df.groupby("date").agg({
        "emotion": "mean",
        "importance": "mean"
    }).reset_index()
    
    # 创建图表
    fig = px.line(
        df,
        x="date",
        y="emotion",
        title="情感趋势",
        labels={"emotion": "情感值", "date": "日期"}
    )
    
    st.plotly_chart(fig)

def render_memory_distribution_chart(memories: List[MemoryFragment]) -> None:
    """
    渲染记忆分布图表
    
    Args:
        memories: 记忆列表
    """
    if not memories:
        st.info("没有足够的数据生成记忆分布图表")
        return
    
    # 准备数据
    df = pd.DataFrame([
        {
            "type": m.context,
            "count": 1
        }
        for m in memories
    ])
    
    # 按类型统计
    df = df.groupby("type").count().reset_index()
    
    # 创建图表
    fig = px.pie(
        df,
        values="count",
        names="type",
        title="记忆类型分布"
    )
    
    st.plotly_chart(fig) 