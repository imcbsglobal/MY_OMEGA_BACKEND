import sqlite3
from datetime import datetime

db = 'db.sqlite3'
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_migrations'")
if not cur.fetchone():
    print('ERROR: django_migrations table not found')
    conn.close()
    raise SystemExit(1)

name = '0005_alter_leavemaster_options_leavemaster_created_by_and_more'
app = 'HR'
cur.execute('SELECT 1 FROM django_migrations WHERE app=? AND name=?', (app, name))
if cur.fetchone():
    print('Migration already marked applied')
else:
    cur.execute('INSERT INTO django_migrations(app, name, applied) VALUES(?, ?, ?)', (app, name, datetime.utcnow().isoformat()))
    conn.commit()
    print('Inserted migration record for', app, name)
conn.close()
