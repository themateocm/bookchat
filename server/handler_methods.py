"""Request handler methods for the BookChat server."""

import json
import logging
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import re
from . import config

logger = logging.getLogger('bookchat')

def serve_file(self, path: str, content_type: str) -> None:
    """Serve a file with the specified content type."""
    try:
        with open(path, 'rb') as f:
            content = f.read()
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', content_type)
        self.end_headers()
        self.wfile.write(content)
    except Exception as e:
        self.handle_error(500, str(e))

def serve_messages(self) -> None:
    """Serve list of messages."""
    try:
        # Use storage backend to get messages
        messages = self.server.storage.get_messages()
        
        response = {
            'messages': messages,
            'messageVerificationEnabled': config.MESSAGE_VERIFICATION_ENABLED
        }
        send_json_response(self, response)
    except Exception as e:
        logger.error(f"Error serving messages: {e}")
        self.handle_error(500, str(e))

def verify_username(self) -> None:
    """Verify if username is valid and available."""
    try:
        query = parse_qs(urlparse(self.path).query)
        username = query.get('username', [''])[0]

        # Use storage backend to verify username
        if username:
            is_valid = self.server.storage.verify_username(username)
            response = {
                'valid': is_valid,
                'username': username,
                'error': None if is_valid else 'Invalid username format'
            }
        else:
            # If no username provided, return current username from session
            response = {
                'valid': True,
                'username': 'anonymous',
                'status': 'verified'
            }

        send_json_response(self, response)
    except Exception as e:
        logger.error(f"Error verifying username: {e}")
        self.handle_error(500, str(e))

def serve_status_page(self) -> None:
    """Serve server status page."""
    try:
        status = {
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'message_verification': config.MESSAGE_VERIFICATION_ENABLED
        }
        send_json_response(self, status)
    except Exception as e:
        logger.error(f"Error serving status page: {e}")
        self.handle_error(500, str(e))

def send_json_response(self, data: dict) -> None:
    """Send a JSON response."""
    try:
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    except Exception as e:
        logger.error(f"Error sending JSON response: {e}")
        self.handle_error(500, str(e))
