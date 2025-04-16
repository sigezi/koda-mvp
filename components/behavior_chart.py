"""
行为图谱分析组件

此模块负责分析宠物行为数据并生成可视化图表。
主要功能包括：
- 加载最近7天的日志数据
- 生成行为建议
- 使用Plotly绘制交互式图表
- 展示用户建议提示
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Optional, TypedDict
from datetime import datetime, timedelta

from utils.types import PetProfile, LogEntry, LogType, EmotionType
from utils.errors import handle_error
from utils.supabase_client import get_pet_logs
from utils.behavior_analysis import BehaviorAnalyzer

# 【类型定义】
class BehaviorRecommendation(TypedDict):
    """行为建议数据结构"""
    type: str  # 建议类型
    content: str  # 建议内容
    priority: str  # 优先级（高/中/低）
    category: str  # 分类（情绪管理/运动健康/饮食管理/日常护理）

class DailyLogSummary(TypedDict):
    """每日日志汇总数据结构"""
    date: str  # 日期
    health_count: int  # 健康记录数
    food_count: int  # 饮食记录数
    mood_count: int  # 情绪记录数
    avg_sentiment: float  # 平均情感值
    main_emotion: Optional[str]  # 主要情绪

# 【数据获取】
def get_last_7days_logs_by_type(pet_id: str) -> Dict[str, List[LogEntry]]:
    """
    获取宠物最近7天的日志数据，按类型分类
    
    Args:
        pet_id: 宠物ID
        
    Returns:
        Dict[str, List[LogEntry]]: 按类型分类的日志列表
    """
    try:
        # 计算7天前的日期
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        # 获取所有日志
        logs = get_pet_logs(pet_id)
        
        # 过滤最近7天的日志
        recent_logs = [log for log in logs if log["date"] >= seven_days_ago]
        
        # 按类型分类
        logs_by_type = {
            "health": [],
            "food": [],
            "mood": []
        }
        
        for log in recent_logs:
            log_type = log["log_type"]
            if log_type in logs_by_type:
                logs_by_type[log_type].append(log)
        
        return logs_by_type
        
    except Exception as e:
        handle_error(e)
        return {"health": [], "food": [], "mood": []}

def generate_daily_summary(logs_by_type: Dict[str, List[LogEntry]]) -> List[DailyLogSummary]:
    """
    生成每日日志汇总数据
    
    Args:
        logs_by_type: 按类型分类的日志列表
        
    Returns:
        List[DailyLogSummary]: 每日日志汇总列表
    """
    # 合并所有日志
    all_logs = []
    for logs in logs_by_type.values():
        all_logs.extend(logs)
    
    # 按日期分组
    logs_by_date: Dict[str, List[LogEntry]] = {}
    for log in all_logs:
        date = log["date"][:10]  # 只取日期部分
        if date not in logs_by_date:
            logs_by_date[date] = []
        logs_by_date[date].append(log)
    
    # 生成每日汇总
    daily_summaries = []
    for date, logs in logs_by_date.items():
        # 统计各类型记录数
        health_count = len([log for log in logs if log["log_type"] == "health"])
        food_count = len([log for log in logs if log["log_type"] == "food"])
        mood_count = len([log for log in logs if log["log_type"] == "mood"])
        
        # 计算平均情感值
        sentiments = [log["sentiment"] for log in logs if log["sentiment"] is not None]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        # 获取主要情绪
        emotions = [log["emotion_type"] for log in logs if log["emotion_type"]]
        main_emotion = max(set(emotions), key=emotions.count) if emotions else None
        
        daily_summaries.append({
            "date": date,
            "health_count": health_count,
            "food_count": food_count,
            "mood_count": mood_count,
            "avg_sentiment": avg_sentiment,
            "main_emotion": main_emotion
        })
    
    return sorted(daily_summaries, key=lambda x: x["date"])

# 【行为建议】
def generate_behavior_recommendation(logs_by_type: Dict[str, List[LogEntry]], pet: PetProfile) -> List[BehaviorRecommendation]:
    """
    生成行为建议
    
    Args:
        logs_by_type: 按类型分类的日志列表
        pet: 宠物档案
        
    Returns:
        List[BehaviorRecommendation]: 行为建议列表
    """
    try:
        # 初始化行为分析器
        analyzer = BehaviorAnalyzer()
        
        # 合并所有日志
        all_logs = []
        for logs in logs_by_type.values():
            all_logs.extend(logs)
        
        # 生成建议
        recommendations = analyzer.generate_behavior_recommendation(all_logs, pet)
        return recommendations
        
    except Exception as e:
        handle_error(e)
        return []

# 【图表渲染】
def render_behavior_chart(pet: PetProfile) -> None:
    """
    渲染行为分析图表
    
    Args:
        pet: 宠物档案
    """
    try:
        # 获取最近7天的日志数据
        logs_by_type = get_last_7days_logs_by_type(pet["id"])
        
        # 生成每日汇总数据
        daily_summary = generate_daily_summary(logs_by_type)
        
        # 生成行为建议
        recommendations = generate_behavior_recommendation(logs_by_type, pet)
        
        # 创建图表
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("每日记录数量", "情绪变化趋势"),
            vertical_spacing=0.2,
            row_heights=[0.4, 0.6]
        )
        
        # 添加每日记录数量柱状图
        dates = [summary["date"] for summary in daily_summary]
        health_counts = [summary["health_count"] for summary in daily_summary]
        food_counts = [summary["food_count"] for summary in daily_summary]
        mood_counts = [summary["mood_count"] for summary in daily_summary]
        
        fig.add_trace(
            go.Bar(name="健康记录", x=dates, y=health_counts),
            row=1, col=1
        )
        fig.add_trace(
            go.Bar(name="饮食记录", x=dates, y=food_counts),
            row=1, col=1
        )
        fig.add_trace(
            go.Bar(name="情绪记录", x=dates, y=mood_counts),
            row=1, col=1
        )
        
        # 添加情绪变化趋势线图
        sentiments = [summary["avg_sentiment"] for summary in daily_summary]
        fig.add_trace(
            go.Scatter(
                name="情感值",
                x=dates,
                y=sentiments,
                mode="lines+markers",
                line=dict(color="blue")
            ),
            row=2, col=1
        )
        
        # 更新布局
        fig.update_layout(
            title_text=f"{pet['name']}的行为分析",
            showlegend=True,
            height=800
        )
        
        # 显示图表
        st.plotly_chart(fig, use_container_width=True)
        
        # 显示行为建议
        st.subheader("行为建议")
        for rec in recommendations:
            with st.expander(f"{rec['category']} - {rec['type']} ({rec['priority']}优先级)"):
                st.write(rec["content"])
                
    except Exception as e:
        handle_error(e)
        st.error("生成行为分析图表时出错")

def render_behavior_analysis(pet: PetProfile) -> None:
    """
    渲染行为分析页面
    
    Args:
        pet: 宠物档案
    """
    try:
        st.title(f"📊 {pet['name']}的行为分析")
        
        # 添加时间范围选择
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "开始日期",
                value=datetime.now() - timedelta(days=7),
                max_value=datetime.now()
            )
        with col2:
            end_date = st.date_input(
                "结束日期",
                value=datetime.now(),
                max_value=datetime.now()
            )
        
        # 添加分析类型选择
        analysis_type = st.radio(
            "分析类型",
            ["行为趋势", "情绪分析", "健康记录", "饮食记录"],
            horizontal=True
        )
        
        # 根据选择的分析类型显示不同的图表
        if analysis_type == "行为趋势":
            render_behavior_chart(pet)
        elif analysis_type == "情绪分析":
            st.info("情绪分析功能开发中...")
        elif analysis_type == "健康记录":
            st.info("健康记录分析功能开发中...")
        elif analysis_type == "饮食记录":
            st.info("饮食记录分析功能开发中...")
            
    except Exception as e:
        handle_error(e)
        st.error("渲染行为分析页面时出错") 