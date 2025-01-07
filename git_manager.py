#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime
from github import Github
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GitManager:
    def __init__(self, repo_path):
        """Initialize GitManager with repository path"""
        self.repo_path = Path(repo_path)
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_name = os.getenv('GITHUB_REPO')
        
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        if not self.repo_name:
            raise ValueError("GITHUB_REPO environment variable is required")
            
        self.g = Github(self.github_token)
        self.repo = self.g.get_repo(self.repo_name)

    def ensure_repo_exists(self):
        """Ensure the local repository exists and is properly configured"""
        if not self.repo_path.exists():
            # Clone the repository if it doesn't exist
            self._clone_repository()
        else:
            # Ensure the remote is properly configured
            self._configure_remote()

    def _clone_repository(self):
        """Clone the repository from GitHub"""
        clone_url = f"https://{self.github_token}@github.com/{self.repo_name}.git"
        subprocess.run(["git", "clone", clone_url, str(self.repo_path)], check=True)

    def _configure_remote(self):
        """Configure the remote with authentication"""
        remote_url = f"https://{self.github_token}@github.com/{self.repo_name}.git"
        subprocess.run(["git", "remote", "set-url", "origin", remote_url], 
                      cwd=str(self.repo_path), check=True)

    def create_message_file(self, message_content, author="anonymous"):
        """Create a file containing the message"""
        # Create a timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"messages/{timestamp}_{author}.txt"
        
        # Ensure messages directory exists
        message_dir = self.repo_path / "messages"
        message_dir.mkdir(exist_ok=True)
        
        # Create the full file path
        file_path = self.repo_path / filename
        
        # Write message content to file
        file_path.write_text(message_content)
        
        return filename

    def commit_and_push_message(self, filename, author="anonymous"):
        """Commit and push a message file to GitHub"""
        try:
            # Add the file
            subprocess.run(["git", "add", filename], 
                         cwd=str(self.repo_path), check=True)
            
            # Create commit
            commit_message = f"Add message from {author}"
            subprocess.run(["git", "commit", "-m", commit_message],
                         cwd=str(self.repo_path), check=True)
            
            # Push to GitHub
            subprocess.run(["git", "push", "origin", "main"],
                         cwd=str(self.repo_path), check=True)
            
            # Get the commit hash
            result = subprocess.run(["git", "rev-parse", "HEAD"],
                                  cwd=str(self.repo_path),
                                  capture_output=True,
                                  text=True,
                                  check=True)
            
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            print(f"Error in Git operations: {e}")
            raise

    def save_message(self, message_content, author="anonymous"):
        """Save a message to a file and push it to GitHub"""
        # Ensure repository is properly set up
        self.ensure_repo_exists()
        
        # Create message file
        filename = self.create_message_file(message_content, author)
        
        # Commit and push the file
        commit_hash = self.commit_and_push_message(filename, author)
        
        return {
            'filename': filename,
            'commit_hash': commit_hash,
            'author': author,
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Test the GitManager functionality"""
    # Get the repository path from environment or use default
    repo_path = os.getenv('REPO_PATH', os.path.expanduser('~/bookchat_messages'))
    
    try:
        # Initialize GitManager
        git_manager = GitManager(repo_path)
        
        # Test message
        test_message = "This is a test message sent at " + datetime.now().isoformat()
        
        # Save the message
        result = git_manager.save_message(test_message, "test_user")
        
        print("Message saved successfully!")
        print(f"Filename: {result['filename']}")
        print(f"Commit hash: {result['commit_hash']}")
        print(f"Author: {result['author']}")
        print(f"Timestamp: {result['timestamp']}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
