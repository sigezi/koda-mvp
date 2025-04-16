"""
组件 key 生成工具

此模块提供用于生成稳定且唯一的 Streamlit 组件 key 的工具函数。
"""

import uuid
import streamlit as st
from typing import Optional

def get_stable_key(name: str, suffix: Optional[str] = None) -> str:
    """
    生成稳定且唯一的组件 key
    
    Args:
        name: 组件基础名称
        suffix: 可选的后缀（如 pet_id）
        
    Returns:
        str: 稳定的组件 key
    """
    # 初始化 key 存储
    if "widget_keys" not in st.session_state:
        st.session_state.widget_keys = {}
    
    # 生成完整的 key 标识
    key_id = f"{name}_{suffix}" if suffix else name
    
    # 如果 key 不存在，生成一个新的
    if key_id not in st.session_state.widget_keys:
        st.session_state.widget_keys[key_id] = f"{key_id}_{uuid.uuid4()}"
    
    return st.session_state.widget_keys[key_id]

def get_pet_key(base_name: str, pet_id: str) -> str:
    """
    生成与特定宠物相关的组件 key
    
    Args:
        base_name: 组件基础名称
        pet_id: 宠物ID
        
    Returns:
        str: 稳定的组件 key
    """
    return get_stable_key(base_name, pet_id) 