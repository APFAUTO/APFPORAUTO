import sqlite3
import os

def fix_database():
    """Fix database issues by creating missing tables and setting up proper counters."""
    db_path = "por.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if batch_counter table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='batch_counter'")
        if not cursor.fetchone():
            print("🔧 Creating missing batch_counter table...")
            cursor.execute("""
                CREATE TABLE batch_counter (
                    id INTEGER PRIMARY KEY,
                    value INTEGER NOT NULL
                )
            """)
            
            # Get the highest PO number from the por table to set the counter
            cursor.execute("SELECT MAX(po_number) FROM por")
            max_po = cursor.fetchone()[0]
            if max_po is None:
                max_po = 0
            
            # Set the counter to the next available PO number
            next_po = max_po + 1
            cursor.execute("INSERT INTO batch_counter (id, value) VALUES (1, ?)", (next_po,))
            print(f"✅ Created batch_counter table with value: {next_po}")
        else:
            print("✅ batch_counter table already exists")
        
        # Commit changes
        conn.commit()
        print("✅ Database fixes completed successfully")
        
        # Verify the fix
        cursor.execute("SELECT * FROM batch_counter")
        counter_data = cursor.fetchall()
        print(f"📊 batch_counter data: {counter_data}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        conn.rollback()
        raise

if __name__ == '__main__':
    fix_database() 