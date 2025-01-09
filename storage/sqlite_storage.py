"""SQLite storage backend for BookChat."""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import uuid

from storage import StorageBackend

class SQLiteStorage(StorageBackend):
    """Storage backend that uses SQLite for message storage."""
    
    def __init__(self, db_path: str):
        """Initialize the SQLite storage backend.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_dir = self.db_path.parent
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper configuration."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_storage(self) -> bool:
        """Initialize the SQLite database with required schema."""
        try:
            self.db_dir.mkdir(parents=True, exist_ok=True)
            
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        user TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL
                    )
                """)
                return True
        except Exception:
            return False
    
    def save_message(self, user: str, content: str, timestamp: datetime) -> bool:
        """Save a new message to the SQLite database.
        
        Args:
            user: Username of the message sender
            content: Message content
            timestamp: Message timestamp
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            message_id = str(uuid.uuid4())
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO messages (id, user, content, timestamp) VALUES (?, ?, ?, ?)",
                    (message_id, user, content, timestamp.isoformat())
                )
                return True
        except Exception:
            return False
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve messages from the SQLite database.
        
        Args:
            limit: Optional maximum number of messages to retrieve
        
        Returns:
            List of message dictionaries
        """
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM messages ORDER BY timestamp DESC"
                if limit is not None:
                    query += f" LIMIT {limit}"
                    
                cursor = conn.execute(query)
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific message by ID.
        
        Args:
            message_id: ID of the message to retrieve
        
        Returns:
            Message dictionary if found, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM messages WHERE id = ?",
                    (message_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return None
