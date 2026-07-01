import os
import json
import streamlit as st
import sqlite3
from openai import OpenAI

# ======================
# 🔐 API KEY
# ======================
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("Missing OPENAI_API_KEY")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# ======================
# CASE SYSTEM（优化版：加入“隐藏底线”）
# ======================
CASES = {
    "price_case": {
        "name": "服务报价谈判",
        "topic": "价格谈判场景：双方就服务单价进行协商",
        "buyer_target": 85,
        "buyer_floor_visible": 100,   # 给用户展示（UI）
        "seller_opening": 120,

        # ⭐隐藏设定（不展示）
        "seller_floor_hidden": 100
    },

    "salary_case": {
        "name": "薪资谈判",
        "topic": "薪资谈判场景：公司与候选人协商月薪",
        "candidate_target": 15000,
        "candidate_floor_visible": 13000,  # UI展示
        "hr_opening": 12000,

        # ⭐隐藏设定（不展示）
        "hr_floor_hidden": 15000
    }
}

case_key = st.sidebar.selectbox("📦 Select Case", list(CASES.keys()))
case = CASES[case_key]

# ======================
# UI 展示（只展示“可见信息”）
# ======================
st.sidebar.markdown("## 📌 Case Info")

if case_key == "price_case":
    st.sidebar.write("**类型：价格谈判**")
    st.sidebar.write("买家目标：85 元/件")
    st.sidebar.write(f"买家底线（公开）：{case['buyer_floor_visible']} 元/件")
    st.sidebar.write("卖家开价：120 元/件")

else:
    st.sidebar.write("**类型：薪资谈判**")
    st.sidebar.write("候选人目标：15000 元/月")
    st.sidebar.write(f"候选人底线（公开）：{case['candidate_floor_visible']} 元/月")
    st.sidebar.write("HR起薪：12000 元/月")

# ======================
# ⭐ 最少轮次控制
# ======================
MIN_TURNS = 3

# ======================
# DB
# ======================
DB_PATH = "app.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        case_name TEXT,
        role TEXT,
        score INTEGER,
        win_rate REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()

def save_record(user, case_name, role, score, win_rate):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO records VALUES (NULL,?,?,?,?,?)",
        (user, case_name, role, score, win_rate)
    )
    conn.commit()
    conn.close()

# ======================
# SESSION STATE
# ======================
if "user" not in st.session_state:
    st.session_state.user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "turns" not in st.session_state:
    st.session_state.turns = 0

if "role" not in st.session_state:
    st.session_state.role = None

if "turn_stage" not in st.session_state:
    st.session_state.turn_stage = "init"

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="AI Negotiation System", layout="wide")
st.title("🤖 Negotiation Lab (Hidden Constraint Version)")

# ======================
# LOGIN
# ======================
if st.session_state.user is None:
    st.subheader("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        st.session_state.user = u
        st.rerun()

    st.stop()

# ======================
# ROLE SELECTION
# ======================
if st.session_state.role is None:

    st.subheader("🎭 Choose Your Role")

    if case_key == "price_case":
        role_options = ["Buyer"]
    else:
        role_options = ["Candidate"]

    role = st.radio("Select role", role_options)

    if st.button("Confirm Role"):
        st.session_state.role = role
        st.session_state.turn_stage = "ai_opening"
        st.rerun()

    st.stop()

# ======================
# HEADER
# ======================
st.sidebar.success(f"User: {st.session_state.user}")
st.sidebar.info(f"Role: {st.session_state.role}")
st.sidebar.metric("Turns", st.session_state.turns)

st.title(f"💬 {case['name']}")
st.write("📌 Scenario:", case["topic"])

# ======================
# CHAT DISPLAY
# ======================
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# ======================
# AI ENGINE（关键：隐藏底线写入 system prompt）
# ======================
def get_ai_response(messages, case):

    if case_key == "price_case":
        system_prompt = f"""
You are SELLER in a price negotiation.

Context:
- Seller opening price: {case['seller_opening']} yuan
- Buyer target price: {case['buyer_target']} yuan

IMPORTANT HIDDEN RULE (do not reveal):
- Seller minimum acceptable price = {case['seller_floor_hidden']}

Behavior:
- Negotiate strategically
- Try to maximize profit
- Do NOT reveal your bottom line
"""

    else:
        system_prompt = f"""
You are HR in salary negotiation.

Context:
- HR opening salary: {case['hr_opening']} yuan/month
- Candidate target salary: {case['candidate_target']} yuan/month

IMPORTANT HIDDEN RULE (do not reveal):
- HR maximum salary limit = {case['hr_floor_hidden']} yuan/month

Behavior:
- Negotiate strategically
- Try to control cost
- Do NOT reveal internal budget constraints
"""

    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": system_prompt}] + messages
    )

    return resp.choices[0].message.content

# ======================
# AI OPENING
# ======================
if st.session_state.turn_stage == "ai_opening":

    if case_key == "price_case":
        opening = f"初始报价：{case['seller_opening']} 元/件。"
    else:
        opening = f"初始薪资：{case['hr_opening']} 元/月。"

    st.session_state.messages.append({
        "role": "assistant",
        "content": opening
    })

    st.session_state.turn_stage = "user_turn"
    st.rerun()

# ======================
# USER INPUT
# ======================
user_input = st.chat_input("Enter your negotiation message...")

if user_input:

    st.session_state.turns += 1

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.spinner("AI thinking..."):
        ai_reply = get_ai_response(st.session_state.messages, case)

    st.session_state.messages.append({
        "role": "assistant",
        "content": ai_reply
    })

    st.rerun()

# ======================
# ENHANCED EVALUATION
# ======================
def evaluate():

    convo = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])

    prompt = f"""
You are a negotiation coach.

Evaluate USER performance.

Case: {case['name']}
Scenario: {case['topic']}
Role: {st.session_state.role}

Conversation:
{convo}

Return STRICT JSON:

{{
  "score": int,
  "win_rate": float,
  "feedback": "3-5 sentences analysis",
  "suggestions": "3 concrete improvement points"
}}

Be strict, realistic, and educational.
"""

    r = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": prompt}]
    )

    return r.choices[0].message.content

# ======================
# BUTTONS
# ======================
st.markdown("---")

if st.button("📊 Evaluate"):

    if st.session_state.turns < MIN_TURNS:
        st.warning(f"⚠️ Please complete at least {MIN_TURNS} rounds before evaluation")
    else:
        result = evaluate()

        st.subheader("🏆 Evaluation Result")
        st.code(result)

        save_record(
            st.session_state.user,
            case["name"],
            st.session_state.role,
            80,
            0.85
        )

if st.button("🔄 Reset Session"):
    st.session_state.messages = []
    st.session_state.turns = 0
    st.session_state.turn_stage = "ai_opening"
    st.rerun()