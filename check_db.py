import sqlite3
import os

def check_database():
    """Check database schema and identify issues."""
    db_path = "por.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 Tables in database: {[t[0] for t in tables]}")
        
        # Check if batch_counter table exists
        if ('batch_counter',) in tables:
            print("✅ batch_counter table exists")
            cursor.execute("SELECT * FROM batch_counter")
            counter_data = cursor.fetchall()
            print(f"📊 batch_counter data: {counter_data}")
        else:
            print("❌ batch_counter table is missing!")
        
        # Check if por table exists
        if ('por',) in tables:
            print("✅ por table exists")
            cursor.execute("PRAGMA table_info(por)")
            columns = cursor.fetchall()
            print(f"📋 por table columns: {[col[1] for col in columns]}")
            
            # Check for unique constraint on po_number
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='por'")
            table_sql = cursor.fetchone()
            if table_sql:
                print(f"🔍 por table definition: {table_sql[0]}")
        else:
            print("❌ por table is missing!")
        
        # Check for other tables
        for table in ['por_files', 'line_items']:
            if (table,) in tables:
                print(f"✅ {table} table exists")
            else:
                print(f"❌ {table} table is missing!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == '__main__':
    check_database() 