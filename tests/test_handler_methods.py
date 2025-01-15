"""Tests for handler methods."""

import pytest
import json
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode
from server.handler_methods import serve_messages, verify_username, serve_status_page
from pathlib import Path

def send_json_response(handler, data):
    """Helper to send JSON response."""
    response = json.dumps(data).encode('utf-8')
    handler.send_response(200)
    handler.send_header('Content-Type', 'application/json')
    handler.end_headers()
    handler.wfile.write(response)

@pytest.fixture
def mock_handler():
    """Create a mock request handler."""
    handler = MagicMock()
    handler.wfile = MagicMock()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.send_json_response = lambda data: send_json_response(handler, data)
    
    # Mock server and storage
    mock_storage = MagicMock()
    mock_storage.get_messages.return_value = ['test1.txt', 'test2.txt']
    mock_storage.verify_username.return_value = True
    
    mock_server = MagicMock()
    mock_server.storage = mock_storage
    handler.server = mock_server
    
    return handler

def test_serve_messages(mock_handler, tmp_path):
    """Test serving message list."""
    with patch('server.config.REPO_PATH', tmp_path):
        # Create test messages
        messages_dir = tmp_path / 'messages'
        messages_dir.mkdir(parents=True)
        (messages_dir / 'test1.txt').touch()
        (messages_dir / 'test2.txt').touch()
        
        serve_messages(mock_handler)
        
        # Verify response headers
        mock_handler.send_response.assert_called_with(200)
        mock_handler.send_header.assert_called_with('Content-Type', 'application/json')
        mock_handler.end_headers.assert_called_once()
        
        # Verify response content
        call_args = mock_handler.wfile.write.call_args[0][0]
        response = json.loads(call_args.decode('utf-8'))
        assert 'messages' in response
        assert len(response['messages']) == 2
        assert 'test1.txt' in response['messages']
        assert 'test2.txt' in response['messages']

def test_verify_username(mock_handler):
    """Test username verification."""
    # Create a proper query string
    query = urlencode({'username': 'test_user'})
    mock_handler.path = f'/verify_username?{query}'
    verify_username(mock_handler)
    
    # Verify response headers
    mock_handler.send_response.assert_called_with(200)
    mock_handler.send_header.assert_called_with('Content-Type', 'application/json')
    mock_handler.end_headers.assert_called_once()
    
    # Verify response content
    call_args = mock_handler.wfile.write.call_args[0][0]
    response = json.loads(call_args.decode('utf-8'))
    assert response['valid'] is True

def test_verify_username_invalid(mock_handler):
    """Test invalid username verification."""
    # Create a proper query string with invalid username
    query = urlencode({'username': 'test/user'})
    mock_handler.path = f'/verify_username?{query}'
    
    # Update mock storage to return False for invalid username
    mock_handler.server.storage.verify_username.return_value = False
    
    verify_username(mock_handler)
    
    # Verify response headers
    mock_handler.send_response.assert_called_with(200)
    mock_handler.send_header.assert_called_with('Content-Type', 'application/json')
    mock_handler.end_headers.assert_called_once()
    
    # Verify response content
    call_args = mock_handler.wfile.write.call_args[0][0]
    response = json.loads(call_args.decode('utf-8'))
    assert response['valid'] is False

def test_serve_status_page(mock_handler):
    """Test serving status page."""
    serve_status_page(mock_handler)
    
    # Verify response headers
    mock_handler.send_response.assert_called_with(200)
    mock_handler.send_header.assert_called_with('Content-Type', 'application/json')
    mock_handler.end_headers.assert_called_once()
    
    # Verify response content
    call_args = mock_handler.wfile.write.call_args[0][0]
    response = json.loads(call_args.decode('utf-8'))
    assert response['status'] == 'running'
