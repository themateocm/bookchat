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
        self.should_sync_to_github = os.environ.get('SYNC_TO_GITHUB', '').lower() == 'true'
        
        # Make GitHub optional
        self.use_github = bool(self.token and self.repo_name and self.should_sync_to_github)
        if self.use_github:
            print("GitHub synchronization enabled")
            # Initialize GitHub API client
            self.g = Github(self.token)
            self.repo = self.g.get_repo(self.repo_name)
            
            # Initialize git repository if needed
            if not (self.repo_path / '.git').exists():
                self.init_git_repo()
        else:
            print("GitHub synchronization disabled")
        
        # Set up messages directory path
        self.messages_dir = self.repo_path / 'messages'
        self.messages_dir.mkdir(parents=True, exist_ok=True)

    def init_git_repo(self):
        """Initialize git repository and set up remote."""
        if not self.use_github:
            return

        # Initialize git repository
        subprocess.run(['git', 'init'], cwd=str(self.repo_path), check=True)
        
        # Configure git
        subprocess.run(['git', 'config', 'user.name', 'BookChat Bot'], cwd=str(self.repo_path), check=True)
        subprocess.run(['git', 'config', 'user.email', 'bot@bookchat.local'], cwd=str(self.repo_path), check=True)
        
        # Add GitHub remote
        remote_url = f'https://{self.token}@github.com/{self.repo_name}.git'
        subprocess.run(['git', 'remote', 'add', 'origin', remote_url], cwd=str(self.repo_path), check=True)
        
        # Pull existing content
        try:
            subprocess.run(['git', 'pull', 'origin', 'main'], cwd=str(self.repo_path), check=True)
        except subprocess.CalledProcessError:
            # If pull fails, create and push initial commit
            subprocess.run(['git', 'checkout', '-b', 'main'], cwd=str(self.repo_path), check=True)

    def sync_changes_to_github(self, filepath, author="BookChat Bot"):
        """Sync changes to GitHub."""
        if not self.use_github:
            return

        try:
            # Stage the file
            relative_path = filepath.relative_to(self.repo_path)
            subprocess.run(['git', 'add', str(relative_path)], cwd=str(self.repo_path), check=True)
            
            # Commit the change
            commit_message = f'Add message from {author}'
            subprocess.run(['git', 'commit', '-m', commit_message], cwd=str(self.repo_path), check=True)
            
            # Push to GitHub
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=str(self.repo_path), check=True)
            print(f"Successfully synced {relative_path} to GitHub")
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to sync to GitHub: {e}")
            # Continue without GitHub sync - don't raise the error

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
        """Save a message to a file and optionally sync to GitHub."""
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
        
        # Sync to GitHub if enabled
        if self.use_github:
            self.sync_changes_to_github(filepath, author)
        
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
