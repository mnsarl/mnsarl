import sqlite3

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# إضافة عمود referred_count إلى جدول users
cursor.execute("ALTER TABLE users ADD COLUMN referred_count INTEGER DEFAULT 0")

conn.commit()
conn.close()
