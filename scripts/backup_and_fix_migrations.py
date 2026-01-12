import shutil, os, sqlite3, datetime, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB = os.path.join(ROOT, 'db.sqlite3')
if not os.path.exists(DB):
    print('DB not found:', DB)
    sys.exit(1)

bak_name = f"db.sqlite3.bak_{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
bak_path = os.path.join(ROOT, bak_name)
shutil.copy2(DB, bak_path)
print('Backup created:', bak_path)

conn = sqlite3.connect(DB)
cur = conn.cursor()
# Show current HR rows
cur.execute("SELECT id, app, name, applied FROM django_migrations WHERE app='HR' ORDER BY id")
rows = cur.fetchall()
print('Before removal:')
for r in rows:
    print(r)

# Remove the problematic applied migration if present
target = '0006_punchrecord_remove_break_attendance_and_more'
cur.execute("SELECT id FROM django_migrations WHERE app='HR' AND name=?", (target,))
found = cur.fetchone()
if found:
    cur.execute("DELETE FROM django_migrations WHERE id=?", (found[0],))
    conn.commit()
    print('Removed migration row:', target)
else:
    print('No row found for', target)

# Show after
cur.execute("SELECT id, app, name, applied FROM django_migrations WHERE app='HR' ORDER BY id")
rows = cur.fetchall()
print('After removal:')
for r in rows:
    print(r)

conn.close()
print('Done')
