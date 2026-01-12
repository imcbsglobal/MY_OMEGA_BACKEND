import sqlite3, os
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3'))
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT id, app, name, applied FROM django_migrations WHERE app='HR' ORDER BY id")
rows = cur.fetchall()
for r in rows:
    print(r)
conn.close()
