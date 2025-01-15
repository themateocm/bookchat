"""Main server module."""

import logging
import os
import signal
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from server import config
from server.handler import ChatRequestHandler
from server.utils import find_available_port, open_browser, ensure_directories
from storage.factory import create_storage

logger = logging.getLogger(__name__)

def setup_signal_handlers(server):
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info("Shutting down server...")
        server.shutdown()
        sys.exit(0)

    # Only set up signal handlers in the main thread
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

def main(open_browser_on_start=True):
    """Start the server.
    
    Args:
        open_browser_on_start: If True, opens the browser after server starts.
                             Set to False in test environments.
    """
    # Ensure required directories exist
    ensure_directories()

    # Initialize storage backend
    logger.info(f"Initializing storage backend with repo path: {config.REPO_PATH}")
    storage = create_storage()

    # Find available port if not specified
    port = int(os.environ.get('PORT', find_available_port()))
    
    # Create server
    server = ThreadingHTTPServer(('', port), ChatRequestHandler)
    server.storage = storage

    # Set up signal handlers
    setup_signal_handlers(server)

    # Start server
    logger.info(f"Starting server on port {port}")
    server_url = f'http://localhost:{port}'
    
    if open_browser_on_start:
        open_browser(server_url)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
