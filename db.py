import sqlite3

DB_PATH = "data/app.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 用户表
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # 谈判记录表
    c.execute("""
    CREATE TABLE IF NOT EXISTS negotiations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        case_name TEXT,
        winner TEXT,
        score TEXT,
        report TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_negotiation(username, case_name, winner, score, report):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    INSERT INTO negotiations (username, case_name, winner, score, report)
    VALUES (?, ?, ?, ?, ?)
    """, (username, case_name, winner, str(score), str(report)))

    conn.commit()
    conn.close()


def get_user_history(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    SELECT case_name, winner, score FROM negotiations
    WHERE username=?
    """, (username,))

    rows = c.fetchall()
    conn.close()
    return rows