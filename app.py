import os
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
# CASE SYSTEM
# ======================
CASES = {
    "price_case": {
        "name": "服务报价谈判",
        "topic": "服务报价120元，买方希望压价到85元",
        "seller_opening": 120,
        "buyer_target": 85,
        "seller_min": 105
    },
    "salary_case": {
        "name": "薪资谈判",
        "topic": "岗位薪资谈判：HR给出12000元月薪，候选人期望15000元",
        "hr_opening": 12000,
        "hr_floor": 15000,
        "candidate_floor": 13000
    }
}

case_key = st.sidebar.selectbox("📦 Select Case", list(CASES.keys()))
case = CASES[case_key]

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
# LOGIN
# ======================
st.set_page_config(page_title="AI Negotiation Role System", layout="wide")
st.title("🤖 Role-Based Negotiation System (MVP+3R Rounds)")

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
st.sidebar.metric("Min Turns Required", MIN_TURNS)

st.title(f"💬 Negotiation Room - {case['name']}")
st.write("📌 Scenario:", case["topic"])

# ======================
# CHAT DISPLAY
# ======================
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# ======================
# AI ENGINE
# ======================
def get_ai_response(messages, case):

    if case_key == "price_case":
        system_prompt = f"""
You are SELLER.

Opening price: {case['seller_opening']}
Minimum price: {case['seller_min']}
Negotiate strategically.
"""
    else:
        system_prompt = f"""
You are HR in salary negotiation.

Opening salary: {case['hr_opening']}
HR floor limit: {case['hr_floor']}
Candidate expectation: {case['candidate_floor']}
Negotiate strategically.
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
        opening = f"初始报价：{case['seller_opening']}元。"
    else:
        opening = f"初始薪资：{case['hr_opening']}元/月。"

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
# EVALUATION（核心控制：至少3轮）
# ======================
def evaluate():

    convo = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])

    prompt = f"""
Evaluate negotiation performance.

Case: {case['name']}
Role: {st.session_state.role}

Conversation:
{convo}

Return JSON:
{{"score": int, "win_rate": float}}
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
        st.warning(f"⚠️ 请至少完成 {MIN_TURNS} 轮谈判后再评分")
    else:
        result = evaluate()

        st.write("🏆 Result")
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