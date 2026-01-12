import sqlite3, os
DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3'))
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM django_migrations WHERE app='HR'")
count = cur.fetchone()[0]
print('HR rows before:', count)
cur.execute("DELETE FROM django_migrations WHERE app='HR'")
conn.commit()
cur.execute("SELECT COUNT(*) FROM django_migrations WHERE app='HR'")
print('HR rows after:', cur.fetchone()[0])
conn.close()
