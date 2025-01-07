#!/usr/bin/env python3

import sqlite3
import os
import sys
from pathlib import Path

def init_database():
    """Initialize the SQLite database with the schema"""
    # Get the directory containing this script
    db_dir = Path(__file__).parent
    schema_path = db_dir / 'schema.sql'
    db_path = db_dir / 'messages.db'

    # Create database directory if it doesn't exist
    os.makedirs(db_dir, exist_ok=True)

    print(f"Initializing database at {db_path}")
    
    try:
        # Connect to SQLite database (creates it if it doesn't exist)
        with sqlite3.connect(db_path) as conn:
            # Enable foreign key support
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Read schema file
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            # Execute schema
            conn.executescript(schema)
            
            # Commit changes
            conn.commit()
            
        print("Database initialization completed successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"An error occurred while initializing the database: {e}", file=sys.stderr)
        return False
    except IOError as e:
        print(f"An error occurred while reading the schema file: {e}", file=sys.stderr)
        return False

def main():
    """Main function to initialize the database"""
    success = init_database()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
