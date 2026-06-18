import sqlite3

conn = sqlite3.connect('pingax_factory.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE orders ADD COLUMN priority TEXT")
    print("Priority column successfully added!")
except:
    print("Column already exists!")
conn.commit()
conn.close()