import os
import streamlit as st
import sqlite3
from openai import OpenAI

# ======================
# 🔐 API Key 安全配置（核心升级）
# ======================

# 优先读取 Streamlit Cloud secrets，其次读取本地环境变量
api_key = None

if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("❌ 未检测到 OPENAI_API_KEY，请在 Streamlit secrets 或环境变量中配置")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# ======================
# CASE系统
# ======================

CASES = {
    "case1": {
        "name": "服务报价谈判",
        "topic": "服务报价120元，买方希望压价到85元",
        "buyer_budget": 85,
        "seller_price": 120,
        "seller_min": 105
    },
    "case2": {
        "name": "咨询服务谈判",
        "topic": "咨询服务报价200元",
        "buyer_budget": 150,
        "seller_price": 200,
        "seller_min": 170
    }
}

# ======================
# 数据库初始化
# ======================

DB_PATH = "app.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        case_name TEXT,
        winner TEXT,
        buyer_score INTEGER,
        seller_score INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ======================
# 用户系统
# ======================

def register(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def login(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )
    result = c.fetchone()
    conn.close()
    return result is not None


def save_record(username, case_name, winner, buyer_score, seller_score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO records (username, case_name, winner, buyer_score, seller_score)
    VALUES (?, ?, ?, ?, ?)
    """, (username, case_name, winner, buyer_score, seller_score))
    conn.commit()
    conn.close()


def get_records(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT case_name, winner, buyer_score, seller_score FROM records WHERE username=?",
        (username,)
    )
    data = c.fetchall()
    conn.close()
    return data

# ======================
# 页面配置
# ======================

st.set_page_config(page_title="AI谈判SaaS系统", layout="wide")
st.title("🤖 AI谈判训练平台 SaaS版")

# ======================
# Session状态
# ======================

if "user" not in st.session_state:
    st.session_state.user = None

# ======================
# 登录/注册
# ======================

if st.session_state.user is None:

    st.subheader("🔐 登录 / 注册")

    mode = st.radio("选择模式", ["登录", "注册"])
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")

    # ======================
    # 注册（只注册，不登录）
    # ======================
    if mode == "注册":
        if st.button("注册"):
            if register(username, password):
                st.success("注册成功，请返回登录")
            else:
                st.error("用户已存在")

    # ======================
    # 登录（唯一进入系统入口）
    # ======================
    if mode == "登录":
        if st.button("登录"):
            if login(username, password):
                st.session_state.user = username
                st.success("登录成功")
                st.rerun()   # ⭐只有登录才进入系统
            else:
                st.error("登录失败")

    st.stop()

# ======================
# 登录成功页面
# ======================

st.success(f"欢迎你：{st.session_state.user}")

case_id = st.selectbox("📦 选择谈判案例", list(CASES.keys()))
case = CASES[case_id]

st.write("📌", case["topic"])

# ======================
# 谈判系统
# ======================

if st.button("▶️ 开始谈判"):

    buyer_history = []
    seller_history = ""

    for i in range(3):

        # ===== 买方 =====
        buyer_prompt = f"""
你是买方。
预算上限：{case['buyer_budget']}
请推进谈判，不要重复。
"""

        buyer_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": buyer_prompt},
                {"role": "user", "content": case["topic"]}
            ]
        ).choices[0].message.content

        buyer_history.append(buyer_resp)

        st.markdown(f"🟦 买方：{buyer_resp}")

        # ===== 卖方 =====
        seller_prompt = f"""
你是卖方。
底价：{case['seller_min']}
请推进谈判，不要重复。
"""

        seller_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": seller_prompt},
                {"role": "user", "content": buyer_resp}
            ]
        ).choices[0].message.content

        seller_history += seller_resp

        st.markdown(f"🟥 卖方：{seller_resp}")

    # ======================
    # 评分系统
    # ======================

    buyer_score = len(buyer_history) * 20
    seller_score = len(seller_history) // 50

    winner = "buyer" if buyer_score > seller_score else "seller"

    st.subheader("📊 评分结果")
    st.write("买方得分：", buyer_score)
    st.write("卖方得分：", seller_score)
    st.write("🏆 胜者：", winner)

    # ======================
    # 存储 SaaS 数据
    # ======================

    save_record(
        st.session_state.user,
        case["name"],
        winner,
        buyer_score,
        seller_score
    )

# ======================
# 历史记录
# ======================

st.markdown("---")
st.subheader("📚 我的历史记录")

records = get_records(st.session_state.user)

if records:
    for r in records:
        st.write({
            "case": r[0],
            "winner": r[1],
            "buyer_score": r[2],
            "seller_score": r[3]
        })
else:
    st.info("暂无记录")