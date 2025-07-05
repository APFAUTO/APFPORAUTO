"""
PO Counter Management
Handles incrementing and persisting Purchase Order numbers.
"""

import os
import threading
from typing import Optional
from models import get_session, BatchCounter, get_or_create_batch_counter

# Configuration
STARTING_PO = 1000
PO_COUNTER_PATH = "po_counter.txt"

# Thread lock for safe concurrent access
_counter_lock = threading.Lock()


class POCounter:
    """Thread-safe PO counter with file persistence."""
    
    def __init__(self, file_path: str = PO_COUNTER_PATH, starting_value: int = STARTING_PO):
        self.file_path = file_path
        self.current_value = starting_value
        self._load_from_file()
    
    def _load_from_file(self) -> None:
        """Load current PO value from file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    value = f.read().strip()
                    if value.isdigit():
                        self.current_value = int(value)
            except (IOError, ValueError) as e:
                print(f"Warning: Could not load PO counter from {self.file_path}: {e}")
                print(f"Using default value: {self.current_value}")
    
    def _save_to_file(self) -> None:
        """Save current PO value to file."""
        try:
            with open(self.file_path, 'w') as f:
                f.write(str(self.current_value))
        except IOError as e:
            print(f"Error saving PO counter to {self.file_path}: {e}")
    
    def get_current(self) -> int:
        """Get current PO number."""
        with _counter_lock:
            return self.current_value
    
    def increment(self) -> int:
        """Increment and return next PO number."""
        with _counter_lock:
            self.current_value += 1
            self._save_to_file()
            return self.current_value
    
    def set_value(self, value: int) -> bool:
        """Set PO counter to specific value."""
        if value < 1:
            return False
        
        with _counter_lock:
            self.current_value = value
            self._save_to_file()
            return True


# Global PO counter instance
_po_counter = POCounter()


def get_current_po() -> int:
    """Get current PO number."""
    return _po_counter.get_current()


def increment_po() -> int:
    """Increment and return next PO number."""
    session = get_session()
    counter = get_or_create_batch_counter(session)
    counter.value += 1
    session.commit()
    po_number = counter.value
    session.close()
    return po_number


def set_po_value(value: int) -> bool:
    """Set PO counter to specific value in the database."""
    if value < 1:
        return False
    session = get_session()
    counter = session.query(BatchCounter).first()
    if not counter:
        counter = BatchCounter(value=value)
        session.add(counter)
    else:
        counter.value = value
    session.commit()
    session.close()
    return True


# Backward compatibility
current_po = get_current_po()
po_counter_path = PO_COUNTER_PATH


if __name__ == '__main__':
    # Test the counter
    print(f"Current PO: {get_current_po()}")
    print(f"Next PO: {increment_po()}")
    print(f"Current PO: {get_current_po()}") 