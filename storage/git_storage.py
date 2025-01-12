"""Git-based storage backend for BookChat."""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import uuid
import subprocess
import traceback

from storage import StorageBackend
from git_manager import GitManager
from key_manager import KeyManager  # Import KeyManager

# Get logger for this module
logger = logging.getLogger(__name__)

class GitStorage(StorageBackend):
    """Storage backend that uses Git repository for message storage."""
    
    def __init__(self, repo_path: str):
        """Initialize the Git storage backend.
        
        Args:
            repo_path: Path to the Git repository
        """
        logger.info(f"Initializing GitStorage with repo_path: {repo_path}")
        self.repo_path = Path(repo_path)
        self.messages_dir = self.repo_path / 'messages'
        self.git_manager = GitManager(str(repo_path))
        
        # Initialize key manager with the same key directories as git manager
        private_keys_dir = os.environ.get('KEYS_DIR', str(self.repo_path / 'keys'))
        public_keys_dir = os.environ.get('PUBLIC_KEYS_DIR', str(self.repo_path / 'identity/public_keys'))
        self.key_manager = KeyManager(private_keys_dir, public_keys_dir)
        
        logger.debug(f"Messages directory: {self.messages_dir}")
        
        # Check if messages directory exists
        if not self.messages_dir.exists():
            logger.warning(f"Messages directory does not exist: {self.messages_dir}")
        else:
            logger.debug(f"Messages directory exists and contains: {list(self.messages_dir.glob('*'))}")
        
        # Check Git repository status
        try:
            result = subprocess.run(
                ['git', 'status'],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True
            )
            logger.debug(f"Git status output: {result.stdout}")
            if result.stderr:
                logger.warning(f"Git status stderr: {result.stderr}")
        except Exception as e:
            logger.error(f"Failed to check Git status: {e}")
        
    def init_storage(self) -> bool:
        """Initialize the storage by creating necessary directories."""
        try:
            # Create messages directory if it doesn't exist
            logger.debug(f"Ensuring messages directory exists: {self.messages_dir}")
            os.makedirs(self.messages_dir, exist_ok=True)
            
            # Check if directory was created successfully
            if not self.messages_dir.exists():
                logger.error("Failed to create messages directory")
                return False
            
            # Check directory permissions
            logger.debug(f"Messages directory permissions: {oct(os.stat(self.messages_dir).st_mode)}")
            
            # List directory contents
            logger.debug(f"Messages directory contents: {list(self.messages_dir.glob('*'))}")
            
            logger.info("Storage initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}\n{traceback.format_exc()}")
            return False
    
    def save_message(self, user: str, content: str, timestamp: datetime, sign: bool = True) -> bool:
        """Save a new message to the Git repository.
        
        Args:
            user: Username of the message sender
            content: Message content
            timestamp: Message timestamp
            sign: Whether to sign the message
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Saving message from user: {user}")
            
            # Format filename like existing messages: YYYYMMDD_HHMMSS_username.txt
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{user}.txt"
            message_path = self.messages_dir / filename
            logger.debug(f"Message will be saved to: {message_path}")
            
            # Check if messages directory exists
            if not self.messages_dir.exists():
                logger.error(f"Messages directory does not exist: {self.messages_dir}")
                return False
            
            # Sign message if requested
            signature = None
            if sign:
                try:
                    signature = self.git_manager.key_manager.sign_message(content)
                    logger.debug(f"Message signed successfully: {signature[:32]}...")
                except Exception as e:
                    logger.error(f"Failed to sign message: {e}")
                    # Continue without signature
            
            # Format message with metadata footers
            # Use RFC 3339 format that JavaScript can definitely parse
            date_str = timestamp.astimezone().strftime('%Y-%m-%dT%H:%M:%S%z')
            # Insert colon in timezone offset (e.g. +0000 -> +00:00)
            date_str = date_str[:-2] + ':' + date_str[-2:]
            
            formatted_message = self.git_manager.format_message(
                content,
                user,
                date_str,
                signature=signature
            )
            
            # Write message to file
            logger.info(f"Writing message to: {message_path}")
            try:
                with open(message_path, 'w') as f:
                    f.write(formatted_message)
                logger.debug(f"Successfully wrote message to file: {message_path}")
                logger.debug(f"File exists after write: {message_path.exists()}")
                logger.debug(f"File contents after write: {message_path.read_text() if message_path.exists() else 'FILE NOT FOUND'}")
            except Exception as e:
                logger.error(f"Failed to write message file: {e}\n{traceback.format_exc()}")
                return False
            
            # Stage and commit the file
            logger.info("Committing message to Git repository")
            try:
                # Add only the specific message file
                result = subprocess.run(
                    ['git', 'add', str(message_path)],
                    cwd=str(self.repo_path),
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.debug(f"Git add output: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Git add stderr: {result.stderr}")
                
                # Commit the specific file
                commit_msg = f'Add message from {user}'
                logger.debug(f"Running git commit with message: {commit_msg}")
                result = subprocess.run(
                    ['git', 'commit', '--no-verify', str(message_path), '-m', commit_msg],
                    cwd=str(self.repo_path),
                    check=True,
                    capture_output=True,
                    text=True,
                    env={**os.environ, 'GIT_AUTHOR_NAME': user, 'GIT_AUTHOR_EMAIL': f'{user}@bookchat.local'}
                )
                logger.debug(f"Git commit output: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Git commit stderr: {result.stderr}")
                
                # Try to sync to GitHub if enabled
                if os.getenv('SYNC_TO_GITHUB', '').lower() == 'true':
                    logger.debug("Attempting to sync to GitHub...")
                    try:
                        self.git_manager.sync_changes_to_github(str(message_path), user)
                        logger.debug("Successfully synced to GitHub")
                    except Exception as e:
                        logger.warning(f"Failed to sync to GitHub: {e}")
                        # Don't fail the save operation if GitHub sync fails
                
                logger.info("Message saved successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to commit message: {e}\n{traceback.format_exc()}")
                return False
        except Exception as e:
            logger.error(f"Error saving message: {e}\n{traceback.format_exc()}")
            return False
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve messages from the Git repository.
        
        Args:
            limit: Optional maximum number of messages to retrieve
        
        Returns:
            List of message dictionaries
        """
        messages = []
        
        try:
            # Get all message files
            message_files = sorted(
                self.messages_dir.glob('*.txt'),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            if limit:
                message_files = message_files[:limit]
            
            # Read each message file
            for message_file in message_files:
                try:
                    message = self.git_manager.read_message(message_file.name)
                    if message:
                        # Add file link
                        message['file'] = f"messages/{message_file.name}"
                        messages.append(message)
                except Exception as e:
                    logger.error(f"Error reading message {message_file}: {e}")
                    continue
            
            return messages
        except Exception as e:
            logger.error(f"Failed to get messages: {e}\n{traceback.format_exc()}")
            return []

    def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific message by ID.
        
        Args:
            message_id: ID of the message to retrieve
        
        Returns:
            Message dictionary if found, None otherwise
        """
        try:
            # Message ID is the filename
            message_path = self.messages_dir / message_id
            if not message_path.exists():
                logger.warning(f"Message not found: {message_id}")
                return None
            
            # Read and parse the message
            message = self.git_manager.read_message(message_id)
            if not message:
                logger.error(f"Failed to parse message: {message_id}")
                return None
            
            # Add file link
            message['file'] = f"messages/{message_id}"
            return message
        except Exception as e:
            logger.error(f"Error retrieving message {message_id}: {e}\n{traceback.format_exc()}")
            return None
