import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import plotly.graph_objects as go

# 加载 API 密钥
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 设置路径
base_dir = "data"
pets_dir = os.path.join(base_dir, "pets")
index_path = os.path.join(base_dir, "pet_index.json")
os.makedirs(pets_dir, exist_ok=True)

# 初始化状态
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "view_logs" not in st.session_state:
    st.session_state.view_logs = None
if "edit_pet" not in st.session_state:
    st.session_state.edit_pet = None

# 页面设置
st.set_page_config(page_title="Koda 宠物伙伴", page_icon="🐾")
st.title("🐶 Koda · AI 宠物伙伴")

# 加载宠物索引
if os.path.exists(index_path):
    with open(index_path, "r") as f:
        pet_index = json.load(f)
else:
    pet_index = {"selected": None, "pets": []}

# 侧边栏宠物列表 + 操作
with st.sidebar:
    st.subheader("🐾 宠物日志中心")
    for pet in pet_index.get("pets", []):
        pet_file = os.path.join(pets_dir, f"{pet}.json")
        if os.path.exists(pet_file):
            with open(pet_file, "r") as f:
                pet_data = json.load(f)
            col1, col2 = st.columns([4,1])
            with col1:
                if st.button(f"📘 {pet_data['name']}", key=f"view_{pet}"):
                    st.session_state.view_logs = pet
                    st.session_state.edit_pet = None
            with col2:
                if st.button("✏️", key=f"edit_{pet}"):
                    st.session_state.edit_pet = pet
                    st.session_state.view_logs = None
    st.markdown("---")
    if st.button("➕ 添加新宠物"):
        st.session_state.edit_pet = "new"
        st.session_state.view_logs = None

# 添加 / 编辑宠物资料表单
if st.session_state.edit_pet:
    editing = st.session_state.edit_pet
    is_new = editing == "new"
    st.subheader("✏️ 编辑宠物资料" if not is_new else "➕ 添加新宠物")

    default = {"name":"", "type":"狗", "breed":"", "age":0, "gender":"公", "size":"中型"}
    if not is_new:
        pet_file = os.path.join(pets_dir, f"{editing}.json")
        if os.path.exists(pet_file):
            with open(pet_file, "r") as f:
                default = json.load(f)

    with st.form("edit_pet_form"):
        name = st.text_input("宠物名字", value=default["name"])
        type_ = st.selectbox("宠物类型", ["狗", "猫", "其他"], index=["狗","猫","其他"].index(default["type"]))
        breed = st.text_input("宠物品种", value=default["breed"])
        age = st.number_input("宠物年龄", min_value=0, step=1, value=default["age"])
        gender = st.radio("性别", ["公", "母"], index=["公","母"].index(default["gender"]))
        size = st.selectbox("体型", ["小型", "中型", "大型"], index=["小型", "中型", "大型"].index(default["size"]))
        submitted = st.form_submit_button("保存")

        if submitted and name:
            path = os.path.join(pets_dir, f"{name.lower()}.json")
            pet_data = {
                "name": name,
                "type": type_,
                "breed": breed,
                "age": age,
                "gender": gender,
                "size": size
            }
            with open(path, "w") as f:
                json.dump(pet_data, f, ensure_ascii=False, indent=2)

            if name.lower() not in pet_index["pets"]:
                pet_index["pets"].append(name.lower())
            pet_index["selected"] = name.lower()
            with open(index_path, "w") as f:
                json.dump(pet_index, f, ensure_ascii=False, indent=2)

            st.success(f"{name} 已保存！")
            st.session_state.edit_pet = None
            st.session_state.view_logs = name.lower()
            st.rerun()
    st.stop()

# 宠物日志页面
if st.session_state.view_logs:
    pet_id = st.session_state.view_logs
    pet_file = os.path.join(pets_dir, f"{pet_id}.json")
    st.subheader(f"📘 {pet_id.capitalize()} 的日志")

    if st.button("⬅️ 返回对话主界面"):
        st.session_state.view_logs = None
        st.rerun()

    if os.path.exists(pet_file):
        with open(pet_file, "r") as f:
            profile = json.load(f)
        st.markdown(f"**品种：** {profile['breed']}  ")
        st.markdown(f"**性别：** {profile['gender']}  ")
        st.markdown(f"**年龄：** {profile['age']} 岁")

    st.markdown("---")
    log_types = {"health": "🩺 健康记录", "food": "🍽 饮食记录", "mood": "💬 情绪记录"}
    stats = {"health": 0, "food": 0, "mood": 0}
    dates = {"health": [], "food": [], "mood": []}

    for key, label in log_types.items():
        st.markdown(f"### {label}")
        for file in sorted(os.listdir(pets_dir)):
            if file.startswith(f"{pet_id}_{key}_"):
                with open(os.path.join(pets_dir, file), "r") as f:
                    record = json.load(f)
                st.markdown(f"**📅 {record['date']}**  ")
                if "input" in record:
                    st.markdown(f"✏️ {record['input']}  ")
                if "summary" in record:
                    st.markdown(f"💡 {record['summary']}  ")
                st.markdown("---")
                stats[key] += 1
                dates[key].append(record["date"])

    if st.checkbox("📈 显示成长趋势图"):
        st.markdown("## 📈 成长趋势")
        for key, label in log_types.items():
            if dates[key]:
                counts = {}
                for d in dates[key]:
                    counts[d] = counts.get(d, 0) + 1
                items = sorted(counts.items())
                x, y = zip(*items)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=list(x), y=list(y), mode='lines+markers'))
                fig.update_layout(title=label, xaxis_title="日期", yaxis_title="记录数")
                st.plotly_chart(fig, use_container_width=True)
    st.stop()

# 聊天界面（带意图识别与日志记录）
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

if len(st.session_state.chat_history) == 0:
    st.session_state.chat_history.append({"role": "assistant", "content": get_greeting()})

with st.container():
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.chat_message("user").markdown(chat["content"])
        else:
            st.chat_message("assistant").markdown(chat["content"])

    if prompt := st.chat_input("和我聊聊你和宠物今天的生活吧..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        matched_pet = None
        for pet in pet_index.get("pets", []):
            if pet.lower() in prompt.lower():
                matched_pet = pet
                break

        if matched_pet:
            pet_index["selected"] = matched_pet
            with open(index_path, "w") as f:
                json.dump(pet_index, f, ensure_ascii=False, indent=2)
            st.toast(f"🐾 我正在陪伴 {matched_pet.capitalize()}！")

        selected_pet = pet_index.get("selected")
        pet_profile = {}
        if selected_pet:
            path = os.path.join(pets_dir, f"{selected_pet}.json")
            if os.path.exists(path):
                with open(path, "r") as f:
                    pet_profile = json.load(f)

        history = [
            {"role": chat["role"], "content": chat["content"]}
            for chat in st.session_state.chat_history[-6:]
        ]

        if pet_profile:
            history.insert(0, {"role": "system", "content": f"当前宠物资料：{json.dumps(pet_profile, ensure_ascii=False)}。你是用户的宠物 AI 伙伴 Koda，请识别是否为健康、情绪或饮食日志，如果是，请总结并说明类型，否则正常陪聊。"})
        else:
            history.insert(0, {"role": "system", "content": "你是用户的宠物 AI 伙伴 Koda，请识别是否为健康、情绪或饮食日志，如果是，请总结并说明类型，否则正常陪聊。"})

        with st.spinner("Koda 正在思考..."):
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=history
            )
            reply = response.choices[0].message.content

        st.chat_message("assistant").markdown(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})

        # 日志识别 + 自动存储
        for log_type in ["health", "mood", "food"]:
            if f"类型：{log_type}" in reply:
                date = datetime.today().strftime("%Y-%m-%d")
                log_path = os.path.join(pets_dir, f"{selected_pet}_{log_type}_{date}.json")
                if not os.path.exists(log_path):
                    record = {
                        "type": log_type,
                        "date": date,
                        "input": prompt,
                        "summary": reply
                    }
                    with open(log_path, "w") as f:
                        json.dump(record, f, ensure_ascii=False, indent=2)
                break