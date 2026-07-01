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
    "case1": {
        "name": "服务报价谈判",
        "topic": "服务报价120元，买方希望压价到85元",
        "price": 120,
        "buyer_target": 85,
        "seller_min": 105
    }
}

case = CASES["case1"]

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

# ======================
# LOGIN (SIMPLE)
# ======================
st.set_page_config(page_title="AI Negotiation Role System", layout="wide")
st.title("🤖 Role-Based Negotiation System")

if st.session_state.user is None:

    st.subheader("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        st.session_state.user = u
        st.success("Login success")
        st.rerun()

    st.stop()

# ======================
# ROLE SELECTION (NEW)
# ======================
if st.session_state.role is None:

    st.subheader("🎭 Choose Your Role")

    role = st.radio("Select role", ["Buyer", "Seller"])

    if st.button("Confirm Role"):
        st.session_state.role = role
        st.rerun()

    st.stop()

# ======================
# UI HEADER
# ======================
st.sidebar.success(f"User: {st.session_state.user}")
st.sidebar.info(f"Role: {st.session_state.role}")
st.sidebar.metric("Turns", st.session_state.turns)

st.title(f"💬 Negotiation Room - You are {st.session_state.role}")

# ======================
# CHAT DISPLAY
# ======================
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# ======================
# AI ENGINE (DYNAMIC ROLE)
# ======================
def get_ai_response(messages, user_role):

    if user_role == "Buyer":
        ai_role = "Seller"
        system_prompt = f"""
You are a professional negotiation AI acting as SELLER.

Case:
{case['topic']}

Rules:
- You are SELLER
- Minimum acceptable price: {case['seller_min']}
- Try to maximize price
"""
    else:
        ai_role = "Buyer"
        system_prompt = f"""
You are a professional negotiation AI acting as BUYER.

Case:
{case['topic']}

Rules:
- You are BUYER
- Target price: {case['buyer_target']}
- Try to minimize price
"""

    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": system_prompt}] + messages
    )

    return resp.choices[0].message.content

# ======================
# INPUT FLOW
# ======================
user_input = st.chat_input("Enter your negotiation message...")

if user_input:

    st.session_state.turns += 1

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.spinner("AI thinking..."):
        ai_reply = get_ai_response(st.session_state.messages, st.session_state.role)

    st.session_state.messages.append({
        "role": "assistant",
        "content": ai_reply
    })

    st.rerun()

# ======================
# EVALUATION (ROLE AWARE)
# ======================
def evaluate():

    convo = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])

    prompt = f"""
Evaluate USER performance in negotiation.

User role: {st.session_state.role}

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
# BUTTON
# ======================
st.markdown("---")

if st.button("📊 Evaluate"):
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

# ======================
# RESET
# ======================
if st.button("🔄 Reset Session"):
    st.session_state.messages = []
    st.session_state.turns = 0
    st.rerun()