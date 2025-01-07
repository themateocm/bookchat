#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock, call
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from git_manager import GitManager

class TestGitManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        # Create a temporary directory for the test repository
        self.test_dir = tempfile.mkdtemp()
        
        # Set up environment variables for testing
        self.env_patcher = patch.dict('os.environ', {
            'GITHUB_TOKEN': 'test_token',
            'GITHUB_REPO': 'test_user/test_repo',
            'REPO_PATH': self.test_dir
        })
        self.env_patcher.start()
        
        # Create the messages directory
        os.makedirs(os.path.join(self.test_dir, 'messages'), exist_ok=True)

    def tearDown(self):
        """Clean up test environment after each test"""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        
        # Stop environment variable patch
        self.env_patcher.stop()

    @patch('github.Github')
    @patch('subprocess.run')
    def test_init(self, mock_run, mock_github):
        """Test GitManager initialization"""
        # Set up mock GitHub API
        mock_github_instance = mock_github.return_value
        mock_repo = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo

        # Initialize GitManager
        manager = GitManager(self.test_dir)

        # Assert GitHub API was initialized correctly
        mock_github.assert_called_once_with('test_token')
        mock_github_instance.get_repo.assert_called_once_with('test_user/test_repo')

    @patch('github.Github')
    @patch('subprocess.run')
    def test_ensure_repo_exists_with_clone(self, mock_run, mock_github):
        """Test repository cloning when directory doesn't exist"""
        # Remove the test directory to simulate non-existent repo
        shutil.rmtree(self.test_dir)

        # Set up mock GitHub API
        mock_github_instance = mock_github.return_value
        mock_repo = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo

        # Initialize and ensure repo exists
        manager = GitManager(self.test_dir)
        manager.ensure_repo_exists()

        # Assert git clone was called
        mock_run.assert_called_with(
            ['git', 'clone', f'https://test_token@github.com/test_user/test_repo.git', self.test_dir],
            check=True
        )

    @patch('github.Github')
    @patch('subprocess.run')
    def test_save_message(self, mock_run, mock_github):
        """Test saving a message to the repository"""
        # Set up mock GitHub API
        mock_github_instance = mock_github.return_value
        mock_repo = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo

        # Mock the git commands
        mock_run.return_value.stdout = "test_commit_hash"

        # Initialize and save message
        manager = GitManager(self.test_dir)
        result = manager.save_message("Test message", "test_author")

        # Assert the message file was created
        message_files = list(Path(self.test_dir).glob('messages/*_test_author.txt'))
        self.assertEqual(len(message_files), 1)
        
        # Assert the message content was written correctly
        with open(message_files[0], 'r') as f:
            content = f.read()
        self.assertEqual(content, "Test message")

        # Assert git commands were called in correct order
        expected_calls = [
            call(['git', 'add', message_files[0].name], cwd=self.test_dir, check=True),
            call(['git', 'commit', '-m', 'Add message from test_author'], cwd=self.test_dir, check=True),
            call(['git', 'push', 'origin', 'main'], cwd=self.test_dir, check=True),
            call(['git', 'rev-parse', 'HEAD'], cwd=self.test_dir, capture_output=True, text=True, check=True)
        ]
        mock_run.assert_has_calls(expected_calls)

    @patch('github.Github')
    @patch('subprocess.run')
    def test_error_handling(self, mock_run, mock_github):
        """Test error handling when git operations fail"""
        # Set up mock GitHub API
        mock_github_instance = mock_github.return_value
        mock_repo = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo

        # Make git push command fail
        mock_run.side_effect = [
            None,  # git add succeeds
            None,  # git commit succeeds
            Exception("Push failed"),  # git push fails
        ]

        # Initialize GitManager
        manager = GitManager(self.test_dir)

        # Assert that save_message raises the exception
        with self.assertRaises(Exception):
            manager.save_message("Test message", "test_author")

if __name__ == '__main__':
    unittest.main()
