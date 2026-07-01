import sqlite3
from db import DB_PATH

def login(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    SELECT * FROM users WHERE username=? AND password=?
    """, (username, password))

    result = c.fetchone()
    conn.close()

    return result is not None


def register(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute("""
        INSERT INTO users (username, password)
        VALUES (?, ?)
        """, (username, password))

        conn.commit()
        conn.close()
        return True

    except:
        return False