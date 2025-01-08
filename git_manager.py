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
        
        if not self.token or not self.repo_name:
            raise ValueError("GITHUB_TOKEN and GITHUB_REPO environment variables must be set")
        
        # Initialize GitHub API client
        self.g = Github(self.token)
        self.repo = self.g.get_repo(self.repo_name)
        
        # Set up messages directory path
        self.messages_dir = self.repo_path / 'messages'

    def ensure_repo_exists(self):
        """Ensure the repository exists locally, clone if it doesn't."""
        if not self.repo_path.exists():
            # Clone the repository
            clone_url = f'https://{self.token}@github.com/{self.repo_name}.git'
            subprocess.run(['git', 'clone', clone_url, str(self.repo_path)], check=True)
        
        # Create messages directory if it doesn't exist
        self.messages_dir.mkdir(parents=True, exist_ok=True)

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

    def save_message(self, message_content, author, parent_id=None, date_str="2025-01-08T08:54:30-05:00"):
        """Save a message to a file, commit, and push to GitHub."""
        # Ensure repository and messages directory exist
        self.ensure_repo_exists()
        
        # Create a timestamped filename
        timestamp = datetime.fromisoformat(date_str).strftime('%Y%m%d_%H%M%S')
        filename = f'{timestamp}_{author}.txt'
        filepath = self.messages_dir / filename
        
        # Format message with metadata
        formatted_message = self.format_message(message_content, author, date_str, parent_id)
        
        # Write message to file
        filepath.write_text(formatted_message)
        
        # Stage the file (use relative path from repo root)
        relative_path = filepath.relative_to(self.repo_path)
        subprocess.run(['git', 'add', str(relative_path)], cwd=str(self.repo_path), check=True)
        
        # Commit the change
        commit_message = f'Add message from {author}'
        subprocess.run(['git', 'commit', '-m', commit_message], cwd=str(self.repo_path), check=True)
        
        # Push to GitHub
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=str(self.repo_path), check=True)
        
        # Get the commit hash
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              cwd=str(self.repo_path), 
                              capture_output=True, 
                              text=True, 
                              check=True)
        commit_hash = result.stdout.strip()
        
        return {
            'filename': filename,
            'commit_hash': commit_hash,
            'parent_id': parent_id,
            'date': date_str
        }

    def read_message(self, filename):
        """Read a message from a file and return its metadata and content."""
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
        result = manager.save_message("Test message", "test_user")
        
        # Print results
        print("Message saved successfully!")
        print(f"Filename: {result['filename']}")
        print(f"Commit hash: {result['commit_hash']}")
        print(f"Parent ID: {result['parent_id']}")
        print(f"Date: {result['date']}")
        
    except Exception as e:
        print(f"Error: {e}")
