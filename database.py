import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data.db')

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS checkin_records
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          user_id TEXT NOT NULL,
                          checkin_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                          continuous_days INTEGER DEFAULT 1,
                          device_info TEXT,
                          location TEXT,
                          UNIQUE(user_id, DATE(checkin_time)))''')
        conn.commit()

def save_checkin_record(user_id, device_info=None, location=None):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO checkin_records 
                             (user_id, device_info, location)
                             VALUES (?, ?, ?)''', 
                          (user_id, device_info, location))
            conn.commit()
            return True
    except sqlite3.IntegrityError as e:
        # 处理重复打卡错误
        return False