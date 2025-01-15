#!/usr/bin/env python3

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime
from github import Github
from github.Repository import Repository

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from git_manager import GitManager

TEST_DATE = "2025-01-08T08:54:30-05:00"

class TestGitManager:
    """Test cases for GitManager class."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test environment."""
        self.test_dir = tmp_path
        self.messages_dir = self.test_dir / 'messages'
        self.messages_dir.mkdir(parents=True)
        
        # Create identity directories
        (self.test_dir / 'identity' / 'public_keys').mkdir(parents=True)
        (self.test_dir / 'identity' / 'private_keys').mkdir(parents=True)
        (self.test_dir / 'keys').mkdir(parents=True)

    @patch('git_manager.Github')
    @patch('subprocess.run')
    def test_init(self, mock_run, mock_github):
        """Test initializing git manager."""
        # Mock git commands
        def mock_subprocess(*args, **kwargs):
            if args[0][0] == 'openssl':
                return MagicMock(stdout=b'test_signature')
            return MagicMock(stdout=b'test_commit_hash')
        mock_run.side_effect = mock_subprocess
        
        manager = GitManager(str(self.test_dir))
        assert isinstance(manager, GitManager)
        
    @patch('git_manager.Github')
    @patch('subprocess.run')
    def test_save_message(self, mock_run, mock_github):
        """Test saving a message to the repository."""
        # Set up mock GitHub API
        mock_github_instance = MagicMock()
        mock_github.return_value = mock_github_instance
        
        mock_repo = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        
        # Mock git commands
        def mock_subprocess(*args, **kwargs):
            if args[0][0] == 'openssl':
                return MagicMock(stdout=b'test_signature')
            return MagicMock(stdout=b'test_commit_hash')
        
        mock_run.side_effect = mock_subprocess
        
        # Initialize and save message
        manager = GitManager(str(self.test_dir))
        result = manager.save_message("Test message", "test_author", date_str=TEST_DATE)
        
        # Assert the message file was created
        message_files = list(Path(self.test_dir).glob('messages/*_test_author.txt'))
        assert len(message_files) == 1
        
        # Assert the message content was written correctly with metadata
        with open(message_files[0], 'r') as f:
            content = f.read()
        
        expected_content = (
            "Test message\n\n"
            "-- \n"
            "Author: test_author\n"
            f"Date: {TEST_DATE}\n"
            "Public-Key: identity/public_keys/test_author.pub\n"
            "Signature: 746573745f7369676e6174757265"
        )
        assert content.strip() == expected_content
        
    @patch('git_manager.Github')
    @patch('subprocess.run')
    def test_save_message_with_parent(self, mock_run, mock_github):
        """Test saving a message with a parent ID."""
        # Set up mock GitHub API
        mock_github_instance = MagicMock()
        mock_github.return_value = mock_github_instance
        
        mock_repo = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        
        # Mock git commands
        def mock_subprocess(*args, **kwargs):
            if args[0][0] == 'openssl':
                return MagicMock(stdout=b'test_signature')
            return MagicMock(stdout=b'test_commit_hash')
        
        mock_run.side_effect = mock_subprocess
        
        # Create parent message
        parent_id = "abc123.txt"
        parent_path = self.test_dir / "messages" / parent_id
        parent_path.parent.mkdir(parents=True, exist_ok=True)
        parent_path.write_text("Parent message content")

        # Initialize and save message with parent
        manager = GitManager(str(self.test_dir))
        result = manager.save_message("Test reply", "test_author", parent_id=parent_id, date_str=TEST_DATE)
        
        # Verify message was saved
        assert result is not None
        assert "Test reply" in result["content"]
        assert parent_id == result["parent_id"]
        
    @patch('git_manager.Github')
    @patch('subprocess.run')
    def test_read_message(self, mock_run, mock_github):
        """Test reading a message from the repository."""
        # Create a test message file
        message_file = self.messages_dir / 'test_message.txt'
        message_content = (
            "Test message\n\n"
            "-- \n"
            "Author: test_author\n"
            f"Date: {TEST_DATE}\n"
            "Public-Key: identity/public_keys/test_author.pub\n"
            "Signature: 746573745f7369676e6174757265"
        )
        message_file.write_text(message_content)
        
        # Mock git commands
        def mock_subprocess(*args, **kwargs):
            if args[0][0] == 'openssl':
                return MagicMock(stdout=b'test_signature')
            return MagicMock(stdout=b'test_commit_hash')
        mock_run.side_effect = mock_subprocess
        
        # Initialize manager and read message
        manager = GitManager(str(self.test_dir))
        result = manager.read_message('test_message.txt')
        
        # Verify message content
        assert result['content'] == 'Test message'
        assert result['author'] == 'test_author'
        assert result['createdAt'] == TEST_DATE
        assert result['signed'] is True
        assert result['verified'] == 'false'  # No public key available
        
    @patch('git_manager.Github')
    @patch('subprocess.run')
    def test_ensure_repo_exists_with_clone(self, mock_run, mock_github):
        """Test repository initialization with cloning."""
        # Set up mock GitHub API
        mock_github_instance = MagicMock()
        mock_github.return_value = mock_github_instance
        
        mock_repo = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        
        # Remove test directory to simulate fresh clone
        import shutil
        shutil.rmtree(self.test_dir)
        
        # Mock git commands
        def mock_subprocess(*args, **kwargs):
            # Create directories when git init is called
            if args[0][0] == 'git' and args[0][1] == 'init':
                os.makedirs(self.test_dir / 'messages', exist_ok=True)
                os.makedirs(self.test_dir / 'identity' / 'public_keys', exist_ok=True)
                os.makedirs(self.test_dir / 'identity' / 'private_keys', exist_ok=True)
                os.makedirs(self.test_dir / 'keys', exist_ok=True)
            elif args[0][0] == 'openssl':
                return MagicMock(stdout=b'test_signature')
            return MagicMock(stdout=b'test_commit_hash')
        
        mock_run.side_effect = mock_subprocess
        
        # Initialize manager (should trigger init)
        with patch('os.environ', {'GITHUB_TOKEN': 'test', 'GITHUB_REPO': 'test/test', 'SYNC_TO_GITHUB': 'true'}):
            manager = GitManager(str(self.test_dir))
        
        # Verify directory was created
        assert self.test_dir.exists()
        assert self.messages_dir.exists()
        assert (self.test_dir / 'identity' / 'public_keys').exists()
        assert (self.test_dir / 'identity' / 'private_keys').exists()
        assert (self.test_dir / 'keys').exists()
        
    def test_error_handling(self):
        """Test error handling in git manager."""
        # Initialize without GitHub
        with patch('os.environ', {}):
            manager = GitManager(str(self.test_dir))
        
        # Test reading non-existent message
        result = manager.read_message('nonexistent.txt')
        assert result is None
            
        # Test saving message with invalid parent
        with pytest.raises(ValueError):
            manager.save_message("Test message", "test_author", parent_id="nonexistent.txt")

if __name__ == '__main__':
    pytest.main()
