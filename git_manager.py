#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime
from pathlib import Path
from github import Github

class GitManager:
    def __init__(self, repo_path):
        """Initialize GitManager with repository path and GitHub credentials."""
        self.repo_path = Path(repo_path)
        self.token = os.environ.get('GITHUB_TOKEN')
        self.repo_name = os.environ.get('GITHUB_REPO')
        
        # Make GitHub optional
        self.use_github = bool(self.token and self.repo_name)
        if self.use_github:
            # Initialize GitHub API client
            self.g = Github(self.token)
            self.repo = self.g.get_repo(self.repo_name)
        
        # Set up messages directory path
        self.messages_dir = self.repo_path / 'messages'
        self.messages_dir.mkdir(parents=True, exist_ok=True)

    def ensure_repo_exists(self):
        """Ensure the repository exists locally, clone if it doesn't."""
        # Create messages directory if it doesn't exist
        self.messages_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep to ensure directory is tracked
        gitkeep_path = self.messages_dir / '.gitkeep'
        if not gitkeep_path.exists():
            gitkeep_path.touch()

    def format_message(self, message_content, author, date_str, parent_id=None):
        """Format a message with metadata headers."""
        header = []
        header.append(f"Date: {date_str}")
        header.append(f"Author: {author}")
        if parent_id:
            header.append(f"Parent-Message: {parent_id}")
        
        # Join headers and add blank line before content
        return "\n".join(header) + "\n\n" + message_content

    def parse_message(self, content):
        """Parse a message file content into metadata and message."""
        lines = content.split("\n")
        metadata = {}
        message_start = 0
        
        # Parse headers
        for i, line in enumerate(lines):
            if not line.strip():  # Empty line marks end of headers
                message_start = i + 1
                break
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
        
        # Get message content
        message = "\n".join(lines[message_start:]).strip()
        
        return metadata, message

    def save_message(self, message_content, author, parent_id=None, date_str=None):
        """Save a message to a file."""
        # Ensure messages directory exists
        self.ensure_repo_exists()
        
        # Use current time if no date provided
        if date_str is None:
            date_str = datetime.now().isoformat()
        
        # Create a timestamped filename
        timestamp = datetime.fromisoformat(date_str).strftime('%Y%m%d_%H%M%S')
        filename = f'{timestamp}_{author}.txt'
        filepath = self.messages_dir / filename
        
        # Format message with metadata
        formatted_message = self.format_message(message_content, author, date_str, parent_id)
        
        # Write message to file
        filepath.write_text(formatted_message)
        
        return filename

    def read_message(self, filename):
        """Read a message from a file."""
        filepath = self.messages_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Message file not found: {filename}")
        
        content = filepath.read_text()
        return self.parse_message(content)

def main():
    """Main function for testing"""
    try:
        # Get repository path from environment
        repo_path = os.getenv('REPO_PATH')
        if not repo_path:
            raise ValueError("REPO_PATH environment variable is required")

        # Initialize GitManager
        manager = GitManager(repo_path)
        
        # Save a test message
        filename = manager.save_message("Test message", "test_user")
        
        # Print results
        print("Message saved successfully!")
        print(f"Filename: {filename}")
        
    except Exception as e:
        print(f"Error: {e}")
