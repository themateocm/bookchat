#!/usr/bin/env python3

import http.server
import socketserver
import json
import os
from urllib.parse import parse_qs, urlparse
from http import HTTPStatus
from dotenv import load_dotenv
from git_manager import GitManager

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv('PORT', 8000))
REPO_PATH = os.getenv('REPO_PATH', os.path.abspath(os.path.dirname(__file__)))

# Initialize GitManager
git_manager = GitManager(REPO_PATH)
git_manager.ensure_repo_exists()

class ChatRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for the chat application"""

    def __init__(self, *args, **kwargs):
        # Set the directory for serving static files
        super().__init__(*args, directory="static", **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Serve the main page
            self.serve_file('templates/index.html', 'text/html')
        elif parsed_path.path.startswith('/static/'):
            # Handle static files directly
            try:
                # Remove the leading '/static/' to get the relative path
                file_path = parsed_path.path[8:]  # len('/static/') == 8
                with open(os.path.join('static', file_path), 'rb') as f:
                    content = f.read()
                    self.send_response(HTTPStatus.OK)
                    content_type = 'text/css' if file_path.endswith('.css') else 'application/javascript'
                    self.send_header('Content-Type', content_type)
                    self.send_header('Content-Length', str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
        elif parsed_path.path == '/messages':
            # Return all messages as JSON
            self.serve_messages()
        else:
            # Try to serve static files
            super().do_GET()

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/messages':
            # Handle new message submission
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                message_data = json.loads(post_data.decode('utf-8'))
                filename = self.save_message(message_data)
                
                # Send success response
                self.send_response(HTTPStatus.CREATED)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'id': filename}).encode('utf-8'))
            except Exception as e:
                # Send error response
                self.send_error(HTTPStatus.BAD_REQUEST, str(e))
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

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
            self.send_error(HTTPStatus.NOT_FOUND)

    def serve_messages(self):
        """Serve all messages from the messages directory as JSON"""
        try:
            messages = []
            if os.path.exists(git_manager.messages_dir):
                message_files = sorted(os.listdir(git_manager.messages_dir))
                for filename in message_files:
                    if filename != '.gitkeep':
                        try:
                            metadata, content = git_manager.read_message(filename)
                            messages.append({
                                'id': filename,
                                'content': content,
                                'author': metadata.get('Author', 'anonymous'),
                                'date': metadata.get('Date')
                            })
                        except Exception as e:
                            print(f"Error reading message {filename}: {e}")
            
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(messages).encode('utf-8'))
        except Exception as e:
            print(f"Error serving messages: {e}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def save_message(self, message_data):
        """Save a new message using GitManager"""
        if 'content' not in message_data:
            raise ValueError('Message content is required')

        try:
            # Save the message using GitManager
            filename = git_manager.save_message(
                message_data['content'],
                message_data.get('author', 'anonymous')
            )
            return filename
        except Exception as e:
            print(f"Error saving message: {e}")
            raise

def find_available_port(start_port=8000, max_attempts=100):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socketserver.TCPServer(("", port), None) as s:
                # If we can bind to the port, it's available
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

def open_browser(port):
    """Open Windows Chrome browser through WSL"""
    try:
        os.system(f'cmd.exe /C start chrome http://localhost:{port}')
    except Exception as e:
        print(f"Failed to open browser: {e}")

def main():
    """Start the server"""
    global git_manager

    # Find an available port
    port = find_available_port(PORT)
    if port != PORT:
        print(f"Port {PORT} was in use, using port {port} instead")

    handler = ChatRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"Repository path: {REPO_PATH}")
            print(f"Messages directory: {git_manager.messages_dir}")
            print(f"Server running at http://localhost:{port}")
            
            # Open browser after server starts
            open_browser(port)
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    main()
