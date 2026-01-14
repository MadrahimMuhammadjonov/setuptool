# ============================================
# database.py - Ma'lumotlar bazasi boshqaruvi
# ============================================

import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'bot_database.db')

def get_db():
    """Database connection olish"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Database yaratish va jadvallarni tuzish"""
    conn = get_db()
    c = conn.cursor()
    
    # Admins jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS admins
                 (user_id INTEGER PRIMARY KEY, 
                  username TEXT,
                  added_date TEXT)''')
    
    # Keywords jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS keywords
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  admin_id INTEGER, 
                  keyword TEXT,
                  added_date TEXT)''')
    
    # Search groups jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS search_groups
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  admin_id INTEGER, 
                  group_id INTEGER, 
                  group_link TEXT, 
                  group_name TEXT,
                  added_date TEXT)''')
    
    # Private groups jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS private_groups
                 (admin_id INTEGER PRIMARY KEY, 
                  group_id INTEGER, 
                  group_link TEXT, 
                  group_name TEXT,
                  added_date TEXT)''')
    
    # Settings jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, 
                  value TEXT,
                  updated_date TEXT)''')
    
    conn.commit()
    conn.close()
    print("✅ Database muvaffaqiyatli yaratildi!")

# ==================== ADMIN FUNKSIYALARI ====================

def add_admin(user_id, username):
    """Yangi admin qo'shish"""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
        if c.fetchone():
            conn.close()
            return False
        c.execute("INSERT INTO admins (user_id, username, added_date) VALUES (?, ?, ?)", 
                  (user_id, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Admin qo'shishda xato: {e}")
        conn.close()
        return False

def is_admin(user_id, super_admin_id):
    """Foydalanuvchi admin ekanligini tekshirish"""
    if user_id == super_admin_id:
        return True
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_all_admins():
    """Barcha adminlarni olish"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, username FROM admins ORDER BY added_date DESC")
    admins = [(row['user_id'], row['username']) for row in c.fetchall()]
    conn.close()
    return admins

def remove_admin(user_id):
    """Adminni o'chirish"""
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM keywords WHERE admin_id = ?", (user_id,))
    c.execute("DELETE FROM search_groups WHERE admin_id = ?", (user_id,))
    c.execute("DELETE FROM private_groups WHERE admin_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ==================== KALIT SO'Z FUNKSIYALARI ====================

def add_keyword(admin_id, keyword):
    """Kalit so'z qo'shish"""
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO keywords (admin_id, keyword, added_date) VALUES (?, ?, ?)", 
              (admin_id, keyword, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_keywords(admin_id):
    """Admin kalit so'zlarini olish"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, keyword FROM keywords WHERE admin_id = ? ORDER BY added_date DESC", (admin_id,))
    keywords = [(row['id'], row['keyword']) for row in c.fetchall()]
    conn.close()
    return keywords

def remove_keyword(keyword_id):
    """Kalit so'zni o'chirish"""
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))
    conn.commit()
    conn.close()

# ==================== IZLOVCHI GURUH FUNKSIYALARI ====================

def add_search_group(admin_id, super_admin_id, group_id=None, group_link=None, group_name=None):
    """Izlovchi guruh qo'shish"""
    conn = get_db()
    c = conn.cursor()
    
    # Super admin uchun limit yo'q
    if admin_id != super_admin_id:
        c.execute("SELECT COUNT(*) as cnt FROM search_groups WHERE admin_id = ?", (admin_id,))
        count = c.fetchone()['cnt']
        if count >= 100:
            conn.close()
            return False, "❌ Limit to'lgan! Maksimal 100 ta guruh qo'shish mumkin."
    
    # Guruh allaqachon qo'shilganmi tekshirish
    if group_id:
        c.execute("SELECT id FROM search_groups WHERE admin_id = ? AND group_id = ?", (admin_id, group_id))
        if c.fetchone():
            conn.close()
            return False, "❌ Bu guruh allaqachon qo'shilgan!"
    
    c.execute("INSERT INTO search_groups (admin_id, group_id, group_link, group_name, added_date) VALUES (?, ?, ?, ?, ?)",
              (admin_id, group_id, group_link, group_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    return True, "✅ Izlovchi guruh qo'shildi"

def get_search_groups(admin_id):
    """Admin izlovchi guruhlarini olish"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, group_name FROM search_groups WHERE admin_id = ? ORDER BY added_date DESC", (admin_id,))
    groups = [(row['id'], row['group_name']) for row in c.fetchall()]
    conn.close()
    return groups

def remove_search_group(group_id):
    """Izlovchi guruhni o'chirish"""
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM search_groups WHERE id = ?", (group_id,))
    conn.commit()
    conn.close()

# ==================== SHAXSIY GURUH FUNKSIYALARI ====================

def add_private_group(admin_id, group_id=None, group_link=None, group_name=None):
    """Shaxsiy guruh qo'shish (har bir admin uchun faqat 1 ta)"""
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM private_groups WHERE admin_id = ?", (admin_id,))
    c.execute("INSERT INTO private_groups (admin_id, group_id, group_link, group_name, added_date) VALUES (?, ?, ?, ?, ?)",
              (admin_id, group_id, group_link, group_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_private_group_id(admin_id):
    """Admin shaxsiy guruh ID sini olish"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT group_id FROM private_groups WHERE admin_id = ?", (admin_id,))
    result = c.fetchone()
    conn.close()
    return result['group_id'] if result else None

def get_private_group_name(admin_id):
    """Admin shaxsiy guruh nomini olish"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT group_name FROM private_groups WHERE admin_id = ?", (admin_id,))
    result = c.fetchone()
    conn.close()
    return result['group_name'] if result else None

def remove_private_group(admin_id):
    """Shaxsiy guruhni o'chirish"""
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM private_groups WHERE admin_id = ?", (admin_id,))
    conn.commit()
    conn.close()

# ==================== SETTINGS FUNKSIYALARI ====================

def get_setting(key, default=None):
    """Sozlamani olish"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result['value'] if result else default

def set_setting(key, value):
    """Sozlamani saqlash"""
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value, updated_date) VALUES (?, ?, ?)", 
              (key, value, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

# ==================== ASOSIY LOGIKA ====================

def check_keywords_in_message(group_id, message_text):
    """Guruh xabarida kalit so'zlarni tekshirish"""
    conn = get_db()
    c = conn.cursor()
    
    # Ushbu guruhni kuzatayotgan adminlar kalit so'zlarini topish
    c.execute("""
        SELECT k.keyword, k.admin_id, p.group_id as private_group_id
        FROM keywords k
        JOIN search_groups s ON k.admin_id = s.admin_id
        LEFT JOIN private_groups p ON k.admin_id = p.admin_id
        WHERE s.group_id = ?
    """, (group_id,))
    
    matches = []
    message_lower = message_text.lower()
    
    for row in c.fetchall():
        if row['keyword'].lower() in message_lower:
            matches.append({
                'keyword': row['keyword'],
                'admin_id': row['admin_id'],
                'private_group_id': row['private_group_id']
            })
    
    conn.close()
    return matches

# Agar to'g'ridan-to'g'ri ishga tushirilsa
if __name__ == '__main__':
    print("🔧 Database yaratilmoqda...")
    init_db()
    print("✅ Tayyor!")
