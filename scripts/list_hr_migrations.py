import sqlite3, os
DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3'))
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT id, app, name, applied FROM django_migrations WHERE lower(app)='hr' ORDER BY id")
rows = cur.fetchall()
for r in rows:
    print(r)
conn.close()
