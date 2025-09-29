import psycopg2
import psycopg2.extras
import os
from datetime import datetime, timedelta

# PostgreSQL connection parameters
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

def init_database():
    """Initialize the PostgreSQL database with required tables."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Create medicines table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicines (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            current_stock INTEGER NOT NULL,
            reorder_point INTEGER NOT NULL,
            expiry_date DATE NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            batch_number VARCHAR(100),
            supplier VARCHAR(255),
            category VARCHAR(100),
            location VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create stock_history table for tracking changes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_history (
            id SERIAL PRIMARY KEY,
            medicine_id INTEGER REFERENCES medicines(id),
            old_stock INTEGER,
            new_stock INTEGER,
            change_reason TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def add_medicine(name, current_stock, reorder_point, expiry_date, unit_price, 
                batch_number, supplier, category, location):
    """Add a new medicine to the inventory."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO medicines (name, current_stock, reorder_point, expiry_date, 
                             unit_price, batch_number, supplier, category, location)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (name, current_stock, reorder_point, expiry_date, unit_price, 
          batch_number, supplier, category, location))
    
    conn.commit()
    conn.close()

def get_all_medicines():
    """Retrieve all medicines from the inventory."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute('''
        SELECT id, name, current_stock, reorder_point, expiry_date, 
               unit_price, batch_number, supplier, category, location
        FROM medicines
        ORDER BY name
    ''')
    
    medicines = cursor.fetchall()
    conn.close()
    return medicines

def update_stock(medicine_id, new_stock, reason="Manual update"):
    """Update the stock level of a medicine."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Get current stock for history
    cursor.execute('SELECT current_stock FROM medicines WHERE id = %s', (medicine_id,))
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"Medicine with ID {medicine_id} not found")
    old_stock = result[0]
    
    # Update stock
    cursor.execute('''
        UPDATE medicines 
        SET current_stock = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE id = %s
    ''', (new_stock, medicine_id))
    
    # Add to history
    cursor.execute('''
        INSERT INTO stock_history (medicine_id, old_stock, new_stock, change_reason)
        VALUES (%s, %s, %s, %s)
    ''', (medicine_id, old_stock, new_stock, reason))
    
    conn.commit()
    conn.close()

def get_low_stock_medicines():
    """Get medicines that are at or below their reorder point."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute('''
        SELECT id, name, current_stock, reorder_point, expiry_date, 
               unit_price, batch_number, supplier, category, location
        FROM medicines
        WHERE current_stock <= reorder_point
        ORDER BY current_stock ASC
    ''')
    
    medicines = cursor.fetchall()
    conn.close()
    return medicines

def get_expiring_medicines(days_ahead=30):
    """Get medicines that will expire within the specified number of days."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Calculate the cutoff date
    cutoff_date = (datetime.now() + timedelta(days=days_ahead)).date()
    
    cursor.execute('''
        SELECT id, name, current_stock, reorder_point, expiry_date, 
               unit_price, batch_number, supplier, category, location
        FROM medicines
        WHERE expiry_date <= %s
        ORDER BY expiry_date ASC
    ''', (cutoff_date,))
    
    medicines = cursor.fetchall()
    conn.close()
    return medicines

def get_medicine_by_id(medicine_id):
    """Get a specific medicine by its ID."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute('''
        SELECT id, name, current_stock, reorder_point, expiry_date, 
               unit_price, batch_number, supplier, category, location
        FROM medicines
        WHERE id = %s
    ''', (medicine_id,))
    
    medicine = cursor.fetchone()
    conn.close()
    return medicine

def search_medicines(search_term):
    """Search medicines by name or category."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute('''
        SELECT id, name, current_stock, reorder_point, expiry_date, 
               unit_price, batch_number, supplier, category, location
        FROM medicines
        WHERE name ILIKE %s OR category ILIKE %s
        ORDER BY name
    ''', (f'%{search_term}%', f'%{search_term}%'))
    
    medicines = cursor.fetchall()
    conn.close()
    return medicines

def get_stock_history(medicine_id=None, limit=50):
    """Get stock change history for a specific medicine or all medicines."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    if medicine_id:
        cursor.execute('''
            SELECT sh.id, m.name, sh.old_stock, sh.new_stock, 
                   sh.change_reason, sh.changed_at
            FROM stock_history sh
            JOIN medicines m ON sh.medicine_id = m.id
            WHERE sh.medicine_id = %s
            ORDER BY sh.changed_at DESC
            LIMIT %s
        ''', (medicine_id, limit))
    else:
        cursor.execute('''
            SELECT sh.id, m.name, sh.old_stock, sh.new_stock, 
                   sh.change_reason, sh.changed_at
            FROM stock_history sh
            JOIN medicines m ON sh.medicine_id = m.id
            ORDER BY sh.changed_at DESC
            LIMIT %s
        ''', (limit,))
    
    history = cursor.fetchall()
    conn.close()
    return history

def delete_medicine(medicine_id):
    """Delete a medicine from the inventory."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Delete from stock_history first (foreign key constraint)
    cursor.execute('DELETE FROM stock_history WHERE medicine_id = %s', (medicine_id,))
    
    # Delete from medicines
    cursor.execute('DELETE FROM medicines WHERE id = %s', (medicine_id,))
    
    conn.commit()
    conn.close()
