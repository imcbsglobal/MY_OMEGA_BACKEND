import sqlite3
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
rows = cur.execute("PRAGMA table_info('delivery_management_delivery')").fetchall()
for r in rows:
    print(r)
