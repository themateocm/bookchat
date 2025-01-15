"""Test fixtures for BookChat server tests."""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock
from server.handler import ChatRequestHandler

class MockServer:
    def __init__(self):
        self.server_name = 'localhost'
        self.server_port = 8000

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        old_cwd = os.getcwd()
        os.chdir(tmpdirname)
        yield Path(tmpdirname)
        os.chdir(old_cwd)

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables."""
    env_vars = {
        'PORT': '8000',
        'REPO_PATH': '/test/path',
        'MESSAGE_VERIFICATION': 'false'
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    # Force reload of config module
    import server.config
    import importlib
    importlib.reload(server.config)
    
    return env_vars

@pytest.fixture
def server_dirs(temp_dir):
    """Create server directory structure."""
    dirs = ['logs', 'messages', 'identity/public_keys', 'static', 'templates']
    for dir_path in dirs:
        Path(temp_dir / dir_path).mkdir(parents=True, exist_ok=True)
    return temp_dir

@pytest.fixture
def mock_handler():
    """Create a mock request handler."""
    mock_request = MagicMock()
    mock_client_address = ('127.0.0.1', 12345)
    mock_server = MockServer()
    
    # Create handler without calling parent __init__
    handler = ChatRequestHandler.__new__(ChatRequestHandler)
    handler.request = mock_request
    handler.client_address = mock_client_address
    handler.server = mock_server
    
    # Mock required attributes
    handler.wfile = MagicMock()
    handler.rfile = MagicMock()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.send_json_response = MagicMock()
    
    return handler
