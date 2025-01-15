"""Utility functions for the server."""

import logging
import socket
import time
import webbrowser
from pathlib import Path

logger = logging.getLogger(__name__)

def find_available_port(start_port=8000, max_attempts=100):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('', port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available ports found between {start_port} and {start_port + max_attempts}")

def open_browser(port, max_attempts=3, delay=1.0):
    """Open the browser to the server URL."""
    url = f'http://localhost:{port}'
    
    for attempt in range(1, max_attempts + 1):
        try:
            if webbrowser.open(url):
                logger.info(f"Opened browser to {url}")
                return True
            else:
                logger.warning(f"Failed to open browser (attempt {attempt})")
        except Exception as e:
            logger.warning(f"Failed to open browser (attempt {attempt}): {e}")
            
        if attempt < max_attempts:
            time.sleep(delay)
    
    return False

def ensure_directories():
    """Ensure required directories exist."""
    required_dirs = ['logs', 'messages', 'identity/public_keys']
    for dir_path in required_dirs:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        except Exception as e:
            logger.error(f"Failed to create directory: {dir_path} - {e}")
