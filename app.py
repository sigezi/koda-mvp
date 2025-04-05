# ✅ Koda v2.9 - 支持 Supabase 用戶隔離，日誌寫入與聊天升級

import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client
import plotly.graph_objects as go
import pandas as pd

# ✅ 加載環境變量
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
USER_ID = os.getenv("USER_ID", "user_001")

client = OpenAI(api_key=OPENAI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ 初始化狀態
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "view_logs" not in st.session_state:
    st.session_state.view_logs = None
if "edit_pet" not in st.session_state:
    st.session_state.edit_pet = None

st.set_page_config(page_title="Koda 宠物伙伴", page_icon="🐾")
st.title("🐶 Koda · AI 宠物伙伴")

# ✅ 加載用戶寵物資料
pet_profiles = supabase.table("pets").select("*").eq("user_id", USER_ID).order("created_at").execute().data or []

# ✅ 構建語境描述
pet_desc_list = []
for p in pet_profiles:
    desc = f"{p['name']}（{p['type']}，{p['breed']}，{p['age']}岁）"
    if p.get("behavior"):
        desc += f"。行为：{p['behavior']}"
    if p.get("diet"):
        desc += f"。饮食：{p['diet']}"
    pet_desc_list.append(desc)
pet_intro = "、".join(pet_desc_list)
pet_context = f"你是温柔的 AI 朋友 Koda，正陪伴主人（用戶ID：{USER_ID}），他養了這些寵物：{pet_intro}。請用朋友語氣陪伴他們，理解寵物的行為與情緒，不要使用機器語言，也不要糾正用戶內容。"

# ✅ 側邊欄 - 寵物日誌中心
with st.sidebar:
    st.subheader("🐾 宠物日志中心")
    for pet in pet_profiles:
        pet_id = pet["id"]
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"📘 {pet['name']}", key=f"view_{pet_id}"):
                st.session_state.view_logs = pet_id
                st.session_state.edit_pet = None
        with col2:
            if st.button("✏️", key=f"edit_{pet_id}"):
                st.session_state.edit_pet = pet_id
                st.session_state.view_logs = None
    st.markdown("---")
    if st.button("➕ 添加新宠物"):
        st.session_state.edit_pet = "new"
        st.session_state.view_logs = None

# ✅ 添加 / 修改宠物
if st.session_state.edit_pet:
    pet_id = st.session_state.edit_pet
    is_new = pet_id == "new"
    st.subheader("✏️ 修改宠物资料" if not is_new else "📝 添加新宠物")

    if not is_new:
        pet_data = next((p for p in pet_profiles if p["id"] == pet_id), {})
    else:
        pet_data = {"name": "", "type": "狗", "breed": "", "age": 1,
                    "gender": "公", "size": "中型", "behavior": "", "diet": ""}

    with st.form("pet_form"):
        name = st.text_input("名字", value=pet_data["name"])
        type_ = st.selectbox("类型", ["狗", "猫", "其他"], index=["狗", "猫", "其他"].index(pet_data.get("type", "狗")))
        breed = st.text_input("品种", value=pet_data["breed"])
        age = st.number_input("年龄（岁）", min_value=0, max_value=50, value=pet_data["age"])
        gender = st.radio("性别", ["公", "母"], index=["公", "母"].index(pet_data["gender"]))
        size = st.selectbox("体型", ["小型", "中型", "大型"], index=["小型", "中型", "大型"].index(pet_data["size"]))
        behavior = st.text_area("行为偏好", value=pet_data.get("behavior", ""))
        diet = st.text_area("饮食偏好", value=pet_data.get("diet", ""))
        submitted = st.form_submit_button("保存")

    if submitted:
        record = {
            "user_id": USER_ID,
            "name": name, "type": type_, "breed": breed, "age": age,
            "gender": gender, "size": size, "behavior": behavior, "diet": diet
        }
        if is_new:
            supabase.table("pets").insert(record).execute()
            st.success(f"欢迎 {name} 加入 Koda 家族！")
        else:
            supabase.table("pets").update(record).eq("id", pet_id).execute()
            st.success("宠物资料已更新 ✅")
        st.session_state.edit_pet = None
        st.rerun()

# ✅ 成長日誌與圖譜
if st.session_state.view_logs:
    pet_id = st.session_state.view_logs
    pet = next((p for p in pet_profiles if p["id"] == pet_id), {})
    st.subheader(f"📘 {pet['name']} 的成长记录")
    st.markdown(f"**年龄**：{pet['age']}岁")
    st.markdown(f"**品种**：{pet['breed']} / {pet['type']}")
    if pet.get("behavior"):
        st.markdown(f"**行为偏好**：{pet['behavior']}")
    if pet.get("diet"):
        st.markdown(f"**饮食偏好**：{pet['diet']}")

    st.markdown("---")
    st.markdown("### 📈 成长图谱（按需加载）")

    def plot_log_chart(log_type):
        logs = supabase.table("logs").select("*").eq("pet_id", pet_id).eq("user_id", USER_ID).eq("log_type", log_type).order("date", desc=True).limit(30).execute().data
        if logs:
            df = pd.DataFrame(logs)
            fig = go.Figure(go.Bar(x=df['date'], y=[1]*len(df), text=df['summary'], hoverinfo="text"))
            fig.update_layout(title=f"{log_type.upper()} 记录趋势", yaxis=dict(visible=False))
            st.plotly_chart(fig)
        else:
            st.info("暂无记录")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("加载健康图谱"):
            plot_log_chart("health")
    with col2:
        if st.button("加载饮食图谱"):
            plot_log_chart("food")
    with col3:
        if st.button("加载情绪图谱"):
            plot_log_chart("mood")

    if st.button("🔙 返回聊天界面"):
        st.session_state.view_logs = None
        st.rerun()
    st.stop()

# ✅ 初次問候
if len(st.session_state.chat_history) == 0:
    def get_greeting():
        hour = datetime.now().hour
        if hour < 5:
            return "夜深了，还好吗？我在呢 🌙"
        elif hour < 11:
            return "早上好呀 ☀️ 今天和宝贝有什么计划？"
        elif hour < 17:
            return "下午好 ☕ 要不要休息一下陪陪你们？"
        elif hour < 22:
            return "晚上好呀 🏠 今天我们有什么值得记录的？"
        else:
            return "夜晚降临了～该和毛孩子抱一抱啦 🐾"
    st.session_state.chat_history.append({"role": "assistant", "content": get_greeting()})

# ✅ 聊天區域
for chat in st.session_state.chat_history:
    st.chat_message(chat["role"]).markdown(chat["content"])

if prompt := st.chat_input("和我聊聊你和宠物今天的生活吧..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    history = [{"role": chat["role"], "content": chat["content"]} for chat in st.session_state.chat_history[-6:]]
    history.insert(0, {"role": "system", "content": pet_context})

    with st.spinner("Koda 正在认真聆听..."):
        reply = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=history
        ).choices[0].message.content

    st.chat_message("assistant").markdown(reply)
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # ✅ 自動分類日誌
    def detect_log_type(text):
        lower = text.lower()
        if any(x in lower for x in ["吃", "喂", "煮"]): return "food"
        if any(x in lower for x in ["焦虑", "开心", "情绪", "烦"]): return "mood"
        if any(x in lower for x in ["便便", "拉", "吐", "检查", "体检"]): return "health"
        return None

    log_type = detect_log_type(prompt)
    if log_type and pet_profiles:
        supabase.table("logs").insert({
            "user_id": USER_ID,
            "pet_id": pet_profiles[0]["id"],
            "log_type": log_type,
            "summary": prompt,
            "date": datetime.today().strftime("%Y-%m-%d")
        }).execute()
        st.toast(f"📝 已记录为 {log_type} 日志")