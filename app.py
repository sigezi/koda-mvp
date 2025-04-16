"""
Koda AI 宠物陪伴系统主程序

提供宠物陪伴系统的主要功能，包括聊天、情绪分析、健康记录等。
"""

import os
import socket
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union, Tuple
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.connection import initialize_clients, USER_ID
from components.chat import render_chat_interface, init_chat_state
from components.log_display import render_log_interface, init_log_state
from components.pet_profile import render_pet_sidebar, render_pet_form, init_pet_state
from check_env import validate_env
from utils.types import PetProfile, LogEntry, MemoryFragment, MemoryContext
from utils.errors import handle_error, DatabaseError, ConnectionError
from utils.memory_manager import (
    retrieve_relevant_memories,
    merge_memory_fragments,
    update_memory_importance
)

from components.behavior_chart import render_behavior_analysis
from components.memory_display import render_memory_library
from components.emotion_response import render_emotion_response
from components.memory_manager import render_memory_manager

# Set page config
st.set_page_config(
    page_title="Koda AI 宠物陪伴系统",
    page_icon="🐱",
    layout="wide"
)

# Add global styles
st.markdown("""
    <style>
    .block-container {
        max-width: 1200px;
        padding: 2rem 3rem;
        margin: 0 auto;
    }
    
    /* 调整聊天界面样式 */
    .stChatMessage {
        margin-left: -6rem !important;
    }
    
    .stChatInput {
        margin-left: -6rem !important;
        max-width: calc(100% + 6rem) !important;
    }
    
    .stChatFloatingInputContainer {
        margin-left: -6rem !important;
        max-width: calc(100% + 6rem) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ✅ Validate environment variables
validate_env()

# Initialize session state
if "initialized" not in st.session_state:
    init_log_state()
    init_pet_state()
    init_chat_state()
    st.session_state.initialized = True

# Initialize clients with error handling
def initialize_application() -> Tuple[Any, Any]:
    """
    初始化应用程序所需的客户端连接
    
    Returns:
        Tuple[Any, Any]: OpenAI客户端和Supabase客户端
    
    Raises:
        ValueError: API密钥或URL格式错误
        ConnectionError: 连接错误
        Exception: 其他初始化错误
    """
    try:
        return initialize_clients()
    except ValueError as e:
        if "OpenAI API" in str(e):
            st.error("❌ OpenAI API 密钥错误")
            st.error(str(e))
            st.error("请检查 .env 文件中的 OPENAI_API_KEY 配置")
            st.stop()
        else:
            st.error(f"❌ URL 格式错误: {str(e)}")
            st.error("请检查 .env 文件中的 SUPABASE_URL 配置")
            st.stop()
    except socket.gaierror:
        st.error("❌ DNS 解析错误: 无法解析域名")
        st.error("可能的解决方案:")
        st.error("1. 检查 URL 是否正确")
        st.error("2. 确认网络连接是否正常")
        st.error("3. 尝试使用 Supabase 管理界面中显示的 URL")
        st.stop()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ 网络连接错误: {str(e)}")
        st.error("请检查网络连接是否正常")
        st.stop()
    except ConnectionError as e:
        st.error(f"❌ 连接错误: {str(e)}")
        st.error("请检查配置是否正确")
        st.stop()
    except Exception as e:
        st.error(f"❌ 初始化错误: {str(e)}")
        st.error("请检查配置是否正确")
        st.stop()

# Initialize clients with error handling
try:
    # Initialize clients
    openai_client, supabase = initialize_application()
    
    # Store OpenAI client in session state if not already stored
    if "openai_client" not in st.session_state:
        st.session_state.openai_client = openai_client
        
except ValueError as e:
    if "OpenAI API" in str(e):
        st.error("❌ OpenAI API 密钥错误")
        st.error(str(e))
        st.error("请检查 .env 文件中的 OPENAI_API_KEY 配置")
        st.stop()
    else:
        st.error(f"❌ URL 格式错误: {str(e)}")
        st.error("请检查 .env 文件中的 SUPABASE_URL 配置")
        st.stop()
    
except socket.gaierror as e:
    st.error(f"❌ DNS 解析错误: 无法解析域名")
    st.error("可能的解决方案:")
    st.error("1. 检查 URL 是否正确")
    st.error("2. 确认网络连接是否正常")
    st.error("3. 尝试使用 Supabase 管理界面中显示的 URL")
    st.stop()
    
except requests.exceptions.RequestException as e:
    st.error(f"❌ 网络连接错误: {str(e)}")
    st.error("请检查网络连接是否正常")
    st.stop()
    
except ConnectionError as e:
    st.error(f"❌ 连接错误: {str(e)}")
    st.error("请检查配置是否正确")
    st.stop()
    
except Exception as e:
    st.error(f"❌ 初始化错误: {str(e)}")
    st.error("请检查配置是否正确")
    st.stop()

st.title("🐶 Koda · AI 宠物伙伴")

# Get pet profiles with error handling
pet_profiles: List[PetProfile] = []
try:
    pet_profiles = supabase.table("pets").select("*").eq("user_id", USER_ID).order("created_at").execute().data or []
except Exception as e:
    handle_error(e)
    st.error("❌ 获取宠物信息失败，请刷新页面重试")

# Store user_id in session state for components
if USER_ID is not None:  # Ensure USER_ID is not None before assignment
    st.session_state.user_id = USER_ID
else:
    st.error("用户ID未设置，请在.env文件中设置USER_ID")
    st.stop()

# Create two columns for layout
col1, col2 = st.columns([1, 3])

# Render sidebar with pet profiles in the first column
with col1:
    render_pet_sidebar(pet_profiles)

# Render main content in the second column
with col2:
    # Render pet form if editing
    if st.session_state.edit_pet is not None:
        render_pet_form(supabase, pet_profiles, USER_ID)
    # Render log interface if viewing logs
    elif st.session_state.view_logs:
        # 查找选中的宠物
        selected_pet = None
        if st.session_state.view_logs:
            selected_pet = next((p for p in pet_profiles if p["id"] == st.session_state.view_logs), None)
        render_log_interface(selected_pet)
    # Render chat interface if not viewing logs or editing
    else:
        render_chat_interface(pet_profiles)

# ✅ Growth chart
if st.session_state.view_logs and pet_profiles:
    pet_id = st.session_state.view_logs
    pet = next((p for p in pet_profiles if p["id"] == pet_id), None)
    if pet:
        st.subheader(f"📘 {pet['name']} 的成长记录")
        st.markdown(f"**年龄**：{pet['age']}岁  ")
        
        try:
            # Get log data
            logs = supabase.table("logs").select("*").eq("pet_id", pet_id).order("date").execute().data
            
            if logs:
                # Convert to DataFrame
                df = pd.DataFrame(logs)
                df['date'] = pd.to_datetime(df['date'])
                
                # Count logs by type and date
                log_counts = df.groupby(['date', 'log_type']).size().unstack(fill_value=0)
                
                # Create line chart
                fig = go.Figure()
                
                colors = {
                    'health': '#FF9999',
                    'food': '#66B2FF',
                    'mood': '#99FF99'
                }
                
                for log_type in ['health', 'food', 'mood']:
                    if log_type in log_counts.columns:
                        # 使用 numpy 的 rolling 函数计算移动平均
                        rolling_mean = np.convolve(log_counts[log_type], np.ones(7)/7, mode='valid')
                        dates = log_counts.index[6:]  # 调整日期范围以匹配移动平均
                        
                        fig.add_trace(go.Scatter(
                            x=dates,
                            y=rolling_mean,
                            name={'health': '健康', 'food': '饮食', 'mood': '情绪'}[log_type],
                            line=dict(color=colors[log_type]),
                            hovertemplate="日期: %{x}<br>记录数: %{y:.1f}<extra></extra>"
                        ))
                
                fig.update_layout(
                    title="每日记录统计 (7日移动平均)",
                    xaxis_title="日期",
                    yaxis_title="记录数",
                    hovermode='x unified',
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            handle_error(e)
            st.error("获取日志数据失败，请稍后重试")

# 初始化页面配置
st.sidebar.title("导航")
page = st.sidebar.radio(
    "选择页面",
    ["聊天", "行为分析", "成长日志", "记忆库", "情绪分析", "健康记录", "记忆管理"]
)

# 渲染宠物选择器
current_pet = render_pet_sidebar(pet_profiles)

if current_pet:
    st.session_state.current_pet = current_pet
    
    # 根据页面选择渲染不同内容
    if page == "聊天":
        render_chat_interface(current_pet)
        
    elif page == "行为分析":
        render_behavior_analysis(current_pet)
        
    elif page == "成长日志":
        render_log_interface(current_pet)
        
    elif page == "记忆库":
        # 获取记忆数据
        memories = retrieve_relevant_memories(
            pet_id=current_pet["id"],
            limit=100
        )
        
        # 按类型组织记忆
        memory_dict = {
            "all": memories,
            "conversation": [m for m in memories if m.context == "conversation"],
            "behavior": [m for m in memories if m.context == "behavior"],
            "emotion": [m for m in memories if m.context == "emotion"]
        }
        
        # 渲染记忆库界面
        render_memory_library(memory_dict)
        
    elif page == "情绪分析":
        render_emotion_response(current_pet["id"], openai_client, supabase)
        
    elif page == "健康记录":
        render_log_interface(current_pet)
        
    elif page == "记忆管理":
        render_memory_manager(current_pet["id"])
        
else:
    st.info("请先添加一个宠物档案")
