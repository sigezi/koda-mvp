"""
日志显示组件

此模块负责显示宠物的日志记录，包括健康、饮食和情绪记录。
使用Plotly生成交互式图表展示数据。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from supabase import Client

from utils.types import PetProfile, LogEntry, LogType, EmotionType
from utils.errors import handle_error, SupabaseQueryError

# 初始化会话状态
def init_log_state() -> None:
    """
    初始化日志相关的会话状态
    """
    if "view_logs" not in st.session_state:
        st.session_state.view_logs = None
    if "log_filter" not in st.session_state:
        st.session_state.log_filter = "all"
    if "log_date_range" not in st.session_state:
        st.session_state.log_date_range = 30  # 默认显示30天

# 渲染日志界面
def render_log_interface(pet: Optional[PetProfile]) -> None:
    """
    渲染宠物日志界面
    
    Args:
        pet: 宠物档案信息
    """
    if not pet:
        st.error("未找到宠物信息")
        return
    
    st.title(f"📊 {pet['name']} 的成长记录")
    
    # 宠物基本信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("年龄", f"{pet['age']}岁")
    with col2:
        st.metric("品种", pet['breed'])
    with col3:
        st.metric("体重", f"{pet['weight']}kg")
    
    # 筛选选项
    col1, col2 = st.columns(2)
    with col1:
        log_type = st.selectbox(
            "日志类型",
            ["全部", "健康", "饮食", "情绪"],
            index=0
        )
        st.session_state.log_filter = "all" if log_type == "全部" else log_type.lower()
    
    with col2:
        date_range = st.selectbox(
            "时间范围",
            ["最近7天", "最近30天", "最近90天", "全部"],
            index=1
        )
        if date_range == "最近7天":
            st.session_state.log_date_range = 7
        elif date_range == "最近30天":
            st.session_state.log_date_range = 30
        elif date_range == "最近90天":
            st.session_state.log_date_range = 90
        else:
            st.session_state.log_date_range = 0  # 0表示全部
    
    # 获取日志数据
    try:
        logs = get_pet_logs(pet["id"])
        if logs:
            # 渲染情绪变化图谱
            render_emotion_chart(logs, pet["name"])
            
            # 渲染行为建议
            render_behavior_recommendations(pet)
            
            # 渲染其他图表
            render_log_charts(logs, pet["name"])
            
            # 渲染日志列表
            render_log_list(logs)
        else:
            st.info(f"还没有为 {pet['name']} 添加任何记录")
    except Exception as e:
        handle_error(e)
        st.error("获取日志数据失败，请稍后重试")

# 获取宠物日志
def get_pet_logs(pet_id: str) -> List[LogEntry]:
    """
    从数据库获取宠物日志
    
    Args:
        pet_id: 宠物ID
    
    Returns:
        List[LogEntry]: 日志列表
    """
    try:
        # 构建查询
        query = st.session_state.supabase.table("logs").select("*").eq("pet_id", pet_id)
        
        # 应用日期过滤
        if st.session_state.log_date_range > 0:
            date_limit = datetime.now() - timedelta(days=st.session_state.log_date_range)
            query = query.gte("date", date_limit.isoformat())
        
        # 应用类型过滤
        if st.session_state.log_filter != "all":
            query = query.eq("log_type", st.session_state.log_filter)
        
        # 执行查询
        result = query.order("date", desc=True).execute()
        
        if not result.data:
            return []
        
        return result.data
    except Exception as e:
        raise SupabaseQueryError(f"获取日志失败: {str(e)}")

# 渲染日志图表
def render_log_charts(logs: List[LogEntry], pet_name: str) -> None:
    """
    渲染日志图表
    
    Args:
        logs: 日志列表
        pet_name: 宠物名称
    """
    # 转换为DataFrame
    df = pd.DataFrame(logs)
    df['date'] = pd.to_datetime(df['date'])
    
    # 创建子图
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("健康记录", "饮食记录", "情绪记录"),
        vertical_spacing=0.1,
        shared_xaxes=True
    )
    
    # 颜色映射
    colors = {
        'health': '#FF9999',
        'food': '#66B2FF',
        'mood': '#99FF99'
    }
    
    # 添加健康记录
    health_logs = df[df['log_type'] == 'health']
    if not health_logs.empty:
        fig.add_trace(
            go.Scatter(
                x=health_logs['date'],
                y=health_logs['sentiment'],
                mode='lines+markers',
                name='健康状态',
                line=dict(color=colors['health']),
                hovertemplate="日期: %{x}<br>状态: %{y:.2f}<extra></extra>"
            ),
            row=1, col=1
        )
    
    # 添加饮食记录
    food_logs = df[df['log_type'] == 'food']
    if not food_logs.empty:
        fig.add_trace(
            go.Scatter(
                x=food_logs['date'],
                y=food_logs['sentiment'],
                mode='lines+markers',
                name='饮食状态',
                line=dict(color=colors['food']),
                hovertemplate="日期: %{x}<br>状态: %{y:.2f}<extra></extra>"
            ),
            row=2, col=1
        )
    
    # 添加情绪记录
    mood_logs = df[df['log_type'] == 'mood']
    if not mood_logs.empty:
        # 情绪类型映射
        emotion_map = {
            'happy': 1.0,
            'excited': 0.8,
            'calm': 0.5,
            'neutral': 0.0,
            'anxious': -0.5,
            'sad': -0.8,
            'angry': -1.0
        }
        
        # 转换情绪类型为数值
        mood_logs['emotion_value'] = mood_logs['emotion_type'].map(emotion_map)
        
        fig.add_trace(
            go.Scatter(
                x=mood_logs['date'],
                y=mood_logs['emotion_value'],
                mode='lines+markers',
                name='情绪状态',
                line=dict(color=colors['mood']),
                hovertemplate="日期: %{x}<br>情绪: %{customdata}<extra></extra>",
                customdata=mood_logs['emotion_type']
            ),
            row=3, col=1
        )
    
    # 更新布局
    fig.update_layout(
        height=800,
        title_text=f"{pet_name} 的成长记录",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # 更新Y轴范围
    fig.update_yaxes(range=[-1, 1], row=1, col=1)
    fig.update_yaxes(range=[-1, 1], row=2, col=1)
    fig.update_yaxes(range=[-1, 1], row=3, col=1)
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True)

# 渲染日志列表
def render_log_list(logs: List[LogEntry]) -> None:
    """
    渲染日志列表
    
    Args:
        logs: 日志列表
    """
    st.subheader("📝 详细记录")
    
    # 日志类型图标
    type_icons = {
        'health': '🏥',
        'food': '🍽️',
        'mood': '😊'
    }
    
    # 情绪图标
    emotion_icons = {
        'happy': '😊',
        'excited': '🤗',
        'calm': '😌',
        'neutral': '😐',
        'anxious': '😰',
        'sad': '😢',
        'angry': '😠'
    }
    
    # 显示日志
    for log in logs:
        with st.expander(f"{type_icons.get(log['log_type'], '📝')} {log['date'][:10]} - {log['content'][:50]}..."):
            st.write(f"**内容**: {log['content']}")
            
            # 显示情绪分析（如果有）
            if log['log_type'] == 'mood' and log['emotion_type']:
                emotion = log['emotion_type']
                st.write(f"**情绪**: {emotion_icons.get(emotion, '😐')} {emotion}")
            
            # 显示AI分析（如果有）
            if log['ai_analysis']:
                st.write(f"**AI分析**: {log['ai_analysis']}")
            
            # 显示时间
            st.caption(f"记录时间: {log['date']}")

def render_emotion_chart(logs: List[LogEntry], pet_name: str) -> None:
    """
    渲染情绪变化图谱
    
    Args:
        logs: 日志列表
        pet_name: 宠物名称
    """
    # 转换为DataFrame
    df = pd.DataFrame(logs)
    df['date'] = pd.to_datetime(df['date'])
    
    # 创建情绪变化图表
    fig = go.Figure()
    
    # 情绪颜色映射
    emotion_colors = {
        'happy': '#FFD700',    # 金色
        'excited': '#FF69B4',  # 粉红色
        'calm': '#98FB98',     # 浅绿色
        'neutral': '#87CEEB',  # 天蓝色
        'anxious': '#DDA0DD',  # 梅红色
        'sad': '#4682B4',      # 钢蓝色
        'angry': '#CD5C5C'     # 印度红
    }
    
    # 情绪图标映射
    emotion_icons = {
        'happy': '😊',
        'excited': '🤗',
        'calm': '😌',
        'neutral': '😐',
        'anxious': '😰',
        'sad': '😢',
        'angry': '😠'
    }
    
    # 添加情绪变化线
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['sentiment'],
        mode='lines+markers',
        name='情绪值',
        line=dict(color='#666666', width=2),
        hovertemplate="日期: %{x}<br>情绪值: %{y:.2f}<extra></extra>"
    ))
    
    # 添加情绪点
    for emotion in emotion_colors.keys():
        emotion_logs = df[df['emotion_type'] == emotion]
        if not emotion_logs.empty:
            fig.add_trace(go.Scatter(
                x=emotion_logs['date'],
                y=emotion_logs['sentiment'],
                mode='markers',
                name=f"{emotion_icons[emotion]} {emotion}",
                marker=dict(
                    color=emotion_colors[emotion],
                    size=12,
                    symbol='circle'
                ),
                hovertemplate="日期: %{x}<br>情绪: %{customdata}<extra></extra>",
                customdata=[f"{emotion_icons[emotion]} {emotion}"] * len(emotion_logs)
            ))
    
    # 更新布局
    fig.update_layout(
        title=f"📊 {pet_name} 的情绪变化趋势",
        xaxis_title="日期",
        yaxis_title="情绪值 (-1 到 1)",
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            range=[-1, 1],
            ticktext=['非常消极', '消极', '中性', '积极', '非常积极'],
            tickvals=[-1, -0.5, 0, 0.5, 1]
        )
    )
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True)

def render_behavior_recommendations(pet: PetProfile) -> None:
    """
    渲染行为建议
    
    Args:
        pet: 宠物档案
    """
    try:
        # 获取最近的日志
        logs = get_pet_logs(pet["id"])
        
        # 初始化行为分析器
        analyzer = BehaviorAnalyzer()
        
        # 生成建议
        recommendations = analyzer.generate_behavior_recommendation(logs, pet)
        
        # 显示建议
        st.subheader("💡 行为建议")
        
        # 按优先级分组
        priority_groups = {
            "高": [],
            "中": [],
            "低": []
        }
        
        for rec in recommendations:
            priority_groups[rec["priority"]].append(rec)
        
        # 显示高优先级建议
        if priority_groups["高"]:
            st.markdown("#### 🔴 重要建议")
            for rec in priority_groups["高"]:
                with st.expander(f"{rec['type']} - {rec['category']}", expanded=True):
                    st.write(rec["content"])
        
        # 显示中优先级建议
        if priority_groups["中"]:
            st.markdown("#### 🟡 一般建议")
            for rec in priority_groups["中"]:
                with st.expander(f"{rec['type']} - {rec['category']}"):
                    st.write(rec["content"])
        
        # 显示低优先级建议
        if priority_groups["低"]:
            st.markdown("#### 🟢 日常建议")
            for rec in priority_groups["低"]:
                with st.expander(f"{rec['type']} - {rec['category']}"):
                    st.write(rec["content"])
                    
    except Exception as e:
        handle_error(e)
        st.error("生成行为建议失败，请稍后重试") 