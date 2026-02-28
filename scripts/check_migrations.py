import sqlite3
conn=sqlite3.connect('db.sqlite3')
cur=conn.cursor()
rows=cur.execute("SELECT app, name FROM django_migrations WHERE app='delivery_management'").fetchall()
print(rows)
