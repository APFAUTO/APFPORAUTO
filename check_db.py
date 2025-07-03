import sqlite3

try:
    conn = sqlite3.connect('por.db')
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(por)')
    columns = cursor.fetchall()
    print("Database columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    conn.close()
except Exception as e:
    print(f"Error: {e}") 