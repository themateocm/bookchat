"""File-based storage backend for BookChat."""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import uuid
import re

from storage import StorageBackend

logger = logging.getLogger(__name__)

class FileStorage(StorageBackend):
    """Storage backend that uses text files for message storage."""
    
    def __init__(self, repo_path: str):
        """Initialize the file storage backend.
        
        Args:
            repo_path: Base path for message storage
        """
        self.repo_path = Path(repo_path)
        self.messages_dir = self.repo_path / 'messages'
        logger.debug(f"Messages directory: {self.messages_dir}")
    
    def init_storage(self) -> bool:
        """Initialize the storage by creating necessary directories."""
        try:
            # Create messages directory if it doesn't exist
            os.makedirs(self.messages_dir, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}")
            return False
    
    def verify_username(self, username: str) -> bool:
        """Verify that a username is valid.
        
        Args:
            username: The username to verify
            
        Returns:
            True if the username is valid, False otherwise
        """
        # Username should be 3-20 characters long and only contain letters, numbers, and underscores
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            return False
        return True
    
    def save_message(self, user: str, content: str, timestamp: datetime) -> bool:
        """Save a new message.
        
        Args:
            user: Username of the author
            content: Message content
            timestamp: Message timestamp
            
        Returns:
            True if message was saved successfully, False otherwise
        """
        try:
            # Format timestamp for filename
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{user}.txt"
            
            # Create message content in the required format
            message_content = f"Date: {timestamp.isoformat()}\nAuthor: {user}\n\n{content}"
            
            # Save message to file
            message_path = self.messages_dir / filename
            with open(message_path, 'w') as f:
                f.write(message_content)
            
            return True
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all messages, optionally limited to a certain number.
        
        Args:
            limit: Optional maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        try:
            messages = []
            
            # Get all message files
            message_files = sorted(
                self.messages_dir.glob('*.txt'),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Apply limit if specified
            if limit:
                message_files = message_files[:limit]
            
            # Read each message file
            for file_path in message_files:
                try:
                    with open(file_path) as f:
                        lines = f.readlines()
                        
                        # Parse message file
                        timestamp = None
                        author = None
                        content = []
                        parsing_content = False
                        
                        for line in lines:
                            line = line.rstrip('\n')  # Preserve line breaks in content
                            if line.startswith('Date: '):
                                timestamp = line[6:]
                            elif line.startswith('Author: '):
                                author = line[8:]
                            elif parsing_content:
                                content.append(line)
                            elif line == '':
                                parsing_content = True
                        
                        if timestamp and author:
                            messages.append({
                                'content': '\n'.join(content),
                                'author': author,
                                'createdAt': timestamp,
                                'id': str(file_path),
                                'verified': 'true',
                                'type': 'message'
                            })
                except Exception as e:
                    logger.error(f"Error reading message file {file_path}: {e}")
                    continue
            
            return messages
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific message by ID.
        
        Args:
            message_id: ID of the message to retrieve
            
        Returns:
            Message dictionary if found, None otherwise
        """
        try:
            # Find message file by ID (which is the filename without extension)
            for file_path in self.messages_dir.glob('*.txt'):
                if file_path.stem == message_id:
                    with open(file_path) as f:
                        lines = f.readlines()
                        
                        # Parse message file
                        timestamp = None
                        author = None
                        content = []
                        parsing_content = False
                        
                        for line in lines:
                            line = line.strip()
                            if line.startswith('Date: '):
                                timestamp = line[6:]
                            elif line.startswith('Author: '):
                                author = line[8:]
                            elif parsing_content:
                                content.append(line)
                            elif line == '':
                                parsing_content = True
                        
                        if timestamp and author:
                            return {
                                'id': message_id,
                                'author': author,
                                'content': '\n'.join(content),
                                'createdAt': timestamp,
                                'verified': 'true',
                                'type': 'message'
                            }
            return None
        except Exception as e:
            logger.error(f"Error getting message by ID: {e}")
            return None
