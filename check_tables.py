import sqlite3

def list_tables():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    
    # Sort for easier reading
    table_names = sorted([t[0] for t in tables])
    
    print("Tables found:")
    for t in table_names:
        if 'leave' in t.lower():
            print(f" -> {t}")
        else:
            print(t)

if __name__ == '__main__':
    list_tables()
