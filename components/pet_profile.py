"""
宠物档案组件

此模块负责处理宠物档案的显示、添加、编辑和删除功能。
包括侧边栏渲染、宠物表单和删除逻辑。
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os
from supabase import Client

from utils.types import PetProfile
from utils.errors import handle_error, SupabaseQueryError, ValidationError
from utils.widget_key import get_stable_key, get_pet_key

# 初始化会话状态
def init_pet_state() -> None:
    """
    初始化宠物相关的会话状态
    """
    if "edit_pet" not in st.session_state:
        st.session_state.edit_pet = None
    if "delete_pet" not in st.session_state:
        st.session_state.delete_pet = None
    if "pet_form_data" not in st.session_state:
        st.session_state.pet_form_data = {}
    if "view_logs" not in st.session_state:
        st.session_state.view_logs = None
    if "selected_pet_index" not in st.session_state:
        st.session_state.selected_pet_index = 0

def handle_click(key: str, **kwargs) -> None:
    """
    处理按钮点击事件
    
    Args:
        key: 按钮标识
        **kwargs: 额外参数
    """
    if key == "add_pet":
        st.session_state.edit_pet = "new"
        st.session_state.pet_form_data = {}
    elif key == "edit_pet":
        st.session_state.edit_pet = kwargs.get("pet_id")
        st.session_state.pet_form_data = kwargs.get("pet_data", {})
    elif key == "delete_pet":
        st.session_state.delete_pet = kwargs.get("pet_id")
    elif key == "view_logs":
        st.session_state.view_logs = kwargs.get("pet_id")
    
    st.rerun()

# 渲染宠物侧边栏
def render_pet_sidebar(pet_profiles: List[PetProfile]) -> Optional[PetProfile]:
    """
    在侧边栏渲染宠物列表
    
    Args:
        pet_profiles: 宠物档案列表
        
    Returns:
        Optional[PetProfile]: 选中的宠物，如果没有选中则返回 None
    """
    # 创建侧边栏容器
    with st.sidebar:
        st.title("🐾 我的宠物")
        
        # 添加新宠物按钮
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 添加新宠物")
        with col2:
            if st.button("➕", key=get_stable_key("add_pet_btn"), help="添加新宠物", use_container_width=True):
                handle_click("add_pet")
        
        # 显示宠物列表
        if not pet_profiles:
            st.info("还没有添加宠物，点击上方按钮添加吧！")
            return None
            
        # 宠物选择器
        selected_index = st.radio(
            "选择宠物",
            options=range(len(pet_profiles)),
            format_func=lambda i: pet_profiles[i]["name"],
            key=get_stable_key("pet_selector"),
            horizontal=True
        )
        st.session_state.selected_pet_index = selected_index
        
        # 获取选中的宠物
        selected_pet = pet_profiles[selected_index]
        
        # 显示宠物列表
        for i, pet in enumerate(pet_profiles):
            pet_id = pet["id"]
            with st.expander(
                f"{pet['name']} ({pet['type']})", 
                expanded=(i == selected_index),
                key=get_pet_key("pet_expander", pet_id)
            ):
                # 显示宠物头像和信息
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    avatar = pet.get("avatar_url", "https://placekitten.com/100/100")
                    st.image(avatar, width=50)
                    st.write(f"**品种：**{pet['breed']}")
                    st.write(f"**性别：**{pet['gender']}")
                    st.write(f"**年龄：**{pet['age']}岁")
                
                with col2:
                    # 操作按钮
                    if st.button("✏️", key=get_pet_key("edit_btn", pet_id), help="编辑宠物信息", use_container_width=True):
                        handle_click("edit_pet", pet_id=pet_id, pet_data=pet.copy())
                    
                    if st.button("🗑️", key=get_pet_key("delete_btn", pet_id), help="删除宠物", use_container_width=True):
                        handle_click("delete_pet", pet_id=pet_id)
                    
                    if st.button("📊", key=get_pet_key("logs_btn", pet_id), help="查看成长记录", use_container_width=True):
                        handle_click("view_logs", pet_id=pet_id)
        
        return selected_pet

# 渲染宠物表单
def render_pet_form(supabase: Client, pet_profiles: List[PetProfile], user_id: str) -> None:
    """
    渲染宠物添加/编辑表单
    
    Args:
        supabase: Supabase客户端
        pet_profiles: 宠物档案列表
        user_id: 用户ID
    """
    # 确定是新建还是编辑
    is_new = st.session_state.edit_pet == "new"
    pet_id = None if is_new else st.session_state.edit_pet
    
    # 获取表单数据
    form_data = st.session_state.pet_form_data
    
    st.title("➕ 添加新宠物" if is_new else "✏️ 编辑宠物信息")
    
    # 表单
    with st.form("pet_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("宠物名称", value=form_data.get("name", ""))
            pet_type = st.selectbox("物种", ["猫", "狗", "兔子", "仓鼠", "其他"], 
                                  index=["猫", "狗", "兔子", "仓鼠", "其他"].index(form_data.get("type", "猫")) if form_data.get("type") else 0)
            age = st.number_input("年龄（岁）", min_value=0.0, max_value=30.0, value=float(form_data.get("age", 0.0)), step=0.1)
        
        with col2:
            breed = st.text_input("品种", value=form_data.get("breed", ""))
            gender = st.selectbox("性别", ["公", "母"], 
                               index=["公", "母"].index(form_data.get("gender", "公")) if form_data.get("gender") else 0)
            size = st.selectbox("体型", ["小型", "中型", "大型"],
                             index=["小型", "中型", "大型"].index(form_data.get("size", "小型")) if form_data.get("size") else 0)
        
        behavior = st.text_area("行为特征", value=form_data.get("behavior", ""))
        diet = st.text_area("饮食习惯", value=form_data.get("diet", ""))
        
        # 提交按钮
        submit_text = "添加宠物" if is_new else "保存修改"
        submitted = st.form_submit_button(submit_text)
    
    # 处理表单提交
    if submitted:
        try:
            # 验证必填字段
            if not name or not pet_type or not breed:
                raise ValidationError("宠物名称、物种和品种为必填项")
            
            # 准备数据
            pet_data = {
                "user_id": user_id,
                "name": name,
                "type": pet_type,
                "breed": breed,
                "age": age,
                "gender": gender,
                "size": size,
                "behavior": behavior if behavior else None,
                "diet": diet if diet else None,
                "created_at": datetime.now().isoformat() if is_new else form_data.get("created_at")
            }
            
            # 添加或更新宠物
            if is_new:
                result = supabase.table("pets").insert(pet_data).execute()
                if result.data:
                    st.success(f"成功添加宠物 {name}！")
                else:
                    raise SupabaseQueryError("添加宠物失败")
            else:
                result = supabase.table("pets").update(pet_data).eq("id", pet_id).execute()
                if result.data:
                    st.success(f"成功更新宠物 {name} 的信息！")
                else:
                    raise SupabaseQueryError("更新宠物信息失败")
            
            # 重置状态并刷新
            st.session_state.edit_pet = None
            st.session_state.pet_form_data = {}
            st.rerun()
            
        except Exception as e:
            handle_error(e)
            st.error("操作失败，请重试")
    
    # 取消按钮
    if st.button("取消"):
        st.session_state.edit_pet = None
        st.session_state.pet_form_data = {}
        st.rerun()

# 处理宠物删除
def handle_pet_deletion(supabase: Client) -> None:
    """
    处理宠物删除逻辑
    
    Args:
        supabase: Supabase客户端
    """
    if st.session_state.delete_pet:
        pet_id = st.session_state.delete_pet
        
        # 获取宠物信息
        try:
            result = supabase.table("pets").select("name").eq("id", pet_id).execute()
            if not result.data:
                raise SupabaseQueryError("未找到要删除的宠物")
            
            pet_name = result.data[0]["name"]
            
            # 确认删除
            st.warning(f"确定要删除宠物 {pet_name} 吗？此操作不可撤销。")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("确认删除"):
                    # 删除宠物
                    delete_result = supabase.table("pets").delete().eq("id", pet_id).execute()
                    if delete_result.data:
                        st.success(f"成功删除宠物 {pet_name}")
                        st.session_state.delete_pet = None
                        st.rerun()
                    else:
                        raise SupabaseQueryError("删除宠物失败")
            
            with col2:
                if st.button("取消"):
                    st.session_state.delete_pet = None
                    st.rerun()
                    
        except Exception as e:
            handle_error(e)
            st.error("删除失败，请重试") 