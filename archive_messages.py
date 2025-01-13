#!/usr/bin/env python3
"""Script to archive old messages."""

import os
import logging
from datetime import datetime
from storage.sqlite_storage import SQLiteStorage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Archive old messages based on current time."""
    db_path = os.environ.get('DB_PATH', 'chat.db')
    storage = SQLiteStorage(db_path)
    
    # Use current time as reference
    reference_time = datetime.now()
    
    # Archive old messages
    archive_path = storage.archive_old_messages(reference_time)
    if archive_path:
        logger.info(f"Created archive: {archive_path}")
    else:
        logger.info("No messages needed archiving")

if __name__ == '__main__':
    main()
