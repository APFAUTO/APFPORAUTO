"""
Database migration script to add missing columns to existing database.
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add missing columns to existing database."""
    db_path = "por.db"
    
    if not os.path.exists(db_path):
        print("Database file not found. Creating new database...")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if created_at column exists
        cursor.execute("PRAGMA table_info(por)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Current columns: {columns}")
        
        if 'created_at' not in columns:
            print("Adding created_at column...")
            cursor.execute("ALTER TABLE por ADD COLUMN created_at DATETIME")
            
            # Set default value for existing records
            current_time = datetime.utcnow().isoformat()
            cursor.execute("UPDATE por SET created_at = ? WHERE created_at IS NULL", (current_time,))
            
            print("✅ Successfully added created_at column")
        else:
            print("✅ created_at column already exists")
        
        # Check for other missing columns and add them if needed
        required_columns = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'po_number': 'INTEGER UNIQUE NOT NULL',
            'requestor_name': 'VARCHAR(255) NOT NULL',
            'date_order_raised': 'VARCHAR(50) NOT NULL',
            'ship_project_name': 'VARCHAR(255)',
            'supplier': 'VARCHAR(255)',
            'filename': 'VARCHAR(255) NOT NULL',
            'job_contract_no': 'VARCHAR(100)',
            'op_no': 'VARCHAR(50)',
            'description': 'TEXT',
            'quantity': 'INTEGER',
            'price_each': 'FLOAT',
            'line_total': 'FLOAT',
            'order_total': 'FLOAT',
            'specification_standards': 'TEXT',
            'supplier_contact_name': 'VARCHAR(255)',
            'supplier_contact_email': 'VARCHAR(255)',
            'quote_ref': 'VARCHAR(255)',
            'quote_date': 'VARCHAR(50)',
            'data_summary': 'TEXT',
            'created_at': 'DATETIME NOT NULL'
        }
        
        for column_name, column_type in required_columns.items():
            if column_name not in columns:
                print(f"Adding {column_name} column...")
                cursor.execute(f"ALTER TABLE por ADD COLUMN {column_name} {column_type}")
                print(f"✅ Successfully added {column_name} column")
        
        # Commit changes
        conn.commit()
        print("✅ Database migration completed successfully")
        
        # Verify the change
        cursor.execute("PRAGMA table_info(por)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"Updated columns: {new_columns}")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database() 