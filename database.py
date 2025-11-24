"""Database management for the inventory system."""
import sqlite3
import os
from flask import g

DATABASE = 'inventory.db'


def get_db():
    """Get database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def close_connection(exception):
    """Close database connection."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize the database with tables."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    # Create assets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT UNIQUE NOT NULL,
            device_type TEXT NOT NULL,
            model TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create associates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS associates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            job_title TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create assignments table (main database joining assets and associates)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            associate_id INTEGER NOT NULL,
            assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (asset_id) REFERENCES assets (id),
            FOREIGN KEY (associate_id) REFERENCES associates (id)
        )
    ''')
    
    # Create transfer requests table for approval workflow
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transfer_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            from_associate_id INTEGER,
            to_associate_id INTEGER NOT NULL,
            requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transferer_approval TEXT DEFAULT 'pending',
            transferee_approval TEXT DEFAULT 'pending',
            it_approval TEXT DEFAULT 'pending',
            status TEXT DEFAULT 'pending',
            notes TEXT,
            FOREIGN KEY (asset_id) REFERENCES assets (id),
            FOREIGN KEY (from_associate_id) REFERENCES associates (id),
            FOREIGN KEY (to_associate_id) REFERENCES associates (id)
        )
    ''')
    
    db.commit()
    db.close()
    print("Database initialized successfully!")


if __name__ == '__main__':
    init_db()
