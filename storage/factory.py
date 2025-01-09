"""Factory module for creating storage backends."""

import os
import logging
from typing import Optional
from pathlib import Path
from storage import StorageBackend
from storage.git_storage import GitStorage
from storage.sqlite_storage import SQLiteStorage

logger = logging.getLogger(__name__)

def create_storage(storage_type: str = None, **kwargs) -> StorageBackend:
    """Create a storage backend based on configuration.
    
    Args:
        storage_type: Type of storage backend ('git' or 'sqlite')
        **kwargs: Additional configuration parameters
    
    Returns:
        StorageBackend instance
    
    Raises:
        ValueError: If storage_type is invalid
    """
    try:
        logger.debug("Creating storage backend")
        
        # Use environment variable if storage_type not specified
        if storage_type is None:
            storage_type = os.getenv('BOOKCHAT_STORAGE', 'sqlite').lower()
        logger.debug(f"Using storage type: {storage_type}")
        
        if storage_type == 'git':
            repo_path = kwargs.get('repo_path') or os.getenv('REPO_PATH') or os.getcwd()
            logger.debug(f"Using repository path: {repo_path}")
            logger.info(f"Creating GitStorage with repo_path: {repo_path}")
            storage = GitStorage(repo_path)
        elif storage_type == 'sqlite':
            db_path = kwargs.get('db_path') or os.getenv('DB_PATH') or os.path.join('database', 'messages.db')
            logger.debug(f"Using database path: {db_path}")
            logger.info(f"Creating SQLiteStorage with db_path: {db_path}")
            storage = SQLiteStorage(db_path)
        else:
            logger.error(f"Invalid storage type: {storage_type}")
            raise ValueError(f"Invalid storage type: {storage_type}")
        
        logger.debug("Storage backend created successfully")
        return storage
        
    except Exception as e:
        logger.error(f"Failed to create storage backend: {e}", exc_info=True)
        raise
