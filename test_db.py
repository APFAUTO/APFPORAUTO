"""
Test script to verify database operations work correctly.
"""

from datetime import datetime, timezone
from models import POR, get_session

def test_database_operations():
    """Test basic database operations."""
    try:
        # Create a new session
        session = get_session()
        
        # Test creating a POR record
        test_data = {
            'po_number': 9999,
            'requestor_name': 'Test User',
            'date_order_raised': '01/01/2025',
            'filename': 'test.xlsx',
            'job_contract_no': 'TEST001',
            'op_no': 'OP001',
            'description': 'Test item',
            'quantity': 1,
            'price_each': 10.0,
            'line_total': 10.0,
            'order_total': 10.0,
            'data_summary': 'Test data',
            'created_at': datetime.now(timezone.utc)
        }
        
        # Create and save record
        por = POR(**test_data)
        session.add(por)
        session.commit()
        
        print("✅ Successfully created test record")
        
        # Query the record
        result = session.query(POR).filter_by(po_number=9999).first()
        if result:
            print(f"✅ Successfully retrieved record: PO #{result.po_number}")
        else:
            print("❌ Failed to retrieve record")
        
        # Clean up - delete test record
        session.delete(result)
        session.commit()
        print("✅ Successfully deleted test record")
        
        session.close()
        print("✅ All database operations successful!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        try:
            session.rollback()
            session.close()
        except:
            pass

if __name__ == '__main__':
    test_database_operations() 