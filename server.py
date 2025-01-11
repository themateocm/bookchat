#!/usr/bin/env python3

import http.server
import socketserver
import json
import os
import pathlib
import logging
import traceback
import re
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from http import HTTPStatus
from dotenv import load_dotenv
from storage.factory import create_storage

# Configure logging with a more detailed format and multiple levels
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
console_format = '%(asctime)s - %(levelname)s - %(message)s'  # Simpler format for console

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Remove all existing handlers
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)

# Configure file handlers for different log levels
debug_handler = logging.FileHandler('logs/debug.log')
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(logging.Formatter(log_format))

info_handler = logging.FileHandler('logs/info.log')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(logging.Formatter(log_format))

error_handler = logging.FileHandler('logs/error.log')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter(log_format))

# Configure console handler with simpler format and WARNING level by default
console_handler = logging.StreamHandler()
console_level = logging.DEBUG if os.getenv('BOOKCHAT_DEBUG') else logging.WARNING
console_handler.setLevel(console_level)
console_handler.setFormatter(logging.Formatter(console_format))

# Add all handlers to root logger
root.addHandler(debug_handler)
root.addHandler(info_handler)
root.addHandler(error_handler)
root.addHandler(console_handler)

# Set root logger to lowest level (DEBUG) to catch all logs
root.setLevel(logging.DEBUG)

# Create a logger specific to this application
logger = logging.getLogger('bookchat')

# Log initial debug state
logger.info(f"Console logging level: {logging.getLevelName(console_level)}")
if console_level == logging.DEBUG:
    logger.info("Debug logging enabled via BOOKCHAT_DEBUG environment variable")

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv('PORT', 8000))
REPO_PATH = os.getenv('REPO_PATH', os.path.abspath(os.path.dirname(__file__)))

# Initialize storage backend
logger.info(f"Initializing storage backend with repo path: {REPO_PATH}")
storage = create_storage(storage_type='git', repo_path=REPO_PATH)

# Log all loggers and their levels
logger.debug("Current logger levels:")
for name in logging.root.manager.loggerDict:
    log = logging.getLogger(name)
    logger.debug(f"Logger {name}: level={logging.getLevelName(log.level)}, handlers={log.handlers}, propagate={log.propagate}")

storage.init_storage()

class ChatRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for the chat application"""

    def __init__(self, *args, **kwargs):
        # Set the directory for serving static files
        logger.debug("Initializing ChatRequestHandler")
        super().__init__(*args, directory="static", **kwargs)

    def handle_error(self, error):
        """Handle errors and return appropriate response"""
        error_msg = f"Error occurred: {str(error)}"
        logger.error(error_msg, exc_info=True)  # Include full stack trace
        error_response = {
            'error': str(error),
            'traceback': traceback.format_exc()
        }
        self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urlparse(self.path)
            client_address = self.client_address[0]
            logger.info(f"GET request from {client_address} to {parsed_path.path}")
            
            if parsed_path.path == '/':
                logger.debug("Serving main page")
                self.serve_file('templates/index.html', 'text/html')
            elif parsed_path.path.startswith('/static/'):
                # Handle static files directly
                try:
                    # Remove the leading '/static/' to get the relative path
                    file_path = parsed_path.path[8:]  # len('/static/') == 8
                    logger.debug(f"Serving static file: {file_path}")
                    with open(os.path.join('static', file_path), 'rb') as f:
                        content = f.read()
                        self.send_response(HTTPStatus.OK)
                        content_type = 'text/css' if file_path.endswith('.css') else 'application/javascript'
                        self.send_header('Content-Type', content_type)
                        self.send_header('Content-Length', str(len(content)))
                        self.end_headers()
                        self.wfile.write(content)
                        logger.debug(f"Successfully served static file: {file_path}")
                except FileNotFoundError:
                    logger.error(f"Static file not found: {file_path}")
                    self.send_error(HTTPStatus.NOT_FOUND)
            elif parsed_path.path == '/messages':
                logger.debug("Handling messages request")
                self.serve_messages()
            elif parsed_path.path == '/verify_username':
                logger.debug("Handling username verification")
                self.verify_username()
            else:
                logger.info(f"Attempting to serve unknown path: {parsed_path.path}")
                super().do_GET()
        except Exception as e:
            logger.error(f"Error in GET request handler", exc_info=True)
            self.handle_error(e)

    def do_POST(self):
        """Handle POST requests"""
        try:
            parsed_path = urlparse(self.path)
            client_address = self.client_address[0]
            logger.info(f"POST request from {client_address} to {parsed_path.path}")
            
            # Handle messages
            if parsed_path.path == '/messages':
                # Get content length
                content_length = int(self.headers.get('Content-Length', 0))
                logger.debug(f"Content length: {content_length}")
                
                # Read and parse the body
                body = self.rfile.read(content_length).decode('utf-8')
                logger.debug(f"Received message body: {body[:200]}...")  # Log first 200 chars to avoid huge logs
                
                # Handle both JSON and form data
                if self.headers.get('Content-Type') == 'application/json':
                    data = json.loads(body)
                    content = data.get('content')
                    author = data.get('author', 'anonymous')
                    logger.info(f"Processing JSON message from {author}: {content}")
                else:
                    # Parse form data
                    form_data = parse_qs(body)
                    content = form_data.get('content', [''])[0]
                    author = 'anonymous'  # No-JS always uses anonymous
                    logger.info(f"Processing form message from {author}: {content}")
                
                # Save the message
                logger.debug("Attempting to save message...")
                try:
                    success = storage.save_message(author, content, datetime.now())
                    logger.info(f"Message save {'successful' if success else 'failed'}")
                except Exception as e:
                    logger.error(f"Exception while saving message: {e}\n{traceback.format_exc()}")
                    success = False
                
                if success:
                    # Get the latest messages to return the new message
                    messages = storage.get_messages(limit=1)
                    new_message = messages[0] if messages else None
                    logger.info(f"Retrieved new message: {new_message}")
                    
                    # Return response based on content type
                    if self.headers.get('Content-Type') == 'application/json':
                        self.send_response(HTTPStatus.OK)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(new_message).encode('utf-8'))
                    else:
                        # Redirect back to home page for form submission
                        self.send_response(HTTPStatus.FOUND)
                        self.send_header('Location', '/')
                        self.end_headers()
                else:
                    raise Exception("Failed to save message")
            
            # Handle username changes
            elif parsed_path.path == '/username':
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                logger.debug(f"Username change request: {body}")
                
                # Parse form data
                form_data = parse_qs(body)
                new_username = form_data.get('new_username', [''])[0]
                
                if new_username:
                    # Create username change message
                    content = json.dumps({
                        'old_username': 'anonymous',
                        'new_username': new_username,
                        'type': 'username_change'
                    })
                    storage.save_message('system', content, datetime.now())
                
                # Redirect back to home page
                self.send_response(HTTPStatus.FOUND)
                self.send_header('Location', '/')
                self.end_headers()
            
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error in POST request handler", exc_info=True)
            self.handle_error(e)

    def serve_file(self, filepath, content_type):
        """Helper method to serve a file with specified content type"""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            self.send_error(HTTPStatus.NOT_FOUND)
        except Exception as e:
            logger.error(f"Error serving file {filepath}: {e}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)

    def serve_messages(self):
        """Helper method to serve messages as JSON"""
        try:
            messages = storage.get_messages()
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(messages).encode('utf-8'))
        except Exception as e:
            logger.error(f"Error serving messages: {e}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def verify_username(self):
        """Helper method to verify username"""
        try:
            # For GET requests, just return anonymous
            if self.command == 'GET':
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'username': 'anonymous',
                    'valid': True,
                    'status': 'verified'
                }).encode('utf-8'))
                return
            
            # For POST requests, validate the username
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            
            # Get username from request
            username = data.get('username', '')
            logger.debug(f"Verifying username: {username}")
            
            # Check if username is valid (3-20 characters, alphanumeric and underscores only)
            is_valid = bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))
            
            # Send response
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'username': username,
                'valid': is_valid,
                'status': 'verified'
            }).encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verifying username: {e}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

def find_available_port(start_port=8000, max_attempts=100):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socketserver.TCPServer(("", port), None) as s:
                s.server_close()
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

def open_browser(port):
    """Open the browser to the application URL"""
    try:
        import platform
        url = f'http://localhost:{port}'
        
        if platform.system() == 'Linux':
            # Check if running in WSL
            with open('/proc/version', 'r') as f:
                if 'microsoft' in f.read().lower():
                    # In WSL, use powershell.exe to start browser
                    os.system(f'powershell.exe -c "Start-Process \'{url}\'"')
                else:
                    # Pure Linux
                    os.system(f'xdg-open {url}')
        elif platform.system() == 'Windows':
            os.system(f'start {url}')
        elif platform.system() == 'Darwin':
            os.system(f'open {url}')
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")

def main():
    """Start the server"""
    try:
        port = find_available_port()
        logger.info(f"Found available port: {port}")
        
        # Create and start the server
        with socketserver.TCPServer(("", port), ChatRequestHandler) as httpd:
            logger.info(f"Server running on port {port}...")
            
            # Open the browser
            open_browser(port)
            
            # Start serving
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise

if __name__ == "__main__":
    main()
