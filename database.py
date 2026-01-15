# ============================================
# database.py - SQLite data layer
# ============================================

import sqlite3
import threading
from datetime import datetime, timedelta

_DB_PATH = 'data.db'
_lock = threading.Lock()

def get_db():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _lock:
        conn = get_db()
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            FOREIGN KEY(admin_id) REFERENCES admins(user_id)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS private_groups (
            admin_id INTEGER PRIMARY KEY,
            group_id INTEGER,
            group_link TEXT,
            group_name TEXT,
            FOREIGN KEY(admin_id) REFERENCES admins(user_id)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS search_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            group_id INTEGER,
            group_link TEXT,
            group_name TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(admin_id) REFERENCES admins(user_id)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS rate_limits (
            admin_id INTEGER PRIMARY KEY,
            last_added_at TEXT
        )
        """)

        conn.commit()
        conn.close()

# ------------------ Settings ------------------

def get_setting(key, default=None):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        return row['value'] if row else default

def set_setting(key, value):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
        INSERT INTO settings(key, value) VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """, (key, value))
        conn.commit()
        conn.close()

# ------------------ Admins ------------------

def is_admin(user_id, super_admin_id):
    if user_id == super_admin_id:
        return True
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        exists = c.fetchone() is not None
        conn.close()
        return exists

def add_admin(user_id, username):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO admins(user_id, username) VALUES(?, ?)", (user_id, username))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

def remove_admin(user_id):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM keywords WHERE admin_id = ?", (user_id,))
        c.execute("DELETE FROM private_groups WHERE admin_id = ?", (user_id,))
        c.execute("DELETE FROM search_groups WHERE admin_id = ?", (user_id,))
        c.execute("DELETE FROM rate_limits WHERE admin_id = ?", (user_id,))
        conn.commit()
        conn.close()

def get_all_admins():
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT user_id, username FROM admins ORDER BY username COLLATE NOCASE")
        rows = c.fetchall()
        conn.close()
        return [(row['user_id'], row['username'] or f"User_{row['user_id']}") for row in rows]

# ------------------ Keywords ------------------

def add_keyword(admin_id, keyword):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO keywords(admin_id, keyword) VALUES(?, ?)", (admin_id, keyword))
        conn.commit()
        conn.close()

def get_keywords(admin_id):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, keyword FROM keywords WHERE admin_id = ? ORDER BY id DESC", (admin_id,))
        rows = c.fetchall()
        conn.close()
        return [(row['id'], row['keyword']) for row in rows]

def remove_keyword(keyword_id):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))
        conn.commit()
        conn.close()

# ------------------ Private groups ------------------

def add_private_group(admin_id, group_id=None, group_link=None, group_name=None):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
        INSERT INTO private_groups(admin_id, group_id, group_link, group_name)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(admin_id) DO UPDATE SET
            group_id=excluded.group_id,
            group_link=excluded.group_link,
            group_name=excluded.group_name
        """, (admin_id, group_id, group_link, group_name))
        conn.commit()
        conn.close()

def get_private_group_name(admin_id):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT group_name FROM private_groups WHERE admin_id = ?", (admin_id,))
        row = c.fetchone()
        conn.close()
        return row['group_name'] if row else None

def get_private_group_id(admin_id):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT group_id FROM private_groups WHERE admin_id = ?", (admin_id,))
        row = c.fetchone()
        conn.close()
        return row['group_id'] if row else None

def remove_private_group(admin_id):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM private_groups WHERE admin_id = ?", (admin_id,))
        conn.commit()
        conn.close()

# ------------------ Search groups ------------------

def _can_add_search_group(admin_id, super_admin_id):
    if admin_id == super_admin_id:
        return True, None
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT last_added_at FROM rate_limits WHERE admin_id = ?", (admin_id,))
        row = c.fetchone()
        now = datetime.utcnow()
        if row and row['last_added_at']:
            last = datetime.strptime(row['last_added_at'], "%Y-%m-%d %H:%M:%S")
            if now - last < timedelta(hours=1):
                conn.close()
                return False, "Bir soatda faqat bitta izlovchi guruh qo'shish mumkin"
        # update rate limit
        c.execute("""
        INSERT INTO rate_limits(admin_id, last_added_at) VALUES(?, ?)
        ON CONFLICT(admin_id) DO UPDATE SET last_added_at=excluded.last_added_at
        """, (admin_id, now.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return True, None

def add_search_group(admin_id, super_admin_id, group_id=None, group_link=None, group_name=None):
    ok, msg = _can_add_search_group(admin_id, super_admin_id)
    if not ok:
        return False, msg or "Cheklov tufayli qo'shib bo'lmadi"

    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
        INSERT INTO search_groups(admin_id, group_id, group_link, group_name, created_at)
        VALUES(?, ?, ?, ?, ?)
        """, (admin_id, group_id, group_link, group_name, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return True, "Izlovchi guruh qo'shildi"

def get_search_groups(admin_id):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, group_name FROM search_groups WHERE admin_id = ? ORDER BY id DESC", (admin_id,))
        rows = c.fetchall()
        conn.close()
        return [(row['id'], row['group_name']) for row in rows]

def get_all_search_group_ids():
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, admin_id, group_id, group_name FROM search_groups")
        rows = c.fetchall()
        conn.close()
        return [{
            'row_id': row['id'],
            'admin_id': row['admin_id'],
            'group_id': row['group_id'],
            'group_name': row['group_name']
        } for row in rows]

def remove_search_group(row_id):
    with _lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM search_groups WHERE id = ?", (row_id,))
        conn.commit()
        conn.close()

# ------------------ Keyword matching ------------------

def check_keywords_in_message(group_id, msg_text):
    """
    Returns list of matches:
    {
        'keyword': str,
        'private_group_id': int or None
    }
    """
    msg_lower = (msg_text or "").lower()

    with _lock:
        conn = get_db()
        c = conn.cursor()
        # find admins who own this search group
        c.execute("SELECT admin_id FROM search_groups WHERE group_id = ?", (group_id,))
        owners = [row['admin_id'] for row in c.fetchall()]

        results = []
        for admin_id in owners:
            c.execute("SELECT keyword FROM keywords WHERE admin_id = ?", (admin_id,))
            kws = [row['keyword'] for row in c.fetchall()]
            c.execute("SELECT group_id FROM private_groups WHERE admin_id = ?", (admin_id,))
            pr = c.fetchone()
            private_gid = pr['group_id'] if pr else None

            for kw in kws:
                if kw and kw.lower() in msg_lower:
                    results.append({
                        'keyword': kw,
                        'private_group_id': private_gid
                    })

        conn.close()
        return results
