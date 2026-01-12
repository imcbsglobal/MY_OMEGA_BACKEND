import sqlite3
import datetime
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3'))
print('DB path:', DB_PATH)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

missing = [
    ('HR', '0005_alter_leavemaster_options_leavemaster_created_by_and_more'),
    ('HR', '0006_alter_leavemaster_category_and_more'),
]
for app, name in missing:
    cur.execute("SELECT 1 FROM django_migrations WHERE app=? AND name=?", (app, name))
    if cur.fetchone():
        print('Already present:', app, name)
    else:
        applied = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
        cur.execute("INSERT INTO django_migrations(app, name, applied) VALUES(?,?,?)", (app, name, applied))
        print('Inserted:', app, name)

conn.commit()
conn.close()
print('Done')
